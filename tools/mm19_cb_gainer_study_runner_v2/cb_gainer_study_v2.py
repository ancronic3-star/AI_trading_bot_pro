import sys, os, json, time, math, csv
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

UA = "mm19-cb-gainer-study-v2"
BASE = "https://api.exchange.coinbase.com"

def fetch_json(url, timeout=40, retries=5, backoff=1.2):
    last=None
    for attempt in range(retries):
        try:
            req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urlopen(req, timeout=timeout) as resp:
                data = resp.read().decode("utf-8")
            return json.loads(data)
        except HTTPError as e:
            last=e
            # rate limit or transient
            wait = backoff ** attempt
            if getattr(e, "code", None) in (429, 500, 502, 503, 504):
                time.sleep(min(15.0, wait))
                continue
            raise
        except URLError as e:
            last=e
            time.sleep(min(15.0, backoff ** attempt))
            continue
        except Exception as e:
            last=e
            time.sleep(min(15.0, backoff ** attempt))
            continue
    raise last if last else RuntimeError("fetch_json failed")

def iso(dt):
    return dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")

def candles(pid, start_dt, end_dt, gran=86400, sleep=0.10):
    qs = {"start": iso(start_dt), "end": iso(end_dt), "granularity": str(gran)}
    url = f"{BASE}/products/{pid}/candles?{urlencode(qs)}"
    try:
        data = fetch_json(url)
    finally:
        time.sleep(sleep)
    if not isinstance(data, list):
        return []
    rows=[]
    for r in data:
        try:
            # [ time, low, high, open, close, volume ]
            rows.append([int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])])
        except:
            pass
    return rows

def fetch_candles_days(pid, days, gran=86400):
    now = datetime.now(timezone.utc)
    end = now
    start = now - timedelta(days=days+2)
    chunk = 280  # keep under Coinbase ~300 candle limit
    rows=[]
    cur = start
    while cur < end:
        cur_end = min(cur + timedelta(days=chunk), end)
        part = candles(pid, cur, cur_end, gran=gran)
        rows.extend(part)
        cur = cur_end
    # Dedup by timestamp
    ded={}
    for r in rows:
        ded[r[0]] = r
    out = [ded[k] for k in sorted(ded.keys())]
    return out

def pct(a,b):
    if a is None or b is None or a == 0:
        return None
    return (b-a)/a*100.0

def write_csv(path, rows, fieldnames):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)

def book_metrics(pid, levels=5):
    url=f"{BASE}/products/{pid}/book?level=2"
    data = fetch_json(url)
    bids=data.get("bids") or []
    asks=data.get("asks") or []
    if not bids or not asks:
        return None
    def take(side):
        out=[]
        for row in side[:levels]:
            try:
                price=float(row[0]); size=float(row[1])
                out.append((price,size))
            except:
                pass
        return out
    b=take(bids); a=take(asks)
    if not b or not a:
        return None
    bb=b[0][0]; ba=a[0][0]
    mid=(bb+ba)/2.0
    spr_pct=(ba-bb)/mid*100.0 if mid>0 else None
    spr_bps=spr_pct*100.0 if spr_pct is not None else None
    bid_usd=sum(px*sz for px,sz in b)
    ask_usd=sum(px*sz for px,sz in a)
    topbook=bid_usd+ask_usd
    pressure=(bid_usd/(bid_usd+ask_usd)) if (bid_usd+ask_usd)>0 else None
    return spr_pct, spr_bps, topbook, pressure

def quantile(xs,q):
    xs=[x for x in xs if x is not None]
    if not xs:
        return None
    xs=sorted(xs)
    if q<=0: return xs[0]
    if q>=1: return xs[-1]
    i=(len(xs)-1)*q
    lo=int(math.floor(i)); hi=int(math.ceil(i))
    if lo==hi: return xs[lo]
    return xs[lo]*(hi-i)+xs[hi]*(i-lo)

def safe_float(x):
    try:
        return float(x)
    except:
        return None

def horizon_pct_from_series(rows, days):
    # rows sorted ascending by timestamp; use close (index 4)
    if len(rows) < 2:
        return None
    end_ts = rows[-1][0]
    start_cut = end_ts - int(days*86400)
    start_close = None
    end_close = rows[-1][4]
    for r in rows:
        if r[0] >= start_cut:
            start_close = r[4]
            break
    if start_close is None:
        start_close = rows[0][4]
    return pct(start_close, end_close)

