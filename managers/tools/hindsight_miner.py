#!/usr/bin/env python
from __future__ import annotations
import argparse, datetime as dt, json, os, time, math, urllib.request, urllib.error, csv
from dataclasses import dataclass
from typing import Any, Dict, List, Tuple, Optional

def http_get_json(url: str, timeout: int = 30):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))

def iso(ts: int) -> str:
    return dt.datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d")

@dataclass
class Candle:
    t: int
    low: float
    high: float
    open: float
    close: float
    vol: float

def fetch_products() -> List[dict]:
    return http_get_json("https://api.exchange.coinbase.com/products")

def fetch_daily_candles(pid: str) -> List[Candle]:
    url = f"https://api.exchange.coinbase.com/products/{pid}/candles?granularity=86400"
    raw = http_get_json(url)
    out=[]
    for row in raw:
        try:
            t, low, high, o, c, v = row
            out.append(Candle(int(t), float(low), float(high), float(o), float(c), float(v)))
        except Exception:
            pass
    out.sort(key=lambda c: c.t)
    return out

def usd_vol(c: Candle) -> float:
    return c.vol * c.close

def pct(a: float, b: float) -> float:
    if a<=0: return 0.0
    return (b/a)-1.0

def bps(a: float, b: float) -> float:
    return pct(a,b)*10000.0

@dataclass(frozen=True)
class Grid:
    TOP_N:int
    MIN_1M_VOL:float
    TREND_TICKS:int
    TREND_BPS_MIN:float
    TP_PCT:float
    SL_PCT:float
    SOLDIER_USD:float

def simulate_day(rows: List[dict], g: Grid, start_usd: float) -> float:
    # buy at open, TP on high, SL on low, else close; allocate SOLDIER_USD until cash exhausted
    filt=[r for r in rows if r["avg_vol_usd"] >= g.MIN_1M_VOL*1e6 and r["trend_days"]>=g.TREND_TICKS and r["trend_bps"]>=g.TREND_BPS_MIN]
    filt.sort(key=lambda r: r["prev_ret"], reverse=True)
    cash=start_usd
    pnl=0.0
    for r in filt[:g.TOP_N]:
        if cash < g.SOLDIER_USD: break
        entry=r["open"]
        if entry<=0: continue
        tp=entry*(1.0+g.TP_PCT)
        sl=entry*(1.0-g.SL_PCT)
        exit_px=r["close"]
        if r["high"]>=tp: exit_px=tp
        elif r["low"]<=sl: exit_px=sl
        pnl += (exit_px-entry)/entry * g.SOLDIER_USD
        cash -= g.SOLDIER_USD
    return pnl

