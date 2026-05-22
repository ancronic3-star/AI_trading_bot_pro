#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
MM23 Run Diagnostics / Run Analytics (Full Metrics, v15)

Read-only diagnostic tool intended to answer:
- Are we buying troughs or crests?
- Are exits (TP/SL) behaving and profitable after fees?
- Are LIMIT_ONLY entries filling cleanly?
- Do held positions have Coinbase-side bracket protection?
- Any duplicate open sells / oversell risk?

Usage examples:
  python -u -m managers.logging_manager.diag_run_analytics --since-ticks 5000 --pause
  python -u -m managers.logging_manager.diag_run_analytics --since-hours 6 --pause
  python -u -m managers.logging_manager.diag_run_analytics --since-run-start --pause

Output:
  Creates mm23_run_diag_pack_<timestamp>.zip in project root.
  Prints key summary lines prefixed [MM23_DIAG].

Guardrails:
  - Read-only (no cancels, no edits, no sells).
  - PFID from env, COINBASE_KEY_FILE from env (via auth_jwt.get_client()).
"""

from __future__ import annotations

import argparse
import inspect
import csv
import json
import os
import sys
import time
import zipfile
import subprocess
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

# Ensure repo root on sys.path for -m runs from anywhere
try:
    _ROOT = Path(__file__).resolve().parents[2]
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
except Exception:
    pass

# External deps are allowed in the project environment
try:
    import requests
except Exception:
    requests = None  # type: ignore

# Project client
from managers.auth_manager.auth_jwt import get_client  # type: ignore


# -----------------------------
# Helpers
# -----------------------------

def _now_utc() -> datetime:
    return datetime.now(timezone.utc)

def _parse_dt(s: str) -> Optional[datetime]:
    if not s:
        return None
    s = str(s).strip()
    # normalize Z
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    fmts = [
        "%Y-%m-%d %H:%M:%S",
    ]
    # try fromisoformat
    try:
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        pass
    for f in fmts:
        try:
            dt = datetime.strptime(s, f).replace(tzinfo=timezone.utc)
            return dt
        except Exception:
            continue
    return None

def _safe_float(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return default
        if isinstance(x, (int, float)):
            return float(x)
        s = str(x).strip()
        if s == "":
            return default
        return float(s)
    except Exception:
        return default

def _safe_int(x: Any, default: int = 0) -> int:
    try:
        if x is None:
            return default
        if isinstance(x, int):
            return int(x)
        if isinstance(x, float):
            return int(x)
        s = str(x).strip()
        if s == "":
            return default
        return int(float(s))
    except Exception:
        return default

def _to_dict(obj: Any) -> Dict[str, Any]:
    if obj is None:
        return {}
    if isinstance(obj, dict):
        return obj
    td = getattr(obj, "to_dict", None)
    if callable(td):
        try:
            d = td()
            return d if isinstance(d, dict) else {}
        except Exception:
            return {}
    try:
        return dict(obj)  # type: ignore
    except Exception:
        return {}

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)

def _root_find(start: Path) -> Path:
    """
    Find project root by searching up for run_settings.json.
    """
    cur = start
    for _ in range(6):
        if (cur / "run_settings.json").exists():
            return cur
        cur = cur.parent
    # fallback to cwd if it has run_settings.json
    cwd = Path.cwd().resolve()
    if (cwd / "run_settings.json").exists():
        return cwd
    # last resort: module-derived
    return start

def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))

def _write_text(path: Path, s: str) -> None:
    path.write_text(s, encoding="utf-8")

def _write_json(path: Path, obj: Any) -> None:
    path.write_text(json.dumps(obj, indent=2, ensure_ascii=False), encoding="utf-8")

def _write_jsonl(path: Path, rows: Iterable[Dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")

def _tail_lines(path: Path, n: int) -> List[str]:
    """
    Tail last n lines from a file efficiently.
    """
    # Simple approach (log sizes manageable on this machine).
    # If extremely large, OS will handle file paging.
    with path.open("r", encoding="utf-8", errors="replace") as f:
        return f.readlines()[-n:]

def _extract_ts(line: str) -> Optional[datetime]:
    # log lines begin: [YYYY-MM-DD HH:MM:SS]
    if not line.startswith("["):
        return None
    if len(line) < 21:
        return None
    ts = line[1:20]
    try:
        return datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except Exception:
        return None

def _find_last_run_start(lines: List[str]) -> Optional[datetime]:
    rs: Optional[datetime] = None
    for l in lines:
        if "[run_start]" in l:
            dt = _extract_ts(l)
            if dt:
                rs = dt
    return rs

def _last_tickdiag_window_start(lines: List[str], since_ticks: int) -> Optional[datetime]:
    # Find earliest timestamp among last N [tick_diag] lines
    tick_lines = [l for l in lines if "[tick_diag]" in l]
    if not tick_lines:
        return None
    use = tick_lines[-since_ticks:] if len(tick_lines) > since_ticks else tick_lines
    first = use[0]
    return _extract_ts(first)

def _slice_since_time(lines: List[str], start: datetime) -> List[str]:
    """Slice log tail by time, but keep non-timestamp continuation lines.

    Many log formats include non-timestamp lines (e.g., [tick_diag]) that follow a
    timestamped line. Once we've crossed 'start', we include all subsequent lines
    even if they lack a timestamp.
    """
    out: List[str] = []
    started = False
    for l in lines:
        dt = _extract_ts(l)
        if dt is not None:
            started = dt >= start
        if started:
            out.append(l)
    return out

def _read_run_slice_tail(activity_path: Path, run_start: datetime, tail_lines: int) -> List[str]:
    # take tail and then slice by run_start (fallback: if slice yields 0 lines, return the raw tail)
    tail = _tail_lines(activity_path, max(1000, tail_lines))
    out = _slice_since_time(tail, run_start)
    return out if out else tail

# -----------------------------
# Coinbase REST helpers (read-only)
# -----------------------------

def _client_list_orders(client: Any, status: str, cursor: Optional[str], limit: int) -> Tuple[List[Dict[str, Any]], Optional[str]]:
    fn = getattr(client, "list_orders", None)
    if not callable(fn):
        raise RuntimeError("REST client missing list_orders()")

    # Some SDKs accept both "CANCELLED" and "CANCELED" — we handle 400s by caller
    kwargs: Dict[str, Any] = {"order_status": [status], "limit": limit}
    if cursor:
        # Coinbase SDK uses "cursor"
        kwargs["cursor"] = cursor
    resp = fn(**kwargs)
    d = _to_dict(resp)
    orders = d.get("orders") or d.get("data") or []
    if not isinstance(orders, list):
        orders = []
    next_cursor = d.get("cursor") or d.get("next_cursor") or d.get("nextCursor") or None
    # Some SDKs include "has_next"
    if d.get("has_next") in (False, 0, "false", "False"):
        next_cursor = None
    return [o if isinstance(o, dict) else _to_dict(o) for o in orders], next_cursor

def _list_orders_since(client: Any, status: str, start: datetime, pfid: str, limit: int = 500) -> List[Dict[str, Any]]:
    """
    List orders with order_status=[status], filter by created_time >= start and retail_portfolio_id==pfid when available.
    """
    out: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    # Loop hard cap to avoid infinite pagination
    for _ in range(120):
        orders, cursor2 = _client_list_orders(client, status, cursor, limit)
        if not orders:
            break
        for o in orders:
            ct = _parse_dt(str(o.get("created_time") or o.get("created_at") or "")) or _now_utc()
            if ct < start:
                continue
            # PFID filter if present
            rp = str(o.get("retail_portfolio_id") or o.get("portfolio_uuid") or "")
            if pfid and rp and rp != pfid:
                continue
            out.append(o)
        if not cursor2 or cursor2 == cursor:
            break
        cursor = cursor2
    return out

def _list_open_orders_all(client: Any, pfid: str, limit: int = 500) -> List[Dict[str, Any]]:
    """
    List ALL OPEN orders for the PFID (no created_time filtering).
    Used for bracket coverage / oversell risk checks.
    """
    out: List[Dict[str, Any]] = []
    cursor: Optional[str] = None
    for _ in range(200):
        orders, cursor2 = _client_list_orders(client, "OPEN", cursor, limit)
        if not orders:
            break
        for o in orders:
            rp = str(o.get("retail_portfolio_id") or o.get("portfolio_uuid") or "")
            if pfid and rp and rp != pfid:
                continue
            out.append(o)
        if not cursor2 or cursor2 == cursor:
            break
        cursor = cursor2
    return out

def _list_orders_window(client: Any, start: datetime, pfid: str) -> List[Dict[str, Any]]:
    """
    Pull orders for diagnostics window:

      - OPEN: include ALL open orders (no created_time filtering) so bracket coverage is accurate.
      - FILLED/CANCELLED: filter by created_time >= start for window stats.
    """
    all_orders: List[Dict[str, Any]] = []

    # OPEN (all)
    try:
        all_orders.extend(_list_open_orders_all(client, pfid))
    except Exception:
        # fallback: if OPEN fetch fails, keep going with the rest
        pass

    # FILLED (window)
    all_orders.extend(_list_orders_since(client, "FILLED", start, pfid))

    # CANCELLED (window) with both spellings fallback
    try:
        all_orders.extend(_list_orders_since(client, "CANCELLED", start, pfid))
    except Exception:
        all_orders.extend(_list_orders_since(client, "CANCELED", start, pfid))
    # Deduplicate by order_id
    seen = set()
    uniq: List[Dict[str, Any]] = []
    for o in all_orders:
        oid = str(o.get("order_id") or o.get("id") or "")
        if oid and oid in seen:
            continue
        if oid:
            seen.add(oid)
        uniq.append(o)
    return uniq

def _get_accounts_holdings(client: Any, pfid: str) -> List[Dict[str, Any]]:
    """
    Returns list of holdings (currency, qty_total, qty_avail, qty_hold) for non-USD with qty_total>0.

    Guardrail:
      balances must read get_accounts(portfolio_uuid=PFID) with available_balance['value'] and hold['value'].

    Notes:
      - Handles pagination when supported by the installed Coinbase SDK.
      - Dedupes accounts by uuid/id across pages.
    """
    fn = getattr(client, "get_accounts", None)
    if not callable(fn):
        return []

    # Detect supported kwargs (cursor/limit vary by SDK version)
    params: set[str] = set()
    try:
        params = set(inspect.signature(fn).parameters.keys())
    except Exception:
        params = set()

    cursor: Optional[str] = None
    out: List[Dict[str, Any]] = []
    seen: set[str] = set()

    for _ in range(200):
        kwargs: Dict[str, Any] = {"portfolio_uuid": pfid}
        if cursor is not None:
            for k in ("cursor", "starting_after", "page_cursor", "after"):
                if k in params:
                    kwargs[k] = cursor
                    break
        if "limit" in params:
            kwargs["limit"] = 250

        # Call with kwargs only when we know signature accepts them
        resp = fn(**kwargs) if params else fn(portfolio_uuid=pfid)
        d = _to_dict(resp)

        accounts = d.get("accounts") or d.get("data") or []
        for a in accounts:
            ad = a if isinstance(a, dict) else _to_dict(a)
            aid = str(ad.get("uuid") or ad.get("account_uuid") or ad.get("id") or "")
            if aid and aid in seen:
                continue
            if aid:
                seen.add(aid)

            cur = str(ad.get("currency") or ad.get("asset") or ad.get("name") or "")
            if not cur or cur.upper() == "USD":
                continue

            avail = _safe_float(((ad.get("available_balance") or {}) or {}).get("value") if isinstance(ad.get("available_balance"), dict) else ad.get("available_balance"))
            hold = _safe_float(((ad.get("hold") or {}) or {}).get("value") if isinstance(ad.get("hold"), dict) else ad.get("hold"))
            total = avail + hold
            if total <= 0:
                continue

            out.append({"currency": cur.upper(), "qty_total": total, "qty_avail": avail, "qty_hold": hold})

        # Pagination fields vary; support common shapes
        cursor2 = d.get("cursor") or d.get("next_cursor") or d.get("nextCursor") or d.get("after") or None
        has_next = bool(d.get("has_next") or d.get("hasNext") or d.get("has_more") or d.get("hasMore") or d.get("next") or False)

        if not cursor2 or cursor2 == cursor:
            break
        # If has_next isn't provided, we still continue when cursor advances
        if not has_next and cursor is not None and cursor2:
            pass

        cursor = str(cursor2)

    return out


def _augment_holdings_with_open_sell_reserves(
    holdings: List[Dict[str, Any]],
    open_sells: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Coinbase accounts sometimes omit assets that are *fully reserved* by OPEN sell orders
    (i.e., available=0 and hold may not reflect outstanding_hold_amount). To avoid false
    "held=0" / "unprotected" diagnostics, we augment holdings with base amounts reserved
    by OPEN SELL orders (using outstanding_hold_amount or trigger_bracket_gtc.base_size).

    Returns holdings list with possible extra fields:
      - qty_reserved_orders: base amount reserved by open sell orders for this currency
      - qty_total_effective: max(qty_total, qty_reserved_orders) (best-effort)
    """
    by_cur: Dict[str, Dict[str, Any]] = {}
    for h in holdings:
        cur = str(h.get("currency") or "").upper()
        if not cur:
            continue
        by_cur[cur] = dict(h)

    # Sum reserved base by currency from open sell orders
    reserved: Dict[str, float] = {}
    for o in open_sells:
        pid = str(o.get("product_id") or "")
        if "-USD" not in pid:
            continue
        base = pid.split("-")[0].upper()

        amt = _safe_float(o.get("outstanding_hold_amount"))
        if amt <= 0:
            # Fallback: trigger_bracket_gtc.base_size
            oc = o.get("order_configuration") or {}
            if isinstance(oc, dict):
                tbg = oc.get("trigger_bracket_gtc") or {}
                if isinstance(tbg, dict):
                    amt = _safe_float(tbg.get("base_size"))
        if amt <= 0:
            continue
        reserved[base] = reserved.get(base, 0.0) + amt

    for base, amt in reserved.items():
        if base in by_cur:
            by_cur[base]["qty_reserved_orders"] = amt
            by_cur[base]["qty_total_effective"] = max(
                _safe_float(by_cur[base].get("qty_total")), amt
            )
        else:
            by_cur[base] = {
                "currency": base,
                "qty_total": amt,
                "qty_avail": 0.0,
                "qty_hold": 0.0,
                "qty_reserved_orders": amt,
                "qty_total_effective": amt,
            }

    # Ensure existing holdings have qty_total_effective at least qty_total
    out: List[Dict[str, Any]] = []
    for cur, h in by_cur.items():
        qt = _safe_float(h.get("qty_total"))
        qte = _safe_float(h.get("qty_total_effective")) if "qty_total_effective" in h else qt
        h["qty_total_effective"] = max(qt, qte)
        out.append(h)

    # Deterministic ordering
    out.sort(key=lambda x: str(x.get("currency") or ""))
    return out


