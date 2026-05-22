import sys, os, json, time, math, csv
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode
from urllib.error import HTTPError, URLError

UA="mm19-cb-gainer-study-v3"
BASE="https://api.exchange.coinbase.com"

def fetch_json(url, timeout=40, retries=6, backoff=1.35):
    last=None
    for attempt in range(retries):
        try:
            req=Request(url, headers={"User-Agent":UA, "Accept":"application/json"})
            with urlopen(req, timeout=timeout) as resp:
                data=resp.read().decode("utf-8")
            return json.loads(data)
        except HTTPError as e:
            last=e
            code=getattr(e,"code",None)
            wait=min(20.0, (backoff**attempt))
            if code in (429,500,502,503,504):
                time.sleep(wait)
                continue
            raise
        except URLError as e:
            last=e
            time.sleep(min(20.0, (backoff**attempt)))
            continue
    raise last

def write_csv(path, rows, fields):
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows: w.writerow(r)

def safe_f(x):
    try: return float(x)
    except: return None

def quantile(xs, q):
    xs=[x for x in xs if x is not None]
    if not xs: return None
    xs=sorted(xs)
    if q<=0: return xs[0]
    if q>=1: return xs[-1]
    i=(len(xs)-1)*q
    lo=int(math.floor(i)); hi=int(math.ceil(i))
    if lo==hi: return xs[lo]
    return xs[lo]*(hi-i)+xs[hi]*(i-lo)

def book_metrics(pid, levels=5):
    url=f"{BASE}/products/{pid}/book?level=2"
    data=fetch_json(url)
    bids=data.get("bids") or []
    asks=data.get("asks") or []
    if not bids or not asks: return None
    def take(side):
        out=[]
        for row in side[:levels]:
            try:
                px=float(row[0]); sz=float(row[1])
                out.append((px,sz))
            except:
                pass
        return out
    b=take(bids); a=take(asks)
    if not b or not a: return None
    bb=b[0][0]; ba=a[0][0]
    mid=(bb+ba)/2.0
    spr_pct=((ba-bb)/mid*100.0) if mid>0 else None
    spr_bps=(spr_pct*100.0) if spr_pct is not None else None
    bid_usd=sum(px*sz for px,sz in b)
    ask_usd=sum(px*sz for px,sz in a)
    topbook=bid_usd+ask_usd
    pressure=(bid_usd/(bid_usd+ask_usd)) if (bid_usd+ask_usd)>0 else None
    return spr_pct, spr_bps, topbook, pressure

def fetch_candles(pid, days, gran=86400, sleep=0.12):
    # Coinbase public candles endpoint returns max 300 points per request.
    # We page backwards from now, requesting 300-day chunks.
    now=datetime.now(timezone.utc)
    end=now
    start=now - timedelta(days=days)
    out=[]
    chunk_days=300
    cur_end=end
    while cur_end > start:
        cur_start=max(start, cur_end - timedelta(days=chunk_days))
        qs=urlencode({
            "start": cur_start.isoformat().replace("+00:00","Z"),
            "end": cur_end.isoformat().replace("+00:00","Z"),
            "granularity": str(gran),
        })
        url=f"{BASE}/products/{pid}/candles?{qs}"
        try:
            data=fetch_json(url)
        except Exception:
            data=[]
        # [ time, low, high, open, close, volume ] newest first
        if isinstance(data,list):
            for r in data:
                try:
                    out.append([int(r[0]), float(r[1]), float(r[2]), float(r[3]), float(r[4]), float(r[5])])
                except:
                    pass
        cur_end=cur_start
        time.sleep(sleep)
    if not out: return []
    out.sort(key=lambda r: r[0])  # oldest->newest
    # dedupe by time
    ded=[]
    seen=set()
    for r in out:
        if r[0] in seen: continue
        seen.add(r[0]); ded.append(r)
    return ded

def pct_from_series(candles, days):
    if len(candles)<2: return None
    # find close at or before now-days
    now_ts=candles[-1][0]
    target_ts=now_ts - days*86400
    # pick the first candle with time >= target_ts
    base=None
    for r in candles:
        if r[0] >= target_ts:
            base=r[4]; break
    if base is None:
        base=candles[0][4]
    last=candles[-1][4]
    if base==0: return None
    return (last-base)/base*100.0

