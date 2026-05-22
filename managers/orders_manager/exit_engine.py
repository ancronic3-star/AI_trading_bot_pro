# C:\ai_trading_bot_koko\managers\orders_manager\exit_engine.py
"""
Exit engine (spot) - LIMIT-only exits.

MM15.13B (Soldier-based TP price scaling FIX):
- Fixes the catastrophic bug: selling ALL available base while targeting only ONE SOLDIER_USD of proceeds
  produced TP prices like 0.26 for FIL.

Final policy (per user):
- TP logic is SOLDIER-based (quote budget), NOT "market price".
- The TP price MUST scale with the number of soldiers represented by the base being sold.

Implementation (soldier-based, scalable):
  entry_px = most-recent BUY fill price
  base_per_soldier = SOLDIER_USD / entry_px
  implied_soldiers  = base_to_sell / base_per_soldier
  # MM17_TP_GROSSFIX: integer soldier targeting (gross SOLDIER_USD baseline; fees post-trade)
  try:
      soldiers_n = int(round(float(implied_soldiers)))
  except Exception:
      soldiers_n = 1
  if soldiers_n < 1:
      soldiers_n = 1

  gross_target_quote = soldiers_n * SOLDIER_USD * (1 + TP_PCT)
  # MM16 percent-points guard: accept TP_PCT=7.7 as 7.7% (and 0.077 as 7.7%)
  try:
      if gross_target_quote > 1:
          gross_target_quote = gross_target_quote / 100
  except Exception:
      pass
  gross_target_quote = (gross_target_quote / Decimal("100"))  # MM16_PCT_POINTS_TP_STRICT
  try:
      if isinstance(s, dict):
          s['TP_PCT'] = str(gross_target_quote)
  except Exception:
      pass  # MM16_PCT_POINTS_TP_STRICT_CFG_SYNC
  tp_price_raw = gross_target_quote / base_to_sell
  tp_price = quantize UP to quote_increment (so proceeds >= target)

With this, selling multiple soldiers worth of base targets multiple-soldier proceeds (not just one).
(Algebra reduces to entry_px*(1+TP_PCT), but the accounting remains soldier-based and scales correctly.)

Managed TP:
- TP_SINGLE_PER_PRODUCT (default True): one TP per product sized to ALL available base (rounded down to base_increment).
- Hygiene: keep only one "managed" TP within TP_MANAGED_BAND_PCT around computed tp_price; cancel duplicates.
- If the kept TP is in-band but size differs from desired by >= base_increment, cancel+replace (resize-to-available).

Notes:
- This file does NOT implement SL/OCO yet; it ensures TP sells and prevents duplicate TP spam.
- Uses client.create_order with client_order_id; does not include portfolio_uuid in bodies.
"""

from __future__ import annotations

import os
import time
import uuid
from decimal import Decimal, ROUND_DOWN, ROUND_UP, getcontext
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

getcontext().prec = 50
D = Decimal

_ACCOUNTS_CACHE: Dict[str, Any] = {"ts": 0.0, "data": {}}


def _now() -> float:
    return time.time()


def _to_dec(x: Any, default: str = "0") -> Decimal:
    try:
        if x is None:
            return D(default)
        s = str(x).strip()
        if s == "":
            return D(default)
        return D(s)
    except Exception:
        return D(default)


def _fmt_decimal(d: Decimal) -> str:
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s if s else "0"


def _round_down_to_increment(val: Decimal, inc: Decimal) -> Decimal:
    if inc <= 0:
        return val
    q = (val / inc).to_integral_value(rounding=ROUND_DOWN)
    return q * inc


def _round_up_to_increment(val: Decimal, inc: Decimal) -> Decimal:
    if inc <= 0:
        return val
    q = (val / inc).to_integral_value(rounding=ROUND_UP)
    return q * inc


def _debug() -> bool:
    return os.getenv("KOKO_DEBUG_EXIT_ENGINE", "").strip().lower() in ("1", "true", "yes", "on")


def _as_dict(o: Any) -> Dict[str, Any]:
    if isinstance(o, dict):
        return o
    if hasattr(o, "to_dict"):
        try:
            return o.to_dict()  # type: ignore[attr-defined]
        except Exception:
            return {}
    try:
        return dict(vars(o))
    except Exception:
        return {}


