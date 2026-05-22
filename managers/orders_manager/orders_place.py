# -*- coding: utf-8 -*-
"""
managers.orders_manager.orders_place

Stable, backwards-compatible order placement wrapper.

Goals:
- Keep the historical call signature used by run_manager.py and older exit_engine.py:
    place_order(product_id, side, size, size_type="QUOTE", limit_price=None, post_only=True, client_order_id=None, ...)
- Quantize price/size to Coinbase product increments to avoid INVALID_PRICE_PRECISION.
- Do not pass non-payload args (e.g., "headers") into create_order payload.

MM23_ATTACHED_TPSL:
- Adds optional Coinbase-managed Attached TP/SL (trigger_bracket_gtc) on BUY orders.
- When enabled (settings.EXIT_ATTACHED_TPSL=True), BUY uses market_market_ioc by default, or limit_limit_gtc when LIMIT_ONLY=True, with attached_order_configuration.
- On any attached-order failure, safely falls back to legacy limit_limit_gtc placement.

Notes:
- This module accepts and ignores extra kwargs to stay compatible with older adapters that might pass
  headers/portfolio_id/etc. We MUST NOT include portfolio_uuid in order bodies (guardrail).
"""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_DOWN, getcontext
import os
import time
import uuid
from typing import Any, Dict, Optional, Tuple

# Higher precision is helpful when converting quote->base and snapping
getcontext().prec = 50

from managers.auth_manager.auth_jwt import get_client  # type: ignore
from managers.config_manager.settings import load_settings  # type: ignore

# ---------- retry policy (transient exchange/server errors) ----------
_RETRY_MAX = 2  # total attempts = 1 + _RETRY_MAX
_RETRY_SLEEP_S = 0.6

def _is_transient_error(msg: str) -> bool:
    m = (msg or "").lower()
    if not m:
        return False
    needles = [
        "500", "502", "503", "504",
        "internal server error",
        "something went wrong",
        "temporarily unavailable",
        "timed out",
        "timeout",
        "connection reset",
        "connection aborted",
        "remote end closed connection",
    ]
    return any(n in m for n in needles)

# Backwards-compat shim
get_settings = load_settings


def _debug_enabled() -> bool:
    return os.getenv("KOKO_DEBUG_ORDERS_PLACE", "").strip().lower() in ("1", "true", "yes", "on")


def _dbg(msg: str) -> None:
    if _debug_enabled():
        print(msg, flush=True)


def _as_dict(o: Any) -> Dict[str, Any]:
    if isinstance(o, dict):
        return o
    if hasattr(o, "to_dict"):
        try:
            return o.to_dict()  # type: ignore[attr-defined]
        except Exception:
            return {}
    return {}


def _get(o: Any, k: str, default: Any = None) -> Any:
    if isinstance(o, dict):
        return o.get(k, default)
    return getattr(o, k, default)


def _to_decimal(x: Any) -> Decimal:
    if isinstance(x, Decimal):
        return x
    try:
        return Decimal(str(x))
    except (InvalidOperation, Exception):
        return Decimal("0")


def _fmt_decimal(d: Decimal) -> str:
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def _round_down_to_increment(value: Any, increment: Any) -> str:
    """Round DOWN to the given increment (as string)."""
    v = _to_decimal(value)
    i = _to_decimal(increment)
    if i <= 0:
        return _fmt_decimal(v)
    q = (v / i).to_integral_value(rounding=ROUND_DOWN)
    snapped = q * i
    return _fmt_decimal(snapped)



def _round_up_to_increment(value: Any, inc: Any) -> str:
    """Snap value up to a step increment. Returns string for API payloads."""
    v = _to_decimal(value)
    i = _to_decimal(inc)
    if i <= 0:
        return _fmt_decimal(v)
    q = (v / i).to_integral_value(rounding=ROUND_DOWN)
    snapped = q * i
    if snapped < v:
        snapped = snapped + i
    return _fmt_decimal(snapped)

def _snap(value: Decimal, inc: Decimal, up: bool) -> Decimal:
    """Snap to increment; up=True uses ceiling via integer arithmetic."""
    if inc <= 0:
        return value
    try:
        q = (value / inc)
        if up:
            # ceil(q) = -floor(-q)
            q = (-q).to_integral_value(rounding=ROUND_DOWN) * Decimal("-1")
        else:
            q = q.to_integral_value(rounding=ROUND_DOWN)
        return q * inc
    except Exception:
        return value