def write_csv(path: str, rows: List[dict]):
    if not rows: return
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path,"w",newline="",encoding="utf-8") as f:
        w=csv.DictWriter(f,fieldnames=list(rows[0].keys()))
        w.writeheader()
        for r in rows: w.writerow(r)

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--days",type=int,default=7)
    ap.add_argument("--start_usd",type=float,default=500.0)
    ap.add_argument("--soldier_usd",type=float,default=10.0)
    ap.add_argument("--max_products",type=int,default=200)
    ap.add_argument("--sleep",type=float,default=0.08)
    args=ap.parse_args()

    run_ts=dt.datetime.now().strftime("%Y%m%d_%H%M%S")
    out_dir=os.path.join(os.getcwd(),"logs","hindsight",f"hindsight_{run_ts}")
    os.makedirs(out_dir,exist_ok=True)

    prods=fetch_products()
    usd=[p.get("id") for p in prods if isinstance(p,dict) and p.get("quote_currency")=="USD" and isinstance(p.get("id"),str) and p.get("id").endswith("-USD")]
    usd=sorted(set(usd))
    print("USD products:",len(usd))

    # fetch candles and rank by avg USD volume
    candles={}
    vols=[]
    for i,pid in enumerate(usd, start=1):
        try:
            c=fetch_daily_candles(pid)
            if len(c) < args.days+2: 
                continue
            c=c[-(args.days+2):]
            candles[pid]=c
            avg=sum(usd_vol(x) for x in c)/len(c)
            vols.append((avg,pid))
        except Exception:
            pass
        if args.sleep>0: time.sleep(args.sleep)
        if i%200==0: print("fetched",i)

    vols.sort(reverse=True)
    top=[pid for _,pid in vols[:args.max_products]]
    print("Kept:",len(top))

    # build rows per day
    day_rows=[]
    for pid in top:
        c=candles[pid]
        avg_vol_usd=sum(usd_vol(x) for x in c)/len(c)
        for i in range(1,len(c)):
            day=c[i].t
            prev_close=c[i-1].close
            prev_ret=pct(prev_close,c[i].close)
            # trend bps map for 1..3 days (enough for our grid)
            tb={}
            for tt in (1,2,3):
                if i-tt<0: continue
                tb[tt]=bps(c[i-tt].close,c[i].close)
            for tt in (1,2,3):
                day_rows.append({
                    "trend_ticks":tt,
                    "product_id":pid,
                    "day":day,
                    "day_iso":iso(day),
                    "open":c[i].open,
                    "high":c[i].high,
                    "low":c[i].low,
                    "close":c[i].close,
                    "avg_vol_usd":avg_vol_usd,
                    "prev_ret":prev_ret,
                    "trend_days":tt,
                    "trend_bps":tb.get(tt,0.0)
                })

    days=sorted(set(r["day"] for r in day_rows))
    by_day={d:[] for d in days}
    for r in day_rows:
        by_day[r["day"]].append(r)

    grids=[]
    for TOP_N in (8,12,16,20):
        for MIN_1M_VOL in (0.5,1.0,2.0,5.0,10.0):
            for TREND_TICKS in (1,2,3):
                for TREND_BPS_MIN in (0.0,1.0,2.0,5.0,10.0):
                    for TP_PCT in (0.02,0.04,0.06,0.077):
                        for SL_PCT in (0.05,0.10,0.20,0.30):
                            grids.append(Grid(TOP_N,MIN_1M_VOL,TREND_TICKS,TREND_BPS_MIN,TP_PCT,SL_PCT,args.soldier_usd))

    overall=[]
    best_by_day=[]
    # overall static best
    for g in grids:
        eq=args.start_usd
        for d in days:
            rows=[r for r in by_day[d] if r["trend_ticks"]==g.TREND_TICKS]
            eq += simulate_day(rows,g,eq)
        overall.append({
            "TOP_N":g.TOP_N,"MIN_1M_VOL":g.MIN_1M_VOL,"TREND_TICKS":g.TREND_TICKS,"TREND_BPS_MIN":g.TREND_BPS_MIN,
            "TP_PCT":g.TP_PCT,"SL_PCT":g.SL_PCT,"final_equity":round(eq,2),"profit":round(eq-args.start_usd,2)
        })
    overall.sort(key=lambda r:r["final_equity"],reverse=True)
    write_csv(os.path.join(out_dir,"grid_best_overall.csv"),overall[:50])

    # hindsight best by day (choose best grid per day)
    for d in days:
        best=None
        for g in grids:
            rows=[r for r in by_day[d] if r["trend_ticks"]==g.TREND_TICKS]
            pnl=simulate_day(rows,g,args.start_usd)
            if best is None or pnl>best["day_profit"]:
                best={"day":iso(d),"day_profit":round(pnl,2),**{k:getattr(g,k) for k in ("TOP_N","MIN_1M_VOL","TREND_TICKS","TREND_BPS_MIN","TP_PCT","SL_PCT")}}
        best_by_day.append(best)
    write_csv(os.path.join(out_dir,"grid_best_by_day.csv"),best_by_day)

    rec={"BEST_OVERALL":overall[0],"START_USD":args.start_usd,"SOLDIER_USD":args.soldier_usd,"ASSUMPTIONS":"daily candles; buy open; TP/SL via high/low; else close; no fees/slippage"}
    with open(os.path.join(out_dir,"recommended_settings.json"),"w",encoding="utf-8") as f: json.dump(rec,f,indent=2)

    print("Output:",out_dir)

if __name__=="__main__":
    main()
