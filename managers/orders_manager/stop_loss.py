from __future__ import annotations

"""
managers/orders_manager/stop_loss.py

Soft stop-loss executor (spot) — v4.1 (re-entry guard).

Fixes:
- When breach >= confirm and execution fails (cancel/balance/order), do NOT fail silently.
- Log a concise [sl_error] line with pid and reason.
- Set last-sl timestamp even on failure to avoid hammering (cooldown applies).
- Cap breach counter at confirm (prevents 999/3 spam).

Behavior:
- Active only when SELL_AT_LOSS=True and SL_PCT>0.
- Soft confirm: SL_CONFIRM_TICKS consecutive breaches.
- Derives bid/ask/mid from get_best_bid_ask for the specific pid (no caller mid).
- Cancels OPEN SELL orders, then sells total base (available+hold) at marketable LIMIT (post_only=False).
- Throttle per pid with SL_COOLDOWN_SEC.
- Rate-limited logs [sl_hold]/[sl_trigger] via SL_LOG_EVERY_SEC.
"""

import os
import time
import uuid
from decimal import Decimal, InvalidOperation, ROUND_DOWN
from typing import Any, Dict, Optional, Tuple, List

D = Decimal

_BREACH: Dict[str, int] = {}
_LAST_SL_TS: Dict[str, float] = {}
_LAST_LOG_TS: Dict[str, float] = {}
_ENTRY_CACHE: Dict[str, Tuple[float, D]] = {}
_BAD_PIDS: Dict[str, float] = {}


def _D(x: Any) -> D:
    if isinstance(x, D):
        return x
    try:
        return D(str(x))
    except (InvalidOperation, Exception):
        return D("0")


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _now() -> float:
    try:
        return time.time()
    except Exception:
        return 0.0


def _best_bid_ask(client, pid: str) -> Tuple[D, D]:
    pid = str(pid or "").upper()
    if not pid:
        return D("0"), D("0")
    if pid in _BAD_PIDS:
        return D("0"), D("0")
    try:
        resp = client.get_best_bid_ask(product_ids=[pid])
    except Exception:
        _BAD_PIDS[pid] = _now()
        return D("0"), D("0")

    pbs = None
    if isinstance(resp, dict):
        pbs = resp.get("pricebooks") or resp.get("data")
    else:
        pbs = getattr(resp, "pricebooks", None) or getattr(resp, "data", None)

    if not pbs or not isinstance(pbs, list):
        _BAD_PIDS[pid] = _now()
        return D("0"), D("0")

    pb = pbs[0]
    bids = _get(pb, "bids", []) or []
    asks = _get(pb, "asks", []) or []
    try:
        b0 = bids[0] if bids else None
        a0 = asks[0] if asks else None
        if not b0 or not a0:
            return D("0"), D("0")
        bid = _D(_get(b0, "price"))
        ask = _D(_get(a0, "price"))
        return bid, ask
    except Exception:
        return D("0"), D("0")


def _mid_from_book(bid: D, ask: D) -> D:
    if bid > 0 and ask > 0:
        return (bid + ask) / D("2")
    return D("0")


def _product_increments(client, pid: str) -> Tuple[D, D]:
    try:
        p = client.get_product(product_id=pid)
        prod = _get(p, "product", p)
        qi = _D(_get(prod, "quote_increment", _get(prod, "price_increment", "0.01")))
        bi = _D(_get(prod, "base_increment", "0.00000001"))
        if qi <= 0:
            qi = D("0.01")
        if bi <= 0:
            bi = D("0.00000001")
        return qi, bi
    except Exception:
        return D("0.01"), D("0.00000001")


def _round_down(val: D, inc: D) -> D:
    try:
        if inc <= 0:
            return val
        q = (val / inc).to_integral_value(rounding=ROUND_DOWN)
        return q * inc
    except Exception:
        return val