def _norm_pct(val: Any) -> Decimal:
    """Accept percent-points (7.7) or fraction (0.077); return fraction."""
    d = _to_decimal(val)
    try:
        if d > 1:
            d = d / Decimal("100")
    except Exception:
        pass
    if d < 0:
        d = Decimal("0")
    return d


def _product_increments(client: Any, product_id: str) -> Tuple[str, str]:
    """Returns (base_increment, quote_increment) as strings."""
    # Reasonable fallbacks if we cannot fetch product metadata
    base_inc = "0.00000001"
    quote_inc = "0.0001"

    try:
        prod = None
        try:
            prod = client.get_product(product_id=product_id)
        except TypeError:
            prod = client.get_product(product_id)
        except Exception:
            prod = None

        d = _as_dict(prod) if prod is not None else {}
        bi = _get(prod, "base_increment", d.get("base_increment", None))
        qi = _get(prod, "quote_increment", d.get("quote_increment", None))

        if bi:
            base_inc = str(bi)
        if qi:
            quote_inc = str(qi)
    except Exception:
        pass

    return (base_inc, quote_inc)


def _best_bid_ask(client: Any, product_id: str) -> tuple[str | None, str | None]:
    """Return (best_bid_price, best_ask_price) as strings."""
    try:
        try:
            r = client.get_product_book(product_id=product_id, limit=1)
        except TypeError:
            r = client.get_product_book(product_id, limit=1)

        d = _as_dict(r)
        if not isinstance(d, dict):
            return (None, None)

        pb = d.get("pricebook")
        if not isinstance(pb, dict):
            return (None, None)

        bids = pb.get("bids") or []
        asks = pb.get("asks") or []

        bid = bids[0].get("price") if bids and isinstance(bids[0], dict) else None
        ask = asks[0].get("price") if asks and isinstance(asks[0], dict) else None

        return (str(bid) if bid else None, str(ask) if ask else None)
    except Exception:
        return (None, None)


def _normalize_side(side: str) -> str:
    s = (side or "").strip().upper()
    return "BUY" if s.startswith("B") else "SELL"


def _normalize_size_type(size_type: str) -> str:
    st = (size_type or "").strip().upper()
    if st in ("BASE", "BASE_SIZE", "BASESIZE"):
        return "BASE"
    if st in ("QUOTE", "QUOTE_SIZE", "QUOTESIZE"):
        return "QUOTE"
    if st.startswith("B"):
        return "BASE"
    return "QUOTE"


