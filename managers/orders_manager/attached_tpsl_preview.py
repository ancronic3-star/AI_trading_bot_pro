# managers/orders_manager/attached_tpsl_preview.py
"""MM23 diagnostic: preview a BUY with attached TP/SL.

Usage (PowerShell):
  python -u managers/orders_manager/attached_tpsl_preview.py --pid XRP-USD --quote 10

This does NOT place a live order unless you explicitly switch the call in this file.
It attempts to call the SDK preview method if present; otherwise it prints the JSON payload
you can compare against Coinbase docs.

Attached TP/SL docs:
- Create Order: attached_order_configuration.trigger_bracket_gtc (omit size on attached config)
- Preview Order supports the same fields.
"""

from __future__ import annotations

import argparse
import json
from decimal import Decimal, ROUND_DOWN
from typing import Any, Dict, Optional, Tuple

from managers.auth_manager.auth_jwt import get_client
from managers.config_manager.settings import load_settings


D = Decimal


def _D(x: Any) -> D:
    if isinstance(x, D):
        return x
    try:
        return D(str(x))
    except Exception:
        return D("0")


def _fmt(d: D) -> str:
    s = format(d, "f")
    if "." in s:
        s = s.rstrip("0").rstrip(".")
    return s or "0"


def _round_down_to_increment(value: Any, increment: Any) -> str:
    v = _D(value)
    i = _D(increment)
    if i <= 0:
        return _fmt(v)
    q = (v / i).to_integral_value(rounding=ROUND_DOWN)
    return _fmt(q * i)


def _snap(v: D, inc: D, up: bool) -> D:
    if inc <= 0:
        return v
    q = v / inc
    if up:
        q = (-q).to_integral_value(rounding=ROUND_DOWN) * D("-1")
    else:
        q = q.to_integral_value(rounding=ROUND_DOWN)
    return q * inc


def _norm_pct(val: Any) -> D:
    d = _D(val)
    try:
        if d > 1:
            d = d / D("100")
    except Exception:
        pass
    if d < 0:
        d = D("0")
    return d


def _product_increments(client: Any, pid: str) -> Tuple[str, str]:
    base_inc = "0.00000001"
    quote_inc = "0.0001"
    try:
        prod = None
        try:
            prod = client.get_product(product_id=pid)
        except TypeError:
            prod = client.get_product(pid)
        d = prod.to_dict() if hasattr(prod, "to_dict") else (prod if isinstance(prod, dict) else {})
        bi = d.get("base_increment") or d.get("baseIncrement")
        qi = d.get("quote_increment") or d.get("quoteIncrement")
        if bi:
            base_inc = str(bi)
        if qi:
            quote_inc = str(qi)
    except Exception:
        pass
    return base_inc, quote_inc


def _best_bid_ask(client: Any, pid: str) -> Tuple[Optional[str], Optional[str]]:
    try:
        try:
            r = client.get_product_book(product_id=pid, limit=1)
        except TypeError:
            r = client.get_product_book(pid, limit=1)
        d = r.to_dict() if hasattr(r, "to_dict") else (r if isinstance(r, dict) else {})
        pb = d.get("pricebook") or {}
        bids = pb.get("bids") or []
        asks = pb.get("asks") or []
        bid = bids[0].get("price") if bids and isinstance(bids[0], dict) else None
        ask = asks[0].get("price") if asks and isinstance(asks[0], dict) else None
        return (str(bid) if bid else None, str(ask) if ask else None)
    except Exception:
        return (None, None)


def build_payload(pid: str, quote_size: Optional[str], base_size: Optional[str], settings: Dict[str, Any], limit_price: Optional[str] = None) -> Dict[str, Any]:
    client = get_client()
    base_inc, quote_inc = _product_increments(client, pid)
    inc = _D(quote_inc)
    bid, ask = _best_bid_ask(client, pid)
    lp = _D(limit_price)

    limit_only = False
    try:
        limit_only = bool(settings.get("LIMIT_ONLY", False))
    except Exception:
        limit_only = False

    # MM26_TPSL_MATH_A: mirror runtime behavior. In LIMIT_ONLY mode, prefer the
    # submitted limit_price as the entry reference whenever it exists.
    if limit_only and lp > 0:
        ref = lp
    else:
        ref = _D(ask) if _D(ask) > 0 else _D(bid)
        if ref <= 0 and lp > 0:
            ref = lp

    tp_pct = _norm_pct(settings.get("TP_PCT", 0))
    sl_pct = _norm_pct(settings.get("SL_PCT", 0))
    tp = _snap(ref * (D("1") + tp_pct), inc, up=True)
    sl = _snap(ref * (D("1") - sl_pct), inc, up=False)

    order_cfg: Dict[str, Any]
    if limit_only:
        if lp > 0:
            lim = _snap(lp, inc, up=False)
        else:
            src = _D(ask) if _D(ask) > 0 else ref
            lim = _snap(src, inc, up=True)
        body: Dict[str, Any] = {"limit_price": _fmt(lim), "post_only": False}
        # MM27_TPSL_GROSS_TICKET_BASIS: mirror runtime behavior.
        # In LIMIT_ONLY + attached TP/SL mode, use the actual submitted limit price to
        # convert quote tickets into explicit base_size, even when no explicit limit_price
        # was passed. This keeps previewed attached proceeds tied to the intended gross
        # soldier basis rather than a smaller post-commission quote basis.
        if quote_size and not base_size and lim > 0:
            implied_base = _D(quote_size) / lim
            body["base_size"] = _round_down_to_increment(_fmt(implied_base), base_inc)
        elif quote_size:
            body["quote_size"] = str(quote_size)
        if base_size:
            body["base_size"] = str(base_size)
        order_cfg = {"limit_limit_gtc": body}
    else:
        order_cfg = {"market_market_ioc": {}}
        if quote_size:
            order_cfg["market_market_ioc"]["quote_size"] = str(quote_size)
        if base_size:
            order_cfg["market_market_ioc"]["base_size"] = str(base_size)

    payload = {
        "product_id": pid,
        "side": "BUY",
        "order_configuration": order_cfg,
        "attached_order_configuration": {
            "trigger_bracket_gtc": {
                "limit_price": _fmt(tp),
                "stop_trigger_price": _fmt(sl),
            }
        },
    }
    return payload


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--pid", required=True)
    ap.add_argument("--quote", default=None)
    ap.add_argument("--base", default=None)
    ap.add_argument("--limit-price", default=None)
    args = ap.parse_args()

    s = load_settings()
    payload = build_payload(args.pid.strip().upper(), args.quote, args.base, s, limit_price=args.limit_price)
    print("Payload:")
    print(json.dumps(payload, indent=2))

    c = get_client()

    # Best-effort preview call (method name varies by SDK version)
    for meth in ("preview_order", "preview_orders", "preview"):
        fn = getattr(c, meth, None)
        if callable(fn):
            try:
                r = fn(**payload) if meth != "preview_orders" else fn(payload)
                d = r.to_dict() if hasattr(r, "to_dict") else (r if isinstance(r, dict) else {"resp": str(r)})
                print(f"\nPreview via {meth}:")
                print(json.dumps(d, indent=2))
                return 0
            except Exception as e:
                print(f"\nPreview call {meth} failed: {type(e).__name__}: {e}")
                break

    print("\nNo preview method found on RESTClient (printed payload only).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())