def main():
    if len(sys.argv)<2:
        print("usage: cb_gainer_study_v3.py OUTDIR")
        return 2
    out_dir=sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)
    print("MM19 Coinbase Gainer Study V3", datetime.now(timezone.utc).isoformat())

    horizons=[("14d",14),("60d",60),("180d",180),("365d",365),("540d",540),("730d",730)]

    products=fetch_json(f"{BASE}/products")
    usd=[p.get("id") for p in products if isinstance(p,dict) and p.get("quote_currency")=="USD" and p.get("status")=="online"]
    usd=[x for x in usd if x and x.endswith("-USD")]

    write_csv(os.path.join(out_dir,"coinbase_products_usd.csv"), [{"product_id":pid} for pid in sorted(usd)], ["product_id"])

    # Pick most liquid by /stats volume. Reduce scan cap for speed.
    scan_cap=250
    stats=[]
    for i,pid in enumerate(usd[:scan_cap], start=1):
        try:
            s=fetch_json(f"{BASE}/products/{pid}/stats")
            vol=safe_f(s.get("volume")) or 0.0
            stats.append((vol,pid))
        except:
            pass
        if i%50==0:
            print(f"stats_progress {i}/{scan_cap}")
        time.sleep(0.05)

    stats.sort(key=lambda t: t[0], reverse=True)
    universe=[pid for _,pid in stats[:120]]
    with open(os.path.join(out_dir,"universe_used.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(universe))

    # Fetch 730d candles ONCE per pid, compute all horizons from same series.
    returns={tag:[] for tag,_ in horizons}
    failures=[]
    candles_cache={}
    for idx,pid in enumerate(universe, start=1):
        try:
            c=fetch_candles(pid, 730, gran=86400, sleep=0.10)
            if len(c)<50:
                failures.append(pid); continue
            candles_cache[pid]=c
            for tag,days in horizons:
                r=pct_from_series(c, days)
                returns[tag].append({"product_id":pid, "pct":r})
        except Exception:
            failures.append(pid)
        if idx%10==0:
            print(f"candles_progress {idx}/{len(universe)}")
        time.sleep(0.03)

    with open(os.path.join(out_dir,"candles_failures.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(failures))

    topN=60
    top_sets={}
    for tag,_ in horizons:
        rows=[r for r in returns[tag] if r["pct"] is not None]
        rows.sort(key=lambda x: x["pct"], reverse=True)
        ranked=[]
        for i,r in enumerate(rows[:topN], start=1):
            ranked.append({"rank":i,"product_id":r["product_id"],"pct":round(r["pct"],4)})
        top_sets[tag]=set([r["product_id"] for r in ranked])
        write_csv(os.path.join(out_dir,f"cb_gainers_{tag}.csv"), ranked, ["rank","product_id","pct"])

    # Persistence across horizons
    counts={}
    for tag,_ in horizons:
        for pid in top_sets[tag]:
            counts[pid]=counts.get(pid,0)+1
    persist=[]
    for pid,c in sorted(counts.items(), key=lambda kv:(-kv[1],kv[0])):
        present=[tag for tag,_ in horizons if pid in top_sets[tag]]
        persist.append({"product_id":pid,"count":c,"horizons":",".join(present)})
    write_csv(os.path.join(out_dir,"cb_gainers_persistence.csv"), persist, ["product_id","count","horizons"])

    # Microstructure snapshot for union of top sets
    union=set()
    for tag,_ in horizons: union |= top_sets[tag]
    micro=[]
    for i,pid in enumerate(sorted(union)[:120], start=1):
        try:
            m=book_metrics(pid, levels=5)
            if not m: continue
            spr_pct,spr_bps,topbook,pressure=m
            micro.append({"product_id":pid,"spread_pct":spr_pct,"spread_bps":spr_bps,"topbook_usd":topbook,"pressure":pressure})
        except:
            pass
        if i%25==0:
            print(f"book_progress {i}/120")
        time.sleep(0.10)
    write_csv(os.path.join(out_dir,"coinbase_microstructure_snapshot.csv"), micro, ["product_id","spread_pct","spread_bps","topbook_usd","pressure"])

    # Gate calibration (independent 80% pass)
    spreads=[r["spread_pct"] for r in micro if r.get("spread_pct") is not None]
    topbooks=[r["topbook_usd"] for r in micro if r.get("topbook_usd") is not None]
    pressures=[r["pressure"] for r in micro if r.get("pressure") is not None]
    rec_spread=quantile(spreads, 0.80)
    rec_topbook=quantile(topbooks, 0.20)
    rec_press=quantile(pressures, 0.20)
    # conservative rounding
    if rec_spread is not None: rec_spread=round(rec_spread,3)
    if rec_topbook is not None: rec_topbook=round(rec_topbook,2)
    if rec_press is not None: rec_press=round(rec_press,3)

    rec={
        "horizons":[tag for tag,_ in horizons],
        "universe_size":len(universe),
        "union_top_size":len(union),
        "calibration":{"spread_pct_p80":rec_spread,"topbook_usd_p20":rec_topbook,"pressure_p20":rec_press},
        "recommended_settings":{
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
    with open(os.path.join(out_dir,"recommended_settings_gainer_mode.json"),"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=2)

    with open(os.path.join(out_dir,"apply_in_menu.txt"),"w",encoding="utf-8") as f:
        f.write("E Settings editor -> set the following:\n")
        f.write("  3 SMART_BUY = False\n")
        f.write("  4 GAINERS_ONLY = True\n")
        f.write("  5 RANK_BY_24H_PCT = True\n")
        f.write(f"  9 MIN_TOPBOOK_USD = {rec['recommended_settings']['MIN_TOPBOOK_USD']}\n")
        f.write(f" 10 MAX_SPREAD_PCT = {rec['recommended_settings']['MAX_SPREAD_PCT']}\n")
        f.write(" 31 MIN_DMID_BPS = -5.0\n")
        f.write(f" 32 BOOK_PRESSURE_MIN = {rec['recommended_settings']['BOOK_PRESSURE_MIN']}\n")
        f.write(" 34 MIN_24H_PCT = 1.0\n")

    print("DONE out_dir=", out_dir)
    return 0

if __name__=="__main__":
    raise SystemExit(main())
