#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""MM24 paper-signal trough wait+score tool (V6).

Purpose
- Wait until a target number of [PAPER_BUY_SIGNAL] lines have been observed
  since the last [run_start] in the activity log.
- Score those signals against Coinbase Exchange candles:
  - trough position over lookback window (default uses TROUGH_LOOKBACK_SEC)
  - forward max return over forward window (default 180 minutes)
  - forward min return (drawdown) over forward window
  - TP hit (normalized TP_PCT)
  - SL hit (normalized SL_PCT)
  - FIRST HIT ordering: TP-first vs SL-first vs BOTH (same candle) vs NEITHER
- Produce a zip report under logs\\analysis_trough and open Explorer selecting it.

Notes
- DRY-safe: never places orders.
- Does NOT depend on [run_start]. It can backfill from the activity log tail and continues
  following new lines. Restarting the bot will not reset the counter.
- Optional FULL-window gating: can require that each scored signal has a complete forward window
  (default: YES) so you don't generate partial-window reports by accident.

- Candle API constraints: uses 1m candles for lookback; uses 1m or 5m for
  forward window depending on forward horizon to avoid request limits.

MM24_MENU_WAIT_SCORE_TOOL_V5:
- Adds first-hit ordering (tp_first / sl_first / both_same / neither)
- Allows selecting forward window (3h / 12h / 24h) interactively in the W console
  (or via --forward-min).

MM24_MENU_WAIT_SCORE_TOOL_V6:
- Adds EVENT WATCH mode: capture next BUY_OK / SELL_OK (or both) into a zipped event pack
  without relying on [run_start] and without requiring you to stare at the screen.

