# managers/orders_manager/limit_maker.py
from __future__ import annotations

import os, json, uuid, time
from decimal import Decimal as D, ROUND_DOWN
from typing import Any, Dict, Optional, Tuple, List

# ---------------------------------------------------------------------
# Public API
#   place_order(product_id, side, size, size_type, *, limit_price=None, post_only=True, settings={})
#   cancel_open_orders(product_id)
#   sell_all_positions(...)
#
# Behavior:
# - place_order: LIMIT only. post_only=True default. No TIF override.
# - size_type in {"BASE","QUOTE"}; QUOTE converts to BASE using computed price.
# - If limit_price is None, compute a maker price:
#     BUY:  min(best_bid - 1t, best_ask - 6t)
#     SELL: max(best_ask, best_bid + 1t)
#   All quantized to price_increment, ROUND_DOWN.
# - Sells are NOT reduce_only (set reduce_only=False).
# - Error echo path: logs\orders_last_error.json
# - Optional hook (safe if missing):
#       attach_bracket_on_fill(c, settings, product_id, avg_fill_price, base_filled, meta)
#
# - sell_all_positions:
#     * Cancels open orders first (optional), then sells ALL non-USD balances for the PFID.
#     * Uses Coinbase Advanced Trade RESTClient market_order_sell with client_order_id.
#     * Reads balances via get_accounts(portfolio_uuid=PFID) using available_balance['value'] and hold['value'].
#     * Never includes portfolio_uuid in order bodies.
# ---------------------------------------------------------------------

_DEC0 = D("0")
_DEF_PI = D("0.01")
_DEF_BI = D("0.000001")

_CASH = {"USD"}
_CONVERT_STABLES = {"USDC", "USDT"}  # optional: can be converted to USD via <STABLE>-USD if enabled


def _to_dec(x: Any) -> D:
    try:
        return x if isinstance(x, D) else D(str(x))
    except Exception:
        return _DEC0


def _q(val: D, inc: D) -> str:
    try:
        return str(val.quantize(inc, rounding=ROUND_DOWN))
    except Exception:
        return "0"


def _plain(x: Any) -> Any:
    try:
        return json.loads(json.dumps(x, default=lambda o: getattr(o, "__dict__", {})))
    except Exception:
        return x


def _log_error(stage: str, echo: Dict[str, Any], err: str) -> None:
    try:
        os.makedirs("logs", exist_ok=True)
        with open(os.path.join("logs", "orders_last_error.json"), "w", encoding="utf-8") as f:
            json.dump({"ts": time.time(), "stage": stage, "echo": echo, "error": err}, f)
    except Exception:
        pass


def _get_client():
    try:
        from managers.auth_manager.auth_jwt import get_client
    except ImportError:
        from auth_jwt import get_client
    return get_client()


# ---------- market data helpers ----------

def _get_increments(c, pid: str) -> Tuple[D, D]:
    """Return (price_increment, base_increment)."""
    p = _plain(c.get_product(product_id=pid))
    pi = _to_dec(p.get("price_increment") or _DEF_PI)
    bi = _to_dec(p.get("base_increment") or _DEF_BI)
    if pi <= _DEC0:
        pi = _DEF_PI
    if bi <= _DEC0:
        bi = _DEF_BI
    return pi, bi


def _best_bid_ask(c, pid: str) -> Tuple[D, D]:
    """Return (bid, ask) as Decimals; raises on empty book."""
    bk = _plain(c.get_best_bid_ask(product_ids=[pid]))
    pb = (bk.get("pricebooks") or [{}])[0]
    bids = pb.get("bids") or []
    asks = pb.get("asks") or []
    bid = _to_dec((bids[0] or {}).get("price")) if bids else _DEC0
    ask = _to_dec((asks[0] or {}).get("price")) if asks else _DEC0
    if bid <= _DEC0 or ask <= _DEC0:
        raise RuntimeError("empty_book")
    return bid, ask


def _maker_px(c, pid: str, side: str) -> D:
    """
    BUY: maker under bid and far under ask -> min(bid-1t, ask-6t)
    SELL: non-crossing ask -> max(ask, bid+1t)
    """
    pi, _ = _get_increments(c, pid)
    bid, ask = _best_bid_ask(c, pid)
    if side == "BUY":
        raw = min(bid - pi, ask - (pi * 6))
    else:
        raw = max(ask, bid + pi)
    if raw <= _DEC0:
        raw = pi
    return raw.quantize(pi, rounding=ROUND_DOWN)