def main():
    if len(sys.argv) < 2:
        print("Usage: cb_gainer_study_v2.py OUT_DIR")
        sys.exit(2)
    out_dir=sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)

    print("MM19 Coinbase Gainer Study v2", datetime.now(timezone.utc).isoformat())
    print("OUT", out_dir)

    # Load bot cfg (for reference)
    ROOT=r"C:\ai_trading_bot_koko"
    bot_cfg={}
    for p in [os.path.join(ROOT,"managers","config_manager","run_settings.json"),
              os.path.join(ROOT,"logs","run_active.json")]:
        if os.path.exists(p):
            try:
                with open(p,"r",encoding="utf-8") as f:
                    j=json.load(f)
                if isinstance(j,dict) and "settings" in j and isinstance(j["settings"],dict):
                    bot_cfg.update(j["settings"])
                elif isinstance(j,dict):
                    bot_cfg.update(j)
            except:
                pass

    horizons=[("14d",14),("60d",60),("180d",180),("365d",365),("540d",540),("730d",730)]

    products = fetch_json(f"{BASE}/products")
    usd=[]
    for p in products:
        try:
            if p.get("quote_currency")=="USD" and p.get("status")=="online":
                usd.append(p.get("id"))
        except:
            pass

    with open(os.path.join(out_dir, "coinbase_products_usd.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(usd)))

    # stats volume ranking (scan cap)
    stats=[]
    scan_cap=400
    for i,pid in enumerate(usd[:scan_cap], start=1):
        try:
            s=fetch_json(f"{BASE}/products/{pid}/stats")
            vol=float(s.get("volume") or 0.0)
            stats.append((vol, pid))
        except:
            continue
        if i % 50 == 0:
            print(f"stats_progress {i}/{scan_cap}")
        time.sleep(0.06)

    stats.sort(key=lambda t: t[0], reverse=True)
    universe=[pid for _,pid in stats[:250]]
    with open(os.path.join(out_dir,"universe_used.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(universe))

    returns={tag:[] for tag,_ in horizons}
    failures=[]
    for idx,pid in enumerate(universe, start=1):
        try:
            series = fetch_candles_days(pid, 730)
            if len(series) < 10:
                failures.append(pid)
                continue
            ok_any=False
            for tag,days in horizons:
                r=horizon_pct_from_series(series, days)
                if r is not None:
                    ok_any=True
                returns[tag].append({"product_id":pid, "pct":r})
        except:
            failures.append(pid)
        if idx % 10 == 0:
            print(f"candles_progress {idx}/{len(universe)}")

    with open(os.path.join(out_dir,"candles_failures.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(failures))

    topN=60
    top_sets={}
    for tag,_ in horizons:
        rows=[r for r in returns[tag] if r["pct"] is not None]
        rows.sort(key=lambda x: x["pct"], reverse=True)
        ranked=[]
        for i,r in enumerate(rows[:topN], start=1):
            ranked.append({"rank":i, "product_id":r["product_id"], "pct": round(r["pct"],4)})
        top_sets[tag]=set([r["product_id"] for r in ranked])
        write_csv(os.path.join(out_dir,f"cb_gainers_{tag}.csv"), ranked, ["rank","product_id","pct"])

    # persistence
    counts={}
    for tag,_ in horizons:
        for pid in top_sets[tag]:
            counts[pid]=counts.get(pid,0)+1
    persist=[]
    for pid,c in sorted(counts.items(), key=lambda kv: (-kv[1],kv[0])):
        present=[tag for tag,_ in horizons if pid in top_sets[tag]]
        persist.append({"product_id":pid, "horizons_in_top": ",".join(present), "count":c})
    write_csv(os.path.join(out_dir,"cb_gainers_persistence.csv"), persist, ["product_id","horizons_in_top","count"])

    # microstructure for union
    union=set()
    for tag,_ in horizons:
        union |= top_sets[tag]
    micro=[]
    for i,pid in enumerate(sorted(list(union))[:120], start=1):
        try:
            m=book_metrics(pid, levels=5)
            if not m:
                continue
            spr_pct,spr_bps,topbook,pressure=m
            micro.append({"product_id":pid,"spread_pct":spr_pct,"spread_bps":spr_bps,"topbook_usd":topbook,"pressure":pressure})
        except:
            pass
        if i % 25 == 0:
            print(f"book_progress {i}/120")
        time.sleep(0.12)

    write_csv(os.path.join(out_dir,"coinbase_microstructure_gainers.csv"), micro,
              ["product_id","spread_pct","spread_bps","topbook_usd","pressure"])

    spreads=[r["spread_pct"] for r in micro if r.get("spread_pct") is not None]
    topbooks=[r["topbook_usd"] for r in micro if r.get("topbook_usd") is not None]
    pressures=[r["pressure"] for r in micro if r.get("pressure") is not None]

    rec_spread=quantile(spreads, 0.80)
    rec_topbook=quantile(topbooks, 0.20)
    rec_press=quantile(pressures, 0.20)

    if rec_spread is not None: rec_spread=round(rec_spread,3)
    if rec_topbook is not None: rec_topbook=round(rec_topbook,2)
    if rec_press is not None: rec_press=round(rec_press,3)

    rec={
        "TARGET_MODE":"GAINER_CATCH_CB",
        "UNIVERSE_SOURCE":"Coinbase USD online, top 250 by /stats volume from first 400 scanned",
        "HORIZONS_DAYS": {tag:days for tag,days in horizons},
        "CURRENT": {
            "GAINERS_ONLY": bool(bot_cfg.get("GAINERS_ONLY", True)),
            "SMART_BUY": bool(bot_cfg.get("SMART_BUY", True)),
            "MIN_24H_PCT": safe_float(bot_cfg.get("MIN_24H_PCT", None)),
            "MIN_TOPBOOK_USD": safe_float(bot_cfg.get("MIN_TOPBOOK_USD", None)),
            "MAX_SPREAD_PCT": safe_float(bot_cfg.get("MAX_SPREAD_PCT", None)),
            "BOOK_PRESSURE_MIN": safe_float(bot_cfg.get("BOOK_PRESSURE_MIN", None)),
            "MIN_DMID_BPS": safe_float(bot_cfg.get("MIN_DMID_BPS", None)),
        },
        "RECOMMENDED": {
            "GAINERS_ONLY": True,
            "RANK_BY_24H_PCT": True,
            "MIN_24H_PCT": 1.0,
            "SMART_BUY": False,
            "MAX_SPREAD_PCT": rec_spread if rec_spread is not None else 0.9,
            "MIN_TOPBOOK_USD": rec_topbook if rec_topbook is not None else 150.0,
            "BOOK_PRESSURE_MIN": rec_press if rec_press is not None else 0.25,
            "MIN_DMID_BPS": -5.0
        }
    }
    with open(os.path.join(out_dir,"recommended_settings_from_cb_gainers.json"),"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=2)

    with open(os.path.join(out_dir,"apply_in_menu.txt"),"w",encoding="utf-8") as f:
        f.write("E Settings editor -> set the following:\n")
        f.write("  3 SMART_BUY = False\n")
        f.write("  4 GAINERS_ONLY = True\n")
        f.write("  5 RANK_BY_24H_PCT = True\n")
        f.write(f"  9 MIN_TOPBOOK_USD = {rec['RECOMMENDED']['MIN_TOPBOOK_USD']}\n")
        f.write(f" 10 MAX_SPREAD_PCT = {rec['RECOMMENDED']['MAX_SPREAD_PCT']}\n")
        f.write(" 31 MIN_DMID_BPS = -5.0\n")
        f.write(f" 32 BOOK_PRESSURE_MIN = {rec['RECOMMENDED']['BOOK_PRESSURE_MIN']}\n")
        f.write(" 34 MIN_24H_PCT = 1.0\n")

    with open(os.path.join(out_dir,"SUMMARY.txt"),"w",encoding="utf-8") as f:
        f.write("Universe size: %d\n" % len(universe))
        f.write("Failures: %d\n" % len(failures))
        f.write("Micro rows: %d\n" % len(micro))
        f.write("Recommended gates derived from gainers microstructure:\n")
        f.write(json.dumps(rec["RECOMMENDED"], indent=2))

    print("DONE")

if __name__ == "__main__":
    main()
