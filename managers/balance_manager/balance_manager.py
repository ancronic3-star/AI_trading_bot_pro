import logging
import os, json
from decimal import Decimal as D, ROUND_DOWN
from typing import Any, Dict, Iterable, Tuple, Optional

# Logging setup
logging.basicConfig(level=logging.DEBUG)

_DEC0 = D("0")
_INC_FIAT = D("0.01")
_DEF_BASE_INC = D("0.000001")
_STABLES = {"USD", "USDC"}

# ---------- helpers ----------
def _sget(o: Any, k: str, d=None):
    try:
        return o.get(k, d) if isinstance(o, dict) else getattr(o, k, d)
    except Exception:
        return d

def _to_plain(x: Any) -> Any:
    try:
        return json.loads(json.dumps(x, default=lambda o: getattr(o, "__dict__", {})))
    except Exception:
        return x

def _to_dec(x: Any) -> D:
    if isinstance(x, D):
        return x
    try:
        return D(str(x))
    except Exception:
        return _DEC0

def _accounts_list(c) -> Iterable[Dict[str, Any]]:
    """Yield ALL accounts by following Coinbase cursor pagination."""
    fn = getattr(c, "get_accounts", None) or getattr(c, "list_accounts", None)
    cursor = None
    for _ in range(20):  # safety cap
        try:
            raw = fn(limit=250, cursor=cursor) if callable(fn) else []
        except Exception:
            raw = []
        obj = _to_plain(raw)
        arr = obj.get("accounts") if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
        arr = arr or []
        for a in arr:
            yield a if isinstance(a, dict) else _to_plain(a)
        if not (isinstance(obj, dict) and obj.get("has_next")):
            break
        cursor = obj.get("cursor") or None

def _avail_total(a: Dict[str, Any]) -> Tuple[D, D]:
    av = _sget(a, "available_balance")
    if isinstance(av, dict):
        av = _sget(av, "value")
    if av is None:
        av = _sget(a, "available")
    if av is None:
        av = _sget(a, "balance")
    tot = _sget(a, "balance")
    if isinstance(tot, dict):
        tot = _sget(tot, "value")
    avd = _to_dec(av); totd = _to_dec(tot or avd)
    if avd < _DEC0: avd = _DEC0
    if totd < _DEC0: totd = _DEC0
    return avd, totd

def _base_inc(c, base: str) -> D:
    b = str(base).upper()
    if b in _STABLES:
        return _INC_FIAT
    try:
        p = _to_plain(c.get_product(product_id=f"{b}-USD"))
        inc = _to_dec(_sget(p, "base_increment", _DEF_BASE_INC))
        return inc if inc > _DEC0 else _DEF_BASE_INC
    except Exception:
        return _DEF_BASE_INC

def _q(val: D, inc: D) -> str:
    try:
        return str(val.quantize(inc, rounding=ROUND_DOWN))
    except Exception:
        return "0"

def _ensure_client(client: Any):
    if client is not None:
        return client
    try:
        from managers.auth_manager.auth_jwt import get_client  # lazy import
    except ImportError:
        from auth_jwt import get_client
    return get_client()


def _resolve_args(client_or_pfid=None, pfid: Optional[str] = None):
    """Supports: get_balances(), get_balances(pfid), get_balances(client,pfid)."""
    if hasattr(client_or_pfid, "get_accounts"):
        c = client_or_pfid; p = pfid
    elif isinstance(client_or_pfid, str) and pfid in (None, ""):
        c = None; p = client_or_pfid
    else:
        c = None; p = pfid
    if p in ("", None):
        p = os.environ.get("PFID", "")
    return _ensure_client(c), (str(p) if p else "")

# ---------- public API ----------
def get_balances(client_or_pfid=None, pfid: Optional[str] = None, view: str = "menu") -> Dict[str, Any]:
    """
    Menu view:
      {
        "USD":  {"total": "<str>", "available": "<str>"},
        "USDC": {"total": "<str>", "available": "<str>"},
        "positions": { "<ASSET>": {"total": "<str>", "available": "<str>"} }
      }
    Compact view: {asset: "<available_str>"}
    """
    c, p = _resolve_args(client_or_pfid, pfid)
    sums: Dict[str, Dict[str, D]] = {}
    for a in _accounts_list(c):
        a_pfid = str(_sget(a, "retail_portfolio_id") or _sget(a, "portfolio_uuid") or "")
        if p and a_pfid and a_pfid != p:
            continue
        cur = str(_sget(a, "currency") or _sget(a, "asset") or "").upper()
        if not cur:
            continue
        av, tot = _avail_total(a)
        b = sums.setdefault(cur, {"available": _DEC0, "total": _DEC0})
        b["available"] += av
        b["total"] += tot

    if view == "compact":
        out: Dict[str, str] = {}
        for asset, vals in sums.items():
            inc = _base_inc(c, asset)
            out[asset] = _q(vals["available"], inc)
        return out

    usd = sums.get("USD", {"available": _DEC0, "total": _DEC0})
    usdc = sums.get("USDC", {"available": _DEC0, "total": _DEC0})
    positions: Dict[str, Dict[str, str]] = {}
    for asset, vals in sums.items():
        if asset in _STABLES:
            continue
        inc = _base_inc(c, asset)
        positions[asset] = {"total": _q(vals["total"], inc), "available": _q(vals["available"], inc)}
    return {
        "USD":  {"total": _q(usd["total"], _INC_FIAT),  "available": _q(usd["available"], _INC_FIAT)},
        "USDC": {"total": _q(usdc["total"], _INC_FIAT), "available": _q(usdc["available"], _INC_FIAT)},
        "positions": positions,
    }

def get_available_base(product_id: str, client_or_pfid=None, pfid: Optional[str] = None) -> str:
    pid = str(product_id or "").upper()
    base = pid.split("-", 1)[0] if "-" in pid else pid
    if not base:
        logging.debug(f"No base for product: {product_id}")
        return "0"
    c, p = _resolve_args(client_or_pfid, pfid)
    b = get_balances(c, p, view="compact")
    
    # Log the available base for the asset
    available_base = b.get(base, "0")
    logging.debug(f"Available base for {product_id}: {available_base}")
    
    inc = _base_inc(c, base)
    return _q(_to_dec(available_base), inc)
