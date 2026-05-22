from __future__ import annotations

"""
managers/tools/pnl_overlay.py

Read-only overlay for live positions:
- Prints per-held-asset entry VWAP from fills, current mid from best_bid_ask, and pnl%.
- Throttled by PNL_OVERLAY_SEC (default 30s).
- Suppresses Coinbase client logging in this process.
- Blacklists invalid product_ids (e.g., FX-USD) after first failure and hides them.

Usage:
  python -X utf8 -u managers/tools/pnl_overlay.py
"""

import os
import sys
import time
import logging
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List

# Silence all logging in this overlay process (prevents RESTClient error spam)
logging.disable(logging.CRITICAL)

# Ensure project root is importable when run directly
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from managers.auth_manager.auth_jwt import get_client  # noqa: E402

D = Decimal
_INVALID_PIDS: Dict[str, float] = {}  # pid -> first_seen_ts


def _D(x: Any) -> D:
    if isinstance(x, D):
        return x
    try:
        return D(str(x))
    except (InvalidOperation, Exception):
        return D("0")


def _get(obj: Any, name: str, default: Any = None) -> Any:
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


def _now() -> float:
    try:
        return time.time()
    except Exception:
        return 0.0


def _accounts(client, pfid: str) -> Dict[str, D]:
    """Return base -> total_base (available+hold), skipping USD-like currencies."""
    out: Dict[str, D] = {}
    try:
        resp = client.get_accounts(limit=250)
    except Exception:
        return out
    accs = resp.get("accounts") if isinstance(resp, dict) else getattr(resp, "accounts", [])
    accs = accs or []
    for a in accs:
        a_pfid = str(_get(a, "retail_portfolio_id", "") or _get(a, "portfolio_uuid", "") or "")
        if pfid and a_pfid and a_pfid != pfid:
            continue
        cur = str(_get(a, "currency", "") or "").upper()
        if not cur or cur in ("USD", "USDC", "USDT"):
            continue
        ab = _get(a, "available_balance", {})
        hv = _get(a, "hold", {})
        av = _D(_get(ab, "value", 0) if isinstance(ab, dict) else _get(ab, "value", 0))
        hd = _D(_get(hv, "value", 0) if isinstance(hv, dict) else _get(hv, "value", 0))
        tot = av + hd
        if tot > 0:
            out[cur] = tot
    return out


def _entry_vwap(client, pid: str) -> D:
    """VWAP of BUY fills (best effort)."""
    try:
        resp = client.get_fills(product_id=pid, limit=200)
    except Exception:
        return D("0")
    fills = _get(resp, "fills", resp) or []
    if not isinstance(fills, list):
        fills = []
    tot_sz = D("0")
    tot_notional = D("0")
    for f in fills:
        side = str(_get(f, "side", "") or _get(f, "direction", "")).upper()
        if side not in ("BUY", "B"):
            continue
        sz = _D(_get(f, "size", _get(f, "base_size", _get(f, "base_quantity", "0"))))
        px = _D(_get(f, "price", _get(f, "average_price", "0")))
        if sz <= 0 or px <= 0:
            continue
        tot_sz += sz
        tot_notional += sz * px
    if tot_sz <= 0 or tot_notional <= 0:
        return D("0")
    return tot_notional / tot_sz


def _mid_one(client, pid: str) -> D:
    """Best-effort mid for one product_id; marks invalid on error."""
    if pid in _INVALID_PIDS:
        return D("0")
    try:
        resp = client.get_best_bid_ask(product_ids=[pid])
    except Exception:
        _INVALID_PIDS.setdefault(pid, _now())
        return D("0")

    pbs = resp.get("pricebooks") if isinstance(resp, dict) else getattr(resp, "pricebooks", None)
    if not pbs:
        pbs = resp.get("data") if isinstance(resp, dict) else getattr(resp, "data", None)
    if not pbs or not isinstance(pbs, list):
        _INVALID_PIDS.setdefault(pid, _now())
        return D("0")

    pb = pbs[0]
    bids = _get(pb, "bids", []) or []
    asks = _get(pb, "asks", []) or []
    try:
        b0 = bids[0] if bids else None
        a0 = asks[0] if asks else None
        if not b0 or not a0:
            return D("0")
        bid = _D(_get(b0, "price"))
        ask = _D(_get(a0, "price"))
        if bid > 0 and ask > 0:
            return (bid + ask) / D("2")
    except Exception:
        pass
    return D("0")


def main() -> None:
    pfid = os.environ.get("PFID", "").strip()
    sec = float(os.environ.get("PNL_OVERLAY_SEC", "30"))
    client = get_client()
    print("PNL overlay (read-only). Ctrl+C to stop.")

    while True:
        pos = _accounts(client, pfid)

        print("-" * 88)
        print(time.strftime("%Y-%m-%d %H:%M:%S"), "positions:", len(pos), "invalid_pids:", len(_INVALID_PIDS))

        for base, amt in sorted(pos.items()):
            pid = f"{base}-USD"
            if pid in _INVALID_PIDS:
                continue  # hide invalid markets entirely

            mid = _mid_one(client, pid)
            if mid <= 0:
                # if it failed, it may have just been blacklisted
                if pid in _INVALID_PIDS:
                    continue

            entry = _entry_vwap(client, pid)
            pnl_pct = ((mid - entry) / entry * D("100")) if (entry > 0 and mid > 0) else D("0")

            mid_s = str(mid) if mid > 0 else "NA"
            entry_s = str(entry) if entry > 0 else "NA"
            pnl_s = f"{pnl_pct:.2f}" if (entry > 0 and mid > 0) else "NA"

            print(f"{pid:<12} amt={str(amt):<16} mid={mid_s:<14} entry={entry_s:<14} pnl%={pnl_s}")

        time.sleep(sec)


if __name__ == "__main__":
    main()