# -----------------------------
# Public candles / ticker (for entry timeline)
# -----------------------------

_CB_EXCHANGE = "https://api.exchange.coinbase.com"

def _fetch_candles(product_id: str, start: datetime, end: datetime, granularity: int) -> List[List[float]]:
    """
    Returns candles [time, low, high, open, close, volume] sorted ascending by time.
    Uses Coinbase Exchange public endpoint.
    """
    if requests is None:
        return []
    # Coinbase expects ISO8601
    params = {
        "start": start.replace(tzinfo=timezone.utc).isoformat(),
        "end": end.replace(tzinfo=timezone.utc).isoformat(),
        "granularity": str(int(granularity)),
    }
    url = f"{_CB_EXCHANGE}/products/{product_id}/candles"
    r = requests.get(url, params=params, timeout=10)
    r.raise_for_status()
    data = r.json()
    if not isinstance(data, list):
        return []
    # sort ascending by time
    data_sorted = sorted(data, key=lambda x: x[0])
    return data_sorted

def _fetch_best_bid_ask(product_id: str) -> Tuple[float, float]:
    if requests is None:
        return (0.0, 0.0)
    url = f"{_CB_EXCHANGE}/products/{product_id}/ticker"
    r = requests.get(url, timeout=10)
    r.raise_for_status()
    d = r.json()
    bid = _safe_float(d.get("bid"))
    ask = _safe_float(d.get("ask"))
    return bid, ask