def _entry_vwap_from_fills_cached(client, pid: str, ttl_sec: float) -> Optional[D]:
    """
    Returns an *estimated* average entry price for the CURRENT open position in `pid`.

    Older versions computed VWAP of BUY fills only, which can be wildly wrong once there
    are SELL fills (re-entry cycles). This version processes BUY/SELL fills using an
    average-cost method to estimate the remaining position cost basis.

    Notes:
      - Uses the most recent 200 fills from the API.
      - If the fill history is truncated (more than 200 fills), the estimate may drift.
    """
    now = _now()
    try:
        ts, v = _ENTRY_CACHE.get(pid, (0.0, D("0")))
        if v > 0 and (now - float(ts)) <= float(ttl_sec):
            return v
    except Exception:
        pass

    try:
        resp = client.get_fills(product_id=pid, limit=200)
    except Exception:
        return None

    fills = _get(resp, "fills", resp) or []
    if not isinstance(fills, list):
        fills = []

    # Sort oldest -> newest if timestamps are present (ISO strings sort correctly).
    try:
        def _fts(f):
            return str(_get(f, "created_at", _get(f, "trade_time", _get(f, "time", ""))) or "")
        fills = sorted(fills, key=_fts)
    except Exception:
        pass

    qty = D("0")
    cost = D("0")

    for f in fills:
        side = str(_get(f, "side", "") or _get(f, "direction", "")).upper()
        sz = _D(_get(f, "size", _get(f, "base_size", _get(f, "base_quantity", "0"))))
        px = _D(_get(f, "price", _get(f, "average_price", "0")))

        if sz <= 0 or px <= 0:
            continue

        if side in ("BUY", "B"):
            qty += sz
            cost += sz * px
            continue

        if side in ("SELL", "S"):
            if qty <= 0 or cost <= 0:
                qty = D("0")
                cost = D("0")
                continue
            # Reduce using average-cost method.
            sell_sz = sz if sz <= qty else qty
            avg_cost = cost / qty
            qty -= sell_sz
            cost -= sell_sz * avg_cost
            # Guard numerical negatives.
            if qty <= 0 or cost <= 0:
                qty = D("0")
                cost = D("0")
            continue

    if qty <= 0 or cost <= 0:
        return None

    entry = cost / qty
    _ENTRY_CACHE[pid] = (now, entry)
    return entry


def _base_total(client, pid: str, pfid: str) -> D:
    base = pid.split("-", 1)[0].upper()
    if not base:
        return D("0")
    try:
        resp = client.get_accounts(limit=250)
    except Exception:
        return D("0")

    accounts = _get(resp, "accounts", resp) or []
    if not isinstance(accounts, list):
        accounts = []

    total = D("0")
    for a in accounts:
        a_pfid = str(_get(a, "retail_portfolio_id", "") or _get(a, "portfolio_uuid", "") or "")
        if pfid and a_pfid and a_pfid != pfid:
            continue
        cur = str(_get(a, "currency", "") or "").upper()
        if cur != base:
            continue
        ab = _get(a, "available_balance", None)
        hv = _get(a, "hold", None)
        av = _D(_get(ab, "value", 0) if ab is not None else 0)
        hd = _D(_get(hv, "value", 0) if hv is not None else 0)
        total += av + hd
    return total


def _list_open_sell_orders(client, pid: str) -> List[str]:
    ids: List[str] = []
    try:
        resp = client.list_orders(product_id=pid, order_status=["OPEN"], limit=200)
    except TypeError:
        try:
            resp = client.list_orders(product_id=pid, limit=200)
        except Exception:
            return ids
    except Exception:
        return ids

    orders = _get(resp, "orders", resp) or []
    if not isinstance(orders, list):
        orders = []

    for o in orders:
        side = str(_get(o, "side", "") or "").upper()
        status = str(_get(o, "status", "") or "").upper()
        opid = str(_get(o, "product_id", _get(o, "productId", "")) or "").upper()
        if opid and opid != pid:
            continue
        if status and status != "OPEN":
            continue
        if side != "SELL":
            continue
        oid = str(_get(o, "order_id", _get(o, "orderId", "")) or "")
        if oid:
            ids.append(oid)
    return ids


def _cancel_orders(client, ids: List[str]) -> None:
    if not ids:
        return
    try:
        client.cancel_orders(order_ids=ids)
    except Exception:
        pass


