# managers/exchange_api/mechanic.py | v2025.10.07-R3
"""
Exchange API Mechanic — R3 rush hotfix. Pure Python. Single-file scope.

Exports:
- list_orders_fixed(client, statuses=['OPEN'], product_id=None) -> list
- create_limit_order_retry(client, product_id, side, limit_price, size, post_only, client_order_id, time_in_force='GTC')

Rules:
- Remove heredoc/PwSh artifacts. OPEN hygiene: never mix OPEN with others.
- Anchor limit_price from get_best_bid_ask(); fallback pricebook.pricebook.bids/asks[0].
- size may be scalar BASE or {'value': x, 'kind': 'BASE'|'QUOTE'}; QUOTE → BASE via price.
- Quantize to product increments. Place LIMIT GTC. Retry once on 'missing reference price' or preview-only.
- Always set client_order_id. No PFID in bodies. Log JSON lines to logs/exapi_hotfix.log. No local exceptions.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_DOWN, InvalidOperation
import datetime as _dt
import inspect
import json
import logging
import os
from typing import Any, Dict, Mapping, Optional, Sequence, Tuple

__all__ = ["list_orders_fixed", "create_limit_order_retry"]

_LOG = logging.getLogger("managers.exchange_api.mechanic")

# ---------- logging ----------

def _jlog(event: str, **kw: Any) -> None:
    try:
        os.makedirs("logs", exist_ok=True)
        payload = {"stage": "exapi_hotfix", "ts": _dt.datetime.utcnow().isoformat() + "Z", "event": event}
        if "exception" in kw or "exc" in kw:
            payload["exception"] = str(kw.get("exception") or kw.get("exc"))
        payload.update({k: v for k, v in kw.items() if k not in {"exception", "exc"}})
        with open(os.path.join("logs", "exapi_hotfix.log"), "a", encoding="ascii", errors="ignore") as fh:
            fh.write(json.dumps(payload, ensure_ascii=True, sort_keys=True) + "\n")
    except Exception:
        pass
    try:
        _LOG.error(json.dumps({"stage": "exapi_hotfix", "event": event, **{k: v for k, v in kw.items() if k != "exception"}}, ensure_ascii=True, sort_keys=True))
    except Exception:
        pass

# ---------- helpers ----------

def _as_attr(obj: Any, name: str, default: Any = None) -> Any:
    if obj is None:
        return default
    if isinstance(obj, Mapping):
        return obj.get(name, default)
    return getattr(obj, name, default)

def _to_decimal(x: Any) -> Optional[Decimal]:
    try:
        if isinstance(x, Decimal):
            return x
        return Decimal(str(x))
    except (InvalidOperation, ValueError, TypeError):
        return None

def _round_to_inc(value: Decimal, inc: Optional[Decimal]) -> Decimal:
    if not isinstance(value, Decimal) or not isinstance(inc, Decimal) or inc <= 0:
        return value
    return (value / inc).to_integral_value(rounding=ROUND_DOWN) * inc

def _product_increments(client: Any, pid: str) -> Tuple[Decimal, Decimal]:
    base_inc = Decimal("0.00000001")
    quote_inc = Decimal("0.01")
    try:
        fn = getattr(client, "get_product", None)
        if callable(fn):
            resp = fn(product_id=pid)
            prod = _as_attr(resp, "product", resp)
            b = _to_decimal(_as_attr(prod, "base_increment", None))
            q = _to_decimal(_as_attr(prod, "quote_increment", None))
            if b:
                base_inc = b
            if q:
                quote_inc = q
    except Exception as e:
        _jlog("read_increments_failed", product_id=pid, exception=e)
    return base_inc, quote_inc

def _best_bid_ask(client: Any, pid: str) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    # Batch endpoint first
    batch = getattr(client, "get_best_bid_ask", None)
    if callable(batch):
        try:
            resp = batch(product_ids=[pid])
            items = _as_attr(resp, "best_bid_ask", _as_attr(resp, "data", resp))
            if isinstance(items, Mapping):
                items = list(items.values())
            it = items[0] if isinstance(items, (list, tuple)) and items else items
            bp = _to_decimal(_as_attr(it, "bid_price", _as_attr(it, "best_bid", _as_attr(it, "bid", None))))
            ap = _to_decimal(_as_attr(it, "ask_price", _as_attr(it, "best_ask", _as_attr(it, "ask", None))))
            if bp and ap:
                return bp, ap
        except Exception as e:
            _jlog("batch_best_bid_ask_failed", product_id=pid, exception=e)
    # Fallback: SDK shape resp.pricebook.bids/asks[0] with dict/object tolerance
    try:
        resp = client.get_product_book(product_id=pid)
    except TypeError:
        resp = client.get_product_book(product=pid)
    pb = _as_attr(resp, "pricebook", resp)
    bids = _as_attr(pb, "bids", _as_attr(pb, "bid", [])) or []
    asks = _as_attr(pb, "asks", _as_attr(pb, "ask", [])) or []
    def _p(level):
        if level is None:
            return None
        price = _as_attr(level, "price", None)
        if price is None and isinstance(level, (list, tuple)) and level:
            price = level[0]
        return _to_decimal(price)
    return _p(bids[0]) if bids else None, _p(asks[0]) if asks else None

def _extract_message(resp: Any) -> str:
    for k in ("message", "error", "reason", "status_message"):
        v = _as_attr(resp, k, None)
        if v:
            return str(v).lower()
    er = _as_attr(resp, "error_response", None)
    if er:
        mv = _as_attr(er, "message", None)
        if mv:
            return str(mv).lower()
    try:
        return str(resp).lower()
    except Exception:
        return ""

def _normalize_base_size(size: Any, price: Decimal, base_inc: Decimal, quote_inc: Decimal) -> Optional[Decimal]:
    """
    Accept scalar base, or {'value': x, 'kind': 'BASE'|'QUOTE'}.
    Return base size Decimal rounded to base_inc, else None.
    """
    try:
        if isinstance(size, Mapping):
            val = _to_decimal(size.get("value"))
            kind = str(size.get("kind", "BASE")).upper()
            if val is None:
                return None
            if kind == "QUOTE":
                base = (val / price) if price and val else None
                return _round_to_inc(base, base_inc) if base is not None else None
            return _round_to_inc(val, base_inc)
        val = _to_decimal(size)
        return _round_to_inc(val, base_inc) if val is not None else None
    except Exception:
        return None

# ---------- public API ----------

def list_orders_fixed(client: Any, statuses: Sequence[str] | None = None, product_id: Optional[str] = None) -> list:
    """
    OPEN hygiene: if 'OPEN' present -> use ['OPEN'] only.
    Calls client.list_orders(order_status=statuses, product_id=product_id) and returns a list.
    """
    sts = [str(s).upper() for s in (statuses or ["OPEN"])]
    if "OPEN" in sts:
        sts = ["OPEN"]

    fn = getattr(client, "list_orders", None)
    if not callable(fn):
        _jlog("client_missing_list_orders")
        return []

    # Preferred signature
    kwargs: Dict[str, Any] = {"order_status": sts}
    if product_id:
        kwargs["product_id"] = product_id

    try:
        resp = fn(**kwargs)
    except TypeError:
        # Fallback param names
        got = False
        for name in ("statuses", "order_statuses", "status"):
            try:
                resp = fn(**({name: sts, **({"product_id": product_id} if product_id else {})}))
                got = True
                break
            except Exception:
                continue
        if not got:
            _jlog("list_orders_call_failed", statuses=sts, product_id=product_id)
            return []
    except Exception as e:
        _jlog("list_orders_failed", statuses=sts, product_id=product_id, exception=e)
        return []

    orders = _as_attr(resp, "orders", None)
    if orders is None:
        if isinstance(resp, (list, tuple)):
            return list(resp)
        return [resp] if resp is not None else []
    return list(orders)

def create_limit_order_retry(
    client: Any,
    product_id: str,
    side: str,
    limit_price: Any,
    size: Any,
    post_only: bool,
    client_order_id: str,
    time_in_force: str = "GTC",
):
    """
    LIMIT GTC placement with anchored price and single retry on 'missing reference price' or preview-only.
    Returns SDK response. On internal failure returns {'ok': False, 'errors': [...]}.
    """
    if not client_order_id or not str(client_order_id).strip():
        _jlog("client_order_id_required")
        return {"ok": False, "errors": ["client_order_id_required"]}

    side = str(side).upper()
    if side not in {"BUY", "SELL"}:
        _jlog("invalid_side", side=side)
        return {"ok": False, "errors": ["invalid_side"]}

    base_inc, quote_inc = _product_increments(client, product_id)

    p = _to_decimal(limit_price) if limit_price is not None else None
    if p is None:
        bid, ask = _best_bid_ask(client, product_id)
        p = bid if side == "BUY" else ask
    if p is None:
        _jlog("reference_price_unavailable", product_id=product_id)
        return {"ok": False, "errors": ["reference_price_unavailable"]}
    p = _round_to_inc(p, quote_inc)

    base_sz = _normalize_base_size(size, p, base_inc, quote_inc)
    if base_sz is None:
        _jlog("invalid_size", product_id=product_id)
        return {"ok": False, "errors": ["invalid_size"]}

    helper = getattr(client, "create_limit_order", None)

    def _call(post_flag: bool):
        if callable(helper):
            return helper(
                product_id=product_id,
                side=side,
                limit_price=str(p),
                base_size=str(base_sz),
                post_only=bool(post_flag),
                time_in_force=time_in_force,
                client_order_id=client_order_id,
            )
        cfg = {"limit_limit_gtc": {"base_size": str(base_sz), "limit_price": str(p), "post_only": bool(post_flag)}}
        payload = {"client_order_id": client_order_id, "product_id": product_id, "side": side, "order_configuration": cfg}
        return client.create_order(**payload)

    try:
        resp = _call(post_only)
        msg = _extract_message(resp)
        if (("missing reference price" in msg) or ("preview" in msg)) and post_only:
            resp = _call(False)
        return resp
    except Exception as e:
        _jlog("create_limit_order_failed", product_id=product_id, side=side, exception=e)
        return {"ok": False, "errors": ["create_limit_order_failed"]}
