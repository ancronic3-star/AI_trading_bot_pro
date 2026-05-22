import time, traceback
from managers.run_manager import run_manager as rm

def main():
    t0=time.time()
    print("MM19 SCORES PROBE START", time.strftime("%Y-%m-%d %H:%M:%S"))
    cfg=rm.load_settings()
    print("load_settings ok", round(time.time()-t0,3))
    c=rm.get_client()
    print("get_client ok", round(time.time()-t0,3))

    t1=time.time()
    print("scores start")
    rows=rm._scores(c, cfg)
    print("scores done", len(rows), "sec", round(time.time()-t1,3))
    if rows:
        pid=rows[0][0]
        t2=time.time()
        print("book_metrics start", pid)
        mid, spr_bps, tob, press = rm._book_metrics(c, pid)
        print("book_metrics done", pid, "mid", mid, "spr_bps", spr_bps, "tob", tob, "press", press, "sec", round(time.time()-t2,3))
    print("MM19 SCORES PROBE END total_sec", round(time.time()-t0,3))

if __name__=="__main__":
    try:
        main()
    except Exception:
        traceback.print_exc()
        raise