# -----------------------------
# Trade + metrics
# -----------------------------

@dataclass
class TradeRow:
    product_id: str
    buy_order_id: str
    buy_client_order_id: str
    buy_created_time: str
    buy_last_fill_time: str
    buy_status: str
    buy_order_type: str
    buy_limit_price: float
    buy_avg_fill_price: float
    buy_filled_value: float
    buy_total_fees: float
    buy_total_value_after_fees: float

    sell_order_id: str
    sell_client_order_id: str
    sell_created_time: str
    sell_last_fill_time: str
    sell_status: str
    sell_order_type: str
    sell_avg_fill_price: float
    sell_filled_value: float
    sell_total_fees: float
    sell_total_value_after_fees: float

    exit_kind: str  # TP / SL / UNKNOWN / OPEN
    pnl_net_usd: float

    entry_pos_lookback: float
    mae_pct: float
    mfe_pct: float
    fwd_ret_1m: float
    fwd_ret_3m: float
    fwd_ret_5m: float
    fwd_ret_10m: float

    fill_seconds: float
    fill_immediate: int

def _order_money_fields(o: Dict[str, Any]) -> Tuple[float, float, float]:
    filled_value = _safe_float(o.get("filled_value"))
    total_fees = _safe_float(o.get("total_fees") or o.get("fee"))
    total_value_after_fees = _safe_float(o.get("total_value_after_fees"))
    # Some open orders have total_value_after_fees precomputed; keep it.
    if total_value_after_fees == 0.0:
        # fallback: BUY -> filled + fees, SELL -> filled - fees
        side = str(o.get("side") or "").upper()
        if side == "BUY":
            total_value_after_fees = max(0.0, filled_value + total_fees)
        elif side == "SELL":
            total_value_after_fees = max(0.0, filled_value - total_fees)
    return filled_value, total_fees, total_value_after_fees

def _buy_limit_price(o: Dict[str, Any]) -> float:
    oc = o.get("order_configuration") or {}
    if isinstance(oc, dict):
        ll = oc.get("limit_limit_gtc") or {}
        if isinstance(ll, dict):
            return _safe_float(ll.get("limit_price"))
    return 0.0

def _sell_bracket_prices(o: Dict[str, Any]) -> Tuple[float, float]:
    oc = o.get("order_configuration") or {}
    if not isinstance(oc, dict):
        return (0.0, 0.0)
    tb = oc.get("trigger_bracket_gtc") or {}
    if not isinstance(tb, dict):
        return (0.0, 0.0)
    tp = _safe_float(tb.get("limit_price"))
    sl = _safe_float(tb.get("stop_trigger_price"))
    return (tp, sl)

def _exit_kind_from_sell(o: Dict[str, Any]) -> str:
    if str(o.get("status")) != "FILLED":
        return "OPEN"
    tp_px, sl_px = _sell_bracket_prices(o)
    fill_px = _safe_float(o.get("average_filled_price"))
    if tp_px > 0 and abs(fill_px - tp_px) / tp_px < 0.002:
        return "TP"
    # Stop-loss fills are often below stop_trigger; detect if fill <= sl_px*(1+1%)
    if sl_px > 0 and fill_px <= sl_px * 1.01:
        return "SL"
    return "UNKNOWN"

