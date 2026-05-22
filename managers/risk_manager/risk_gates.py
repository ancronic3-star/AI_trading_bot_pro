# managers/risk_manager/risk_gates.py
# Version: v0.4.1 (2025-10-02)
"""Per-tick risk gates with limit-only skip and auto cooldown.

Public API
    gate_tick(snapshot: dict, settings: dict) -> (ok: bool, reason: str)
    product_tradable(meta: dict) -> (bool, str)
    mark_cooldown(product_id: str, seconds: int = 900, reason: str = "limit_only", now_ts: float | None = None) -> float
    is_cooldown_active(product_id: str, now_ts: float | None = None) -> bool

Rules
- No HTTP, no filesystem I/O, no subprocess.
- Deterministic when caller provides now_ts in snapshot and mark_cooldown.

Settings keys (read from settings["risk"] if present, else from settings directly)
- MAX_SPREAD_PCT: float      # percent, e.g., 0.50 means 0.5%
- MIN_TOPBOOK_USD: float
- COOLDOWN_TICKS: int
- VOL_MAX: float (optional, percent)
- LIMIT_ONLY_COOLDOWN_SEC: int (optional, default 900)

Snapshot keys
- product_id: str | None
- best_bid: float
- best_ask: float
- bid_size: float
- ask_size: float
- ticks_since_last_trade: int | None      # optional; cooldown gate skipped if absent
- vol_pct: float | None                   # optional; fallbacks: sigma_pct, volatility_pct
- mid: float | None                       # optional; computed if absent
- topbook_usd: float | None               # optional; computed if absent
- now_ts: float | None                    # optional; used for cooldown expiry checks
- product_meta: dict | None               # optional; flags: limit_only, post_only, cancel_only, trading_disabled

Return
- (True, "ok") on allow
- (False, "spread" | "liquidity" | "cooldown" | "volatility") on block

Programmer errors (missing keys, bad types) raise ValueError or KeyError.
"""

from typing import Any, Dict, Tuple, Optional
import time as _time

__all__ = ["gate_tick", "product_tradable", "mark_cooldown", "is_cooldown_active"]

# In-memory cooldown registry: product_id -> expiry_ts
_COOLDOWN: Dict[str, float] = {}


def _risk_section(settings: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(settings, dict):
        raise ValueError("settings must be a dict")
    return settings.get("risk", settings)


def product_tradable(meta: Dict[str, Any]) -> Tuple[bool, str]:
    """Check product meta flags and return (ok, reason)."""
    if not isinstance(meta, dict):
        raise ValueError("meta must be a dict")
    flags = ("limit_only", "post_only", "cancel_only", "trading_disabled")
    for k in flags:
        if bool(meta.get(k, False)):
            return False, k
    return True, "ok"


def mark_cooldown(product_id: str, seconds: int = 900, reason: str = "limit_only", now_ts: Optional[float] = None) -> float:
    """Start a cooldown for product_id. Returns expiry timestamp."""
    if not isinstance(product_id, str) or not product_id:
        raise ValueError("product_id required")
    if seconds < 0:
        seconds = 0
    now = float(now_ts) if now_ts is not None else _time.time()
    exp = now + float(seconds)
    _COOLDOWN[product_id] = exp
    return exp


def is_cooldown_active(product_id: str, now_ts: Optional[float] = None) -> bool:
    """True if product_id is in cooldown and not expired. Cleans expired entries."""
    if product_id not in _COOLDOWN:
        return False
    now = float(now_ts) if now_ts is not None else _time.time()
    exp = _COOLDOWN.get(product_id, 0.0)
    if now >= exp:
        try:
            del _COOLDOWN[product_id]
        except KeyError:
            pass
        return False
    return True


def gate_tick(snapshot: Dict[str, Any], settings: Dict[str, Any]) -> Tuple[bool, str]:
    """Evaluate spread (percent), liquidity, optional volatility (percent), cooldown ticks, and limit-only cooldown."""
    if not isinstance(snapshot, dict):
        raise ValueError("snapshot must be a dict")

    risk = _risk_section(settings)
    try:
        max_spread_pct = float(risk["MAX_SPREAD_PCT"])
        min_topbook_usd = float(risk["MIN_TOPBOOK_USD"])
        cooldown_ticks = int(risk["COOLDOWN_TICKS"])
    except KeyError as e:
        raise KeyError(f"missing risk setting: {e.args[0]}")
    except Exception as e:
        raise ValueError(f"invalid risk setting types: {e}")

    vol_max = risk.get("VOL_MAX", None)
    if vol_max is not None:
        try:
            vol_max = float(vol_max)
        except Exception as e:
            raise ValueError(f"invalid VOL_MAX type: {e}")

    limonly_cooldown = risk.get("LIMIT_ONLY_COOLDOWN_SEC", 900)
    try:
        limonly_cooldown = int(limonly_cooldown)
    except Exception as e:
        raise ValueError(f"invalid LIMIT_ONLY_COOLDOWN_SEC: {e}")

    product_id = snapshot.get("product_id")
    now_ts = snapshot.get("now_ts", None)
    now_val = float(now_ts) if now_ts is not None else None

    # Auto cooldown check
    if isinstance(product_id, str) and product_id and is_cooldown_active(product_id, now_val):
        return False, "cooldown"

    # Meta-based skip and cooldown
    meta = snapshot.get("product_meta")
    if isinstance(meta, dict):
        ok_meta, reason_meta = product_tradable(meta)
        if not ok_meta:
            if isinstance(product_id, str) and product_id:
                mark_cooldown(product_id, seconds=limonly_cooldown, reason=reason_meta, now_ts=now_val)
            return False, "cooldown"

    # Required snapshot values
    try:
        bid = float(snapshot["best_bid"])
        ask = float(snapshot["best_ask"])
        bid_size = float(snapshot["bid_size"])
        ask_size = float(snapshot["ask_size"])
    except KeyError as e:
        raise KeyError(f"missing snapshot key: {e.args[0]}")
    except Exception as e:
        raise ValueError(f"invalid snapshot types: {e}")

    # Invalid book counts as a spread failure.
    if not (bid > 0.0 and ask > bid):
        return False, "spread"

    mid = snapshot.get("mid")
    if mid is None:
        mid = (bid + ask) / 2.0
    else:
        mid = float(mid)
    if mid <= 0.0:
        return False, "spread"

    # Spread percent
    spread_pct = (ask - bid) / mid * 100.0
    if spread_pct > max_spread_pct:
        return False, "spread"

    # Top-of-book liquidity
    topbook_usd = snapshot.get("topbook_usd")
    if topbook_usd is None:
        topbook_usd = min(bid_size * bid, ask_size * ask)
    else:
        topbook_usd = float(topbook_usd)
    if topbook_usd < min_topbook_usd:
        return False, "liquidity"

    # Optional volatility gate
    if vol_max is not None:
        vol = snapshot.get("vol_pct")
        if vol is None:
            vol = snapshot.get("sigma_pct")
            if vol is None:
                vol = snapshot.get("volatility_pct")
        if vol is not None:
            try:
                vol_val = float(vol)
            except Exception as e:
                raise ValueError(f"invalid volatility value: {e}")
            if vol_val > vol_max:
                return False, "volatility"

    # Cooldown in ticks
    t_since = snapshot.get("ticks_since_last_trade", None)
    if t_since is not None:
        try:
            t_since_int = int(t_since)
        except Exception as e:
            raise ValueError(f"invalid ticks_since_last_trade: {e}")
        if cooldown_ticks > 0 and t_since_int < cooldown_ticks:
            return False, "cooldown"

    return True, "ok"
