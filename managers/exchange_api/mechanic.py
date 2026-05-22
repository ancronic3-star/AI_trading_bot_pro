# managers/exchange_api/mechanic.py
"""
Exchange API helper functions (Coinbase Advanced Trade RESTClient).

Purpose in this project:
- Provide *stable* helpers for:
  - best bid/ask from get_product_book()
  - increments from get_product()
  - list_orders / list_fills with tolerant response-shape parsing

Key robustness:
Coinbase RESTClient responses may be objects with attributes, dict-like, or wrappers like:
  {"pricebook": {"bids":[...], "asks":[...], ...}, ...}

This module normalizes these shapes so callers don't have to.
"""

from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


# -------- helpers --------

def _to_decimal(v: Any) -> Optional[Decimal]:
    if v is None:
        return None
    try:
        return Decimal(str(v))
    except (InvalidOperation, ValueError, TypeError):
        return None

def _as_dict(obj: Any) -> Dict[str, Any]:
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
    # attribute bag fallback
    try:
        return {k: getattr(obj, k) for k in dir(obj) if not k.startswith("_")}
    except Exception:
        return {}

def _first_key(d: Mapping[str, Any]) -> str:
    for k in d.keys():
        return str(k)
    return ""

def _extract_pricebook(book_resp: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Return (bids, asks) as list-of-dicts.
    Supports:
      {"pricebook": {"bids":[{"price":..,"size":..}], "asks":[...]}, ...}
      {"bids":[...], "asks":[...]}
      object.pricebook.bids / object.bids, etc.
    """
    d = _as_dict(book_resp)

    # common: top-level "pricebook"
    pb = d.get("pricebook")
    if isinstance(pb, dict):
        bids = pb.get("bids") or []
        asks = pb.get("asks") or []
        return (list(bids) if isinstance(bids, list) else [], list(asks) if isinstance(asks, list) else [])

    # sometimes: nested under "pricebook" key inside dict from to_dict already
    if "pricebook" in d and not isinstance(pb, dict):
        pb2 = _as_dict(pb)
        bids = pb2.get("bids") or []
        asks = pb2.get("asks") or []
        return (list(bids) if isinstance(bids, list) else [], list(asks) if isinstance(asks, list) else [])

    # fallback: top-level bids/asks
    bids = d.get("bids") or []
    asks = d.get("asks") or []
    return (list(bids) if isinstance(bids, list) else [], list(asks) if isinstance(asks, list) else [])


# -------- public API --------

def get_increments(client: Any, product_id: str) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Return (base_increment, quote_increment) as Decimal.
    Uses client.get_product(product_id).
    """
    p = None
    fn = getattr(client, "get_product", None)
    if callable(fn):
        p = fn(product_id)
    d = _as_dict(p)

    # common fields on object: base_increment / quote_increment
    base_inc = d.get("base_increment") or getattr(p, "base_increment", None)
    quote_inc = d.get("quote_increment") or getattr(p, "quote_increment", None)

    return (_to_decimal(base_inc), _to_decimal(quote_inc))

def get_best_bid_ask(client: Any, product_id: str, *, limit: int = 1) -> Tuple[Optional[Decimal], Optional[Decimal]]:
    """
    Return (best_bid, best_ask) as Decimal.
    Uses client.get_product_book(product_id, limit=limit).
    Handles nested pricebook shape.
    """
    fn = getattr(client, "get_product_book", None)
    if not callable(fn):
        return (None, None)

    book = fn(product_id, limit=limit)
    bids, asks = _extract_pricebook(book)

    bid = _to_decimal(bids[0].get("price")) if bids else None
    ask = _to_decimal(asks[0].get("price")) if asks else None
    return (bid, ask)

def list_orders_fixed(client: Any, statuses: Sequence[str] | None = None, product_id: Optional[str] = None) -> List[Any]:
    """
    Tolerant wrapper around RESTClient.list_orders().
    - If OPEN present, force only OPEN.
    - Returns list of order objects/dicts (best-effort).
    """
    sts = [str(s).upper() for s in (statuses or ["OPEN"])]
    if "OPEN" in sts:
        sts = ["OPEN"]

    fn = getattr(client, "list_orders", None)
    if not callable(fn):
        return []

    resp = fn(order_status=sts, product_id=product_id)  # Coinbase SDK uses order_status
    d = _as_dict(resp)

    # common shapes
    for key in ("orders", "order", "data", "results"):
        v = d.get(key)
        if isinstance(v, list):
            return v

    # sometimes response itself is list-like
    if isinstance(resp, list):
        return resp

    return []

def list_fills_fixed(client: Any, product_id: Optional[str] = None, *, limit: int = 250) -> List[Any]:
    """
    Tolerant wrapper around fills.
    Tries client.list_fills(product_id=..., limit=...).
    Returns list.
    """
    fn = getattr(client, "list_fills", None)
    if not callable(fn):
        return []

    # Coinbase SDK varies parameter names; try both.
    try:
        resp = fn(product_id=product_id, limit=limit)
    except TypeError:
        resp = fn(product_id, limit)

    d = _as_dict(resp)
    for key in ("fills", "data", "results"):
        v = d.get(key)
        if isinstance(v, list):
            return v
    if isinstance(resp, list):
        return resp
    return []