def _compute_entry_timeline(product_id: str, entry_time: datetime, entry_price: float, lookback_min: int, forward_min: int, granularity: int) -> Tuple[float, float, float, float, float, float, float]:
    """
    Returns: entry_pos, mae_pct, mfe_pct, fwd_1m, fwd_3m, fwd_5m, fwd_10m
    """
    if requests is None:
        return (float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), float("nan"))

    lb_start = entry_time - timedelta(minutes=lookback_min)
    lb_end = entry_time
    fw_start = entry_time
    fw_end = entry_time + timedelta(minutes=forward_min)

    try:
        lb = _fetch_candles(product_id, lb_start, lb_end, granularity)
        fw = _fetch_candles(product_id, fw_start, fw_end, granularity)
    except Exception:
        return (float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), float("nan"), float("nan"))

    # lookback range
    if not lb:
        entry_pos = float("nan")
    else:
        lows = [c[1] for c in lb]
        highs = [c[2] for c in lb]
        lo = min(lows) if lows else 0.0
        hi = max(highs) if highs else 0.0
        if hi > lo > 0:
            entry_pos = (entry_price - lo) / (hi - lo)
            entry_pos = max(0.0, min(1.0, entry_pos))
        else:
            entry_pos = float("nan")

    # forward MAE/MFE and forward horizon returns (use candle closes)
    mae = float("nan")
    mfe = float("nan")
    fwd = {1: float("nan"), 3: float("nan"), 5: float("nan"), 10: float("nan")}

    if fw:
        lows = [c[1] for c in fw]
        highs = [c[2] for c in fw]
        lo = min(lows) if lows else entry_price
        hi = max(highs) if highs else entry_price
        if entry_price > 0:
            mae = (lo / entry_price - 1.0) * 100.0
            mfe = (hi / entry_price - 1.0) * 100.0

        # map candle end-times to minute offset (granularity seconds)
        # fw candles returned ascending by time (epoch seconds at candle start)
        # We'll pick the candle whose start time is closest to entry_time + k minutes.
        times = [int(c[0]) for c in fw]
        closes = [float(c[4]) for c in fw]
        entry_epoch = int(entry_time.timestamp())
        for k in fwd.keys():
            target = entry_epoch + k * 60
            # find closest
            idx = min(range(len(times)), key=lambda i: abs(times[i] - target))
            px = closes[idx]
            if entry_price > 0 and px > 0:
                fwd[k] = (px / entry_price - 1.0) * 100.0

    return (entry_pos, mae, mfe, fwd[1], fwd[3], fwd[5], fwd[10])

def _median(xs: List[float]) -> float:
    xs2 = [x for x in xs if x == x and abs(x) < 1e9]  # drop nan/inf
    if not xs2:
        return float("nan")
    xs2.sort()
    m = len(xs2) // 2
    return xs2[m] if len(xs2) % 2 == 1 else (xs2[m-1] + xs2[m]) / 2

def _gate_stats_from_tick_diag(lines: List[str], last_n: int = 5000) -> Dict[str, Any]:
    tick = [l for l in lines if "[tick_diag]" in l]
    use = tick[-last_n:] if len(tick) > last_n else tick
    hard: Dict[str, int] = {}
    soft: Dict[str, int] = {}
    top_sum = chk_sum = pass_sum = n = 0

    for l in use:
        # top/chk/pass
        m = None
        try:
            import re
            m = re.search(r"top=(\d+).*?chk=(\d+).*?pass=(\d+)", l)
        except Exception:
            m = None
        if m:
            top_sum += int(m.group(1))
            chk_sum += int(m.group(2))
            pass_sum += int(m.group(3))
            n += 1

        # rej block
        if "rej=" in l:
            try:
                import re
                m2 = re.search(r"rej=(.*?)(?:\s+soft=|$)", l)
                if m2:
                    block = m2.group(1)
                    toks = [t for t in re.split(r"[,\s]+", block) if re.match(r"^[A-Za-z0-9_]+:\d+$", t)]
                    for t in toks:
                        k, v = t.split(":", 1)
                        hard[k] = hard.get(k, 0) + int(v)
            except Exception:
                pass

        if "soft=" in l:
            try:
                import re
                m3 = re.search(r"soft=(.*)$", l)
                if m3:
                    block = m3.group(1)
                    toks = [t for t in re.split(r"[,\s]+", block) if re.match(r"^[A-Za-z0-9_]+:\d+$", t)]
                    for t in toks:
                        k, v = t.split(":", 1)
                        soft[k] = soft.get(k, 0) + int(v)
            except Exception:
                pass

    avg = {
        "n": n,
        "avg_top": (top_sum / n) if n else 0.0,
        "avg_chk": (chk_sum / n) if n else 0.0,
        "avg_pass": (pass_sum / n) if n else 0.0,
    }

    hard_top = sorted(hard.items(), key=lambda kv: kv[1], reverse=True)[:15]
    soft_top = sorted(soft.items(), key=lambda kv: kv[1], reverse=True)[:10]

    return {"avg": avg, "hard_top": hard_top, "soft_top": soft_top}

# -----------------------------
# Main
# -----------------------------