def _get(obj: Any, key: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _call_first_ok(callables):
    last_err = None
    for fn in callables:
        try:
            return fn()
        except (TypeError, AttributeError) as e:
            last_err = e
            continue
    if last_err:
        raise last_err
    raise RuntimeError("No callable candidates provided")


# ---------- increments ----------

def _product_increments(client: Any, pid: str) -> Tuple[Decimal, Decimal]:
    base_inc = D("0.00000001")
    quote_inc = D("0.0001")
    try:
        prod = None
        try:
            prod = client.get_product(product_id=pid)
        except TypeError:
            prod = client.get_product(pid)
        d = _as_dict(prod) if prod is not None else {}
        bi = _get(prod, "base_increment", d.get("base_increment"))
        qi = _get(prod, "quote_increment", d.get("quote_increment"))
        if bi:
            base_inc = _to_dec(bi, default=str(base_inc))
        if qi:
            quote_inc = _to_dec(qi, default=str(quote_inc))
    except Exception:
        pass
    return base_inc, quote_inc


# ---------- accounts ----------

def invalidate_accounts_cache() -> None:
    _ACCOUNTS_CACHE["ts"] = _now()
    _ACCOUNTS_CACHE["data"] = {}


def _get_accounts_raw(client):
    cands = []
    if hasattr(client, "get_accounts"):
        cands.extend([lambda: client.get_accounts(limit=250), lambda: client.get_accounts()])
    if hasattr(client, "list_accounts"):
        cands.extend([lambda: client.list_accounts(limit=250), lambda: client.list_accounts()])
    return _call_first_ok(cands)


def list_accounts_by_product(client, *, force: bool = False, cache_ttl_sec: float = 0.75) -> Dict[str, Dict[str, str]]:
    t = _now()
    if (not force) and _ACCOUNTS_CACHE["data"] and (t - float(_ACCOUNTS_CACHE["ts"])) < cache_ttl_sec:
        return _ACCOUNTS_CACHE["data"]

    try:
        res = _get_accounts_raw(client)
    except Exception:
        invalidate_accounts_cache()
        return {}

    accounts = None
    if isinstance(res, dict):
        accounts = res.get("accounts") or res.get("data")
        if accounts is None and isinstance(res.get("success_response"), dict):
            accounts = res["success_response"].get("accounts") or res["success_response"].get("data")
    elif isinstance(res, list):
        accounts = res
    else:
        accounts = getattr(res, "accounts", None)

    if not isinstance(accounts, list):
        invalidate_accounts_cache()
        return {}

    out: Dict[str, Dict[str, str]] = {}
    for a in accounts:
        cur = _get(a, "currency", None)
        if not cur:
            ab = _get(a, "available_balance", None)
            if ab is not None:
                cur = _get(ab, "currency", None)
        if not cur:
            continue

        pid = f"{cur}-USD"
        avail_obj = _get(a, "available_balance", None)
        hold_obj = _get(a, "hold", None)
        total_obj = _get(a, "total_balance", None)

        avail = str(_get(avail_obj, "value", "0")) if avail_obj is not None else "0"
        hold = str(_get(hold_obj, "value", "0")) if hold_obj is not None else "0"
        total = str(_get(total_obj, "value", "0")) if total_obj is not None else "0"
        if total == "0":
            try:
                total = str(_to_dec(avail) + _to_dec(hold))
            except Exception:
                total = avail

        out[pid] = {"available": avail, "hold": hold, "total": total}

    _ACCOUNTS_CACHE["ts"] = _now()
    _ACCOUNTS_CACHE["data"] = out
    return out


# ---------- orders ----------

def _normalize_order(o: Any) -> Dict[str, Any]:
    d = _as_dict(o)
    if "order_id" not in d:
        for k in ("id", "_order_id"):
            if k in d:
                d["order_id"] = d[k]
                break
    if "order_configuration" not in d:
        oc = getattr(o, "order_configuration", None)
        if oc is not None:
            d["order_configuration"] = _as_dict(oc)
    else:
        oc = d.get("order_configuration")
        if oc is not None and not isinstance(oc, dict):
            d["order_configuration"] = _as_dict(oc)
    return d


def _list_orders_open(client, pid: str, limit: int = 200) -> List[Dict[str, Any]]:
    res = _call_first_ok(
        [
            lambda: client.list_orders(product_id=pid, order_status=["OPEN"], limit=limit),
            lambda: client.list_orders(product_id=pid, order_status="OPEN", limit=limit),
            lambda: client.list_orders(product_id=pid, order_status="OPEN"),
            lambda: client.list_orders(product_id=pid, order_status=["OPEN"]),
        ]
    )
    orders = getattr(res, "orders", None)
    if orders is None and isinstance(res, dict):
        orders = res.get("orders")
    if not isinstance(orders, list):
        return []
    return [_normalize_order(o) for o in orders]


def _cancel_order_ids(client, order_ids: List[str]) -> Dict[str, Any]:
    if not order_ids:
        return {"stage": "exit_engine.cancel_orders", "ok": True, "action": "noop", "reason": "no order ids"}
    try:
        _ = client.cancel_orders(order_ids=order_ids)
        invalidate_accounts_cache()
        return {"stage": "exit_engine.cancel_orders", "ok": True, "action": "cancel", "order_ids": order_ids}
    except Exception as e:
        return {"stage": "exit_engine.cancel_orders", "ok": False, "action": "error", "order_ids": order_ids, "error": repr(e)}


# ---------- fills ----------

def _parse_time(t: Any) -> Optional[datetime]:
    if t is None:
        return None
    s = str(t).strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s2 = s[:-1] + "+00:00"
            return datetime.fromisoformat(s2)
        return datetime.fromisoformat(s)
    except Exception:
        return None


def read_order_fills(client, pid: str, limit: int = 50) -> List[Dict[str, Any]]:
    res = _call_first_ok(
        [
            lambda: client.get_fills(product_id=pid, limit=limit),
            lambda: client.get_fills(product_id=pid),
            lambda: client.list_fills(product_id=pid, limit=limit),
            lambda: client.list_fills(product_id=pid),
        ]
    )
    fills = None
    if isinstance(res, dict):
        fills = res.get("fills")
        if fills is None and isinstance(res.get("success_response"), dict):
            fills = res["success_response"].get("fills")
    elif isinstance(res, list):
        fills = res
    else:
        fills = getattr(res, "fills", None)

    if not isinstance(fills, list):
        return []

    return [_as_dict(f) for f in fills]


def recent_buy_entry(client, pid: str) -> Optional[Tuple[Decimal, Decimal, Decimal]]:
    fills = read_order_fills(client, pid, limit=25)
    buys = []
    for f in fills:
        if str(f.get("side") or "").upper() != "BUY":
            continue
        px = _to_dec(f.get("price"), default="0")
        if px <= 0:
            continue
        t = _parse_time(f.get("trade_time") or f.get("created_time") or f.get("time") or f.get("timestamp"))
        buys.append((t, f, px))

    if not buys:
        return None

    buys.sort(key=lambda x: (x[0] is not None, x[0] or datetime(1970, 1, 1, tzinfo=timezone.utc)), reverse=True)
    _, f, px = buys[0]

    siq = f.get("size_in_quote")
    if siq is True:
        q = _to_dec(f.get("size"), default="0")
        if q <= 0:
            return None
        base = q / px
        quote = q
    else:
        base = _to_dec(f.get("base_size") or f.get("size"), default="0")
        if base <= 0:
            return None
        quote = base * px

    if base <= 0 or quote <= 0:
        return None

    return (px, base, quote)


# ---------- TP hygiene ----------

def _extract_limit_price_and_size(order: Dict[str, Any]) -> Tuple[Decimal, Decimal, bool]:
    try:
        if str(order.get("side") or "").upper() != "SELL":
            return (D("0"), D("0"), False)
        oc = order.get("order_configuration") or {}
        oc = oc if isinstance(oc, dict) else _as_dict(oc)
        ll = oc.get("limit_limit_gtc") or {}
        ll = ll if isinstance(ll, dict) else _as_dict(ll)
        lp = _to_dec(ll.get("limit_price"), default="0")
        bs = _to_dec(ll.get("base_size"), default="0")
        if lp > 0 and bs > 0:
            return (lp, bs, True)
    except Exception:
        pass
    return (D("0"), D("0"), False)


def _managed_tp_candidates(open_orders: List[Dict[str, Any]], tp_px: Decimal, band_pct: Decimal) -> List[Dict[str, Any]]:
    if tp_px <= 0:
        return []
    lo = tp_px * (D("1") - band_pct)
    hi = tp_px * (D("1") + band_pct)
    out: List[Dict[str, Any]] = []
    for o in open_orders:
        lp, _, ok = _extract_limit_price_and_size(o)
        if not ok:
            continue
        if lo <= lp <= hi:
            out.append(o)
    return out


def _best_tp_match(cands: List[Dict[str, Any]], tp_px: Decimal, desired_size: Decimal) -> Optional[Dict[str, Any]]:
    best = None
    best_score = None
    for o in cands:
        lp, bs, ok = _extract_limit_price_and_size(o)
        if not ok:
            continue
        dp = abs(lp - tp_px)
        ds = abs(bs - desired_size) if desired_size > 0 else D("0")
        score = (dp, ds)
        if best_score is None or score < best_score:
            best_score = score
            best = o
    return best


def _run_tp_hygiene(client, pid: str, tp_px_q: Decimal, desired_q: Decimal, band: Decimal, base_inc: Decimal) -> Dict[str, Any]:
    open_orders = _list_orders_open(client, pid, limit=200)
    cands = _managed_tp_candidates(open_orders, tp_px_q, band)
    if _debug():
        print(f"[exit_engine][TP_HYGIENE_SCAN] pid={pid} open={len(open_orders)} cands={len(cands)} tp_px={_fmt_decimal(tp_px_q)} band={_fmt_decimal(band)} desired={_fmt_decimal(desired_q)}")

    if not cands:
        return {"ok": True, "action": "noop", "reason": "no_candidates", "open": len(open_orders)}

    best = _best_tp_match(cands, tp_px_q, desired_q)
    best_id = str(best.get("order_id") or "") if best else ""

    cancel_ids: List[str] = []
    for o in cands:
        oid = str(o.get("order_id") or "")
        if not oid or oid == best_id:
            continue
        cancel_ids.append(oid)

    if cancel_ids:
        cr = _cancel_order_ids(client, cancel_ids)
        if _debug():
            print(f"[exit_engine][TP_HYGIENE] pid={pid} cancelled={len(cancel_ids)} ok={cr.get('ok')} kept={best_id}")
    else:
        cr = {"ok": True}

    if not best_id:
        return {"ok": True, "action": "cleaned" if cancel_ids else "noop", "cancelled": len(cancel_ids), "kept_order_id": "", "cancel_ok": bool(cr.get("ok"))}

    lp, bs, ok = _extract_limit_price_and_size(best)
    size_diff = abs(bs - desired_q) if ok else desired_q
    needs_resize = desired_q > 0 and size_diff >= base_inc

    if needs_resize:
        cr2 = _cancel_order_ids(client, [best_id])
        if _debug():
            print(f"[exit_engine][TP_HYGIENE_RESIZE] pid={pid} kept={best_id} bs={_fmt_decimal(bs)} desired={_fmt_decimal(desired_q)} cancel_ok={cr2.get('ok')}")
        return {"ok": True, "action": "replace", "kept_order_id": best_id, "old_size": _fmt_decimal(bs), "desired_size": _fmt_decimal(desired_q), "cancel_ok": bool(cr2.get("ok")), "cancelled_dupes": len(cancel_ids)}

    return {"ok": True, "action": "noop", "reason": "only_one", "kept_order_id": best_id, "cancelled_dupes": len(cancel_ids)}


# ---------- core ----------

def _list_open_orders(client, product_id: str):
    """Best-effort list of OPEN orders for a product."""
    pid = str(product_id or "").upper()
    try:
        return client.list_orders(product_id=pid, order_status=["OPEN"], limit=200)
    except TypeError:
        try:
            return client.list_orders(product_id=pid, order_status="OPEN", limit=200)
        except Exception:
            try:
                return client.list_orders(product_id=pid, limit=200)
            except Exception:
                return None
    except Exception:
        return None

def _iter_orders(resp):
    if resp is None:
        return []
    if isinstance(resp, dict):
        o = resp.get("orders") or resp.get("data") or []
        return o if isinstance(o, list) else []
    o = getattr(resp, "orders", None)
    if isinstance(o, list):
        return o
    return []

def _get_order_field(o, name, default=None):
    if isinstance(o, dict):
        return o.get(name, default)
    return getattr(o, name, default)

def _cancel_orders(client, order_ids):
    ids = [str(x) for x in (order_ids or []) if str(x)]
    if not ids:
        return
    try:
        client.cancel_orders(order_ids=ids)
    except Exception:
        pass

def _tp_band_ok(px: Decimal, target: Decimal, band_bps: Decimal) -> bool:
    try:
        if target <= 0:
            return False
        diff = abs(px - target) / target * Decimal("10000")
        return diff <= band_bps
    except Exception:
        return False

def ensure_tp_for_product(*args, **kwargs) -> Dict[str, Any]:

    if len(args) < 2:
        raise TypeError("ensure_tp_for_product expects at least (client, pid, ...)")

    client = args[0]
    pid = args[1]
    cfg = args[2] if (len(args) >= 3 and isinstance(args[2], dict)) else {}

    # MM24_DRY_GUARD: do not place TP orders when DRY=True
    try:
        if bool((cfg or {}).get("DRY", False)):
            return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "dry"}
    except Exception:
        pass

    # MM16_TP_SL_NORM_GUARD
    try:
        if isinstance(cfg, dict):
            _tpv = _to_dec(cfg.get('TP_PCT', 0))
            # MM16 percent-points guard: accept TP_PCT=7.7 as 7.7% (and 0.077 as 7.7%)
            try:
                if _tpv > 1:
                    _tpv = _tpv / 100
            except Exception:
                pass
            if _tpv > _to_dec('1'):
                cfg['TP_PCT'] = str(_tpv / _to_dec('100'))
            _slv = _to_dec(cfg.get('SL_PCT', 0))
            try:
                if _slv > 1:
                    _slv = _slv / 100
            except Exception:
                pass
            if _slv > _to_dec('1'):
                cfg['SL_PCT'] = str(_slv / _to_dec('100'))
    except Exception:
        pass

    if not hasattr(client, "create_order"):
        raise TypeError("first arg must be a Coinbase RESTClient (missing create_order)")

    allow_cancel_sells = bool(cfg.get("ALLOW_CANCEL_SELLS", False))

    # MM23_ATTACHED_TPSL: when enabled, TP is managed exchange-side via attached TP/SL.
    try:
        if bool(cfg.get("EXIT_ATTACHED_TPSL", False)):
            return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "attached_tpsl"}
    except Exception:
        pass

    tp_pct = _to_dec(cfg.get("TP_PCT"), default="0")
    # MM16 percent-points guard: accept TP_PCT=7.7 as 7.7% (and 0.077 as 7.7%)
    try:
        if tp_pct > 1:
            tp_pct = tp_pct / 100
    except Exception:
        pass
    if tp_pct <= 0:
        return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "tp_disabled"}

    soldier_q = _to_dec(cfg.get("SOLDIER_USD"), default="0")
    single = cfg.get("TP_SINGLE_PER_PRODUCT")
    if single is None:
        single = True
    band = _to_dec(cfg.get("TP_MANAGED_BAND_PCT"), default="0.10")

    base_inc, quote_inc = _product_increments(client, pid)

    accts = list_accounts_by_product(client)
    info = accts.get(pid, {})
    avail = _to_dec(info.get("available"), default="0")
    hold = _to_dec(info.get("hold"), default="0")
    total = _to_dec(info.get("total"), default="0")
    if total <= 0:
        total = avail + hold
    if total <= 0:
        return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "no_position"}
    avail_q = _round_down_to_increment(avail, base_inc)

    ent = recent_buy_entry(client, pid)
    if not ent:
        return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "no_entry"}
    entry_px, entry_base, entry_quote = ent

    if entry_px <= 0 or entry_base <= 0 or entry_quote <= 0:
        return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "no_entry_quote"}

    desired_base = total if bool(single) else min(total, entry_base)
    desired_q = _round_down_to_increment(desired_base, base_inc)

    if desired_q <= 0:
        return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "size_too_small", "base_inc": str(base_inc)}

    # MM26_TPSL_MATH_A:
    # Managed TP fallback should use simple notional math derived from the actual entry
    # quote/base instead of soldier-based quote targeting. This keeps TP math aligned with
    # the same percent logic the user expects from the attached bracket path.
    quote_basis = (entry_quote / entry_base) * desired_q
    if quote_basis <= 0:
        return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "no_quote_basis"}

    gross_target_quote = quote_basis * (D("1") + tp_pct)
    tp_px_raw = gross_target_quote / desired_q
    tp_px_q = _round_up_to_increment(tp_px_raw, quote_inc)

    # Keep legacy debug/output fields populated for compatibility.
    soldier_q = entry_quote
    base_per_soldier = entry_base
    implied_soldiers = D("1")
    soldiers_n = 1
    soldiers_n_dec = D("1")

    hygiene_res = None
    if bool(single) and allow_cancel_sells:
        hygiene_res = _run_tp_hygiene(client, pid, tp_px_q, desired_q, band, base_inc)
        if isinstance(hygiene_res, dict) and hygiene_res.get("action") == "noop" and hygiene_res.get("reason") == "only_one":
            return {
                "stage": "exit_engine.ensure_tp_for_product",
                "ok": True,
                "action": "noop",
                "pid": pid,
                "reason": "existing_tp_ok",
                "tp_px": _fmt_decimal(tp_px_q),
                "tp_size": _fmt_decimal(desired_q),
                "hygiene": hygiene_res,
            }
        if isinstance(hygiene_res, dict) and hygiene_res.get("action") == "replace":
            accts2 = list_accounts_by_product(client, force=True)
            info2 = accts2.get(pid, info or {})
            avail2 = _to_dec((info2 or {}).get("available"), default=str(avail))
            hold2 = _to_dec((info2 or {}).get("hold"), default="0")
            total2 = _to_dec((info2 or {}).get("total"), default=str(avail2 + hold2))
            desired_q = _round_down_to_increment(total2, base_inc)
            if desired_q <= 0:
                return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "size_too_small_after_hygiene", "hygiene": hygiene_res}
            quote_basis = (entry_quote / entry_base) * desired_q
            if quote_basis <= 0:
                return {"stage": "exit_engine.ensure_tp_for_product", "ok": True, "action": "skip", "pid": pid, "reason": "no_quote_basis_after_hygiene", "hygiene": hygiene_res}
            gross_target_quote = quote_basis * (D("1") + tp_pct)
            tp_px_raw = gross_target_quote / desired_q
            tp_px_q = _round_up_to_increment(tp_px_raw, quote_inc)
            implied_soldiers = D("1")
            soldiers_n = 1
            soldiers_n_dec = D("1")
            if _debug():
                print(f"[exit_engine][TP_RESIZE] pid={pid} new_desired={_fmt_decimal(desired_q)} new_tp_px={_fmt_decimal(tp_px_q)}")

    client_order_id = str(uuid.uuid4())
    # TP hygiene: do not stack multiple OPEN TP sells
    band_bps = _to_dec(cfg.get('TP_EXIST_BAND_BPS', 25), default='25')  # 0.25% default
    open_resp = _list_open_orders(client, pid)
    open_orders = _iter_orders(open_resp)
    sell_ids = []
    in_band = []  # (abs_price, abs_size, oid, lp, bs)
    for o in open_orders:
        try:
            side = str(_get_order_field(o, 'side', '') or '').upper()
            status = str(_get_order_field(o, 'status', '') or '').upper()
            if status and status != 'OPEN':
                continue
            if side != 'SELL':
                continue
            opid = str(_get_order_field(o, 'product_id', _get_order_field(o, 'productId', '')) or '').upper()
            if opid and opid != pid:
                continue
            oid = str(_get_order_field(o, 'order_id', _get_order_field(o, 'orderId', '')) or '')
            if oid:
                sell_ids.append(oid)
            norm = _normalize_order(o)
            lp, bs, ok = _extract_limit_price_and_size(norm)
            if not ok:
                continue
            if _tp_band_ok(lp, tp_px_q, band_bps):
                try:
                    in_band.append((abs(lp - tp_px_q), abs(bs - desired_q), oid, lp, bs))
                except Exception:
                    in_band.append((D('0'), D('0'), oid, lp, bs))
        except Exception:
            continue
    # If cancels are disabled, we can only TP the currently AVAILABLE (unheld) base.
    # This prevents silent TP failures when an older OPEN sell is holding part of the position.
    if not allow_cancel_sells:
        if avail_q <= 0:
            return {'stage': 'exit_engine.ensure_tp_for_product', 'ok': True, 'action': 'noop', 'pid': pid, 'reason': 'no_available_to_tp'}
        desired_q = avail_q
    if in_band:
        in_band.sort(key=lambda x: (x[0], x[1]))
        _, _, best_id, best_lp, best_bs = in_band[0]
        try:
            if best_id and desired_q > 0 and abs(best_bs - desired_q) < base_inc:
                return {'stage': 'exit_engine.ensure_tp_for_product', 'ok': True, 'action': 'noop', 'pid': pid, 'reason': 'existing_tp_ok'}
        except Exception:
            pass
        # in-band TP exists but wrong size -> cancel sells so we can replace
        if allow_cancel_sells and sell_ids:
            _cancel_orders(client, sell_ids)
    else:
        # no in-band TP -> clear sells (stale) so we can place fresh TP
        if allow_cancel_sells and sell_ids:
            _cancel_orders(client, sell_ids)
    resp = client.create_order(
        client_order_id=client_order_id,
        product_id=pid,
        side="SELL",
        order_configuration={
            "limit_limit_gtc": {
                "base_size": _fmt_decimal(desired_q),
                "limit_price": _fmt_decimal(tp_px_q),
                "post_only": False,
            }
        },
    )
    d = _as_dict(resp)
    ok = True
    err = ""
    oid = ""
    if d.get("success") is False:
        ok = False
        er = d.get("error_response") or {}
        err = str((er.get("error") if isinstance(er, dict) else None) or "CREATE_ORDER_FAILED")
    if d.get("success") is True:
        sr = d.get("success_response") or {}
        if isinstance(sr, dict):
            oid = str(sr.get("order_id") or "")

    if _debug():
        print(
            f"[exit_engine][TP] ok={ok} order_id={oid} err={err} price={_fmt_decimal(tp_px_q)} size={_fmt_decimal(desired_q)} "
            f"entry_quote_basis={_fmt_decimal(quote_basis)} soldier={_fmt_decimal(soldier_q)} base_per_soldier={_fmt_decimal(base_per_soldier)} implied_soldiers={_fmt_decimal(implied_soldiers)} "
            f"target={_fmt_decimal(gross_target_quote)} resp={d or str(resp)[:300]}"
        )

    if not ok:
        return {
            "stage": "exit_engine.ensure_tp_for_product.error",
            "ok": False,
            "action": "error",
            "pid": pid,
            "error": err,
            "tp_px": _fmt_decimal(tp_px_q),
            "tp_size": _fmt_decimal(desired_q),
            "client_order_id": client_order_id,
            "hygiene": hygiene_res,
        }

    invalidate_accounts_cache()
    return {
        "stage": "exit_engine.ensure_tp_for_product.placed",
        "ok": True,
        "action": "place",
        "pid": pid,
        "order_id": oid,
        "tp_px": _fmt_decimal(tp_px_q),
        "tp_size": _fmt_decimal(desired_q),
        "entry_quote_basis": _fmt_decimal(quote_basis),
        "soldier_quote": _fmt_decimal(soldier_q),
        "base_per_soldier": _fmt_decimal(base_per_soldier),
        "implied_soldiers": _fmt_decimal(implied_soldiers),
        "gross_target_quote": _fmt_decimal(gross_target_quote),
        "tp_pct": str(tp_pct),
        "client_order_id": client_order_id,
        "hygiene": hygiene_res,
    }


def ensure_tp_for_inventory(client, cfg: Dict[str, Any]) -> Dict[str, Any]:
    try:
        accts = list_accounts_by_product(client, force=True)
    except Exception as e:
        return {"ok": False, "action": "batch", "count": 0, "errors": 1, "error": repr(e)}

    pids: List[str] = []
    for pid, row in (accts or {}).items():
        base = str(pid).split("-", 1)[0].upper()
        if base in ("USD", "USDC", "USDT"):
            continue
        tot = _to_dec((row or {}).get("total"), default="0")
        if tot > 0:
            pids.append(pid)

    count = 0
    errs = 0
    for pid in pids:
        try:
            _ = ensure_tp_for_product(client, pid, cfg, None)
            count += 1
        except Exception:
            errs += 1

    return {"ok": True, "action": "batch", "count": count, "errors": errs}