def _maybe_log(pid: str, msg: str, every_sec: float, settings: Dict[str, Any]) -> None:
    now = _now()
    last = float(_LAST_LOG_TS.get(pid, 0.0))
    if now - last >= float(every_sec):
        _LAST_LOG_TS[pid] = now
        _activity(settings, msg)

def check_and_exit(client, product_id: str, settings: Dict[str, Any], mid_price: Any = None) -> Dict[str, Any]:
    # MM16_TP_SL_NORM_GUARD (safe: operate on settings dict only)
    try:
        if isinstance(settings, dict):
            tpv = _D(settings.get('TP_PCT', 0))
            if tpv > _D('1'):
                settings['TP_PCT'] = str(tpv / _D('100'))
            slv = _D(settings.get('SL_PCT', 0))
            try:
                if slv > 1:
                    slv = slv / 100
            except Exception:
                pass
            if slv > _D('1'):
                settings['SL_PCT'] = str(slv / _D('100'))
    except Exception:
        pass
    pid = str(product_id or "").upper()
    if not pid:
        return {"ok": True, "action": "skip", "pid": pid, "reason": "no_pid"}

    # MM24_DRY_GUARD: never place stop-loss orders when DRY=True
    try:
        if bool((settings or {}).get('DRY', False)):
            return {'ok': True, 'action': 'skip', 'pid': pid, 'reason': 'dry'}
    except Exception:
        pass


    
    # MM23_ATTACHED_TPSL: when enabled, stop-loss is handled exchange-side via attached TP/SL.
    # Do not run loop-triggered stop-loss sells in this mode.
    try:
        if bool((settings or {}).get("EXIT_ATTACHED_TPSL", False)):
            return {"ok": True, "action": "skip", "pid": pid, "reason": "attached_tpsl"}
    except Exception:
        pass
    s = settings or {}
    if not bool(s.get("SELL_AT_LOSS", False)):
        return {"ok": True, "action": "skip", "pid": pid, "reason": "disabled"}

    sl_pct = _D(s.get("SL_PCT", 0))
    # MM16 percent-points guard: accept SL_PCT=7.7 as 7.7% (and 0.077 as 7.7%)
    try:
        if sl_pct > 1:
            sl_pct = sl_pct / 100
    except Exception:
        pass
    # sl_pct already normalized above (percent-points guard); do not divide by 100 again.  # MM17_SLPCT_FIX
    try:
        if isinstance(s, dict):
            s['SL_PCT'] = str(sl_pct)
    except Exception:
        pass  # MM16_PCT_POINTS_SL_STRICT_CFG_SYNC
    if sl_pct <= 0:
        return {"ok": True, "action": "skip", "pid": pid, "reason": "no_sl_pct"}

    confirm = int(s.get("SL_CONFIRM_TICKS", 3) or 3)
    if confirm < 1:
        confirm = 1
    cooldown_s = float(s.get("SL_COOLDOWN_SEC", 120) or 120)
    log_every = float(s.get("SL_LOG_EVERY_SEC", 60) or 60)
    entry_ttl = float(s.get("ENTRY_CACHE_SEC", 300) or 300)

    now = _now()
    last_sl = float(_LAST_SL_TS.get(pid, 0.0))
    if now - last_sl < cooldown_s:
        return {"ok": True, "action": "skip", "pid": pid, "reason": "cooldown"}

    entry = _entry_vwap_from_fills_cached(client, pid, entry_ttl)
    if entry is None or entry <= 0:
        return {"ok": True, "action": "skip", "pid": pid, "reason": "no_entry"}

    stop_px = entry * (D("1") - sl_pct)

    bid, ask = _best_bid_ask(client, pid)
    mid = _mid_from_book(bid, ask)
    if bid <= 0:
        return {"ok": True, "action": "skip", "pid": pid, "reason": "no_bid"}

    # Stop-loss should evaluate against the *executable* side of the book.
    # Using mid can materially delay stop triggers on wide-spread / thin books.
    px_ref = bid if bid > 0 else mid

    if px_ref > stop_px:
        _BREACH[pid] = 0
        return {"ok": True, "action": "noop", "pid": pid, "reason": "above_stop"}

    # below stop: increment and cap
    b = int(_BREACH.get(pid, 0)) + 1
    if b > confirm:
        b = confirm
    _BREACH[pid] = b
    _maybe_log(pid, f"[sl_hold] pid={pid} breach={b}/{confirm} px_ref={px_ref} bid={bid} mid={mid} stop={stop_px} entry={entry}", log_every, s)

    if b < confirm:
        return {"ok": True, "action": "hold", "pid": pid, "breach": b, "confirm": confirm}

    # Trigger attempt
    pfid = os.environ.get("PFID", "").strip() or str(s.get("PFID") or "").strip()

    try:
        ids = _list_open_sell_orders(client, pid)
        if ids:
            _cancel_orders(client, ids)

        base_tot = _base_total(client, pid, pfid)
        if base_tot <= 0:
            _LAST_SL_TS[pid] = now  # throttle anyway
            return {"ok": True, "action": "error", "pid": pid, "reason": "no_position"}

        qi, bi = _product_increments(client, pid)
        px = bid if bid > 0 else stop_px
        px_q = _round_down(px, qi)
        sz_q = _round_down(base_tot, bi)
        if sz_q <= 0:
            _LAST_SL_TS[pid] = now
            return {"ok": True, "action": "error", "pid": pid, "reason": "dust"}

        client.create_order(
            client_order_id=str(uuid.uuid4()),
            product_id=pid,
            side="SELL",
            order_configuration={
                "limit_limit_gtc": {
                    "base_size": str(sz_q),
                    "limit_price": str(px_q),
                    "post_only": False,
                    "rfq_disabled": False,
                    "reduce_only": False,
                }
            },
        )
        _LAST_SL_TS[pid] = now
        _BREACH[pid] = 0
        _activity(settings, f"[sl_trigger] pid={pid} px_ref={px_ref} bid={bid} mid={mid} stop={stop_px} entry={entry} sell_px={px_q} size={sz_q}")
        return {"ok": True, "action": "stop_loss", "pid": pid, "mid": str(mid), "stop_px": str(stop_px), "sl_px": str(px_q), "size": str(sz_q)}

    except Exception as e:
        _LAST_SL_TS[pid] = now  # throttle on failure
        _activity(settings, f"[sl_error] pid={pid} err={str(e)[:200]}")
        return {"ok": False, "action": "error", "pid": pid, "error": str(e)}
