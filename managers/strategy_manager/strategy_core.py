# managers/strategy_manager/strategy_core.py
# Version: v1.1.3-compat
#
# Fix:
# - Unwrap Coinbase "product book" responses that are commonly shaped like:
#     {"pricebook": {"bids":[...], "asks":[...], ...}}
#   or SDK objects with .pricebook.
# - This fixes "no_mid" situations caused by failing to find bids/asks.
#
# Goal remains:
# - Stable get_action_scores() API regardless of how run_manager calls it.
# - Correctly extract best bid/ask + sizes from Coinbase RESTClient responses
# - Provide market fields run_manager expects: bid/ask/mid/spr_bps/tob_usd/press.

from __future__ import annotations

from decimal import Decimal as D
from typing import Any, Dict, List, Optional, Sequence, Tuple

__all__ = ["get_action_scores"]
__version__ = "v1.1.3-compat"


# ---------------------------
# Generic helpers (dict/object)
# ---------------------------

def _get(obj: Any, key: str, default: Any = None) -> Any:
    """Get field from dict or attribute from object."""
    if obj is None:
        return default
    if isinstance(obj, dict):
        return obj.get(key, default)
    return getattr(obj, key, default)


def _as_dict(obj: Any) -> Optional[Dict[str, Any]]:
    """Best-effort conversion of SDK objects to dict."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return obj
    td = getattr(obj, "to_dict", None)
    if callable(td):
        try:
            d = td()
            return d if isinstance(d, dict) else None
        except Exception:
            return None
    if hasattr(obj, "__dict__"):
        try:
            return dict(obj.__dict__)
        except Exception:
            return None
    return None


def _is_rest_client(obj: Any) -> bool:
    """Heuristic: Coinbase RESTClient-like object."""
    return bool(obj) and (
        callable(getattr(obj, "get_best_bid_ask", None))
        or callable(getattr(obj, "get_product_book", None))
        or callable(getattr(obj, "get_product_book", None))
    )


def _to_decimal(x: Any, default: str = "0") -> D:
    try:
        if x is None:
            return D(default)
        return D(str(x))
    except Exception:
        return D(default)


def _unwrap_pricebook(container: Any) -> Any:
    """
    Coinbase product book often returns:
      {"pricebook": {...}}
    or an SDK object with attribute .pricebook.
    This function returns the inner pricebook if present, otherwise returns input.
    """
    if container is None:
        return None

    # dict wrapper
    if isinstance(container, dict):
        pb = container.get("pricebook") or container.get("priceBook") or container.get("price_book")
        if pb is not None:
            return pb
        return container

    # object wrapper
    pb = getattr(container, "pricebook", None) or getattr(container, "priceBook", None) or getattr(container, "price_book", None)
    if pb is not None:
        return pb

    # try to_dict wrapper
    d = _as_dict(container)
    if isinstance(d, dict):
        pb2 = d.get("pricebook") or d.get("priceBook") or d.get("price_book")
        if pb2 is not None:
            return pb2

    return container


# ---------------------------
# Level parsing (dict/object/scalar/list)
# ---------------------------

def _level_price(level: Any) -> D:
    """
    Accept:
      - scalar: "1.23" / 1.23
      - list/tuple: ["1.23","10",...] -> price at index 0
      - dict/object: keys/attrs like price/px/limit_price
    """
    if level is None:
        return D("0")
    if isinstance(level, (str, int, float, D)):
        return _to_decimal(level, default="0")
    if isinstance(level, (list, tuple)):
        return _to_decimal(level[0] if len(level) >= 1 else None, default="0")

    return _to_decimal(
        _get(level, "price", None)
        or _get(level, "px", None)
        or _get(level, "limit_price", None)
        or _get(level, "limitPrice", None)
        or _get(level, "rate", None),
        default="0",
    )


def _level_size(level: Any) -> D:
    """
    Accept:
      - scalar: "10" / 10
      - list/tuple: ["1.23","10",...] -> size at index 1
      - dict/object: keys/attrs like size/quantity/base_size
    """
    if level is None:
        return D("0")
    if isinstance(level, (str, int, float, D)):
        return _to_decimal(level, default="0")
    if isinstance(level, (list, tuple)):
        return _to_decimal(level[1] if len(level) >= 2 else None, default="0")

    return _to_decimal(
        _get(level, "size", None)
        or _get(level, "quantity", None)
        or _get(level, "qty", None)
        or _get(level, "base_size", None)
        or _get(level, "baseSize", None),
        default="0",
    )


# ---------------------------
# Input coercion (compat)
# ---------------------------

def _coerce_inputs(
    args: Tuple[Any, ...],
    kwargs: Dict[str, Any],
) -> Tuple[Optional[Any], Dict[str, Any], List[str], Optional[List[Dict[str, Any]]]]:
    """
    Normalize call-shapes into:
      client: RESTClient-like or None
      settings: dict
      universe: list[str]
      candidates: legacy list[dict] or None
    """
    client = kwargs.pop("client", None) or kwargs.pop("c", None)
    settings = (
        kwargs.pop("settings", None)
        or kwargs.pop("cfg", None)
        or kwargs.pop("config", None)
        or {}
    )
    universe = (
        kwargs.pop("universe", None)
        or kwargs.pop("u", None)
        or kwargs.pop("products", None)
    )
    candidates: Optional[List[Dict[str, Any]]] = kwargs.pop("candidates", None)

    if args:
        if len(args) == 1:
            a0 = args[0]
            if client is None and _is_rest_client(a0):
                client = a0
            elif candidates is None and isinstance(a0, list) and (not a0 or isinstance(a0[0], dict)):
                candidates = a0
            elif universe is None and isinstance(a0, (list, tuple)) and (not a0 or isinstance(a0[0], str)):
                universe = list(a0)
            elif isinstance(a0, dict) and (not isinstance(settings, dict) or not settings):
                settings = a0

        elif len(args) == 2:
            a0, a1 = args
            if client is None and _is_rest_client(a0):
                client = a0
                if isinstance(a1, dict):
                    settings = a1
                elif universe is None and isinstance(a1, (list, tuple)) and (not a1 or isinstance(a1[0], str)):
                    universe = list(a1)
                elif candidates is None and isinstance(a1, list) and (not a1 or isinstance(a1[0], dict)):
                    candidates = a1
            elif candidates is None and isinstance(a0, list) and (not a0 or isinstance(a0[0], dict)):
                candidates = a0
                if isinstance(a1, dict):
                    settings = a1
            else:
                if isinstance(a0, dict) and universe is None and isinstance(a1, (list, tuple)):
                    settings = a0
                    universe = list(a1)

        else:
            a0, a1, a2 = args[0], args[1], args[2]
            if client is None and _is_rest_client(a0):
                client = a0
                if isinstance(a1, list) and a1:
                    if isinstance(a1[0], dict):
                        candidates = a1  # type: ignore[assignment]
                    elif isinstance(a1[0], str):
                        universe = list(a1)  # type: ignore[assignment]
                elif isinstance(a1, (list, tuple)):
                    universe = list(a1)

                if isinstance(a2, dict):
                    settings = a2
            elif candidates is None and isinstance(a0, list) and (not a0 or isinstance(a0[0], dict)):
                candidates = a0
                if isinstance(a1, dict):
                    settings = a1
                if universe is None and isinstance(a2, (list, tuple)):
                    universe = list(a2)

    if not isinstance(settings, dict):
        settings = {}

    if universe is None:
        u = settings.get("UNIVERSE") or settings.get("UNIVERSE_LIST") or []
        if isinstance(u, str):
            universe = [p.strip() for p in u.split(",") if p.strip()]
        elif isinstance(u, list):
            universe = [str(x) for x in u]
        else:
            universe = []

    # Normalize universe to list[str]
    if isinstance(universe, (list, tuple)):
        universe_list: List[str] = []
        for x in universe:
            if isinstance(x, str):
                s = x.strip().upper()
                if s:
                    universe_list.append(s)
        universe = universe_list
    else:
        universe = []

    return client, settings, universe, candidates


# ---------------------------
# Coinbase market data extraction
# ---------------------------

def _iter_pricebooks(resp: Any) -> List[Any]:
    """Return list of pricebook objects/dicts from various SDK response shapes."""
    if resp is None:
        return []
    if isinstance(resp, list):
        return resp

    if isinstance(resp, dict):
        # Some endpoints return a single wrapped pricebook
        if "pricebook" in resp or "priceBook" in resp or "price_book" in resp:
            return [_unwrap_pricebook(resp)]

        pbs = resp.get("pricebooks") or resp.get("priceBooks") or resp.get("price_books")
        if isinstance(pbs, list):
            return pbs
        if pbs is not None:
            return [pbs]
        data = resp.get("data")
        if isinstance(data, list):
            return data
        if data is not None:
            return [data]
        return []

    # object forms
    pb_attr = getattr(resp, "pricebook", None) or getattr(resp, "priceBook", None) or getattr(resp, "price_book", None)
    if pb_attr is not None:
        return [_unwrap_pricebook(pb_attr)]

    pbs = getattr(resp, "pricebooks", None) or getattr(resp, "priceBooks", None) or getattr(resp, "price_books", None)
    if isinstance(pbs, list):
        return pbs
    if pbs is not None:
        return [pbs]

    d = _as_dict(resp) or {}
    return _iter_pricebooks(d)


def _best_from_book(book: Any) -> Tuple[D, D, D, D]:
    """Extract top bid/ask and sizes from a product book response."""
    book = _unwrap_pricebook(book)

    bids = _get(book, "bids", None)
    asks = _get(book, "asks", None)

    if not isinstance(bids, list):
        bd = _as_dict(book) or {}
        bids = bd.get("bids")
    if not isinstance(asks, list):
        bd = _as_dict(book) or {}
        asks = bd.get("asks")

    b0 = bids[0] if isinstance(bids, list) and bids else None
    a0 = asks[0] if isinstance(asks, list) and asks else None

    bid = _level_price(b0)
    ask = _level_price(a0)
    bid_sz = _level_size(b0)
    ask_sz = _level_size(a0)
    return bid, ask, bid_sz, ask_sz


def _product_book(client: Any, pid: str, level: int = 2) -> Optional[Any]:
    """
    Return an unwrapped pricebook dict/object (SDK-dependent).
    """
    resp: Any = None
    for call in (
        lambda: client.get_product_book(product_id=pid, level=level),
        lambda: client.get_product_book(product_id=pid, limit=level),
        lambda: client.get_product_book(pid, level),
        lambda: client.get_product_book(pid),
    ):
        try:
            resp = call()
            break
        except Exception:
            resp = None

    if resp is None:
        return None

    # Unwrap common wrapper: {"pricebook": {...}} or obj.pricebook
    unwrapped = _unwrap_pricebook(resp)

    # If dict wrapper still contains the fields directly, return it
    if isinstance(unwrapped, dict):
        if "bids" in unwrapped and "asks" in unwrapped:
            return unwrapped
        if isinstance(unwrapped.get("book"), dict):
            return unwrapped["book"]
        if isinstance(unwrapped.get("data"), dict):
            return unwrapped["data"]
        return unwrapped

    # If object, try dict conversion after unwrap
    d = _as_dict(unwrapped)
    if isinstance(d, dict):
        if "bids" in d and "asks" in d:
            return d
        if isinstance(d.get("book"), dict):
            return d["book"]
        if isinstance(d.get("data"), dict):
            return d["data"]
        if isinstance(d.get("pricebook"), dict):
            return d["pricebook"]

    return unwrapped


def _best_bid_ask(client: Any, pid: str) -> Tuple[D, D, D, D]:
    """
    Return (bid, ask, bid_size, ask_size) as Decimals.

    Supports:
      - get_best_bid_ask response with pricebooks containing:
          bid/ask/bid_size/ask_size
        OR best_bid/best_ask objects/scalars
        OR bids/asks arrays
      - fallback to get_product_book() to populate missing values.
    """
    resp: Any = None
    last_err: Optional[Exception] = None

    for call in (
        lambda: client.get_best_bid_ask(product_ids=[pid]),
        lambda: client.get_best_bid_ask(product_ids=pid),
        lambda: client.get_best_bid_ask(product_id=pid),
        lambda: client.get_best_bid_ask(pid),
    ):
        try:
            resp = call()
            last_err = None
            break
        except Exception as e:
            last_err = e
            resp = None

    bid = D("0")
    ask = D("0")
    bid_sz = D("0")
    ask_sz = D("0")

    if resp is not None:
        pricebooks = _iter_pricebooks(resp)

        pb_match: Optional[Any] = None
        for pb in pricebooks:
            pb_pid = _get(pb, "product_id", None) or _get(pb, "productId", None)
            if isinstance(pb_pid, str) and pb_pid.upper() == pid.upper():
                pb_match = pb
                break
        if pb_match is None and pricebooks:
            pb_match = pricebooks[0]

        if pb_match is not None:
            # Common shape: direct fields bid/ask/bid_size/ask_size
            bid_obj = (
                _get(pb_match, "bid", None)
                or _get(pb_match, "best_bid", None)
                or _get(pb_match, "bestBid", None)
            )
            ask_obj = (
                _get(pb_match, "ask", None)
                or _get(pb_match, "best_ask", None)
                or _get(pb_match, "bestAsk", None)
            )

            bid = _level_price(bid_obj)
            ask = _level_price(ask_obj)

            bid_sz = _level_size(
                _get(pb_match, "bid_size", None)
                or _get(pb_match, "bidSize", None)
                or _get(pb_match, "best_bid_size", None)
                or _get(pb_match, "bestBidSize", None)
            )
            ask_sz = _level_size(
                _get(pb_match, "ask_size", None)
                or _get(pb_match, "askSize", None)
                or _get(pb_match, "best_ask_size", None)
                or _get(pb_match, "bestAskSize", None)
            )

            # Alternate shape: best_bid / best_ask objects
            best_bid = _get(pb_match, "best_bid", None) or _get(pb_match, "bestBid", None)
            best_ask = _get(pb_match, "best_ask", None) or _get(pb_match, "bestAsk", None)
            if (bid <= 0 or ask <= 0) and (best_bid is not None and best_ask is not None):
                bid = _level_price(best_bid)
                ask = _level_price(best_ask)
                if bid_sz <= 0:
                    bid_sz = _level_size(best_bid)
                if ask_sz <= 0:
                    ask_sz = _level_size(best_ask)

            # Alternate shape: bids/asks arrays
            if bid <= 0 or ask <= 0:
                bids = _get(pb_match, "bids", None)
                asks = _get(pb_match, "asks", None)
                if not isinstance(bids, list) or not isinstance(asks, list):
                    d = _as_dict(pb_match) or {}
                    bids = d.get("bids")
                    asks = d.get("asks")
                if isinstance(bids, list) and isinstance(asks, list) and bids and asks:
                    b0 = bids[0]
                    a0 = asks[0]
                    bid = _level_price(b0)
                    ask = _level_price(a0)
                    if bid_sz <= 0:
                        bid_sz = _level_size(b0)
                    if ask_sz <= 0:
                        ask_sz = _level_size(a0)

    # If bid/ask are missing OR sizes are missing, fallback to product book.
    need_book = (bid <= 0 or ask <= 0) or (bid_sz <= 0 and ask_sz <= 0)
    if need_book:
        book = _product_book(client, pid, level=10) or _product_book(client, pid, level=2) or _product_book(client, pid, level=1)
        if book is not None:
            b2, a2, b2_sz, a2_sz = _best_from_book(book)
            if bid <= 0:
                bid = b2
            if ask <= 0:
                ask = a2
            if bid_sz <= 0:
                bid_sz = b2_sz
            if ask_sz <= 0:
                ask_sz = a2_sz

    if bid <= 0 or ask <= 0:
        if last_err is not None and resp is None:
            raise last_err
        return D("0"), D("0"), D("0"), D("0")

    return bid, ask, bid_sz, ask_sz


def _sum_sizes(levels: Sequence[Any]) -> D:
    total = D("0")
    for lvl in levels:
        try:
            total += _level_size(lvl)
        except Exception:
            continue
    return total


def _book_pressure(client: Any, pid: str, levels: int = 10) -> Optional[float]:
    """
    Compute bid pressure in [0,1]:
      sum(bid_sizes)/(sum(bid_sizes)+sum(ask_sizes)) from level2 book.
    """
    book = _product_book(client, pid, level=max(levels, 10))
    if not book:
        return None

    book = _unwrap_pricebook(book)
    bids = _get(book, "bids", None)
    asks = _get(book, "asks", None)

    if not isinstance(bids, list):
        bd = _as_dict(book) or {}
        bids = bd.get("bids")
    if not isinstance(asks, list):
        bd = _as_dict(book) or {}
        asks = bd.get("asks")

    if not isinstance(bids, list) or not isinstance(asks, list):
        return None

    bid_qty = _sum_sizes(bids[:levels])
    ask_qty = _sum_sizes(asks[:levels])
    tot = bid_qty + ask_qty
    if tot <= 0:
        return None
    return float(bid_qty / tot)


def _clamp01(x: float) -> float:
    if x < 0.0:
        return 0.0
    if x > 1.0:
        return 1.0
    return x


# ---------------------------
# Scoring
# ---------------------------

def _score_one(client: Any, pid: str, settings: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    bid, ask, bid_sz, ask_sz = _best_bid_ask(client, pid)
    if bid <= 0 or ask <= 0:
        return None

    mid = (bid + ask) / D("2")
    if mid <= 0:
        return None

    spr_bps = float(((ask - bid) / mid) * D("10000"))

    tob_usd = float((bid * bid_sz) + (ask * ask_sz))

    levels = int(settings.get("PRESSURE_LEVELS", 10))
    press = _book_pressure(client, pid, levels=levels)

    if press is None:
        tot = bid_sz + ask_sz
        press = float(bid_sz / tot) if tot > 0 else 0.5

    spread_penalty_bps = float(settings.get("SPREAD_PENALTY_BPS", 0.0))
    score = float(press)
    if spread_penalty_bps > 0:
        score = score - (spr_bps / max(spread_penalty_bps, 1.0)) * 0.05
    score = _clamp01(score)

    return {
        "pid": pid,
        "product_id": pid,
        "score": score,
        "signal": score,
        "press": float(press),
        "bid": float(bid),
        "ask": float(ask),
        "mid": float(mid),
        "bid_sz": float(bid_sz),
        "ask_sz": float(ask_sz),
        "spr_bps": float(spr_bps),
        "tob_usd": float(tob_usd),
        "topbook_usd": float(tob_usd),
    }


def _normalize_candidates(candidates: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for row in candidates:
        if not isinstance(row, dict):
            continue
        pid = (row.get("pid") or row.get("product_id") or row.get("productId") or "").upper()
        if not pid:
            continue
        out.append({"pid": pid, **row, "product_id": pid})
    return out


def get_action_scores(*args: Any, **kwargs: Any) -> List[Dict[str, Any]]:
    """
    Entry point used by run_manager.

    Returns list[dict] including:
      pid/product_id, score, press, bid/ask/mid/spr_bps/tob_usd (best-effort)

    Tolerates older run_manager call shapes.
    """
    client, settings, universe, candidates = _coerce_inputs(args, dict(kwargs))

    # Candidate-enrichment path
    if candidates is not None:
        base = _normalize_candidates(candidates)

        if client is None:
            for r in base:
                if "score" not in r:
                    r["score"] = float(r.get("signal", r.get("press", 0.0)) or 0.0)
                r["score"] = _clamp01(float(r["score"]))
                r["signal"] = r["score"]
            base.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
            return base

        enriched: List[Dict[str, Any]] = []
        for r in base:
            pid = r["pid"]
            try:
                m = _score_one(client, pid, settings)
            except Exception:
                m = None

            if m:
                upstream_score = r.get("score", None)
                out = dict(r)
                out.update(m)
                # If upstream gave an explicit score, preserve it
                if upstream_score is not None:
                    try:
                        s = float(upstream_score)
                        out["score"] = _clamp01(s)
                        out["signal"] = out["score"]
                    except Exception:
                        pass
                enriched.append(out)
            else:
                # Keep row; run_manager may reject if no mid
                if "score" not in r:
                    r["score"] = float(r.get("signal", r.get("press", 0.0)) or 0.0)
                r["score"] = _clamp01(float(r["score"]))
                r["signal"] = r["score"]
                enriched.append(r)

        enriched.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
        return enriched

    # Universe-scoring path
    if client is None:
        return []

    results: List[Dict[str, Any]] = []
    for pid in universe:
        try:
            row = _score_one(client, pid, settings)
            if row:
                results.append(row)
        except Exception:
            continue

    results.sort(key=lambda r: float(r.get("score", 0.0)), reverse=True)
    return results
