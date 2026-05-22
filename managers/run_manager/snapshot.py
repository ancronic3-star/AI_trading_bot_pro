# snapshot.py  — lightweight, fast snapshot builder for run_manager
# Full-file overwrite.

from __future__ import annotations
from types import SimpleNamespace
from decimal import Decimal
from datetime import datetime, timezone

def _to_dec(x) -> Decimal:
    return Decimal(str(x))

def _get(obj, name, default=None):
    # Works for dicts and SDK objects
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

def _first_price(side_rows) -> Decimal | None:
    if not side_rows:
        return None
    row0 = side_rows[0]
    # row can be dict or SDK object with .price
    p = _get(row0, "price")
    return _to_dec(p) if p is not None else None

def _pricebooks_iter(resp):
    """
    Normalizes coinbase get_best_bid_ask() return types:
      - dict with 'pricebooks' (list of dicts/objects), or
      - object with .pricebooks, or
      - already a list
    """
    if resp is None:
        return []
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        pb = resp.get("pricebooks") or []
        return pb if isinstance(pb, list) else []
    # object
    pb = getattr(resp, "pricebooks", None)
    return pb if isinstance(pb, list) else []

def build_live_snapshot(
    c,
    universe: list[str] | None = None,
    lookback_sec: int = 300,   # kept for signature compatibility (unused here)
    usd_only_quotes: bool = True,
) -> SimpleNamespace:
    """
    Returns SimpleNamespace with:
      uni: list[str] product_ids
      ba:  dict[product_id] -> {'bid': Decimal, 'ask': Decimal}
      now: datetime (UTC)

    Notes:
    - Fast path: only one network call (best_bid_ask). Do not fetch per-product
      metadata here to avoid strategy timeouts.
    - Universe is expected to be decided upstream (menu/universe manager).
      If None, fall back to a small USD majors set.
    """
    if not universe:
        # Safe fallback majors; upstream should normally provide a TOP list.
        universe = ["BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD"]

    # Batch best bid/ask in one call
    resp = c.get_best_bid_ask(product_ids=universe)
    ba = {}
    for pb in _pricebooks_iter(resp):
        pid = _get(pb, "product_id", _get(pb, "productId"))
        if not pid:
            continue
        bid = _first_price(_get(pb, "bids", []))
        ask = _first_price(_get(pb, "asks", []))
        if bid is None or ask is None:
            continue
        ba[pid] = {"bid": bid, "ask": ask}

    return SimpleNamespace(
        uni=list(universe),
        ba=ba,
        now=datetime.now(timezone.utc),
    )
