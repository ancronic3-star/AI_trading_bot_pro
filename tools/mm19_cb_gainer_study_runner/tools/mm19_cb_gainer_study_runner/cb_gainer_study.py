import sys, os, json, time, math, csv
from datetime import datetime, timedelta, timezone
from urllib.request import Request, urlopen
from urllib.parse import urlencode

UA = "mm19-cb-gainer-study"
BASE = "https://api.exchange.coinbase.com"

def fetch_json(url, timeout=40):
    req = Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
    with urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode("utf-8")
    return json.loads(data)

def iso(dt):
    # Coinbase expects ISO8601 with Z
    return dt.replace(tzinfo=timezone.utc).isoformat().replace("+00:00", "Z")

def candles(pid, start_dt, end_dt, gran=86400, sleep=0.12):
    # Coinbase returns max ~300 rows; we split into chunks outside
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
        # [time, low, high, open, close, volume]
        if isinstance(r, list) and len(r) >= 6:
            rows.append(r)
    # sort asc by time
    rows.sort(key=lambda x: x[0])
    return rows

def fetch_candles_days(pid, days, gran=86400):
    # Need days+1 closes; we request in chunks of 280 days to be safe
    now = datetime.utcnow().replace(tzinfo=timezone.utc)
    end = now
    start = now - timedelta(days=days+2)
    chunk = 280
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

def last_first_close(rows):
    if len(rows) < 2:
        return None, None
    first = rows[0][4]
    last = rows[-1][4]
    try:
        return float(first), float(last)
    except:
        return None, None

def pct(a,b):
    if a is None or b is None or a == 0:
        return None
    return (b-a)/a*100.0

def book_metrics(pid, levels=5, sleep=0.12):
    url = f"{BASE}/products/{pid}/book?level=2"
    try:
        data = fetch_json(url)
    finally:
        time.sleep(sleep)
    bids = data.get("bids") or []
    asks = data.get("asks") or []
    def take(side):
        out=[]
        for row in side[:levels]:
            try:
                price=float(row[0]); size=float(row[1])
                out.append((price,size))
            except:
                pass
        return out
    b = take(bids); a = take(asks)
    if not b or not a:
        return None
    bb=b[0][0]; ba=a[0][0]
    mid=(bb+ba)/2.0
    spr_pct=(ba-bb)/mid*100.0 if mid>0 else None
    bid_usd=sum(px*sz for px,sz in b)
    ask_usd=sum(px*sz for px,sz in a)
    topbook=bid_usd+ask_usd
    pressure=(bid_usd/(bid_usd+ask_usd)) if (bid_usd+ask_usd)>0 else None
    return spr_pct, topbook, pressure, bb, ba

def write_csv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w=csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow(r)

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