def _to_base(size: str, size_type: str, px: D, base_inc: D) -> str:
    s = _to_dec(size)
    if size_type == "BASE":
        return _q(s, base_inc)
    if px <= _DEC0:
        return "0"
    return _q((s / px), base_inc)


# ---------- public functions ----------

def place_order(
    product_id: str,
    side: str,
    size: str,
    size_type: str,
    *,
    limit_price: Optional[str] = None,
    post_only: bool = True,
    settings: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Maker-only LIMIT. QUOTE size converts to BASE using computed price when needed."""
    settings = settings or {}
    pid = str(product_id or "").upper()
    side = side.upper()
    size_type = size_type.upper()

    echo = {
        "product_id": pid,
        "side": side,
        "size": str(size),
        "size_type": size_type,
        "client_order_id": str(uuid.uuid4()),
        "limit_price": limit_price,
        "post_only": bool(post_only),
    }
    print(json.dumps(echo))

    if side not in ("BUY", "SELL") or size_type not in ("BASE", "QUOTE"):
        _log_error("place_order", echo, "invalid_args")
        return {"ok": False, "error": "invalid_args"}

    try:
        c = _get_client()
        pi, bi = _get_increments(c, pid)

        # price
        px = _to_dec(limit_price) if limit_price not in (None, "") else _maker_px(c, pid, side)

        # base size
        base_sz = _to_base(size, size_type, px, bi)
        if _to_dec(base_sz) <= _DEC0:
            raise RuntimeError("base_size_zero")

        # flags
        reduce_only = False  # allow opening maker sells

        # DRY path
        if settings.get("DRY", False):
            print({"stage": "orders_place", "event": "dry_run", "cid": echo["client_order_id"]})
            return {"ok": True, "response": {"dry": True}}

        # build request
        order_cfg = {
            "limit_limit_gtc": {
                "base_size": base_sz,
                "limit_price": _q(px, pi),
                "post_only": bool(post_only),
                "rfq_disabled": False,
                "reduce_only": reduce_only,
            }
        }

        resp = c.create_order(
            client_order_id=echo["client_order_id"],
            product_id=pid,
            side=side,
            order_configuration=order_cfg,
        )

        print({"stage": "orders_place", "event": "venue_response", "product_id": pid, "side": side, "cid": echo["client_order_id"]})

        # optional bracket hook
        try:
            from managers.orders_manager.attach_bracket import attach_bracket_on_fill  # type: ignore

            try:
                attach_bracket_on_fill(
                    c,
                    settings,
                    pid,
                    avg_fill_price=_q(px, pi),
                    base_filled=base_sz,
                    meta={"link_cid": echo["client_order_id"]},
                )
            except Exception:
                pass
        except Exception:
            pass

        return {"ok": True, "response": _plain(resp)}

    except Exception as e:
        msg = str(e)
        known = ("INVALID_LIMIT_PRICE_POST_ONLY", "INSUFFICIENT_FUND", "PERMISSION_DENIED")
        err_out = next((k for k in known if k in msg), msg or "unknown")
        print({"stage": "orders_place", "event": "order_error", "pid": pid, "err": err_out})
        _log_error("place_order", echo, err_out)
        return {"ok": False, "error": err_out}



def cancel_open_orders(product_id: str) -> Dict[str, Any]:
    """Cancel OPEN/PENDING/ACTIVE for a product."""
    pid = str(product_id or "").upper()
    c = _get_client()
    o = c.list_orders(product_id=pid, limit=200)
    ids = [
        getattr(x, "order_id", "")
        for x in getattr(o, "orders", [])
        if getattr(x, "status", "") in ("OPEN", "PENDING", "ACTIVE")
    ]
    if not ids:
        return {"ok": True, "result": "none_open"}
    r = _plain(c.cancel_orders(order_ids=ids))
    return {"ok": True, "canceled": ids, "resp": r}


# ---------- liquidation helpers ----------

def _resolve_pfid(pfid: Optional[str], settings: Optional[Dict[str, Any]]) -> str:
    env_p = (os.environ.get("PFID") or "").strip()
    if env_p:
        return env_p
    if pfid:
        return str(pfid).strip()
    try:
        if settings and settings.get("PFID"):
            return str(settings.get("PFID")).strip()
    except Exception:
        pass
    return ""


def _acct_val(a: Any, key: str) -> D:
    try:
        v = a.get(key) if isinstance(a, dict) else getattr(a, key, None)
    except Exception:
        v = None
    if isinstance(v, dict):
        try:
            v = v.get("value")
        except Exception:
            v = None
    if v is None:
        return _DEC0
    return _to_dec(v)


def _get_accounts_balances(c, pfid: str) -> List[Dict[str, Any]]:
    """Return list of {currency, available, hold} using get_accounts(portfolio_uuid=PFID) pagination."""
    out: List[Dict[str, Any]] = []
    cursor = None
    for _ in range(50):
        try:
            if pfid:
                resp = c.get_accounts(portfolio_uuid=pfid, cursor=cursor) if cursor else c.get_accounts(portfolio_uuid=pfid)
            else:
                resp = c.get_accounts(cursor=cursor) if cursor else c.get_accounts()
        except TypeError:
            if pfid:
                resp = c.get_accounts(portfolio_uuid=pfid, starting_after=cursor) if cursor else c.get_accounts(portfolio_uuid=pfid)
            else:
                resp = c.get_accounts(starting_after=cursor) if cursor else c.get_accounts()

        obj = resp if isinstance(resp, dict) else _plain(resp)
        accounts = obj.get("accounts") if isinstance(obj, dict) else (getattr(resp, "accounts", []) if resp is not None else [])
        accounts = accounts or []
        for a in accounts:
            if not a:
                continue
            try:
                cur = str((a.get("currency") if isinstance(a, dict) else getattr(a, "currency", "")) or "").upper()
                if not cur:
                    continue
                ab = _acct_val(a, "available_balance")
                hd = _acct_val(a, "hold")
                out.append({"currency": cur, "available": ab, "hold": hd})
            except Exception:
                continue

        has_next = bool(obj.get("has_next")) if isinstance(obj, dict) else bool(getattr(resp, "has_next", False))
        cursor = (obj.get("cursor") if isinstance(obj, dict) else getattr(resp, "cursor", None)) if has_next else None
        if not has_next or not cursor:
            break
    return out


def _list_open_order_ids(c) -> List[str]:
    ids: List[str] = []
    cursor = None
    for _ in range(50):
        try:
            resp = c.list_orders(cursor=cursor, limit=200) if cursor else c.list_orders(limit=200)
        except TypeError:
            resp = c.list_orders(starting_after=cursor, limit=200) if cursor else c.list_orders(limit=200)

        obj = resp if isinstance(resp, dict) else _plain(resp)
        orders = obj.get("orders") if isinstance(obj, dict) else getattr(resp, "orders", [])
        orders = orders or []

        for o in orders:
            try:
                st = (o.get("status") if isinstance(o, dict) else getattr(o, "status", "")) or ""
                if str(st).upper() not in ("OPEN", "PENDING", "ACTIVE"):
                    continue
                oid = (o.get("order_id") if isinstance(o, dict) else getattr(o, "order_id", "")) or ""
                if oid:
                    ids.append(str(oid))
            except Exception:
                continue

        has_next = bool(obj.get("has_next")) if isinstance(obj, dict) else bool(getattr(resp, "has_next", False))
        cursor = (obj.get("cursor") if isinstance(obj, dict) else getattr(resp, "cursor", None)) if has_next else None
        if not has_next or not cursor:
            break

    # de-dupe
    seen = set()
    out = []
    for x in ids:
        if x and x not in seen:
            seen.add(x)
            out.append(x)
    return out


def _cancel_orders_chunked(c, ids: List[str]) -> Dict[str, Any]:
    if not ids:
        return {"ok": True, "canceled": 0}
    canceled = 0
    last_resp = None
    for i in range(0, len(ids), 100):
        chunk = ids[i : i + 100]
        try:
            last_resp = _plain(c.cancel_orders(order_ids=chunk))
            canceled += len(chunk)
        except Exception:
            pass
    return {"ok": True, "canceled": canceled, "resp": last_resp}


def _market_sell(c, pid: str, base_size: str, client_order_id: str) -> Any:
    """Call market_order_sell with best-effort arg compatibility."""
    if not hasattr(c, "market_order_sell"):
        raise RuntimeError("market_order_sell_unavailable")
    fn = getattr(c, "market_order_sell")

    try:
        return fn(client_order_id=client_order_id, product_id=pid, base_size=base_size)
    except TypeError:
        pass
    try:
        return fn(client_order_id=client_order_id, product_id=pid, size=base_size)
    except TypeError:
        pass

    try:
        return fn(client_order_id, pid, base_size)
    except Exception:
        return fn(client_order_id, pid, size=base_size)


# ---------- Sell All (complete liquidation) ----------

def sell_all_positions(
    client: Any = None,
    settings: Optional[Dict[str, Any]] = None,
    pfid: Optional[str] = None,
    *,
    quote: str = "USD",
    cancel_orders_first: bool = True,
    sell_convert_stables: bool = True,
    min_notional_usd: float = 1.0,
    verbose: bool = True,
) -> Dict[str, Any]:
    """Sell ALL positions (non-USD) for the PFID.

    - Cancels open orders first (optional) so holds can be freed.
    - Uses get_accounts(portfolio_uuid=PFID) and sells available + hold (best-effort).
    - Places MARKET sells using market_order_sell with a unique client_order_id per product.
    - Never includes portfolio_uuid in order bodies.

    Returns:
      {
        ok: bool,
        canceled_orders: int,
        sold: [ {pid, base, size, cid} ... ],
        skipped: [ {base, reason} ... ],
        errors: [ {pid, error} ... ],
      }
    """
    settings = settings or {}
    c = client or _get_client()
    pf = _resolve_pfid(pfid, settings)

    sold: List[Dict[str, Any]] = []
    skipped: List[Dict[str, Any]] = []
    errors: List[Dict[str, Any]] = []

    # 1) cancel open orders
    canceled_n = 0
    if cancel_orders_first and not settings.get("DRY", False):
        try:
            ids = _list_open_order_ids(c)
            r = _cancel_orders_chunked(c, ids)
            canceled_n = int(r.get("canceled", 0) or 0)
            if verbose:
                print({"stage": "sell_all", "event": "cancel_orders", "count": canceled_n})
        except Exception as e:
            errors.append({"pid": None, "error": f"cancel_orders_failed:{e}"})

    # brief settle pause for holds to release
    if cancel_orders_first and not settings.get("DRY", False):
        try:
            time.sleep(1.0)
        except Exception:
            pass

    # 2) read balances
    try:
        accts = _get_accounts_balances(c, pf)
    except Exception as e:
        return {"ok": False, "error": f"get_accounts_failed:{e}", "sold": [], "skipped": [], "errors": errors}

    # reduce to per-currency totals
    sums: Dict[str, Dict[str, D]] = {}
    for a in accts:
        cur = str(a.get("currency") or "").upper()
        if not cur:
            continue
        b = sums.setdefault(cur, {"available": _DEC0, "hold": _DEC0})
        b["available"] += _to_dec(a.get("available", _DEC0))
        b["hold"] += _to_dec(a.get("hold", _DEC0))

    # 3) build sell list
    quote = str(quote or "USD").upper()
    items = []
    for base, vals in sums.items():
        if base in _CASH:
            continue
        if base in _CONVERT_STABLES and not sell_convert_stables:
            skipped.append({"base": base, "reason": "stable_skip"})
            continue
        pid = f"{base}-{quote}"
        total = vals.get("available", _DEC0) + vals.get("hold", _DEC0)
        if total <= _DEC0:
            continue
        items.append((base, pid, total))

    if not items:
        return {"ok": True, "canceled_orders": canceled_n, "sold": [], "skipped": skipped, "errors": errors, "note": "no_positions"}

    # 4) sell with progress
    n = len(items)
    for idx, (base, pid, total) in enumerate(items, start=1):
        try:
            # ensure product exists + increments
            try:
                _, bi = _get_increments(c, pid)
            except Exception:
                skipped.append({"base": base, "pid": pid, "reason": "no_product"})
                continue

            size = _to_dec(_q(total, bi))
            if size <= _DEC0:
                skipped.append({"base": base, "pid": pid, "reason": "size_zero"})
                continue

            # notional estimate (best effort)
            try:
                bid, _ask = _best_bid_ask(c, pid)
                notional = float(bid * size)
            except Exception:
                notional = float(min_notional_usd)

            if notional < float(min_notional_usd):
                skipped.append({"base": base, "pid": pid, "reason": "dust", "notional": notional, "size": str(size)})
                continue

            cid = str(uuid.uuid4())
            pct = int(round((idx / max(1, n)) * 100))
            if verbose:
                print({"stage": "sell_all", "event": "sell", "i": idx, "n": n, "pct": pct, "pid": pid, "size": str(size), "cid": cid})

            if settings.get("DRY", False):
                sold.append({"pid": pid, "base": base, "size": str(size), "cid": cid, "dry": True})
                continue

            resp = _market_sell(c, pid, base_size=_q(size, bi), client_order_id=cid)
            sold.append({"pid": pid, "base": base, "size": str(size), "cid": cid, "resp": _plain(resp)})
        except Exception as e:
            msg = str(e) or "unknown"
            errors.append({"pid": pid, "base": base, "error": msg})
            _log_error("sell_all_positions", {"pid": pid, "base": base}, msg)
            continue

    ok = (len(errors) == 0)
    return {"ok": ok, "canceled_orders": canceled_n, "sold": sold, "skipped": skipped, "errors": errors}