def place_order(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    """Compatibility wrapper for order placement."""
    # ---- client: keyword wins, else detect from first positional
    client = kwargs.get("client")
    pos = list(args)

    if client is None and pos:
        cand = pos[0]
        if hasattr(cand, "get_product") and hasattr(cand, "create_order"):
            client = cand
            pos = pos[1:]

    # ---- positional mapping (after optional client)
    if "product_id" not in kwargs and len(pos) >= 1:
        kwargs["product_id"] = pos[0]
    if "side" not in kwargs and len(pos) >= 2:
        kwargs["side"] = pos[1]
    if "size" not in kwargs and len(pos) >= 3:
        kwargs["size"] = pos[2]
    if "size_type" not in kwargs and len(pos) >= 4:
        kwargs["size_type"] = pos[3]

    # ---- legacy: settings dict sometimes passed positionally after size_type
    if "settings" not in kwargs and len(pos) >= 5 and isinstance(pos[4], dict):
        kwargs["settings"] = pos[4]

    # ---- legacy: sometimes limit_price and/or post_only follow
    if "limit_price" not in kwargs and len(pos) >= 6 and not isinstance(pos[5], dict):
        kwargs["limit_price"] = pos[5]
    if "post_only" not in kwargs and len(pos) >= 7 and isinstance(pos[6], bool):
        kwargs["post_only"] = pos[6]

    if client is not None:
        kwargs["client"] = client

    return _place_order_impl(**kwargs)


def _compute_attached_tp_sl_prices(
    *,
    pid: str,
    client: Any,
    settings: Dict[str, Any],
    quote_inc: str,
    mid: Any = None,
    bid: Any = None,
    ask: Any = None,
    limit_price: Any = None,
) -> Tuple[Optional[str], Optional[str], Optional[str]]:
    """Return (entry_ref, tp_price, sl_trigger_price) as strings."""
    inc = _to_decimal(quote_inc)
    if inc <= 0:
        inc = Decimal("0.0001")

    # MM26_TPSL_MATH_A:
    # For attached TP/SL, LIMIT_ONLY buys must use the submitted limit_price as the
    # entry reference whenever it is available. Falling back to ask/mid in the
    # limit path makes a 6.2% TP or 8.0% SL drift away from the intended entry.
    ref = Decimal("0")
    a = _to_decimal(ask)
    b = _to_decimal(bid)
    m = _to_decimal(mid)
    lp = _to_decimal(limit_price)

    limit_only = False
    try:
        limit_only = bool(settings.get("LIMIT_ONLY", False))
    except Exception:
        limit_only = False

    if limit_only and lp > 0:
        ref = lp
    elif a > 0:
        ref = a
    elif m > 0:
        ref = m
    elif lp > 0:
        ref = lp
    elif b > 0:
        ref = b

    if ref <= 0:
        return (None, None, None)

    tp_pct = _norm_pct(settings.get("TP_PCT", 0))
    sl_pct = _norm_pct(settings.get("SL_PCT", 0))

    if tp_pct <= 0 or sl_pct <= 0:
        return (_fmt_decimal(ref), None, None)

    tp_raw = ref * (Decimal("1") + tp_pct)
    sl_raw = ref * (Decimal("1") - sl_pct)

    # Round: TP up (slightly harder to hit), SL down (triggers slightly earlier)
    tp_px = _snap(tp_raw, inc, up=True)
    sl_px = _snap(sl_raw, inc, up=False)

    if tp_px <= 0 or sl_px <= 0:
        return (_fmt_decimal(ref), None, None)

    return (_fmt_decimal(ref), _fmt_decimal(tp_px), _fmt_decimal(sl_px))


def _place_order_impl(
    product_id: str,
    side: str,
    size: Any,
    size_type: str = "QUOTE",
    limit_price: Any = None,
    post_only: bool = True,
    client_order_id: Optional[str] = None,
    reduce_only: Optional[bool] = None,
    rfq_disabled: Optional[bool] = False,
    mid: Any = None,
    settings: Optional[Dict[str, Any]] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Backwards-compatible order placement."""

    client = kwargs.get("client") or kwargs.get("c") or None
    if client is None:
        client = get_client()

    pid = (product_id or "").strip().upper()
    sd = _normalize_side(side)
    st = _normalize_size_type(size_type)

    if settings is None:
        try:
            settings = load_settings()
        except Exception:
            settings = {}
    cfg = settings or {}

    # Increments: prefer explicit kwargs if provided (some callers pre-fetch)
    base_inc = kwargs.get("base_increment")
    quote_inc = kwargs.get("quote_increment")
    if not base_inc or not quote_inc:
        bi, qi = _product_increments(client, pid)
        base_inc = str(base_inc) if base_inc else bi
        quote_inc = str(quote_inc) if quote_inc else qi

    # Quantize size first (needed for market orders)
    try:
        if st == "BASE":
            base_sz = _round_down_to_increment(size, base_inc)
            quote_sz = None
        else:
            quote_sz = _round_down_to_increment(size, quote_inc)
            base_sz = None
    except Exception as e:
        return {
            "ok": False,
            "error": f"BAD_SIZE:{type(e).__name__}",
            "product_id": pid,
            "side": sd,
            "size": str(size),
            "size_type": st,
        }

    cid = client_order_id or str(uuid.uuid4())

    # MM24_DRY_GUARD: never place real orders when DRY=True
    try:
        if bool(cfg.get('DRY', False)):
            return {
                'ok': False,
                'dry_run': True,
                'error': 'DRY_MODE_BLOCK',
                'product_id': pid,
                'side': sd,
                'client_order_id': cid,
            }
    except Exception:
        pass

    # Best bid/ask used both for pricing and for maker-cross check.
    bid, ask = _best_bid_ask(client, pid)

    # ---------- MM23_ATTACHED_TPSL (BUY only) ----------
    try:
        use_attached = bool(cfg.get("EXIT_ATTACHED_TPSL", False))
    except Exception:
        use_attached = False

    if use_attached and sd == "BUY":
        # Require stop protection enabled and valid tp/sl pct.
        if not bool(cfg.get("SELL_AT_LOSS", False)):
            use_attached = False

    if use_attached and sd == "BUY":
        entry_ref, tp_px, sl_px = _compute_attached_tp_sl_prices(
            pid=pid,
            client=client,
            settings=cfg,
            quote_inc=str(quote_inc),
            mid=mid,
            bid=bid,
            ask=ask,
            limit_price=limit_price,
        )
        if tp_px and sl_px:
            limit_only = False
            try:
                limit_only = bool(cfg.get("LIMIT_ONLY", False))
            except Exception:
                limit_only = False

            order_cfg: Dict[str, Any]
            if limit_only:
                # MM26_TPSL_MATH_A:
                # Preserve the intended entry reference in LIMIT_ONLY mode. If the caller
                # supplied a limit_price, use that exact price (snapped to tick) for both the
                # buy order and the attached TP/SL math. Otherwise use the actual submitted
                # LIMIT_ONLY price derived from ask/entry_ref, not the smaller exchange-derived
                # effective quote basis from a quote_size ticket.
                lp_dec = _to_decimal(limit_price)
                if lp_dec > 0:
                    src_px = _fmt_decimal(lp_dec)
                    limit_px = _round_down_to_increment(src_px, quote_inc)
                else:
                    src_px = ask or entry_ref
                    limit_px = _round_up_to_increment(src_px, quote_inc)
                limit_px_dec = _to_decimal(limit_px)

                # MM27_TPSL_GROSS_TICKET_BASIS:
                # In LIMIT_ONLY + attached TP/SL mode, a quote_size payload makes Coinbase
                # treat the acquired base from the post-commission quote amount, so a 5% TP on
                # a $3.00 soldier can preview around $3.1249 instead of the intended ~$3.15.
                # Convert quote_size tickets to explicit base_size using the actual submitted
                # limit price whether or not the caller supplied limit_price explicitly.
                # That keeps the attached bracket tied to the intended gross soldier basis,
                # with only base-increment snapping remaining.
                if limit_px_dec > 0:
                    recomputed_entry_ref, recomputed_tp_px, recomputed_sl_px = _compute_attached_tp_sl_prices(
                        pid=pid,
                        client=client,
                        settings=cfg,
                        quote_inc=str(quote_inc),
                        mid=mid,
                        bid=bid,
                        ask=ask,
                        limit_price=_fmt_decimal(limit_px_dec),
                    )
                    if recomputed_tp_px and recomputed_sl_px:
                        entry_ref = recomputed_entry_ref
                        tp_px = recomputed_tp_px
                        sl_px = recomputed_sl_px

                cfg_body: Dict[str, Any] = {"limit_price": str(limit_px), "post_only": False}
                attached_ticket_basis = None
                if quote_sz and not base_sz and limit_px_dec > 0:
                    try:
                        implied_base = _to_decimal(quote_sz) / limit_px_dec
                        implied_base_q = _round_down_to_increment(_fmt_decimal(implied_base), base_inc)
                        implied_base_d = _to_decimal(implied_base_q)
                        if implied_base_d > 0:
                            cfg_body["base_size"] = str(implied_base_q)
                            attached_ticket_basis = _fmt_decimal(implied_base_d * limit_px_dec)
                        else:
                            cfg_body["quote_size"] = str(quote_sz)
                    except Exception:
                        cfg_body["quote_size"] = str(quote_sz)
                elif quote_sz:
                    cfg_body["quote_size"] = str(quote_sz)
                if base_sz:
                    cfg_body["base_size"] = str(base_sz)
                order_cfg = {"limit_limit_gtc": cfg_body}
            else:
                order_cfg = {"market_market_ioc": {}}
                if quote_sz:
                    order_cfg["market_market_ioc"]["quote_size"] = str(quote_sz)
                if base_sz:
                    order_cfg["market_market_ioc"]["base_size"] = str(base_sz)

            attached_cfg: Dict[str, Any] = {
                "trigger_bracket_gtc": {
                    "limit_price": str(tp_px),
                    "stop_trigger_price": str(sl_px),
                }
            }

            payload: Dict[str, Any] = {
                "client_order_id": cid,
                "product_id": pid,
                "side": sd,
                "order_configuration": order_cfg,
                "attached_order_configuration": attached_cfg,
            }

            _dbg(f"[ATTACHED_TPSL] placing {'limit_limit_gtc' if limit_only else 'market_market_ioc'} with trigger_bracket_gtc: "f'{{"product_id":"{pid}","quote_size":"{quote_sz}","base_size":"{base_sz}",'
                 f'"entry_ref":"{entry_ref}","tp":"{tp_px}","sl":"{sl_px}","client_order_id":"{cid}",'
                 f'"attached_ticket_basis":"{locals().get("attached_ticket_basis") or ""}"}}')

            try:
                last_exc = None
                resp = None
                for attempt in range(0, 1 + _RETRY_MAX):
                    try:
                        resp = client.create_order(**payload)
                        last_exc = None
                        break
                    except TypeError as _e:
                        # SDK might not accept attached_order_configuration keyword; fall back to legacy.
                        raise _e
                    except Exception as _e:
                        last_exc = _e
                        emsg = str(_e)
                        if attempt >= _RETRY_MAX or not _is_transient_error(emsg):
                            raise
                        try:
                            time.sleep(_RETRY_SLEEP_S * (attempt + 1))
                        except Exception:
                            pass

                d = _as_dict(resp)

                success = d.get("success")
                if success is False:
                    err = d.get("failure_reason") or d.get("error") or d.get("message") or "CREATE_ORDER_FAILED"
                    return {
                        "ok": False,
                        "error": str(err),
                        "product_id": pid,
                        "side": sd,
                        "client_order_id": cid,
                        "attached_tpsl": True,
                        "attached_tp": tp_px,
                        "attached_sl": sl_px,
                        "resp": d,
                    }

                order_id = None
                try:
                    sr = d.get("success_response") or {}
                    if isinstance(sr, dict):
                        order_id = sr.get("order_id") or sr.get("orderId")
                except Exception:
                    order_id = None

                return {
                    "ok": True,
                    "product_id": pid,
                    "side": sd,
                    "client_order_id": cid,
                    "order_id": str(order_id) if order_id else "",
                    "attached_tpsl": True,
                    "attached_entry_ref": entry_ref,
                    "attached_tp": tp_px,
                    "attached_sl": sl_px,
                    "resp": d,
                }

            except Exception as e:
                _dbg(f"[ATTACHED_TPSL_FAIL] pid={pid} err={type(e).__name__}:{e} (falling back to limit_limit_gtc)")
                # fall through to legacy limit logic

    # ---------- Legacy LIMIT placement ----------
    # Price: explicit override or best bid/ask
    if limit_price is None or str(limit_price).strip() == "":
        if sd == "BUY":
            limit_price = bid or ask
        else:
            limit_price = ask or bid

    if limit_price is None or str(limit_price).strip() == "":
        return {
            "ok": False,
            "error": "NO_LIMIT_PRICE_AVAILABLE",
            "product_id": pid,
            "side": sd,
        }

    # Quantize price to quote increment (tick size)
    try:
        limit_px = _round_down_to_increment(limit_price, quote_inc)
    except Exception as e:
        return {
            "ok": False,
            "error": f"BAD_LIMIT_PRICE:{type(e).__name__}",
            "product_id": pid,
            "side": sd,
            "limit_price": str(limit_price),
        }

    # If post_only would cross the book, force it off (prevents POST_ONLY rejections)
    try:
        if post_only and bid and ask:
            b = _to_decimal(bid)
            a = _to_decimal(ask)
            px = _to_decimal(limit_px)
            if sd == "BUY" and px >= a:
                post_only = False
            if sd == "SELL" and px <= b:
                post_only = False
    except Exception:
        pass

    cfg_body: Dict[str, Any] = {
        "limit_price": str(limit_px),
        "post_only": bool(post_only),
    }
    if base_sz:
        cfg_body["base_size"] = str(base_sz)
    if quote_sz:
        cfg_body["quote_size"] = str(quote_sz)
    if rfq_disabled is not None:
        cfg_body["rfq_disabled"] = bool(rfq_disabled)
    if reduce_only is not None:
        cfg_body["reduce_only"] = bool(reduce_only)

    order_cfg: Dict[str, Any] = {"limit_limit_gtc": cfg_body}

    _dbg(f"[orders_place] placing limit_limit_gtc: "
         f'{{"product_id":"{pid}","side":"{sd}","size_type":"{st}","size":"{size}",'
         f'"limit_price":"{limit_px}","post_only":{str(post_only).lower()},'
         f'"base_increment":"{base_inc}","quote_increment":"{quote_inc}","client_order_id":"{cid}"}}')

    try:
        resp = None
        for attempt in range(0, 1 + _RETRY_MAX):
            try:
                resp = client.create_order(
                    client_order_id=cid,
                    product_id=pid,
                    side=sd,
                    order_configuration=order_cfg,
                )
                break
            except Exception as _e:
                emsg = str(_e)
                if attempt >= _RETRY_MAX or not _is_transient_error(emsg):
                    raise
                try:
                    time.sleep(_RETRY_SLEEP_S * (attempt + 1))
                except Exception:
                    pass

        d = _as_dict(resp)

        success = d.get("success")
        if success is False:
            err = d.get("failure_reason") or d.get("error") or d.get("message")
            if not err:
                er = d.get("error_response") or d.get("errorResponse") or d.get("error_response")
                if isinstance(er, dict):
                    code = er.get("error") or er.get("failure_reason") or er.get("reason")
                    msg = er.get("message") or er.get("error_message") or er.get("details")
                    if code and msg:
                        err = f"{code}: {msg}"
                    else:
                        err = msg or code
            if not err:
                details = d.get("error_details") or d.get("errorDetails")
                if isinstance(details, list) and details:
                    err = str(details[0])
            err = str(err or "CREATE_ORDER_FAILED")
            return {
                "ok": False,
                "error": err,
                "product_id": pid,
                "side": sd,
                "client_order_id": cid,
                "resp": d,
            }

        order_id = None
        try:
            sr = d.get("success_response") or {}
            if isinstance(sr, dict):
                order_id = sr.get("order_id") or sr.get("orderId")
        except Exception:
            order_id = None

        return {
            "ok": True,
            "product_id": pid,
            "side": sd,
            "client_order_id": cid,
            "order_id": str(order_id) if order_id else "",
            "resp": d,
        }

    except Exception as e:
        return {
            "ok": False,
            "error": f"exception:{type(e).__name__}",
            "exception": repr(e),
            "product_id": pid,
            "side": sd,
            "client_order_id": cid,
        }


def cancel_open_orders(
    product_id: Optional[str] = None,
    side: Optional[str] = None,
    **kwargs: Any,
) -> Dict[str, Any]:
    """Best-effort cancel for OPEN orders."""
    client = kwargs.get("client") or kwargs.get("c") or None
    if client is None:
        client = get_client()

    pid = (product_id or "").strip()
    sd = _normalize_side(side) if side else None

    orders = []
    try:
        from managers.exchange_api.mechanic import list_orders_fixed  # type: ignore
        orders = list_orders_fixed(client, statuses=["OPEN"], product_id=pid or None)
    except Exception:
        try:
            orders = _as_dict(client.list_orders(product_id=pid, order_status="OPEN")).get("orders", [])
        except Exception:
            orders = []

    ids = []
    for o in orders or []:
        d = _as_dict(o)
        if pid and d.get("product_id") != pid:
            continue
        if sd and str(d.get("side", "")).upper() != sd:
            continue
        oid = d.get("order_id") or d.get("id")
        if oid:
            ids.append(str(oid))

    if not ids:
        return {"ok": True, "action": "cancel_open_orders", "canceled": 0, "product_id": pid or None, "side": sd}

    try:
        if hasattr(client, "cancel_orders"):
            resp = client.cancel_orders(order_ids=ids)
            return {"ok": True, "action": "cancel_open_orders", "canceled": len(ids), "resp": _as_dict(resp)}
        if hasattr(client, "cancel_order"):
            n = 0
            last = None
            for oid in ids:
                last = client.cancel_order(order_id=oid)
                n += 1
            return {"ok": True, "action": "cancel_open_orders", "canceled": n, "resp": _as_dict(last)}
        return {"ok": False, "error": "NO_CANCEL_METHOD", "order_ids": ids[:50]}
    except Exception as e:
        return {"ok": False, "error": f"exception:{type(e).__name__}", "exception": repr(e), "order_ids": ids[:50]}