def main():
    if len(sys.argv) < 2:
        print("Usage: cb_gainer_study.py OUT_DIR")
        sys.exit(2)
    out_dir=sys.argv[1]
    os.makedirs(out_dir, exist_ok=True)

    print("MM19 Coinbase Gainer Study", datetime.utcnow().isoformat()+"Z")
    print("OUT", out_dir)

    # Fetch products
    products = fetch_json(f"{BASE}/products")
    usd = []
    for p in products:
        try:
            if p.get("quote_currency")=="USD" and p.get("status")=="online":
                usd.append(p.get("id"))
        except:
            pass

    usd = sorted(set([x for x in usd if isinstance(x,str) and "-" in x]))
    with open(os.path.join(out_dir, "coinbase_products_usd.txt"), "w", encoding="utf-8") as f:
        f.write("\n".join(usd))

    # Horizons in days (approx)
    horizons = [
        ("14d", 14),
        ("60d", 60),
        ("180d", 180),
        ("365d", 365),
        ("540d", 540),
        ("730d", 730),
    ]

    # For speed: start with a liquid subset by sampling top-N by volume via stats endpoint
    # Coinbase /products/<pid>/stats is light; we'll use it to pick top 250 by volume
    stats=[]
    for i,pid in enumerate(usd[:800]):  # cap scan
        try:
            s=fetch_json(f"{BASE}/products/{pid}/stats")
            vol=float(s.get("volume") or 0.0)
            stats.append((vol, pid))
        except:
            pass
        time.sleep(0.05)
    stats.sort(reverse=True)
    universe=[pid for _,pid in stats[:250]]  # focus on top 250 USD by recent volume

    with open(os.path.join(out_dir,"universe_used.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(universe))

    # Compute returns per horizon
    returns = {tag: [] for tag,_ in horizons}
    failures=[]
    for idx,pid in enumerate(universe, start=1):
        row={"product_id":pid}
        ok_any=False
        for tag,days in horizons:
            try:
                rows=fetch_candles_days(pid, days)
                a,b=last_first_close(rows)
                r=pct(a,b)
                row[tag]=r
                ok_any = ok_any or (r is not None)
            except Exception as e:
                row[tag]=None
        if ok_any:
            for tag,_ in horizons:
                returns[tag].append({"product_id":pid, "pct": row[tag]})
        else:
            failures.append(pid)
        if idx % 25 == 0:
            print(f"progress {idx}/{len(universe)}")

    with open(os.path.join(out_dir,"candles_failures.txt"),"w",encoding="utf-8") as f:
        f.write("\n".join(failures))

    # Rank top gainers for each horizon
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

    # Cross-horizon persistence score: count in how many horizons a pid appears
    persist=[]
    for pid in universe:
        c=sum(1 for tag,_ in horizons if pid in top_sets[tag])
        if c>0:
            persist.append({"product_id":pid, "horizons_in_top":c})
    persist.sort(key=lambda x: (-x["horizons_in_top"], x["product_id"]))
    write_csv(os.path.join(out_dir,"cb_gainers_persistence.csv"), persist, ["product_id","horizons_in_top"])

    # Microstructure snapshot for union of all horizon gainers (limited)
    union=set()
    for tag,_ in horizons:
        union |= top_sets[tag]
    union=sorted(union)
    micro=[]
    for pid in union[:120]:
        m=book_metrics(pid, levels=5)
        if not m: 
            continue
        spr_pct, topbook, pressure, bb, ba = m
        micro.append({
            "product_id":pid,
            "spread_pct": None if spr_pct is None else round(spr_pct,4),
            "topbook_usd": None if topbook is None else round(topbook,2),
            "pressure": None if pressure is None else round(pressure,4),
            "best_bid": bb, "best_ask": ba
        })
    write_csv(os.path.join(out_dir,"cb_micro_snapshot.csv"), micro,
              ["product_id","spread_pct","topbook_usd","pressure","best_bid","best_ask"])

    spreads=[r["spread_pct"] for r in micro if r.get("spread_pct") is not None]
    topbooks=[r["topbook_usd"] for r in micro if r.get("topbook_usd") is not None]
    pressures=[r["pressure"] for r in micro if r.get("pressure") is not None]

    # Recommend gates that allow ~80% of these gainers by current microstructure
    rec = {
        "generated_utc": datetime.utcnow().isoformat()+"Z",
        "universe_size": len(universe),
        "gainer_union_size": len(union),
        "micro_rows": len(micro),
        "recommended": {
            "GAINERS_ONLY": True,
            "RANK_BY_24H_PCT": True,
            "MIN_24H_PCT": 1.0,
            "SMART_BUY": False,
            "MIN_DMID_BPS": -5.0,
            "MAX_SPREAD_PCT": None,
            "MIN_TOPBOOK_USD": None,
            "BOOK_PRESSURE_MIN": None
        },
        "calibration": {}
    }

    rec["calibration"]["spread_pct_p80"]=quantile(spreads,0.80)
    rec["calibration"]["topbook_usd_p20"]=quantile(topbooks,0.20)
    rec["calibration"]["pressure_p20"]=quantile(pressures,0.20)

    # Round and clamp to sane ranges
    sp=rec["calibration"]["spread_pct_p80"]
    tb=rec["calibration"]["topbook_usd_p20"]
    bp=rec["calibration"]["pressure_p20"]

    if sp is not None:
        rec["recommended"]["MAX_SPREAD_PCT"]=round(float(sp),3)
    if tb is not None:
        rec["recommended"]["MIN_TOPBOOK_USD"]=max(100.0, round(float(tb),2))
    if bp is not None:
        rec["recommended"]["BOOK_PRESSURE_MIN"]=round(float(bp),3)

    with open(os.path.join(out_dir,"recommended_settings_from_cb_gainers.json"),"w",encoding="utf-8") as f:
        json.dump(rec,f,indent=2)

    # Human summary
    with open(os.path.join(out_dir,"SUMMARY.txt"),"w",encoding="utf-8") as f:
        f.write("MM19 Coinbase Gainer Study\n")
        f.write(f"Universe used (top by volume): {len(universe)}\n")
        f.write(f"Gainer union (any horizon top {topN}): {len(union)}\n")
        f.write(f"Micro rows: {len(micro)}\n\n")
        f.write("Recommended settings (menu keys):\n")
        for k,v in rec["recommended"].items():
            f.write(f"  {k} = {v}\n")
        f.write("\nCalibration:\n")
        for k,v in rec["calibration"].items():
            f.write(f"  {k} = {v}\n")

    print("DONE")

if __name__=="__main__":
    main()