# ---------- MM16_REENTRY_GUARD ----------
def in_reentry_cooldown(pid: str, settings: Dict[str, Any]) -> bool:
    """
    True if this pid recently triggered stop-loss and should not be re-bought.
    Controlled by:
      SL_REENTRY_COOLDOWN_SEC (default 1800s = 30m)
      SL_REENTRY_SCORE_MIN (default 0.90) is handled by caller (buy logic)
    """
    try:
        sec = float((settings or {}).get("SL_REENTRY_COOLDOWN_SEC", 1800) or 1800)
    except Exception:
        sec = 1800.0
    now = _now()
    try:
        last = float(_LAST_SL_TS.get(str(pid).upper(), 0.0))
    except Exception:
        last = 0.0
    return (now - last) < sec
# ---------- MM16_REENTRY_GUARD ----------







# Activity ticker helper (MM21) — stop-loss telemetry must not go to stdout.
def _activity(settings, msg: str) -> None:
    try:
        if isinstance(settings, dict) and not bool(settings.get("ACTIVITY_TICKER", True)):
            return
    except Exception:
        pass
    try:
        import time as _time
        from pathlib import Path as _Path
        root = _Path(__file__).resolve().parents[2]
        ap = root / "logs" / "activity_ticker.log"
        ts = _time.strftime("%Y-%m-%d %H:%M:%S", _time.localtime())
        ap.parent.mkdir(parents=True, exist_ok=True)
        with ap.open("a", encoding="utf-8") as f:
            f.write(f"[{ts}] {msg}\n")
    except Exception:
        pass