def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(prog="diag_run_analytics", add_help=True)
    g = ap.add_mutually_exclusive_group()
    g.add_argument("--since-run-start", action="store_true", help="Analyze since last [run_start] in activity log (default).")
    g.add_argument("--since-ticks", type=int, default=0, help="Analyze since last N tick_diag lines (approx ticks).")
    g.add_argument("--since-hours", type=int, default=0, help="Analyze last N hours (log slice by timestamp).")

    ap.add_argument("--run-tail-lines", type=int, default=20000, help="How many activity log lines to include in run tail artifact.")
    ap.add_argument("--max-trades", type=int, default=60, help="Max trades to compute candle windows for (most recent).")
    ap.add_argument("--lookback-min", type=int, default=60, help="Lookback minutes for entry position.")
    ap.add_argument("--forward-min", type=int, default=30, help="Forward minutes for MAE/MFE/forward returns.")
    ap.add_argument("--granularity", type=int, default=60, help="Candle granularity seconds (60 recommended).")
    ap.add_argument("--pause", action="store_true", help="Wait for ENTER before exit.")

    args = ap.parse_args(argv)

    module_path = Path(__file__).resolve()
    root = _root_find(module_path.parents[2])
    run_settings_path = root / "run_settings.json"
    if not run_settings_path.exists():
        print(f"Missing {run_settings_path}")
        return 2

    settings = _read_json(run_settings_path)
    activity_rel = settings.get("ACTIVITY_LOG_PATH") or "logs/activity_ticker.log"
    activity_path = (root / activity_rel).resolve()
    if not activity_path.exists():
        print(f"Missing {activity_path}")
        return 2

    pfid = os.environ.get("PFID") or str(settings.get("PFID") or "")
    # Derive analysis window start
    tail_for_start = _tail_lines(activity_path, max(5000, int(args.run_tail_lines)))
    run_start: Optional[datetime] = None

    if args.since_hours and args.since_hours > 0:
        run_start = _now_utc() - timedelta(hours=int(args.since_hours))
    elif args.since_ticks and args.since_ticks > 0:
        # Need enough tail to include N tick_diag lines (tick_diag lines may not be timestamped)
        tail_big = _tail_lines(activity_path, max(30000, int(args.since_ticks) * 6))
        rs = _last_tickdiag_window_start(tail_big, int(args.since_ticks))
        tick_sec_est = _safe_float(settings.get("TICK_SEC", 2.0), 2.0)
        run_start_guess = _now_utc() - timedelta(seconds=int(args.since_ticks) * tick_sec_est)
        run_start = rs or run_start_guess
    else:
        # default: since last run_start
        rs = _find_last_run_start(tail_for_start)
        run_start = rs or (_now_utc() - timedelta(hours=6))

    # Build run slice lines for gates and artifacts
    tail_lines = int(args.run_tail_lines)
    if args.since_ticks and args.since_ticks > 0:
        tail_lines = max(tail_lines, int(args.since_ticks) * 8, 30000)
    run_lines = _read_run_slice_tail(activity_path, run_start, tail_lines)
    # Gate stats
    gate = _gate_stats_from_tick_diag(run_lines, last_n=5000)

    # Orders + holdings
    client = get_client()
    orders = _list_orders_window(client, run_start, pfid)

    # Build open orders by product
    open_orders = [o for o in orders if str(o.get("status")) == "OPEN"]
    open_sells = [o for o in open_orders if str(o.get("side")).upper() == "SELL"]
    open_buys = [o for o in open_orders if str(o.get("side")).upper() == "BUY"]

    # Holdings from accounts (PFID) + reserves implied by OPEN sell orders
    holdings_accounts = _get_accounts_holdings(client, pfid)
    holdings = _augment_holdings_with_open_sell_reserves(holdings_accounts, open_sells)

    # Map holdings to product_id -> qty_total/avail/hold
    holding_by_pid: Dict[str, Dict[str, Any]] = {}
    for h in holdings:
        pid = f"{h.get('currency','')}-USD"
        holding_by_pid[pid] = h

    held_products = sorted(set(holding_by_pid.keys()))

    # OPEN SELL grouping (used for bracket coverage + oversell checks)
    def _order_sell_base(o: Dict[str, Any]) -> float:
        return _safe_float(o.get("outstanding_hold_amount") or o.get("workable_size") or o.get("size") or 0.0)

    open_sell_by_pid: Dict[str, List[Dict[str, Any]]] = {}
    for o in open_sells:
        pid = str(o.get("product_id") or "")
        if not pid:
            continue
        open_sell_by_pid.setdefault(pid, []).append(o)

    # Compatibility: dup_open_sells + types (count>1)
    dup_open_sells: Dict[str, int] = {pid: len(lst) for pid, lst in open_sell_by_pid.items() if len(lst) > 1}
    dup_open_sells_types: Dict[str, List[str]] = {}
    for pid, lst in open_sell_by_pid.items():
        if len(lst) <= 1:
            continue
        types = sorted(set([str(o.get("order_type") or "") for o in lst if str(o.get("order_type") or "")]))
        dup_open_sells_types[pid] = types

    # Coverage and risk classification
    EPS = 1e-9
    unprotected_details: List[Dict[str, Any]] = []
    orphan_sell_pids: List[str] = []
    oversell_risk_pids: List[str] = []
    multi_lot_pids: List[str] = []

    # Compute per held product: covered_base (sum open bracket sells) and uncovered
    for pid, h in holding_by_pid.items():
        total = _safe_float(h.get("qty_total"))
        covered = 0.0
        for o in open_sell_by_pid.get(pid, []):
            ot = str(o.get("order_type") or "")
            if ot == "TAKE_PROFIT_STOP_LOSS" or ("trigger_bracket_gtc" in (o.get("order_configuration") or {})):
                covered += _order_sell_base(o)
        uncovered = max(0.0, total - covered)
        if uncovered > EPS:
            unprotected_details.append({
                "product_id": pid,
                "qty_total": total,
                "qty_avail": _safe_float(h.get("qty_avail")),
                "qty_hold": _safe_float(h.get("qty_hold")),
                "covered_base": covered,
                "uncovered_base": uncovered,
            })

    unprotected_held = [d.get("product_id","") for d in unprotected_details if d.get("product_id")]

    # Duplicate OPEN SELL order details (count>1) and oversell classification
    dup_open_sells_details: Dict[str, List[Dict[str, Any]]] = {}
    for pid, lst in open_sell_by_pid.items():
        if len(lst) <= 1:
            continue

        total = _safe_float(holding_by_pid.get(pid, {}).get("qty_total"))
        sell_sum = sum(_order_sell_base(o) for o in lst)

        det: List[Dict[str, Any]] = []
        for o in sorted(lst, key=lambda x: str(x.get("created_time") or "")):
            det.append({
                "order_id": str(o.get("order_id") or o.get("id") or ""),
                "client_order_id": str(o.get("client_order_id") or ""),
                "order_type": str(o.get("order_type") or ""),
                "status": str(o.get("status") or ""),
                "created_time": str(o.get("created_time") or ""),
                "sell_base": _order_sell_base(o),
            })
        dup_open_sells_details[pid] = det

        if total <= EPS:
            orphan_sell_pids.append(pid)
        elif sell_sum > total + max(0.000001, total * 0.002):
            oversell_risk_pids.append(pid)
        else:
            multi_lot_pids.append(pid)

    # Keep stable ordering
    unprotected_details = sorted(unprotected_details, key=lambda x: x.get("product_id", ""))
    unprotected_held = sorted(set([p for p in unprotected_held if p]))
    orphan_sell_pids = sorted(set(orphan_sell_pids))
    oversell_risk_pids = sorted(set(oversell_risk_pids))
    multi_lot_pids = sorted(set(multi_lot_pids))

    # Missed limit buys: CANCELLED buys with 0 filled_size
    missed_limit_buys = 0
    for o in orders:
        if str(o.get("side")).upper() != "BUY":
            continue
        if str(o.get("status")) != "CANCELLED":
            continue
        if _safe_float(o.get("filled_size")) > 0:
            continue
        if str(o.get("order_type")) != "LIMIT":
            continue
        missed_limit_buys += 1

    # Build trade pairing
    buys: List[Dict[str, Any]] = []
    sells: List[Dict[str, Any]] = []
    for o in orders:
        side = str(o.get("side") or "").upper()
        if side == "BUY":
            # executed buy includes filled_size > 0
            if _safe_float(o.get("filled_size")) > 0:
                buys.append(o)
        elif side == "SELL":
            sells.append(o)

    # newest first
    def _created(o: Dict[str, Any]) -> float:
        dt = _parse_dt(str(o.get("created_time") or "")) or datetime(1970, 1, 1, tzinfo=timezone.utc)
        return dt.timestamp()

    buys.sort(key=_created, reverse=True)
    sells.sort(key=_created, reverse=True)

    # map sells by originating_order_id and by client_order_id prefix
    sells_by_origin: Dict[str, Dict[str, Any]] = {}
    sells_by_client: Dict[str, Dict[str, Any]] = {}
    for s in sells:
        origin = str(s.get("originating_order_id") or "")
        if origin:
            # prefer FILLED if multiple
            prev = sells_by_origin.get(origin)
            if prev is None or (str(prev.get("status")) != "FILLED" and str(s.get("status")) == "FILLED"):
                sells_by_origin[origin] = s
        coid = str(s.get("client_order_id") or "")
        if coid.endswith("_attached"):
            base = coid[:-9]
            prev = sells_by_client.get(base)
            if prev is None or (str(prev.get("status")) != "FILLED" and str(s.get("status")) == "FILLED"):
                sells_by_client[base] = s

    # Build rows (limit candle fetch to max_trades)
    rows: List[TradeRow] = []
    candle_fail = 0

    for b in buys[: int(args.max_trades)]:
        pid = str(b.get("product_id") or "")
        buy_oid = str(b.get("order_id") or "")
        buy_coid = str(b.get("client_order_id") or "")
        s = sells_by_origin.get(buy_oid) or sells_by_client.get(buy_coid) or {}

        buy_ct = str(b.get("created_time") or "")
        buy_lft = str(b.get("last_fill_time") or "")
        buy_status = str(b.get("status") or "")
        buy_ot = str(b.get("order_type") or "")
        buy_lim = _buy_limit_price(b)
        buy_avg = _safe_float(b.get("average_filled_price"))
        buy_fv, buy_fees, buy_ta = _order_money_fields(b)

        sell_oid = str(s.get("order_id") or "")
        sell_coid = str(s.get("client_order_id") or "")
        sell_ct = str(s.get("created_time") or "")
        sell_lft = str(s.get("last_fill_time") or "")
        sell_status = str(s.get("status") or "")
        sell_ot = str(s.get("order_type") or "")
        sell_avg = _safe_float(s.get("average_filled_price"))
        sell_fv, sell_fees, sell_ta = _order_money_fields(s)

        exit_kind = _exit_kind_from_sell(s) if s else "OPEN"
        pnl = (sell_ta - buy_ta) if (sell_ta and buy_ta and sell_status == "FILLED") else 0.0

        # fill seconds (limit buys only)
        fill_sec = float("nan")
        fill_immediate = 0
        if buy_ot == "LIMIT":
            cdt = _parse_dt(buy_ct)
            ldt = _parse_dt(buy_lft) or _parse_dt(str(b.get("last_update_time") or ""))
            if cdt and ldt:
                fill_sec = max(0.0, (ldt - cdt).total_seconds())
                fill_immediate = 1 if fill_sec <= 2.0 else 0

        # entry timeline metrics
        entry_pos = mae = mfe = r1 = r3 = r5 = r10 = float("nan")
        et = _parse_dt(buy_lft) or _parse_dt(buy_ct)
        if et and buy_avg > 0:
            try:
                entry_pos, mae, mfe, r1, r3, r5, r10 = _compute_entry_timeline(
                    pid, et, buy_avg, int(args.lookback_min), int(args.forward_min), int(args.granularity)
                )
            except Exception:
                candle_fail += 1

        rows.append(
            TradeRow(
                product_id=pid,
                buy_order_id=buy_oid,
                buy_client_order_id=buy_coid,
                buy_created_time=buy_ct,
                buy_last_fill_time=buy_lft,
                buy_status=buy_status,
                buy_order_type=buy_ot,
                buy_limit_price=buy_lim,
                buy_avg_fill_price=buy_avg,
                buy_filled_value=buy_fv,
                buy_total_fees=buy_fees,
                buy_total_value_after_fees=buy_ta,
                sell_order_id=sell_oid,
                sell_client_order_id=sell_coid,
                sell_created_time=sell_ct,
                sell_last_fill_time=sell_lft,
                sell_status=sell_status,
                sell_order_type=sell_ot,
                sell_avg_fill_price=sell_avg,
                sell_filled_value=sell_fv,
                sell_total_fees=sell_fees,
                sell_total_value_after_fees=sell_ta,
                exit_kind=exit_kind,
                pnl_net_usd=pnl,
                entry_pos_lookback=entry_pos,
                mae_pct=mae,
                mfe_pct=mfe,
                fwd_ret_1m=r1,
                fwd_ret_3m=r3,
                fwd_ret_5m=r5,
                fwd_ret_10m=r10,
                fill_seconds=fill_sec,
                fill_immediate=fill_immediate,
            )
        )

    # Summary metrics
    buys_exec = len(buys)
    trades = len(rows)
    closed = sum(1 for r in rows if r.sell_status == "FILLED")
    tp = sum(1 for r in rows if r.exit_kind == "TP")
    sl = sum(1 for r in rows if r.exit_kind == "SL")

    pnl_closed = [r.pnl_net_usd for r in rows if r.sell_status == "FILLED"]
    wins = [p for p in pnl_closed if p > 0]
    losses = [p for p in pnl_closed if p < 0]
    win_rate = (len(wins) / len(pnl_closed)) if pnl_closed else float("nan")
    net_pnl = sum(pnl_closed) if pnl_closed else 0.0
    avg_pnl = (net_pnl / len(pnl_closed)) if pnl_closed else 0.0
    avg_win = (sum(wins) / len(wins)) if wins else 0.0
    avg_loss = (sum(losses) / len(losses)) if losses else 0.0
    profit_factor = (sum(wins) / abs(sum(losses))) if losses else float("inf") if wins else float("nan")

    # Entry pos counts
    entry_pos_vals = [r.entry_pos_lookback for r in rows if r.entry_pos_lookback == r.entry_pos_lookback]
    trough = sum(1 for x in entry_pos_vals if x <= 0.2)
    crest = sum(1 for x in entry_pos_vals if x >= 0.8)
    entry_pos_n = len(entry_pos_vals)

    # MAE/MFE medians
    mae_med = _median([r.mae_pct for r in rows])
    mfe_med = _median([r.mfe_pct for r in rows])
    r5_med = _median([r.fwd_ret_5m for r in rows])

    # Fees totals
    fees_total = sum(_safe_float(o.get("total_fees") or 0.0) for o in orders)
    fees_closed = sum(r.buy_total_fees + r.sell_total_fees for r in rows if r.sell_status == "FILLED")

    # Limit fill stats
    limit_fills = [r.fill_seconds for r in rows if r.buy_order_type == "LIMIT" and r.fill_seconds == r.fill_seconds]
    limit_fill_med = _median(limit_fills) if limit_fills else float("nan")
    limit_fill_immediate = sum(1 for r in rows if r.buy_order_type == "LIMIT" and r.fill_immediate == 1)

    # Build artifacts
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    out_zip = root / f"mm23_run_diag_pack_{stamp}.zip"
    out_dir = root / f"mm23_run_diag_pack_{stamp}"
    _ensure_dir(out_dir)

    # Write summary
    summary: Dict[str, Any] = {
        "window_start": run_start.isoformat(),
        "pfid": pfid,
        "settings": {k: settings.get(k) for k in [
            "DRY","AUTO_TRADE","LIMIT_ONLY","EXIT_ATTACHED_TPSL",
            "SOLDIER_USD","USD_RESERVE","TP_PCT","SL_PCT",
            "TOP_N","UNIVERSE_TOP","INV_MAX_PIDS","MAX_SOLDIERS_PER_PID",
            "BUY_CHASE_BPS","BUY_CHASE_MAX_SPREAD_BPS",
            "MIN_TOPBOOK_USD","MAX_SPREAD_PCT","MIN_1M_VOL","MIN_DMID_BPS","BOOK_PRESSURE_MIN","TREND_BPS_MIN"
        ] if k in settings},
        "counts": {
            "buys_exec": buys_exec,
            "trades": trades,
            "closed": closed,
            "tp": tp,
            "sl": sl,
            "wins": len(wins),
            "losses": len(losses),
            "open_orders": len(open_orders),
            "open_sells": len(open_sells),
            "open_buys": len(open_buys),
            "held_products": len(held_products),
            "unprotected_held": len(unprotected_held),
            "dup_open_sells": len(dup_open_sells),
            "missed_limit_buys": missed_limit_buys,
        },
        "pnl": {
            "net_pnl_usd": net_pnl,
            "avg_pnl_usd": avg_pnl,
            "win_rate": win_rate,
            "profit_factor": profit_factor,
            "avg_win_usd": avg_win,
            "avg_loss_usd": avg_loss,
            "fees_total_usd": fees_total,
            "fees_closed_usd": fees_closed,
        },
        "entry_timeline": {
            "entry_pos_n": entry_pos_n,
            "trough_le_0_2": trough,
            "crest_ge_0_8": crest,
            "mae_median_pct": mae_med,
            "mfe_median_pct": mfe_med,
            "fwd_5m_median_pct": r5_med,
            "candle_fail_count": candle_fail,
        },
        "limit_fill": {
            "limit_fill_median_sec": limit_fill_med,
            "limit_fill_immediate_count": limit_fill_immediate,
        },
        "coverage": {
            "held_products": held_products,
            "unprotected_held_products": unprotected_held,
            "unprotected_held_details": unprotected_details,
            "dup_open_sells_by_product": dup_open_sells,
            "dup_open_sells_types": dup_open_sells_types,
            "dup_open_sells_details": dup_open_sells_details,
        },
        "gates": gate,
    }

    _write_json(out_dir / "SUMMARY.json", summary)

    # Human summary
    lines = []
    lines.append(f"MM23 RUN DIAGNOSTICS {stamp}")
    lines.append(f"window_start={run_start.isoformat()}")
    lines.append(f"buys_exec={buys_exec} trades={trades} closed={closed} tp={tp} sl={sl}")
    lines.append(f"win_rate={win_rate:.3f} net_pnl_usd={net_pnl:.6f} avg_pnl_usd={avg_pnl:.6f} pf={profit_factor if profit_factor==profit_factor else float('nan')}")
    lines.append(f"fees_total_usd={fees_total:.6f} fees_closed_usd={fees_closed:.6f}")
    lines.append(f"entry_pos trough<=0.2 {trough}/{entry_pos_n} crest>=0.8 {crest}/{entry_pos_n} mae_med={mae_med:.2f}% mfe_med={mfe_med:.2f}% fwd5m_med={r5_med:.2f}%")
    lines.append(f"held={len(held_products)} unprotected={len(unprotected_held)} dup_open_sells={len(dup_open_sells)} missed_limit_buys={missed_limit_buys}")

    # Details for safety debugging (so operator doesn't need to open JSON)
    if unprotected_details:
        lines.append("")
        lines.append("Unprotected held products (no OPEN bracket sell):")
        for d in unprotected_details[:25]:
            lines.append(f"  {d['product_id']} qty_total={d['qty_total']:.10f} qty_hold={d['qty_hold']:.10f}")
        if len(unprotected_details) > 25:
            lines.append(f"  ... ({len(unprotected_details)-25} more)")

    if dup_open_sells_details:
        lines.append("")
        lines.append("Duplicate OPEN SELL orders (count>1):")
        # sort by count desc
        for pid in sorted(dup_open_sells_details.keys(), key=lambda k: (-len(dup_open_sells_details[k]), k)):
            det = dup_open_sells_details[pid]
            types = ",".join(dup_open_sells_types.get(pid, []))
            lines.append(f"  {pid} count={len(det)} types={types}")
            for o in det[:12]:
                oid = o.get("order_id","")
                ot = o.get("order_type","")
                cid = o.get("client_order_id","")
                lines.append(f"    oid={oid} type={ot} client={cid}")
            if len(det) > 12:
                lines.append(f"    ... ({len(det)-12} more)")
    if limit_fills:
        lines.append(f"limit_fill_median_sec={limit_fill_med:.2f} immediate_limit_fills={limit_fill_immediate}/{sum(1 for r in rows if r.buy_order_type=='LIMIT')}")
    lines.append("")
    lines.append("Top hard rejects:")
    for k, v in gate.get("hard_top", [])[:8]:
        lines.append(f"  {k}={v}")
    _write_text(out_dir / "SUMMARY.txt", "\n".join(lines))

    # trades.csv
    with (out_dir / "trades.csv").open("w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow([field for field in TradeRow.__dataclass_fields__.keys()])
        for r in rows:
            w.writerow([
                r.product_id, r.buy_order_id, r.buy_client_order_id, r.buy_created_time, r.buy_last_fill_time,
                r.buy_status, r.buy_order_type, f"{r.buy_limit_price:.10f}", f"{r.buy_avg_fill_price:.10f}",
                f"{r.buy_filled_value:.10f}", f"{r.buy_total_fees:.10f}", f"{r.buy_total_value_after_fees:.10f}",
                r.sell_order_id, r.sell_client_order_id, r.sell_created_time, r.sell_last_fill_time,
                r.sell_status, r.sell_order_type, f"{r.sell_avg_fill_price:.10f}", f"{r.sell_filled_value:.10f}",
                f"{r.sell_total_fees:.10f}", f"{r.sell_total_value_after_fees:.10f}",
                r.exit_kind, f"{r.pnl_net_usd:.10f}",
                f"{r.entry_pos_lookback:.6f}", f"{r.mae_pct:.6f}", f"{r.mfe_pct:.6f}",
                f"{r.fwd_ret_1m:.6f}", f"{r.fwd_ret_3m:.6f}", f"{r.fwd_ret_5m:.6f}", f"{r.fwd_ret_10m:.6f}",
                f"{r.fill_seconds:.6f}", r.fill_immediate
            ])

    # orders jsonl
    _write_jsonl(out_dir / "orders_window.jsonl", orders)
    _write_json(out_dir / "holdings.json", holdings)

    # activity tail
    (out_dir / "activity_run_tail.txt").write_text("".join(run_lines[-20000:]), encoding="utf-8", errors="replace")

    # settings snapshot
    (out_dir / "run_settings.json").write_text(run_settings_path.read_text(encoding="utf-8"), encoding="utf-8")
    run_active_path = root / "logs" / "run_active.json"
    if run_active_path.exists():
        (out_dir / "run_active.json").write_text(run_active_path.read_text(encoding="utf-8"), encoding="utf-8")

    # zip pack
    if out_zip.exists():
        out_zip.unlink()
    with zipfile.ZipFile(out_zip, "w", compression=zipfile.ZIP_DEFLATED) as z:
        for p in out_dir.rglob("*"):
            if p.is_file():
                z.write(p, arcname=str(p.relative_to(root)))
    # Clean folder (keep zip only)
    try:
        for p in sorted(out_dir.rglob("*"), reverse=True):
            if p.is_file():
                p.unlink()
        for p in sorted(out_dir.rglob("*"), reverse=True):
            if p.is_dir():
                p.rmdir()
        out_dir.rmdir()
    except Exception:
        pass

    # Console output lines (keep concise)
    print(f"[MM23_DIAG] zip={out_zip}")
    print(f"[MM23_DIAG] buys_exec={buys_exec} trades={trades} closed={closed} win_rate={0.0 if win_rate!=win_rate else win_rate:.3f} net_pnl_usd={net_pnl:.6f} avg_pnl_usd={avg_pnl:.6f} pf={profit_factor if profit_factor==profit_factor else 0.0} tp={tp} sl={sl}")
    print(f"[MM23_DIAG] entry_pos trough<=0.2 {trough}/{entry_pos_n} crest>=0.8 {crest}/{entry_pos_n} mae_med={mae_med:.2f}% mfe_med={mfe_med:.2f}% fwd5m_med={r5_med:.2f}%")
    print(f"[MM23_DIAG] coverage held={len(held_products)} unprotected={len(unprotected_held)} dup_open_sells={len(dup_open_sells)} missed_limit_buys={missed_limit_buys} limit_fill_med_sec={0.0 if limit_fill_med!=limit_fill_med else limit_fill_med:.2f}")

    # Safety details (first items; full details in SUMMARY.txt / SUMMARY.json)
    if unprotected_details:
        parts = [f"{d['product_id']}({d['qty_total']:.6g})" for d in unprotected_details[:10]]
        more = len(unprotected_details) - len(parts)
        s = ", ".join(parts) + (f",...(+{more})" if more > 0 else "")
        print(f"[MM23_DIAG] unprotected_pids={s}")
    if dup_open_sells:
        parts2 = []
        for pid, cnt in sorted(dup_open_sells.items(), key=lambda kv: (-kv[1], kv[0])):
            types = ",".join(dup_open_sells_types.get(pid, []))
            parts2.append(f"{pid}({cnt}" + (f";{types}" if types else "") + ")")
        more2 = len(parts2) - min(len(parts2), 10)
        s2 = ", ".join(parts2[:10]) + (f",...(+{more2})" if more2 > 0 else "")
        print(f"[MM23_DIAG] dup_open_sell_pids={s2}")


    # Persist last summary for menu users (even if console output is not visible)
    try:
        last_lines = [
            f"[MM23_DIAG] zip={out_zip}",
            f"[MM23_DIAG] buys_exec={buys_exec} trades={trades} closed={closed} win_rate={0.0 if win_rate!=win_rate else win_rate:.3f} net_pnl_usd={net_pnl:.6f} avg_pnl_usd={avg_pnl:.6f} pf={profit_factor if profit_factor==profit_factor else 0.0} tp={tp} sl={sl}",
            f"[MM23_DIAG] entry_pos trough<=0.2 {trough}/{entry_pos_n} crest>=0.8 {crest}/{entry_pos_n} mae_med={mae_med:.2f}% mfe_med={mfe_med:.2f}% fwd5m_med={r5_med:.2f}%",
            f"[MM23_DIAG] coverage held={len(held_products)} unprotected={len(unprotected_held)} dup_open_sells={len(dup_open_sells)} missed_limit_buys={missed_limit_buys} limit_fill_med_sec={0.0 if limit_fill_med!=limit_fill_med else limit_fill_med:.2f}",
        ]
        
        # Append safety detail lines
        if unprotected_details:
            parts = [f"{d['product_id']}({d['qty_total']:.6g})" for d in unprotected_details[:10]]
            more = len(unprotected_details) - len(parts)
            s = ", ".join(parts) + (f",...(+{more})" if more > 0 else "")
            last_lines.append(f"[MM23_DIAG] unprotected_pids={s}")
        if dup_open_sells:
            parts2 = []
            for pid, cnt in sorted(dup_open_sells.items(), key=lambda kv: (-kv[1], kv[0])):
                types = ",".join(dup_open_sells_types.get(pid, []))
                parts2.append(f"{pid}({cnt}" + (f";{types}" if types else "") + ")")
            more2 = len(parts2) - min(len(parts2), 10)
            s2 = ", ".join(parts2[:10]) + (f",...(+{more2})" if more2 > 0 else "")
            last_lines.append(f"[MM23_DIAG] dup_open_sell_pids={s2}")

        if oversell_risk_pids:
            s3 = ", ".join(oversell_risk_pids[:10]) + (f",...(+{len(oversell_risk_pids)-10})" if len(oversell_risk_pids)>10 else "")
            last_lines.append(f"[MM23_DIAG] oversell_risk_pids={s3}")
        if orphan_sell_pids:
            s4 = ", ".join(orphan_sell_pids[:10]) + (f",...(+{len(orphan_sell_pids)-10})" if len(orphan_sell_pids)>10 else "")
            last_lines.append(f"[MM23_DIAG] orphan_sell_pids={s4}")
        if multi_lot_pids:
            s5 = ", ".join(multi_lot_pids[:10]) + (f",...(+{len(multi_lot_pids)-10})" if len(multi_lot_pids)>10 else "")
            last_lines.append(f"[MM23_DIAG] multi_lot_pids={s5}")


        (root / "mm23_run_diag_last.txt").write_text("\n".join(last_lines) + "\n", encoding="utf-8")
    except Exception:
        pass

    # Reveal created zip in Explorer (useful when spawned console output isn't visible)
    try:
        subprocess.Popen(["explorer.exe", f"/select,{out_zip}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception:
        pass

    if args.pause:
        try:
            input("Press ENTER to close...")
        except Exception:
            pass

    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit:
        raise
    except Exception:
        # Write a last-error file so menu-spawn runs don't "flash and vanish" silently
        try:
            import traceback as _tb
            _root = Path(__file__).resolve().parents[2]
            _err = _root / "mm23_run_diag_last_error.txt"
            _err.write_text(_tb.format_exc(), encoding="utf-8")
            try:
                subprocess.Popen(["explorer.exe", f"/select,{_err}"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        except Exception:
            pass
        raise
