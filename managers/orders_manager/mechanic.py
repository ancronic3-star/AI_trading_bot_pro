"""managers/orders_manager/mechanic.py | shim v2025.12.25-R2

This file is intentionally small and dependency-light.

Why this file exists
- Some diagnostics/one-liners import helpers from `managers.orders_manager.mechanic`.
- The project’s exchange/query helpers live in `managers.exchange_api.mechanic`.
- A previous patch introduced an import-time failure by trying to import
  `get_best_bid_ask` from managers.exchange_api.mechanic (that module exports
  `_best_bid_ask` internally but does not export a public `get_best_bid_ask`).

What this provides
- list_orders_fixed: re-exported from managers.exchange_api.mechanic
- get_best_bid_ask: thin wrapper around client.get_best_bid_ask (best-effort)
- list_fills_fixed: thin wrapper around client.get_fills (best-effort)
"""

from __future__ import annotations

from typing import Any, Sequence

# Re-export the known-good implementation.
from managers.exchange_api.mechanic import list_orders_fixed as list_orders_fixed


def get_best_bid_ask(
    client: Any,
    *,
    product_ids: Sequence[str] | None = None,
    product_id: str | None = None,
) -> Any:
    """Compatibility wrapper.

    Supports client SDKs that accept either:
      - get_best_bid_ask(product_ids=[...])
      - get_best_bid_ask(product_id="XRP-USD")
    """
    fn = getattr(client, "get_best_bid_ask", None)
    if not callable(fn):
        return None

    if product_ids is None and product_id:
        product_ids = [product_id]
    product_ids = list(product_ids or [])

    try:
        return fn(product_ids=product_ids)
    except TypeError:
        # Some SDK variants accept product_id instead of product_ids.
        if len(product_ids) == 1:
            try:
                return fn(product_id=product_ids[0])
            except Exception:
                pass
        try:
            return fn(product_ids)
        except Exception:
            return None
    except Exception:
        return None


def list_fills_fixed(client: Any, product_id: str, limit: int = 200) -> list[Any]:
    """Best-effort wrapper around client.get_fills() returning a list."""
    fn = getattr(client, "get_fills", None)
    if not callable(fn):
        return []

    try:
        resp = fn(product_id=product_id, limit=limit)
    except TypeError:
        try:
            resp = fn(product_id=product_id)
        except Exception:
            try:
                resp = fn(product_id, limit)
            except Exception:
                return []
    except Exception:
        return []

    fills = getattr(resp, "fills", None)
    if fills is None:
        if isinstance(resp, list):
            return resp
        return []

    return list(fills)


__all__ = [
    "list_orders_fixed",
    "get_best_bid_ask",
    "list_fills_fixed",
]