"""

from __future__ import annotations

import argparse
import json
import shutil
import zipfile
import os
import re
import subprocess
import sys
import time
from bisect import bisect_right
from collections import deque
from datetime import datetime, timedelta, timezone
from typing import Any, Deque, Dict, List, Optional, Tuple

try:
    _LOCAL_TZ = datetime.now().astimezone().tzinfo or timezone.utc
except Exception:
    _LOCAL_TZ = timezone.utc

from urllib.parse import urlencode
from urllib.request import Request, urlopen


# Ensure repo root is on sys.path when executed directly
try:
    from pathlib import Path

    _ROOT = Path(__file__).resolve().parents[2]
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
except Exception:
    pass


def _load_settings() -> Dict[str, Any]:
    try:
        from managers.config_manager.settings import load_settings

        s = load_settings()
        if isinstance(s, dict):
            return s
    except Exception:
        pass
    # fallback to local run_settings.json
    try:
        p = os.path.join(os.getcwd(), "run_settings.json")
        with open(p, "r", encoding="utf-8") as f:
            d = json.load(f)
        return d if isinstance(d, dict) else {}
    except Exception:
        return {}


def _repo_root() -> str:
    try:
        from pathlib import Path

        return str(Path(__file__).resolve().parents[2])
    except Exception:
        return os.getcwd()


def _abs_path(root: str, p: str) -> str:
    if not p:
        return p
    if os.path.isabs(p):
        return p
    return os.path.join(root, p)


def _find_last_run_start_offset(path: str, max_bytes: int = 50 * 1024 * 1024) -> int:
    """Return byte offset of the start of the last line containing '[run_start]'.

    Reads from the end of the file backwards up to max_bytes.
    Returns -1 if not found.
    """
    needle = b"[run_start]"
    try:
        size = os.path.getsize(path)
    except Exception:
        return -1

    block = 1024 * 1024
    read_total = 0
    buf = b""
    with open(path, "rb") as f:
        pos = size
        while pos > 0 and read_total < max_bytes:
            take = block if pos >= block else pos
            pos -= take
            f.seek(pos)
            chunk = f.read(take)
            read_total += take
            buf = chunk + buf
            idx = buf.rfind(needle)
            if idx != -1:
                nl = buf.rfind(b"\n", 0, idx)
                line_start_in_buf = 0 if nl == -1 else nl + 1
                return pos + line_start_in_buf
            if len(buf) > max_bytes:
                buf = buf[-max_bytes:]
    return -1


def _tail_offset(path: str, max_bytes: int = 50 * 1024 * 1024) -> int:
    """Return a safe seek offset near the end of the file.

    Does NOT depend on [run_start]. Reads from max(size-max_bytes, 0).
    Caller should discard the first partial line if offset > 0.
    """
    try:
        size = os.path.getsize(path)
    except Exception:
        return 0
    off = size - int(max_bytes)
    return off if off > 0 else 0


def _extract_json_after_tag(line: str, tag: str) -> Optional[Dict[str, Any]]:
    try:
        i = line.find(tag)
        if i == -1:
            return None
        payload = line[i + len(tag) :].strip()
        if not payload:
            return None
        return json.loads(payload)
    except Exception:
        return None


def _parse_ts(ts_utc: Any) -> Optional[datetime]:
    """Parse ts_utc strings like '2026-02-24T19:20:09Z' into aware UTC datetime."""
    if not ts_utc:
        return None
    s = str(ts_utc).strip()
    s = s.replace("Z", "")
    for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def _norm_pct(x_raw: Any) -> Optional[float]:
    """Normalize percent values that might be stored as fraction (<=1) or percent (>1)."""
    try:
        x = float(x_raw)
    except Exception:
        return None
    return x * 100.0 if x <= 1.0 else x


def _dt_iso_z(dt_utc: datetime) -> str:
    """Return ISO string with trailing Z for UTC datetimes."""
    if dt_utc.tzinfo is None:
        dt_utc = dt_utc.replace(tzinfo=timezone.utc)
    return dt_utc.isoformat().replace("+00:00", "Z")


def _fetch_candles(pid: str, start_dt: datetime, end_dt: datetime, gran: int) -> List[List[float]]:
    base = f"https://api.exchange.coinbase.com/products/{pid}/candles"
    qs = urlencode(
        {
            "start": _dt_iso_z(start_dt),
            "end": _dt_iso_z(end_dt),
            "granularity": str(int(gran)),
        }
    )
    req = Request(base + "?" + qs, headers={"User-Agent": "mm24-trough-wait-score"})
    with urlopen(req, timeout=25) as r:
        data = json.loads(r.read().decode("utf-8"))
    return sorted(data, key=lambda x: x[0])  # [time, low, high, open, close, volume]


def _choose_forward_gran(forward_min: int) -> int:
    # Keep per-request candles <= ~300:
    #  - 3h @1m = 180 candles
    #  - 12h @5m = 144 candles
    #  - 24h @5m = 288 candles
    if forward_min <= 240:
        return 60
    if forward_min <= 2000:
        return 300
    return 900


def _first_hit(post: List[List[float]], entry: float, tp_pct: Optional[float], sl_pct: Optional[float]) -> Tuple[str, Optional[int], Optional[int]]:
    """Return (first_hit, tp_hit_epoch, sl_hit_epoch).

    first_hit in {'tp','sl','both','neither'}.
    If both TP and SL touch in the same candle, first_hit='both' (ambiguous ordering).
    """
    if not post or entry <= 0:
        return ("neither", None, None)

    tp_px = entry * (1.0 + (tp_pct or 0.0) / 100.0) if tp_pct is not None else None
    sl_px = entry * (1.0 - (sl_pct or 0.0) / 100.0) if sl_pct is not None else None

    tp_hit: Optional[int] = None
    sl_hit: Optional[int] = None

    for c in post:
        ts = int(c[0])
        lo = float(c[1])
        hi = float(c[2])

        hit_tp = (tp_px is not None) and (hi >= tp_px)
        hit_sl = (sl_px is not None) and (lo <= sl_px)

        if hit_tp and hit_sl:
            return ("both", ts, ts)
        if hit_tp and tp_hit is None:
            tp_hit = ts
        if hit_sl and sl_hit is None:
            sl_hit = ts
        if tp_hit is not None and sl_hit is not None:
            break

    if tp_hit is None and sl_hit is None:
        return ("neither", None, None)
    if tp_hit is not None and sl_hit is None:
        return ("tp", tp_hit, None)
    if sl_hit is not None and tp_hit is None:
        return ("sl", None, sl_hit)

    # both present, different candles
    assert tp_hit is not None and sl_hit is not None
    if tp_hit < sl_hit:
        return ("tp", tp_hit, sl_hit)
    if sl_hit < tp_hit:
        return ("sl", tp_hit, sl_hit)
    return ("both", tp_hit, sl_hit)


def _score_signal(sig: Dict[str, Any], lookback_min: int, forward_min: int, now_utc: datetime) -> Dict[str, Any]:
    pid = str(sig.get("product_id") or "")
    mid = float(sig.get("mid", 0.0) or 0.0)
    t = _parse_ts(sig.get("ts_utc"))
    blocked = str(sig.get("blocked_by") or "")

    cfg = sig.get("cfg") or {}
    tp_raw = cfg.get("TP_PCT")
    sl_raw = cfg.get("SL_PCT")
    tp_pct = _norm_pct(tp_raw)
    sl_pct = _norm_pct(sl_raw)

    t_internal = sig.get("trough_pct")

    out: Dict[str, Any] = {
        "ts_utc": sig.get("ts_utc"),
        "tick": sig.get("tick"),
        "product_id": pid,
        "blocked_by": blocked,
        "mid": mid,
        "score": sig.get("score"),
        # internal trough model from bot (if present)
        "trough_pct_internal": t_internal,
        "trough_n": sig.get("trough_n"),
        "trough_lo": sig.get("trough_lo"),
        "trough_hi": sig.get("trough_hi"),
        "trough_max": sig.get("trough_max"),
        # candle-lookback trough
        "trough_pct_lookback": None,
        # forward window stats
        "forward_min_target": forward_min,
        "forward_min_available": None,
        "forward_full_window": False,
        "fwd_max_return_pct": None,
        "fwd_min_return_pct": None,
        # TP/SL settings
        "tp_pct_setting_raw": tp_raw,
        "tp_pct_setting_norm": tp_pct,
        "sl_pct_setting_raw": sl_raw,
        "sl_pct_setting_norm": sl_pct,
        # Touch stats
        "would_hit_tp": False,
        "would_hit_sl": False,
        # Ordering
        "first_hit": "neither",
        "tp_hit_min": None,
        "sl_hit_min": None,
        "both_hit_min": None,
    }

    if not pid or mid <= 0 or t is None:
        return out

    start_pre = t - timedelta(minutes=int(lookback_min))
    end_pre = t

    end_post_target = t + timedelta(minutes=int(forward_min))
    end_post = end_post_target if end_post_target <= now_utc else now_utc
    if end_post < t:
        end_post = t

    out["forward_min_available"] = int(max(0, (end_post - t).total_seconds() / 60.0))
    out["forward_full_window"] = bool(end_post >= end_post_target)

    pre: List[List[float]] = []
    post: List[List[float]] = []
    forward_gran = _choose_forward_gran(forward_min)

    # fetch lookback (1m) and forward (adaptive gran) separately
    for attempt in range(3):
        try:
            pre = _fetch_candles(pid, start_pre, end_pre, 60)
            break
        except Exception:
            time.sleep(1.5 * (attempt + 1))

    for attempt in range(3):
        try:
            if end_post > t:
                post = _fetch_candles(pid, t, end_post, forward_gran)
            else:
                post = []
            break
        except Exception:
            time.sleep(1.5 * (attempt + 1))

    # trough percentile over pre window
    if pre:
        lows = [float(c[1]) for c in pre]
        highs = [float(c[2]) for c in pre]
        lo = min(lows)
        hi = max(highs)
        if hi > lo:
            out["trough_pct_lookback"] = round((mid - lo) / (hi - lo), 6)

    # forward returns over post window
    if post:
        mx = max(float(c[2]) for c in post)
        mn = min(float(c[1]) for c in post)
        out["fwd_max_return_pct"] = round((mx / mid - 1.0) * 100.0, 4)
        out["fwd_min_return_pct"] = round((mn / mid - 1.0) * 100.0, 4)

    if out["fwd_max_return_pct"] is not None and tp_pct is not None:
        out["would_hit_tp"] = bool(float(out["fwd_max_return_pct"]) >= float(tp_pct))

    if out["fwd_min_return_pct"] is not None and sl_pct is not None:
        out["would_hit_sl"] = bool(float(out["fwd_min_return_pct"]) <= -float(sl_pct))

    # First-hit ordering
    if post:
        hit, tp_epoch, sl_epoch = _first_hit(post, mid, tp_pct, sl_pct)
        out["first_hit"] = hit
        t0 = int(t.timestamp())
        if hit == "both" and tp_epoch is not None:
            out["both_hit_min"] = round((tp_epoch - t0) / 60.0, 2)
        if tp_epoch is not None:
            out["tp_hit_min"] = round((tp_epoch - t0) / 60.0, 2)
        if sl_epoch is not None:
            out["sl_hit_min"] = round((sl_epoch - t0) / 60.0, 2)

    return out


def _median(vals: List[float]) -> Optional[float]:
    if not vals:
        return None
    vals = sorted(vals)
    return vals[len(vals) // 2]


def _pct(vals: List[float], p: float) -> Optional[float]:
    if not vals:
        return None
    vals = sorted(vals)
    if len(vals) == 1:
        return vals[0]
    idx = int(round((p / 100.0) * (len(vals) - 1)))
    idx = max(0, min(idx, len(vals) - 1))
    return vals[idx]


def _open_explorer_select(path: str) -> None:
    try:
        if os.name == "nt":
            subprocess.Popen(["explorer.exe", f"/select,{path}"])
    except Exception:
        pass


def _prompt_int(prompt: str, default: int, lo: int = 1, hi: int = 1000000) -> int:
    try:
        s = input(prompt).strip()
        if not s:
            return default
        v = int(s)
        if v < lo:
            return lo
        if v > hi:
            return hi
        return v
    except Exception:
        return default


def _prompt_float(prompt: str, default: float, lo: float = 0.0, hi: float = 1000000.0) -> float:
    try:
        s = input(prompt).strip()
        if not s:
            return float(default)
        v = float(s)
        if v < lo:
            return float(lo)
        if v > hi:
            return float(hi)
        return float(v)
    except Exception:
        return float(default)


def _open_explorer_select(p: str) -> None:
    """Open Windows Explorer selecting the given file (best-effort)."""
    try:
        if os.name == "nt":
            subprocess.Popen(["explorer.exe", f"/select,{p}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass


def _read_tail_lines(path: str, max_lines: int = 250000, max_bytes: int = 50 * 1024 * 1024) -> List[str]:
    """Read up to max_lines from the end of a text file (best-effort)."""
    try:
        off = _tail_offset(path, max_bytes=max_bytes)
        dq: Deque[str] = deque(maxlen=max_lines)
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(off)
            if off > 0:
                try:
                    f.readline()  # discard partial
                except Exception:
                    pass
            for line in f:
                dq.append(line.rstrip("\n"))
        return list(dq)
    except Exception:
        return []


def _zip_dir(src_dir: str, zip_path: str) -> None:
    os.makedirs(os.path.dirname(zip_path), exist_ok=True)
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for root, _dirs, files in os.walk(src_dir):
            for fn in files:
                fp = os.path.join(root, fn)
                rel = os.path.relpath(fp, src_dir)
                z.write(fp, rel)


def _copy_if_exists(src: str, dst_dir: str) -> Optional[str]:
    try:
        if os.path.exists(src):
            os.makedirs(dst_dir, exist_ok=True)
            dst = os.path.join(dst_dir, os.path.basename(src))
            shutil.copy2(src, dst)
            return dst
    except Exception:
        return None
    return None


def _make_event_pack(
    event_tag: str,
    event_line: str,
    root: str,
    act_path: str,
    out_dir: str,
    tail_lines: int = 250000,
) -> str:
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    dir_name = f"mm24_event_{event_tag}_{stamp}"
    pack_dir = os.path.join(out_dir, dir_name)
    os.makedirs(pack_dir, exist_ok=True)

    # Write event line
    try:
        with open(os.path.join(pack_dir, "event_line.txt"), "w", encoding="utf-8") as f:
            f.write(event_line.rstrip("\n") + "\n")
    except Exception:
        pass

    # Copy core state (best effort)
    _copy_if_exists(_abs_path(root, "run_settings.json"), pack_dir)
    _copy_if_exists(_abs_path(root, os.path.join("logs", "run_active.json")), pack_dir)
    _copy_if_exists(_abs_path(root, "fills_all.json"), pack_dir)
    _copy_if_exists(_abs_path(root, os.path.join("logs", "orders_window.jsonl")), pack_dir)
    _copy_if_exists(_abs_path(root, os.path.join("logs", "holdings.json")), pack_dir)

    # Tail activity log
    tail = _read_tail_lines(act_path, max_lines=max(1, tail_lines))
    tail_path = os.path.join(pack_dir, f"activity_tail_{max(1, tail_lines)}.txt")
    try:
        with open(tail_path, "w", encoding="utf-8") as f:
            f.write("\n".join(tail) + ("\n" if tail else ""))
    except Exception:
        pass

    # Summary counts from tail
    buy_ok = sum(1 for ln in tail if "[BUY_OK]" in ln)
    sell_ok = sum(1 for ln in tail if "[SELL_OK]" in ln)
    paper = sum(1 for ln in tail if "[PAPER_BUY_SIGNAL]" in ln)
    tick_diag = next((ln for ln in reversed(tail) if "[tick_diag]" in ln), "")

    try:
        with open(os.path.join(pack_dir, "SUMMARY.txt"), "w", encoding="utf-8") as f:
            f.write(f"event={event_tag}\n")
            f.write(f"event_time_local={datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"BUY_OK={buy_ok}\n")
            f.write(f"SELL_OK={sell_ok}\n")
            f.write(f"PAPER_BUY_SIGNAL={paper}\n")
            if tick_diag:
                f.write(f"LAST_TICK_DIAG={tick_diag}\n")
    except Exception:
        pass

    # Zip
    zip_name = f"mm24_event_{event_tag}_{stamp}.zip"
    zip_path = os.path.join(out_dir, zip_name)
    _zip_dir(pack_dir, zip_path)
    _open_explorer_select(zip_path)
    print(f"CREATED: {zip_path}", flush=True)
    return zip_path


def _event_watch(
    act_path: str,
    root: str,
    out_dir: str,
    capture: str = "both",
    tail_lines: int = 250000,
    max_minutes: int = 720,
    retro: bool = False,
) -> int:
    os.makedirs(out_dir, exist_ok=True)

    want_buy = capture in ("buy", "both")
    want_sell = capture in ("sell", "both")
    got_buy = False
    got_sell = False

    start = time.time()
    deadline = start + max(1, int(max_minutes)) * 60.0

    last_report = 0.0

    print("=== MM24 EVENT WATCH (BUY_OK / SELL_OK) ===", flush=True)
    print(f"activity_log={act_path}", flush=True)
    print(f"capture={capture}  tail_lines={tail_lines}  max_wait_min={max_minutes}", flush=True)

    if not os.path.exists(act_path):
        print("ERROR: activity log not found.", flush=True)
        return 2


    if retro:
        print("RETRO: scanning tail for last matching events...", flush=True)
        tail = _read_tail_lines(act_path, max_lines=max(1, tail_lines))
        if want_buy and (not got_buy):
            last_buy = next((ln for ln in reversed(tail) if "[BUY_OK]" in ln), None)
            if last_buy:
                got_buy = True
                _make_event_pack("BUY_OK_retro", last_buy, root, act_path, out_dir, tail_lines=tail_lines)
            else:
                print("RETRO: no BUY_OK found in tail.", flush=True)

        if want_sell and (not got_sell):
            last_sell = next((ln for ln in reversed(tail) if "[SELL_OK]" in ln), None)
            if last_sell:
                got_sell = True
                _make_event_pack("SELL_OK_retro", last_sell, root, act_path, out_dir, tail_lines=tail_lines)
            else:
                print("RETRO: no SELL_OK found in tail.", flush=True)

        if ((not want_buy) or got_buy) and ((not want_sell) or got_sell):
            print("DONE: captured requested events (retro).", flush=True)
            return 0

        print("RETRO: continuing to live-follow for remaining events...", flush=True)

    # Tail-follow from end of file (no [run_start] dependency).
    # Handles truncation by reopening if size shrinks.
    try:
        with open(act_path, "r", encoding="utf-8", errors="ignore") as f:
            f.seek(0, os.SEEK_END)
            last_size = os.path.getsize(act_path)
            while True:
                now = time.time()
                if now >= deadline:
                    print("TIMEOUT: no event captured before deadline.", flush=True)
                    return 1

                if (now - last_report) >= 10.0:
                    req_buy = 1 if want_buy else 0
                    req_sell = 1 if want_sell else 0
                    el = int(now - start)
                    rem = int(max(0, deadline - now))
                    print(f"WAIT elapsed={el}s buy={int(got_buy)}/{req_buy} sell={int(got_sell)}/{req_sell} remain={rem}s", flush=True)
                    last_report = now

                line = f.readline()
                if not line:
                    # handle truncation/rotation
                    try:
                        sz = os.path.getsize(act_path)
                        if sz < last_size or f.tell() > sz:
                            f.close()
                            f = open(act_path, "r", encoding="utf-8", errors="ignore")
                            f.seek(0, os.SEEK_END)
                            last_size = sz
                        else:
                            last_size = sz
                    except Exception:
                        pass
                    time.sleep(0.5)
                    continue

                # Literal substring checks (correct; avoids PowerShell wildcard bracket issue)
                if want_buy and (not got_buy) and ("[BUY_OK]" in line):
                    got_buy = True
                    _make_event_pack("BUY_OK", line, root, act_path, out_dir, tail_lines=tail_lines)

                if want_sell and (not got_sell) and ("[SELL_OK]" in line):
                    got_sell = True
                    _make_event_pack("SELL_OK", line, root, act_path, out_dir, tail_lines=tail_lines)

                if ((not want_buy) or got_buy) and ((not want_sell) or got_sell):
                    print("DONE: captured requested events.", flush=True)
                    return 0
    except KeyboardInterrupt:
        print("CANCELLED.", flush=True)
        return 130
    except Exception as e:
        print(f"ERROR: event watch failed: {e}", flush=True)
        return 2


def _parse_local_bracket_ts(line: str) -> Optional[datetime]:
    """Parse the leading [YYYY-mm-dd HH:MM:SS] local timestamp into aware UTC."""
    try:
        if not line.startswith("["):
            return None
        i = line.find("]")
        if i <= 1:
            return None
        s = line[1:i]
        dt_local = datetime.strptime(s, "%Y-%m-%d %H:%M:%S").replace(tzinfo=_LOCAL_TZ)
        return dt_local.astimezone(timezone.utc)
    except Exception:
        return None


def _extract_buy_ok_pid(line: str) -> str:
    for pat in (
        r"\bpid=([A-Z0-9-]+)\b",
        r"\bproduct_id=([A-Z0-9-]+)\b",
        r"\b([A-Z0-9]+-USD)\b",
    ):
        m = re.search(pat, line)
        if m:
            try:
                return str(m.group(1) or "")
            except Exception:
                return ""
    return ""


def _load_tdi_rows(tdi_path: str, since_utc: Optional[datetime], max_lines: int = 50000) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    for line in _read_tail_lines(tdi_path, max_lines=max(1000, int(max_lines))):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        pid = str(d.get("product_id") or "").strip()
        ts = _parse_ts(d.get("ts"))
        if (not pid) or (ts is None):
            continue
        if (since_utc is not None) and (ts < since_utc):
            continue
        reasons = d.get("top_reasons") if isinstance(d.get("top_reasons"), list) else []
        rows.append({
            "product_id": pid,
            "ts": ts,
            "ts_epoch": ts.timestamp(),
            "tdi_score": d.get("tdi_score"),
            "tdi_trough": d.get("tdi_trough"),
            "tdi_momentum": d.get("tdi_momentum"),
            "tdi_liquidity": d.get("tdi_liquidity"),
            "tdi_spread": d.get("tdi_spread"),
            "tdi_pressure": d.get("tdi_pressure"),
            "top_reasons": reasons,
            "top1": reasons[0] if reasons else "",
        })
    rows.sort(key=lambda x: (x["product_id"], x["ts_epoch"]))
    return rows


def _rows_to_table(rows: List[Dict[str, Any]], columns: List[str]) -> str:
    if not rows:
        return "<none>"

    def _sv(v: Any) -> str:
        if v is None:
            return ""
        if isinstance(v, float):
            if abs(v - round(v)) < 1e-9:
                return str(int(round(v)))
            return f"{v:.2f}"
        return str(v)

    widths: Dict[str, int] = {}
    for c in columns:
        widths[c] = len(c)
    for row in rows:
        for c in columns:
            widths[c] = max(widths[c], len(_sv(row.get(c))))

    header = " ".join(c.ljust(widths[c]) for c in columns)
    sep = " ".join("-" * widths[c] for c in columns)
    body = [" ".join(_sv(row.get(c)).ljust(widths[c]) for c in columns) for row in rows]
    return "\n".join([header, sep] + body)


def _write_json(path: str, data: Any) -> None:
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False, default=str)


def _tdi_entry_attribution(
    act_path: str,
    root: str,
    out_dir: str,
    entry_source: str = "paper",
    latest_rows: int = 40,
    tail_lines: int = 5000,
) -> int:
    os.makedirs(out_dir, exist_ok=True)

    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pack_dir = os.path.join(out_dir, f"mm25_tdi_entry_attribution_{entry_source}_{stamp}")
    os.makedirs(pack_dir, exist_ok=True)

    cfg = _load_settings()
    tdi_rel = str(cfg.get("TDI_SNAPSHOT_PATH") or os.path.join("logs", "tdi_snapshots.jsonl"))
    tdi_path = _abs_path(root, tdi_rel)
    if not os.path.exists(tdi_path):
        with open(os.path.join(pack_dir, "join_report.txt"), "w", encoding="utf-8") as f:
            f.write(f"ERROR: TDI snapshot log not found: {tdi_path}\n")
        zip_path = os.path.join(out_dir, f"mm25_tdi_entry_attribution_{entry_source}_{stamp}.zip")
        _zip_dir(pack_dir, zip_path)
        _open_explorer_select(zip_path)
        print(f"CREATED: {zip_path}", flush=True)
        return 2

    want_paper = entry_source in ("paper", "both")
    want_buy = entry_source in ("buy", "both")

    run_start_off = _find_last_run_start_offset(act_path)
    run_start_line = ""
    run_start_local = ""
    run_start_utc: Optional[datetime] = None
    fallback = False

    try:
        with open(act_path, "r", encoding="utf-8", errors="ignore") as f:
            if run_start_off >= 0:
                f.seek(run_start_off)
                run_start_line = f.readline().rstrip("\n")
                if run_start_line.startswith("[") and "]" in run_start_line:
                    run_start_local = run_start_line[1:20]
                run_start_utc = _parse_local_bracket_ts(run_start_line)
            else:
                fallback = True
    except Exception:
        fallback = True

    off = run_start_off if run_start_off >= 0 else _tail_offset(act_path)
    tail_ctx: Deque[str] = deque(maxlen=max(500, int(tail_lines)))
    events: List[Dict[str, Any]] = []
    paper_count = 0
    buy_ok_count = 0
    sell_ok_count = 0

    with open(act_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(off)
        if (run_start_off < 0) and (off > 0):
            try:
                f.readline()
            except Exception:
                pass
        elif run_start_line:
            tail_ctx.append(run_start_line)

        for raw in f:
            line = raw.rstrip("\n")
            tail_ctx.append(line)

            if "[SELL_OK]" in line:
                sell_ok_count += 1
            if "[BUY_OK]" in line:
                buy_ok_count += 1
                if want_buy:
                    ts_utc = _parse_local_bracket_ts(line)
                    pid = _extract_buy_ok_pid(line)
                    if ts_utc is not None and pid:
                        events.append({
                            "event": "BUY_OK",
                            "ts_local": line[1:20] if line.startswith("[") else "",
                            "ts_utc": ts_utc,
                            "ts_epoch": ts_utc.timestamp(),
                            "product_id": pid,
                            "blocked_by": "",
                            "signal_score": None,
                            "trough_pct": None,
                            "trough_n": None,
                        })

            if "[PAPER_BUY_SIGNAL]" in line:
                paper_count += 1
                if want_paper:
                    d = _extract_json_after_tag(line, "[PAPER_BUY_SIGNAL]")
                    ts_utc = _parse_local_bracket_ts(line)
                    if isinstance(d, dict) and ts_utc is not None and d.get("product_id"):
                        events.append({
                            "event": "PAPER_BUY_SIGNAL",
                            "ts_local": line[1:20] if line.startswith("[") else "",
                            "ts_utc": ts_utc,
                            "ts_epoch": ts_utc.timestamp(),
                            "product_id": str(d.get("product_id") or ""),
                            "blocked_by": str(d.get("blocked_by") or ""),
                            "signal_score": d.get("score"),
                            "trough_pct": d.get("trough_pct"),
                            "trough_n": d.get("trough_n"),
                        })

    tdi_rows = _load_tdi_rows(tdi_path, since_utc=run_start_utc, max_lines=max(5000, int(tail_lines) * 4))
    by_pid: Dict[str, Dict[str, Any]] = {}
    for row in tdi_rows:
        pid = row["product_id"]
        if pid not in by_pid:
            by_pid[pid] = {"times": [], "rows": []}
        by_pid[pid]["times"].append(row["ts_epoch"])
        by_pid[pid]["rows"].append(row)

    joined: List[Dict[str, Any]] = []
    for e in events:
        bucket = by_pid.get(e["product_id"])
        if not bucket:
            continue
        idx = bisect_right(bucket["times"], e["ts_epoch"]) - 1
        if idx < 0:
            continue
        prior = bucket["rows"][idx]
        age_sec = round(float(e["ts_epoch"] - prior["ts_epoch"]), 1)
        joined.append({
            "ts_local": e["ts_local"],
            "event": e["event"],
            "product_id": e["product_id"],
            "blocked_by": e["blocked_by"],
            "signal_score": e["signal_score"],
            "trough_pct": e["trough_pct"],
            "trough_n": e["trough_n"],
            "age_sec": age_sec,
            "tdi_score": prior.get("tdi_score"),
            "tdi_trough": prior.get("tdi_trough"),
            "tdi_momentum": prior.get("tdi_momentum"),
            "tdi_liquidity": prior.get("tdi_liquidity"),
            "tdi_spread": prior.get("tdi_spread"),
            "tdi_pressure": prior.get("tdi_pressure"),
            "top1": prior.get("top1") or "",
            "top_reasons": ",".join(prior.get("top_reasons") or []),
        })

    driver_map: Dict[str, int] = {}
    for row in joined:
        k = str(row.get("top1") or "<none>")
        driver_map[k] = driver_map.get(k, 0) + 1
    driver_rows = [
        {"top1": k, "count": v, "pct": round(v / max(1, len(joined)) * 100.0, 2)}
        for k, v in sorted(driver_map.items(), key=lambda kv: (-kv[1], kv[0]))
    ]

    counts = {
        "run_start_local": run_start_local,
        "run_start_utc": _dt_iso_z(run_start_utc) if run_start_utc is not None else None,
        "fallback_tail_mode": fallback,
        "entry_source": entry_source,
        "tdi_snapshot_path": tdi_path,
        "tdi_snapshots_since_scope": len(tdi_rows),
        "paper_buy_signal_since_scope": paper_count,
        "buy_ok_since_scope": buy_ok_count,
        "sell_ok_since_scope": sell_ok_count,
        "selected_events_since_scope": len(events),
        "joined_rows": len(joined),
        "latest_rows_requested": int(latest_rows),
    }

    latest = joined[-max(1, int(latest_rows)):] if joined else []

    counts_lines = [f"{k}={v}" for k, v in counts.items()]
    report_lines: List[str] = []
    report_lines.append("MM25 TDI ENTRY ATTRIBUTION")
    report_lines.append("")
    report_lines.append("COUNTS")
    report_lines.extend(counts_lines)
    report_lines.append("")

    if joined:
        report_lines.append("TOP1 DRIVER DISTRIBUTION")
        report_lines.append(_rows_to_table(driver_rows, ["top1", "count", "pct"]))
        report_lines.append("")
        report_lines.append("LATEST JOINED ENTRY EVENTS")
        report_lines.append(_rows_to_table(
            latest,
            [
                "ts_local", "event", "product_id", "blocked_by", "signal_score",
                "trough_pct", "trough_n", "age_sec", "tdi_score", "tdi_trough", "top1",
            ],
        ))
        report_lines.append("")
    else:
        report_lines.append("NO JOIN ROWS PRODUCED")
        if len(events) == 0:
            report_lines.append("reason=no matching entry events found in the selected scope")
        elif len(tdi_rows) == 0:
            report_lines.append("reason=no TDI snapshots found in the selected scope")
        else:
            report_lines.append("reason=entry events existed, but none had a prior TDI snapshot for the same product_id")
        report_lines.append("")

    report_text = "\n".join(report_lines) + "\n"

    with open(os.path.join(pack_dir, "join_report.txt"), "w", encoding="utf-8") as f:
        f.write(report_text)
    _write_json(os.path.join(pack_dir, "counts.json"), counts)
    _write_json(os.path.join(pack_dir, "top1_driver_distribution.json"), driver_rows)
    _write_json(os.path.join(pack_dir, "joined_latest.json"), latest)
    _write_json(os.path.join(pack_dir, "joined_all.json"), joined)

    try:
        with open(os.path.join(pack_dir, f"activity_tail_{max(500, int(tail_lines))}.txt"), "w", encoding="utf-8") as f:
            f.write("\n".join(tail_ctx) + ("\n" if tail_ctx else ""))
    except Exception:
        pass

    _copy_if_exists(_abs_path(root, "run_settings.json"), pack_dir)

    zip_path = os.path.join(out_dir, f"mm25_tdi_entry_attribution_{entry_source}_{stamp}.zip")
    _zip_dir(pack_dir, zip_path)
    _open_explorer_select(zip_path)
    print(report_text, flush=True)
    print(f"CREATED: {zip_path}", flush=True)
    return 0




def _recent_signal_products(act_path: str, max_count: int = 8) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    run_start_off = _find_last_run_start_offset(act_path)
    off = run_start_off if run_start_off >= 0 else _tail_offset(act_path)
    with open(act_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(off)
        if off > 0 and run_start_off < 0:
            try:
                f.readline()
            except Exception:
                pass
        for raw in f:
            line = raw.rstrip("\n")
            if "[PAPER_BUY_SIGNAL]" not in line:
                continue
            d = _extract_json_after_tag(line, "[PAPER_BUY_SIGNAL]")
            pid = str((d or {}).get("product_id") or "").strip().upper()
            if not pid or pid in seen:
                continue
            seen.add(pid)
            out.append(pid)
    out.reverse()
    return out[: max(1, int(max_count))]


_DEFAULT_CYCLE_WATCHLIST: List[str] = [
    "XRP-USD", "SOL-USD", "ADA-USD", "HBAR-USD", "AVAX-USD", "LTC-USD",
    "LINK-USD", "DOGE-USD", "XLM-USD", "SUI-USD", "NEAR-USD", "TAO-USD",
]


def _recent_tdi_products(root: str, max_count: int = 8, tail_lines: int = 12000) -> List[str]:
    path = _abs_path(root, os.path.join("logs", "tdi_snapshots.jsonl"))
    if not os.path.exists(path):
        return []
    dq: Deque[str] = deque(maxlen=max(500, int(tail_lines)))
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as f:
            for raw in f:
                dq.append(raw.rstrip("\n"))
    except Exception:
        return []
    out: List[str] = []
    seen: set[str] = set()
    for line in reversed(list(dq)):
        try:
            d = json.loads(line)
        except Exception:
            d = None
        pid = str((d or {}).get("product_id") or "").strip().upper()
        if not pid or pid in seen:
            continue
        seen.add(pid)
        out.append(pid)
        if len(out) >= max(1, int(max_count)):
            break
    return out


def _default_cycle_products(cfg: Dict[str, Any], max_count: int = 8) -> List[str]:
    out: List[str] = []
    seen: set[str] = set()
    candidates: List[str] = []
    default_pid = str(cfg.get("DEFAULT_PRODUCT_ID") or "").strip().upper()
    if default_pid:
        candidates.append(default_pid)
    for key in ("UNIVERSE_LIST", "MAJORS_LIST"):
        vals = cfg.get(key) or []
        if isinstance(vals, list):
            for v in vals:
                sv = str(v or "").strip().upper()
                if sv:
                    candidates.append(sv)
    candidates.extend(_DEFAULT_CYCLE_WATCHLIST)
    for pid in candidates:
        if not pid or pid in seen:
            continue
        seen.add(pid)
        out.append(pid)
        if len(out) >= max(1, int(max_count)):
            break
    return out


def _resolve_cycle_products(act_path: str, root: str, cfg: Dict[str, Any], max_count: int = 8) -> Tuple[List[str], str]:
    recent_paper = _recent_signal_products(act_path, max_count=max_count)
    if recent_paper:
        return recent_paper, "recent_paper_signals"
    recent_tdi = _recent_tdi_products(root, max_count=max_count)
    if recent_tdi:
        return recent_tdi, "recent_tdi_snapshots"
    return _default_cycle_products(cfg, max_count=max_count), "default_watchlist"


def _fetch_candles_by_count(pid: str, gran: int, bars: int) -> List[List[float]]:
    """Fetch up to ``bars`` candles using the Exchange candles endpoint.

    The Exchange endpoint rejects requests whose requested time span implies
    more than 300 buckets. We therefore page backward in chunks that stay
    safely under that cap and de-duplicate by timestamp across pages.
    """
    bars = max(10, int(bars))
    gran = int(gran)
    # Keep a safety margin under the endpoint's 300-candle hard cap so that
    # inclusive boundary handling never tips a request into HTTP 400.
    chunk_max = 295
    out: List[List[float]] = []
    seen_ts: set[int] = set()
    cursor_end = datetime.now(timezone.utc)
    attempts = 0

    while len(out) < bars and attempts < 20:
        remaining = max(0, bars - len(out))
        if remaining <= 0:
            break
        need = max(10, min(chunk_max, remaining))
        # Request exactly ``need`` buckets worth of span (minus one interval
        # because the end boundary itself already accounts for the final bar).
        span_bars = max(1, int(need) - 1)
        start_dt = cursor_end - timedelta(seconds=gran * span_bars)
        chunk = _fetch_candles(pid, start_dt, cursor_end, gran)
        if not chunk:
            break

        fresh: List[List[float]] = []
        for c in chunk:
            try:
                ts = int(c[0])
            except Exception:
                continue
            if ts in seen_ts:
                continue
            seen_ts.add(ts)
            fresh.append(c)
        if not fresh:
            break

        out = fresh + out
        earliest_ts = int(fresh[0][0])
        cursor_end = datetime.fromtimestamp(max(0, earliest_ts - gran), tz=timezone.utc)
        attempts += 1

    if len(out) > bars:
        out = out[-bars:]
    return sorted(out, key=lambda x: x[0])


def _aggregate_candles(candles: List[List[float]], group_size: int) -> List[List[float]]:
    if not candles or group_size <= 1:
        return list(candles)
    out: List[List[float]] = []
    for i in range(0, len(candles), int(group_size)):
        chunk = candles[i : i + int(group_size)]
        if len(chunk) < int(group_size):
            continue
        ts = int(chunk[0][0])
        low = min(float(c[1]) for c in chunk)
        high = max(float(c[2]) for c in chunk)
        open_px = float(chunk[0][3])
        close_px = float(chunk[-1][4])
        vol = sum(float(c[5]) for c in chunk)
        out.append([ts, low, high, open_px, close_px, vol])
    return out


def _zigzag_swings(candles: List[List[float]], min_swing_pct: float, min_bars: int) -> Tuple[List[Dict[str, Any]], int]:
    swings: List[Dict[str, Any]] = []
    if len(candles) < 3:
        return swings, 0

    closes = [float(c[4]) for c in candles]
    min_idx = max_idx = 0
    min_price = max_price = closes[0]
    direction = 0  # 1=rising from trough, -1=falling from crest, 0=unknown

    for i in range(1, len(closes)):
        p = closes[i]
        if direction == 0:
            if p <= min_price:
                min_price = p
                min_idx = i
            if p >= max_price:
                max_price = p
                max_idx = i
            up_move = ((p / min_price) - 1.0) * 100.0 if min_price > 0 else 0.0
            down_move = ((max_price / p) - 1.0) * 100.0 if p > 0 else 0.0
            if up_move >= min_swing_pct and (i - min_idx) >= min_bars:
                swings.append({
                    "idx": min_idx,
                    "type": "trough",
                    "ts_epoch": int(candles[min_idx][0]),
                    "ts_utc": datetime.fromtimestamp(int(candles[min_idx][0]), tz=timezone.utc),
                    "price": float(min_price),
                })
                direction = 1
                max_idx = i
                max_price = p
            elif down_move >= min_swing_pct and (i - max_idx) >= min_bars:
                swings.append({
                    "idx": max_idx,
                    "type": "crest",
                    "ts_epoch": int(candles[max_idx][0]),
                    "ts_utc": datetime.fromtimestamp(int(candles[max_idx][0]), tz=timezone.utc),
                    "price": float(max_price),
                })
                direction = -1
                min_idx = i
                min_price = p
        elif direction == 1:
            if p >= max_price:
                max_price = p
                max_idx = i
            down_move = ((max_price / p) - 1.0) * 100.0 if p > 0 else 0.0
            if down_move >= min_swing_pct and (i - max_idx) >= min_bars:
                swings.append({
                    "idx": max_idx,
                    "type": "crest",
                    "ts_epoch": int(candles[max_idx][0]),
                    "ts_utc": datetime.fromtimestamp(int(candles[max_idx][0]), tz=timezone.utc),
                    "price": float(max_price),
                })
                direction = -1
                min_idx = i
                min_price = p
        else:
            if p <= min_price:
                min_price = p
                min_idx = i
            up_move = ((p / min_price) - 1.0) * 100.0 if min_price > 0 else 0.0
            if up_move >= min_swing_pct and (i - min_idx) >= min_bars:
                swings.append({
                    "idx": min_idx,
                    "type": "trough",
                    "ts_epoch": int(candles[min_idx][0]),
                    "ts_utc": datetime.fromtimestamp(int(candles[min_idx][0]), tz=timezone.utc),
                    "price": float(min_price),
                })
                direction = 1
                max_idx = i
                max_price = p
    return swings, direction


def _avg(vals: List[float]) -> Optional[float]:
    if not vals:
        return None
    return sum(vals) / float(len(vals))


def _current_phase(swings: List[Dict[str, Any]], direction: int) -> str:
    if not swings:
        return "unknown"
    last_type = str(swings[-1].get("type") or "")
    if direction > 0 and last_type == "trough":
        return "lifting_from_trough"
    if direction < 0 and last_type == "crest":
        return "descending_from_crest"
    if last_type == "trough":
        return "bottoming"
    if last_type == "crest":
        return "rolling_over"
    return "unknown"


def _safe_round(v: Optional[float], nd: int = 2) -> Optional[float]:
    if v is None:
        return None
    try:
        return round(float(v), nd)
    except Exception:
        return None


_INTERVALS: List[Tuple[str, int, int, str]] = [
    ("1m", 60, 1, "native_exchange"),
    ("5m", 300, 1, "native_exchange"),
    ("15m", 900, 1, "native_exchange"),
    ("30m", 900, 2, "synthetic_from_15m"),
    ("1h", 3600, 1, "native_exchange"),
    ("2h", 3600, 2, "synthetic_from_1h"),
    ("4h", 3600, 4, "synthetic_from_1h"),
    ("6h", 21600, 1, "native_exchange"),
    ("1d", 86400, 1, "native_exchange"),
]


def _analyze_cycle_interval(
    product_id: str,
    interval_name: str,
    candles: List[List[float]],
    tp_pct: float,
    adverse_pct: float,
    min_swing_pct: float,
    min_bars: int,
    source_kind: str,
) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    summary: Dict[str, Any] = {
        "product_id": product_id,
        "interval": interval_name,
        "source": source_kind,
        "bars": len(candles),
        "crests": 0,
        "troughs": 0,
        "swings": 0,
        "crest_to_crest_med_min": None,
        "trough_to_trough_med_min": None,
        "crest_to_trough_med_min": None,
        "trough_to_crest_med_min": None,
        "avg_drawdown_pct": None,
        "avg_rebound_pct": None,
        "tp_hit_rate_pct": None,
        "adverse_first_rate_pct": None,
        "both_same_rate_pct": None,
        "neither_rate_pct": None,
        "median_min_to_tp": None,
        "qualified_troughs": 0,
        "current_phase": "unknown",
        "note": "",
    }
    if len(candles) < max(12, int(min_bars) + 3):
        summary["note"] = "insufficient_bars"
        return summary, []

    swings, direction = _zigzag_swings(candles, float(min_swing_pct), int(min_bars))
    summary["swings"] = len(swings)
    summary["crests"] = sum(1 for s in swings if s["type"] == "crest")
    summary["troughs"] = sum(1 for s in swings if s["type"] == "trough")
    summary["current_phase"] = _current_phase(swings, direction)

    swing_rows: List[Dict[str, Any]] = []
    crest_to_crest: List[float] = []
    trough_to_trough: List[float] = []
    crest_to_trough: List[float] = []
    trough_to_crest: List[float] = []
    drawdowns: List[float] = []
    rebounds: List[float] = []

    prev_crest: Optional[Dict[str, Any]] = None
    prev_trough: Optional[Dict[str, Any]] = None
    for i, s in enumerate(swings):
        swing_rows.append({
            "product_id": product_id,
            "interval": interval_name,
            "source": source_kind,
            "swing_idx": i,
            "type": s["type"],
            "ts_utc": _dt_iso_z(s["ts_utc"]),
            "price": _safe_round(s["price"], 8),
        })
        if s["type"] == "crest":
            if prev_crest is not None:
                crest_to_crest.append((s["ts_epoch"] - prev_crest["ts_epoch"]) / 60.0)
            prev_crest = s
        if s["type"] == "trough":
            if prev_trough is not None:
                trough_to_trough.append((s["ts_epoch"] - prev_trough["ts_epoch"]) / 60.0)
            prev_trough = s

    for a, b in zip(swings, swings[1:]):
        if a["type"] == "crest" and b["type"] == "trough":
            crest_to_trough.append((b["ts_epoch"] - a["ts_epoch"]) / 60.0)
            if a["price"] > 0:
                drawdowns.append((1.0 - (b["price"] / a["price"])) * 100.0)
        elif a["type"] == "trough" and b["type"] == "crest":
            trough_to_crest.append((b["ts_epoch"] - a["ts_epoch"]) / 60.0)
            if a["price"] > 0:
                rebounds.append(((b["price"] / a["price"]) - 1.0) * 100.0)

    summary["crest_to_crest_med_min"] = _safe_round(_median(crest_to_crest), 2)
    summary["trough_to_trough_med_min"] = _safe_round(_median(trough_to_trough), 2)
    summary["crest_to_trough_med_min"] = _safe_round(_median(crest_to_trough), 2)
    summary["trough_to_crest_med_min"] = _safe_round(_median(trough_to_crest), 2)
    summary["avg_drawdown_pct"] = _safe_round(_avg(drawdowns), 4)
    summary["avg_rebound_pct"] = _safe_round(_avg(rebounds), 4)

    tp_hits = 0
    adverse_hits = 0
    both_same = 0
    neither = 0
    tp_minutes: List[float] = []
    qualified = 0
    for i, s in enumerate(swings):
        if s["type"] != "trough":
            continue
        next_crest = None
        for j in range(i + 1, len(swings)):
            if swings[j]["type"] == "crest":
                next_crest = swings[j]
                break
        end_idx = int(next_crest["idx"]) if next_crest is not None else (len(candles) - 1)
        if end_idx <= int(s["idx"]):
            continue
        qualified += 1
        entry = float(s["price"])
        tp_px = entry * (1.0 + (float(tp_pct) / 100.0))
        adv_px = entry * (1.0 - (float(adverse_pct) / 100.0)) if float(adverse_pct) > 0 else None
        first = "neither"
        for c in candles[int(s["idx"]) + 1 : end_idx + 1]:
            lo = float(c[1])
            hi = float(c[2])
            ts_epoch = int(c[0])
            hit_tp = hi >= tp_px
            hit_adv = (adv_px is not None) and (lo <= adv_px)
            if hit_tp and hit_adv:
                both_same += 1
                first = "both"
                break
            if hit_tp:
                tp_hits += 1
                tp_minutes.append((ts_epoch - int(s["ts_epoch"])) / 60.0)
                first = "tp"
                break
            if hit_adv:
                adverse_hits += 1
                first = "adverse"
                break
        if first == "neither":
            neither += 1

    summary["qualified_troughs"] = int(qualified)
    if qualified > 0:
        summary["tp_hit_rate_pct"] = _safe_round((tp_hits / float(qualified)) * 100.0, 2)
        summary["adverse_first_rate_pct"] = _safe_round((adverse_hits / float(qualified)) * 100.0, 2)
        summary["both_same_rate_pct"] = _safe_round((both_same / float(qualified)) * 100.0, 2)
        summary["neither_rate_pct"] = _safe_round((neither / float(qualified)) * 100.0, 2)
        summary["median_min_to_tp"] = _safe_round(_median(tp_minutes), 2)
    else:
        summary["note"] = "no_qualified_trough_to_crest_pairs"

    return summary, swing_rows


def _tp_relative_cycle_map(
    act_path: str,
    root: str,
    out_dir: str,
    product_ids: List[str],
    tp_pct: float,
    adverse_pct: float,
    bars_per_interval: int = 240,
    min_swing_pct: float = 3.0,
    min_bars: int = 2,
    products_source: str = "provided",
) -> int:
    os.makedirs(out_dir, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    pack_dir = os.path.join(out_dir, f"mm25_cycle_map_{stamp}")
    os.makedirs(pack_dir, exist_ok=True)

    bars_per_interval = max(30, min(int(bars_per_interval), 300))
    product_ids = [str(x or "").strip().upper() for x in product_ids if str(x or "").strip()]
    product_ids = list(dict.fromkeys(product_ids))

    summary_rows: List[Dict[str, Any]] = []
    swing_rows: List[Dict[str, Any]] = []
    fetch_errors: List[Dict[str, Any]] = []

    daily_caches: Dict[str, List[List[float]]] = {}

    for pid in product_ids:
        for interval_name, fetch_gran, agg_size, source_kind in _INTERVALS:
            candles: List[List[float]] = []
            fetch_bars = int(bars_per_interval) * max(1, int(agg_size))
            try:
                base_candles = _fetch_candles_by_count(pid, fetch_gran, fetch_bars)
                candles = _aggregate_candles(base_candles, agg_size) if int(agg_size) > 1 else list(base_candles)
                if len(candles) > int(bars_per_interval):
                    candles = candles[-int(bars_per_interval):]
            except Exception as e:
                fetch_errors.append({"product_id": pid, "interval": interval_name, "error": f"{type(e).__name__}: {e}"})
                candles = []
            if interval_name == "1d":
                daily_caches[pid] = list(candles)
            summary, swings = _analyze_cycle_interval(
                pid,
                interval_name,
                candles,
                tp_pct=tp_pct,
                adverse_pct=adverse_pct,
                min_swing_pct=min_swing_pct,
                min_bars=min_bars,
                source_kind=source_kind,
            )
            summary_rows.append(summary)
            swing_rows.extend(swings)

        daily = daily_caches.get(pid) or []
        for interval_name, group_size in (("1w", 7), ("1mo", 30)):
            agg = _aggregate_candles(daily, group_size)
            summary, swings = _analyze_cycle_interval(
                pid,
                interval_name,
                agg,
                tp_pct=tp_pct,
                adverse_pct=adverse_pct,
                min_swing_pct=min_swing_pct,
                min_bars=max(1, min_bars),
                source_kind="synthetic_from_1d",
            )
            summary_rows.append(summary)
            swing_rows.extend(swings)

    def _winner_eligible(row: Dict[str, Any]) -> bool:
        try:
            troughs = int(row.get("qualified_troughs") or 0)
        except Exception:
            troughs = 0
        try:
            swings = int(row.get("swings") or 0)
        except Exception:
            swings = 0
        try:
            bars = int(row.get("bars") or 0)
        except Exception:
            bars = 0
        if troughs < 3:
            return False
        if swings < 5:
            return False
        if bars < 24:
            return False
        return True

    def _rank_key(row: Dict[str, Any]) -> Tuple[float, float, float, float, float]:
        tp_hit = float(row.get("tp_hit_rate_pct") or 0.0)
        adverse = float(row.get("adverse_first_rate_pct") or 0.0)
        both = float(row.get("both_same_rate_pct") or 0.0)
        med = float(row.get("median_min_to_tp") or 1e9)
        troughs = float(row.get("qualified_troughs") or 0.0)
        sparse_penalty = 0.0
        if str(row.get("source") or "") == "synthetic_from_1d":
            sparse_penalty += 7.5
            if troughs < 4.0:
                sparse_penalty += 7.5
        return (-(tp_hit - sparse_penalty), adverse + both, med, -float(row.get("avg_rebound_pct") or 0.0), -troughs)

    best_rows: List[Dict[str, Any]] = []
    by_pid: Dict[str, List[Dict[str, Any]]] = {}
    for row in summary_rows:
        by_pid.setdefault(str(row.get("product_id") or ""), []).append(row)
    for pid, rows in by_pid.items():
        good = [r for r in rows if r.get("bars") and (r.get("tp_hit_rate_pct") is not None)]
        if not good:
            continue
        eligible = [r for r in good if _winner_eligible(r)]
        ranked = eligible if eligible else good
        best_rows.append(sorted(ranked, key=_rank_key)[0])
    best_rows.sort(key=lambda r: (str(r.get("product_id") or ""), _rank_key(r)))

    meta = {
        "created_local": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tp_pct": tp_pct,
        "adverse_pct": adverse_pct,
        "bars_per_interval": bars_per_interval,
        "min_swing_pct": min_swing_pct,
        "min_bars_between_swings": min_bars,
        "products": product_ids,
        "products_source": products_source,
        "products_count": len(product_ids),
        "intervals": [x[0] for x in _INTERVALS] + ["1w", "1mo"],
        "winner_min_qualified_troughs": 3,
        "winner_min_swings": 5,
        "winner_synthetic_penalty": "synthetic_from_1d intervals get a ranking penalty; extra penalty when qualified_troughs < 4",
        "note": "1w and 1mo are synthesized from 1d Coinbase candles.",
        "fetch_errors": fetch_errors,
    }

    report_lines: List[str] = []
    report_lines.append("MM25 TP-RELATIVE CYCLE MAP")
    report_lines.append("")
    for k, v in meta.items():
        report_lines.append(f"{k}={v}")
    report_lines.append("")
    report_lines.append("BEST INTERVAL PER PRODUCT")
    report_lines.append(_rows_to_table(best_rows, [
        "product_id", "interval", "source", "bars", "qualified_troughs", "tp_hit_rate_pct", "adverse_first_rate_pct",
        "median_min_to_tp", "trough_to_crest_med_min", "crest_to_crest_med_min", "avg_rebound_pct",
        "avg_drawdown_pct", "current_phase",
    ]))
    report_lines.append("")
    report_lines.append("ALL PRODUCT / INTERVAL ROWS")
    report_lines.append(_rows_to_table(summary_rows, [
        "product_id", "interval", "source", "bars", "swings", "crests", "troughs", "qualified_troughs",
        "tp_hit_rate_pct", "adverse_first_rate_pct", "median_min_to_tp", "trough_to_crest_med_min",
        "crest_to_crest_med_min", "avg_rebound_pct", "avg_drawdown_pct", "current_phase", "note",
    ]))
    report_text = "\n".join(report_lines) + "\n"

    with open(os.path.join(pack_dir, "cycle_structure_report.txt"), "w", encoding="utf-8") as f:
        f.write(report_text)
    _write_json(os.path.join(pack_dir, "cycle_structure_meta.json"), meta)
    _write_json(os.path.join(pack_dir, "cycle_structure_best_intervals.json"), best_rows)
    _write_json(os.path.join(pack_dir, "cycle_structure_fetch_errors.json"), fetch_errors)

    # CSVs (Excel-friendly)
    import csv
    def _write_csv(path_csv: str, rows_csv: List[Dict[str, Any]], columns_csv: List[str]) -> None:
        with open(path_csv, "w", encoding="utf-8", newline="") as f:
            w = csv.DictWriter(f, fieldnames=columns_csv)
            w.writeheader()
            for row in rows_csv:
                out = {c: row.get(c) for c in columns_csv}
                w.writerow(out)

    summary_cols = [
        "product_id", "interval", "source", "bars", "swings", "crests", "troughs",
        "crest_to_crest_med_min", "trough_to_trough_med_min", "crest_to_trough_med_min", "trough_to_crest_med_min",
        "avg_drawdown_pct", "avg_rebound_pct", "tp_hit_rate_pct", "adverse_first_rate_pct", "both_same_rate_pct",
        "neither_rate_pct", "median_min_to_tp", "current_phase", "note",
    ]
    swing_cols = ["product_id", "interval", "source", "swing_idx", "type", "ts_utc", "price"]
    best_cols = [
        "product_id", "interval", "source", "bars", "tp_hit_rate_pct", "adverse_first_rate_pct",
        "median_min_to_tp", "trough_to_crest_med_min", "crest_to_crest_med_min", "avg_rebound_pct",
        "avg_drawdown_pct", "current_phase", "note",
    ]
    _write_csv(os.path.join(pack_dir, "cycle_structure_per_coin.csv"), summary_rows, summary_cols)
    _write_csv(os.path.join(pack_dir, "cycle_structure_swings.csv"), swing_rows, swing_cols)
    _write_csv(os.path.join(pack_dir, "cycle_structure_best_intervals.csv"), best_rows, best_cols)

    try:
        with open(os.path.join(pack_dir, "products_analyzed.txt"), "w", encoding="utf-8") as f:
            for pid in product_ids:
                f.write(f"{pid}\n")
    except Exception:
        pass
    _copy_if_exists(_abs_path(root, "run_settings.json"), pack_dir)

    zip_path = os.path.join(out_dir, f"mm25_cycle_map_{stamp}.zip")
    _zip_dir(pack_dir, zip_path)
    _open_explorer_select(zip_path)
    print(report_text, flush=True)
    print(f"CREATED: {zip_path}", flush=True)
    return 0
def main() -> int:
    ap = argparse.ArgumentParser(add_help=True)
    ap.add_argument("--target", type=int, default=50, help="Target PAPER_BUY_SIGNAL count")
    ap.add_argument("--max-minutes", type=int, default=120, help="Max minutes to wait")
    ap.add_argument("--limit", type=int, default=50, help="Max signals to score (most recent)")
    ap.add_argument("--forward-min", type=int, default=180, help="Forward window minutes (default 180)")
    ap.add_argument("--allow-partial", action="store_true", help="Allow scoring partial forward windows (default requires full window)")
    ap.add_argument("--pause", action="store_true", help="Wait for ENTER before exit")
    ap.add_argument("--mode", choices=["score", "event", "tdi", "cycle"], default="score", help="Tool mode: score=wait+score paper signals, event=watch BUY_OK/SELL_OK, tdi=entry attribution zip, cycle=TP-relative cycle map zip")
    ap.add_argument("--event", choices=["buy", "sell", "both"], default="both", help="Event watch: which events to capture")
    ap.add_argument("--entry-source", choices=["paper", "buy", "both"], default="paper", help="TDI attribution: which entry events to join")
    ap.add_argument("--latest-rows", type=int, default=40, help="TDI attribution: how many latest joined rows to include in the report")
    ap.add_argument("--tail-lines", type=int, default=250000, help="Event watch: how many activity log lines to include in the zip tail")
    ap.add_argument("--retro", action="store_true", help="Event watch: retro-capture last matching events from tail before live-follow")
    ap.add_argument("--event-out", type=str, default=os.path.join("logs", "analysis_live"), help="Event watch: output dir (relative to repo root)")
    ap.add_argument("--tdi-out", type=str, default=os.path.join("logs", "analysis_tdi"), help="TDI attribution: output dir (relative to repo root)")
    ap.add_argument("--event-max-minutes", type=int, default=720, help="Event watch: max minutes to wait for events")
    ap.add_argument("--cycle-out", type=str, default=os.path.join("logs", "analysis_cycle"), help="Cycle map: output dir (relative to repo root)")
    ap.add_argument("--products", type=str, default="", help="Cycle map: comma-separated product ids (blank=recent paper symbols)")
    ap.add_argument("--recent-products", type=int, default=8, help="Cycle map: if --products blank, analyze this many recent unique PAPER_BUY_SIGNAL symbols")
    ap.add_argument("--tp-pct", type=float, default=0.0, help="Cycle map: target TP percent (blank/0=use settings TP_PCT)")
    ap.add_argument("--adverse-pct", type=float, default=0.0, help="Cycle map: adverse move percent (blank/0=use settings SL_PCT)")
    ap.add_argument("--bars-per-interval", type=int, default=240, help="Cycle map: candles per interval (max 300)")
    ap.add_argument("--min-swing-pct", type=float, default=0.0, help="Cycle map: minimum swing percent (blank/0=auto max(tp/2,0.5))")
    ap.add_argument("--min-bars", type=int, default=2, help="Cycle map: minimum bars between swings")
    ap.add_argument("--no-prompt", action="store_true", help="Disable interactive prompts (useful when launched from menu)")
    args = ap.parse_args()

    no_prompt = bool(getattr(args, "no_prompt", False))

    cfg = _load_settings()
    root = _repo_root()

    act_rel = str(cfg.get("ACTIVITY_LOG_PATH") or "logs/activity_ticker.log")
    act_path = _abs_path(root, act_rel)

    # --- Mode selection (W tool) ---
    mode = str(getattr(args, "mode", "score") or "score").strip().lower()
    if sys.stdin.isatty() and (not no_prompt):
        print("")
        print("W tool modes:", flush=True)
        print("  1) Wait+score PAPER_BUY_SIGNAL (paper trough scoring)", flush=True)
        print("  2) Watch live BUY_OK/SELL_OK events (create event zips)", flush=True)
        print("  3) TDI entry attribution (zip report)", flush=True)
        print("  4) TP-relative cycle map (zip report)", flush=True)
        try:
            sel = input("Select mode [1]: ").strip()
            if sel == "2":
                mode = "event"
            elif sel == "3":
                mode = "tdi"
            elif sel == "4":
                mode = "cycle"
        except Exception:
            pass

    if mode == "event":
        capture = str(getattr(args, "event", "both") or "both").strip().lower()
        tail_lines = int(getattr(args, "tail_lines", 250000) or 250000)
        max_ev = int(getattr(args, "event_max_minutes", 720) or 720)
        if sys.stdin.isatty() and (not no_prompt):
            print("")
            print("Event capture options: 1) BUY_OK 2) SELL_OK 3) BOTH", flush=True)
            try:
                s = input("Capture [3]: ").strip()
                if s == "1":
                    capture = "buy"
                elif s == "2":
                    capture = "sell"
                else:
                    capture = "both"
            except Exception:
                pass
            tail_lines = _prompt_int(f"Tail lines [{tail_lines}]: ", tail_lines, lo=1000, hi=2000000)
            max_ev = _prompt_int(f"Max wait minutes [{max_ev}]: ", max_ev, lo=1, hi=100000)

        out_rel = str(getattr(args, "event_out", os.path.join("logs", "analysis_live")) or os.path.join("logs", "analysis_live"))
        out_dir = _abs_path(root, out_rel)
        rc = _event_watch(act_path, root, out_dir, capture=capture, tail_lines=tail_lines, max_minutes=max_ev, retro=bool(getattr(args, 'retro', False)))
        if bool(getattr(args, "pause", False)) and sys.stdin.isatty():
            input("Press ENTER to exit...")
        return rc


    if mode == "tdi":
        entry_source = str(getattr(args, "entry_source", "paper") or "paper").strip().lower()
        latest_rows = int(getattr(args, "latest_rows", 40) or 40)
        tail_lines = int(getattr(args, "tail_lines", 5000) or 5000)
        if sys.stdin.isatty() and (not no_prompt):
            print("")
            print("TDI entry attribution options: 1) PAPER_BUY_SIGNAL 2) BUY_OK 3) BOTH", flush=True)
            try:
                s = input("Source [1]: ").strip()
                if s == "2":
                    entry_source = "buy"
                elif s == "3":
                    entry_source = "both"
                else:
                    entry_source = "paper"
            except Exception:
                pass
            latest_rows = _prompt_int(f"Latest joined rows [{latest_rows}]: ", latest_rows, lo=1, hi=5000)
            tail_lines = _prompt_int(f"Activity/TDI tail lines in zip [{tail_lines}]: ", tail_lines, lo=500, hi=2000000)

        out_rel = str(getattr(args, "tdi_out", os.path.join("logs", "analysis_tdi")) or os.path.join("logs", "analysis_tdi"))
        out_dir = _abs_path(root, out_rel)
        rc = _tdi_entry_attribution(act_path, root, out_dir, entry_source=entry_source, latest_rows=latest_rows, tail_lines=tail_lines)
        if bool(getattr(args, "pause", False)) and sys.stdin.isatty():
            input("Press ENTER to exit...")
        return rc




    if mode == "cycle":
        tp_default = _norm_pct(cfg.get("TP_PCT")) or 2.0
        adverse_default = _norm_pct(cfg.get("SL_PCT")) or float(tp_default)
        bars_per_interval = int(getattr(args, "bars_per_interval", 240) or 240)
        recent_products = int(getattr(args, "recent_products", 8) or 8)
        min_bars = int(getattr(args, "min_bars", 2) or 2)
        products_csv = str(getattr(args, "products", "") or "").strip()
        tp_pct = float(getattr(args, "tp_pct", 0.0) or 0.0)
        adverse_pct = float(getattr(args, "adverse_pct", 0.0) or 0.0)
        min_swing_pct = float(getattr(args, "min_swing_pct", 0.0) or 0.0)

        if sys.stdin.isatty() and (not no_prompt):
            print("")
            print("TP-relative cycle map:", flush=True)
            print("Leave Product IDs blank to use recent PAPER_BUY_SIGNAL symbols.", flush=True)
            try:
                products_csv = input(f"Product IDs csv [recent paper x{recent_products}]: ").strip()
            except Exception:
                products_csv = products_csv
            recent_products = _prompt_int(f"Recent unique PAPER_BUY_SIGNAL symbols [{recent_products}]: ", recent_products, lo=1, hi=100)
            tp_pct = _prompt_float(f"Target TP percent [{tp_default}]: ", tp_default, lo=0.05, hi=100.0)
            adverse_pct = _prompt_float(f"Adverse move percent [{adverse_default}]: ", adverse_default, lo=0.05, hi=100.0)
            bars_per_interval = _prompt_int(f"Candles per interval [{bars_per_interval}] (max 300): ", bars_per_interval, lo=30, hi=300)
            auto_swing = max(float(tp_pct) / 2.0, 0.5)
            default_swing = float(min_swing_pct) if float(min_swing_pct) > 0 else auto_swing
            min_swing_pct = _prompt_float(f"Min swing percent [{default_swing}]: ", default_swing, lo=0.05, hi=100.0)
            min_bars = _prompt_int(f"Min bars between swings [{min_bars}]: ", min_bars, lo=1, hi=50)

        if tp_pct <= 0:
            tp_pct = float(tp_default)
        if adverse_pct <= 0:
            adverse_pct = float(adverse_default)
        if min_swing_pct <= 0:
            min_swing_pct = max(float(tp_pct) / 2.0, 0.5)

        product_ids = [x.strip().upper() for x in products_csv.split(",") if x.strip()]
        products_source = "provided_csv"
        if not product_ids:
            product_ids, products_source = _resolve_cycle_products(act_path, root, cfg, max_count=recent_products)
        print(
            f"Cycle map using {len(product_ids)} products [{products_source}]: {', '.join(product_ids)}",
            flush=True,
        )

        out_rel = str(getattr(args, "cycle_out", os.path.join("logs", "analysis_cycle")) or os.path.join("logs", "analysis_cycle"))
        out_dir = _abs_path(root, out_rel)
        rc = _tp_relative_cycle_map(
            act_path,
            root,
            out_dir,
            product_ids=product_ids,
            tp_pct=float(tp_pct),
            adverse_pct=float(adverse_pct),
            bars_per_interval=int(bars_per_interval),
            min_swing_pct=float(min_swing_pct),
            min_bars=int(min_bars),
            products_source=products_source,
        )
        if bool(getattr(args, "pause", False)) and sys.stdin.isatty():
            input("Press ENTER to exit...")
        return rc
    look_sec = float(cfg.get("TROUGH_LOOKBACK_SEC", 7200) or 7200)
    look_min = int(round(look_sec / 60.0))
    if look_min < 10:
        look_min = 10

    target = int(args.target or 0)
    if target < 1:
        target = 1
    max_minutes = int(args.max_minutes or 0)
    if max_minutes < 1:
        max_minutes = 1
    limit = int(args.limit or target)
    if limit < 1:
        limit = 1

    # Prompt for forward window inside the tool console (menu stays unchanged).
    forward_min = int(args.forward_min or 180)
    if sys.stdin.isatty() and (not no_prompt):
        print("")
        print("Forward window minutes options: 180=3h, 720=12h, 1440=24h", flush=True)
        forward_min = _prompt_int(f"Forward minutes [{forward_min}]: ", forward_min, lo=30, hi=20000)

    out_dir = _abs_path(root, os.path.join("logs", "analysis_trough"))
    os.makedirs(out_dir, exist_ok=True)

    print("=== MM24 PAPER-SIGNAL TROUGH WAIT+SCORE ===", flush=True)
    print(f"activity_log={act_path}", flush=True)
    print(f"target_signals={target}  max_wait_min={max_minutes}  score_limit={limit}", flush=True)
    print(f"lookback_min={look_min}  forward_min={forward_min}", flush=True)

    if not os.path.exists(act_path):
        print("ERROR: activity log not found.", flush=True)
        if args.pause:
            input("Press ENTER to exit...")
        return 2

    # By default, require a full forward window before counting/scoring a signal.
    # This prevents generating partial-window reports by accident.
    require_full = not bool(getattr(args, "allow_partial", False))
    if sys.stdin.isatty() and (not no_prompt):
        try:
            ans = input("Require full forward window? [Y/n]: ").strip().lower()
            if ans in ("n", "no", "0"):
                require_full = False
        except Exception:
            pass

    off = _tail_offset(act_path)
    # Keep enough history so long forward windows (12h/24h) can still reach target.
    signals: Deque[Dict[str, Any]] = deque(maxlen=max(target, limit, 20000))
    seen: set = set()
    total_seen = 0
    last_tick: Optional[int] = None

    start_time = time.time()
    deadline = start_time + (max_minutes * 60.0)

    def _is_mature(sig: Dict[str, Any], now_epoch: int) -> bool:
        if not require_full:
            return True
        e = sig.get("_ts_epoch")
        if not isinstance(e, int):
            return False
        return (e + int(forward_min) * 60) <= now_epoch

    with open(act_path, "r", encoding="utf-8", errors="ignore") as f:
        f.seek(off)
        if off > 0:
            # discard partial line
            try:
                f.readline()
            except Exception:
                pass

        # Backfill from log tail (does NOT depend on [run_start])
        for line in f:
            if "[PAPER_BUY_SIGNAL]" in line:
                d = _extract_json_after_tag(line, "[PAPER_BUY_SIGNAL]")
                if isinstance(d, dict):
                    ts = _parse_ts(d.get("ts_utc"))
                    if ts is not None:
                        d["_ts_epoch"] = int(ts.timestamp())
                    key = (d.get("ts_utc"), d.get("product_id"), d.get("tick"))
                    if key in seen:
                        continue
                    seen.add(key)
                    signals.append(d)
                    total_seen += 1
                    try:
                        last_tick = int(d.get("tick") or 0)
                    except Exception:
                        pass

        # Wait for enough eligible signals (mature-only if require_full=True)
        while True:
            now_epoch = int(datetime.now(timezone.utc).timestamp())
            eligible = sum(1 for s in signals if _is_mature(s, now_epoch))
            if eligible >= target:
                break
            if time.time() >= deadline:
                break

            line = f.readline()
            if line:
                if "[PAPER_BUY_SIGNAL]" in line:
                    d = _extract_json_after_tag(line, "[PAPER_BUY_SIGNAL]")
                    if isinstance(d, dict):
                        ts = _parse_ts(d.get("ts_utc"))
                        if ts is not None:
                            d["_ts_epoch"] = int(ts.timestamp())
                        key = (d.get("ts_utc"), d.get("product_id"), d.get("tick"))
                        if key in seen:
                            continue
                        seen.add(key)
                        signals.append(d)
                        total_seen += 1
                        try:
                            last_tick = int(d.get("tick") or 0)
                        except Exception:
                            pass
                        # progress line on every new signal
                        pct = int(min(100, round((eligible / max(1, target)) * 100)))
                        lt = "" if last_tick is None else f" tick={last_tick}"
                        print(
                            f'GOT total={total_seen} eligible={eligible}/{target} ({pct}%) pid={d.get("product_id")}{lt} blocked={d.get("blocked_by")}',
                            flush=True,
                        )
                continue

            # no new line -> heartbeat
            elapsed = int(time.time() - start_time)
            if elapsed % 10 == 0:
                pct = int(min(100, round((eligible / max(1, target)) * 100)))
                lt = "" if last_tick is None else f" last_tick={last_tick}"
                mode = "FULL" if require_full else "PARTIAL"
                print(
                    f"WAIT {pct:>3}%  eligible={eligible}/{target}  total={total_seen}  mode={mode}{lt}  elapsed={elapsed}s",
                    flush=True,
                )
            time.sleep(1.0)

            
    now_utc = datetime.now(timezone.utc)
    now_epoch = int(now_utc.timestamp())
    eligible_signals = [s for s in signals if _is_mature(s, now_epoch)]

    if len(eligible_signals) < 1:
        print("No eligible PAPER_BUY_SIGNAL lines collected; nothing to score.", flush=True)
        if args.pause:
            input("Press ENTER to exit...")
        return 0

    sig_list = eligible_signals[-limit:]

    scored: List[Dict[str, Any]] = []
    total = len(sig_list)
    for i, s in enumerate(sig_list, start=1):
        pid = s.get("product_id")
        ts = s.get("ts_utc")
        print(f"[{i}/{total}] score {pid} {ts} ...", flush=True)
        scored.append(_score_signal(s, look_min, forward_min, now_utc))
        time.sleep(0.15)

    # Summary
    internal_vals = [
        float(x["trough_pct_internal"])
        for x in scored
        if isinstance(x.get("trough_pct_internal"), (int, float))
    ]
    lookback_vals = [
        float(x["trough_pct_lookback"])
        for x in scored
        if isinstance(x.get("trough_pct_lookback"), (int, float))
    ]

    fwd_have = sum(
        1
        for x in scored
        if x.get("fwd_max_return_pct") is not None or x.get("fwd_min_return_pct") is not None
    )
    full_forward = sum(1 for x in scored if x.get("forward_full_window") is True)

    tp_hits = sum(1 for x in scored if x.get("would_hit_tp") is True)
    sl_hits = sum(1 for x in scored if x.get("would_hit_sl") is True)

    runup_vals = [
        float(x["fwd_max_return_pct"])
        for x in scored
        if isinstance(x.get("fwd_max_return_pct"), (int, float))
    ]
    dd_vals = [
        float(x["fwd_min_return_pct"])
        for x in scored
        if isinstance(x.get("fwd_min_return_pct"), (int, float))
    ]

    tp_first = sum(1 for x in scored if x.get("first_hit") == "tp")
    sl_first = sum(1 for x in scored if x.get("first_hit") == "sl")
    both_same = sum(1 for x in scored if x.get("first_hit") == "both")
    neither = sum(1 for x in scored if x.get("first_hit") == "neither")

    summ = {
        "signals_scored": len(scored),
        "lookback_min": look_min,
        "forward_min": forward_min,
        "fwd_data_pct": None if len(scored) == 0 else round(fwd_have / len(scored) * 100.0, 2),
        "full_forward_pct": None if len(scored) == 0 else round(full_forward / len(scored) * 100.0, 2),
        # trough timing: internal vs candle lookback
        "internal_trough_pct_median": _median(internal_vals),
        "internal_pct_in_bottom_10pct": None
        if not internal_vals
        else round(sum(1 for v in internal_vals if v <= 0.10) / len(internal_vals) * 100.0, 2),
        "internal_pct_in_bottom_20pct": None
        if not internal_vals
        else round(sum(1 for v in internal_vals if v <= 0.20) / len(internal_vals) * 100.0, 2),
        "lookback_trough_pct_median": _median(lookback_vals),
        "lookback_pct_in_bottom_10pct": None
        if not lookback_vals
        else round(sum(1 for v in lookback_vals if v <= 0.10) / len(lookback_vals) * 100.0, 2),
        "lookback_pct_in_bottom_20pct": None
        if not lookback_vals
        else round(sum(1 for v in lookback_vals if v <= 0.20) / len(lookback_vals) * 100.0, 2),
        # TP/SL touch stats
        "tp_hit_rate_window_pct": None if len(scored) == 0 else round(tp_hits / len(scored) * 100.0, 2),
        "sl_hit_rate_window_pct": None if len(scored) == 0 else round(sl_hits / len(scored) * 100.0, 2),
        # First-hit ordering
        "tp_first_rate_pct": None if len(scored) == 0 else round(tp_first / len(scored) * 100.0, 2),
        "sl_first_rate_pct": None if len(scored) == 0 else round(sl_first / len(scored) * 100.0, 2),
        "both_same_candle_rate_pct": None if len(scored) == 0 else round(both_same / len(scored) * 100.0, 2),
        "neither_rate_pct": None if len(scored) == 0 else round(neither / len(scored) * 100.0, 2),
        # Run-up / drawdown distributions
        "runup_p50_pct": _pct(runup_vals, 50),
        "runup_p75_pct": _pct(runup_vals, 75),
        "runup_p90_pct": _pct(runup_vals, 90),
        "runup_max_pct": max(runup_vals) if runup_vals else None,
        "dd_p50_pct": _pct(dd_vals, 50),
        "dd_p10_pct": _pct(dd_vals, 10),
        "dd_worst_pct": min(dd_vals) if dd_vals else None,
    }

    # Write artifacts
    stamp = time.strftime("%Y%m%d_%H%M%S")
    paper_path = os.path.join(out_dir, "paper_signals.jsonl")
    with open(paper_path, "w", encoding="utf-8") as f:
        for s in sig_list:
            f.write(json.dumps(s, separators=(",", ":")) + "\n")

    score_path = os.path.join(out_dir, "paper_signal_trough_score.json")
    with open(score_path, "w", encoding="utf-8") as f:
        json.dump(scored, f, indent=2)

    summ_path = os.path.join(out_dir, "paper_signal_trough_summary.json")
    with open(summ_path, "w", encoding="utf-8") as f:
        json.dump(summ, f, indent=2)

    zip_name = f"mm24_paper_signal_trough_score_fixedtp_{stamp}.zip"
    zip_path = os.path.join(out_dir, zip_name)

    import zipfile

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as z:
        z.write(paper_path, arcname="paper_signals.jsonl")
        z.write(score_path, arcname="paper_signal_trough_score.json")
        z.write(summ_path, arcname="paper_signal_trough_summary.json")

    print("SUMMARY:", json.dumps(summ, separators=(",", ":")), flush=True)
    print("CREATED:", zip_path, flush=True)
    _open_explorer_select(zip_path)

    if args.pause:
        input("Press ENTER to close...")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())