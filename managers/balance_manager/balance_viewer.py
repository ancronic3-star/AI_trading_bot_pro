from __future__ import annotations

"""
managers/balance_manager/balance_viewer.py

Standalone balances viewer.

MM26 repair:
- Read-only.
- Uses the active PFID (env first, then run_settings.json) with get_accounts(portfolio_uuid=PFID).
- Reads available_balance['value'] and hold['value'].
- Prints non-zero TOTAL rows from the active portfolio only.
"""

import os
import sys
import json
from decimal import Decimal, InvalidOperation
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterable


# ---------- path / imports ----------

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from managers.auth_manager import get_client  # type: ignore
except Exception:
    try:
        import auth_manager  # type: ignore
        get_client = auth_manager.get_client  # type: ignore[attr-defined]
    except Exception as exc:  # pragma: no cover
        raise RuntimeError("Unable to import get_client from auth_manager") from exc


# ---------- helpers (local, read-only) ----------

D = Decimal
_RUN_SETTINGS = Path(_PROJECT_ROOT) / "run_settings.json"


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


def _to_plain(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    if x is None:
        return {}
    for meth in ("model_dump", "dict", "to_dict"):
        if hasattr(x, meth):
            try:
                d = getattr(x, meth)()
                if isinstance(d, dict):
                    return d
            except Exception:
                pass
    try:
        d = getattr(x, "__dict__", None)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return {}


def _load_settings() -> Dict[str, Any]:
    try:
        with _RUN_SETTINGS.open("r", encoding="utf-8") as f:
            obj = json.load(f)
        return obj if isinstance(obj, dict) else {}
    except Exception:
        return {}


def _resolve_pfid() -> str:
    settings = _load_settings()
    return str(os.environ.get("PFID") or settings.get("PFID") or "").strip()


def _iter_accounts(client: Any, pfid: str) -> Iterable[Dict[str, Any]]:
    fn = getattr(client, "get_accounts", None) or getattr(client, "list_accounts", None)
    if not callable(fn):
        return []
    cursor = None
    for _ in range(30):
        kwargs: Dict[str, Any] = {"limit": 250}
        if cursor:
            kwargs["cursor"] = cursor
        if pfid:
            kwargs["portfolio_uuid"] = pfid
        try:
            raw = fn(**kwargs)
        except TypeError:
            try:
                raw = fn(portfolio_uuid=pfid) if pfid else fn()
            except Exception:
                break
        except Exception as e:
            print(f"[balance_viewer] Error fetching accounts: {e}")
            break

        obj = _to_plain(raw)
        arr = obj.get("accounts") if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
        arr = arr or []
        for a in arr:
            d = a if isinstance(a, dict) else _to_plain(a)
            a_pfid = str(d.get("portfolio_uuid") or d.get("retail_portfolio_id") or "")
            if pfid and a_pfid and a_pfid != pfid:
                continue
            yield d

        if not (isinstance(obj, dict) and obj.get("has_next")):
            break
        cursor = obj.get("cursor") or None
        if not cursor:
            break


def _accounts_by_currency(client: Any, pfid: str) -> Dict[str, Dict[str, D]]:
    """
    Returns mapping currency -> {"available": D, "hold": D, "total": D}.

    Read-only: uses client.get_accounts(portfolio_uuid=PFID).
    """
    out: Dict[str, Dict[str, D]] = {}
    if client is None:
        return out

    for a in _iter_accounts(client, pfid):
        cur = _get(a, "currency") or _get(a, "asset")
        if not isinstance(cur, str) or not cur:
            continue
        avail = _get(_get(a, "available_balance", {}), "value", 0)
        hold = _get(_get(a, "hold", {}), "value", 0)
        bal = _get(a, "balance", None)
        total = _get(bal, "value", None) if isinstance(bal, dict) else None
        out[cur.upper()] = {
            "available": _D(avail),
            "hold": _D(hold),
            "total": _D(total if total is not None else _D(avail) + _D(hold)),
        }
    return out


def _fmt_amount(x: D) -> str:
    try:
        if x == 0:
            return "0"
        ax = abs(x)
        if ax >= D("1"):
            s = f"{x:,.4f}"
        else:
            s = f"{x:.8f}"
        s = s.rstrip("0").rstrip(".")
        return s or "0"
    except Exception:
        return str(x)


def _compute_total_usd(accounts: Dict[str, Dict[str, D]]) -> D:
    total = D("0")
    for cur, row in accounts.items():
        if cur in ("USD", "USDC", "USDT"):
            total += row.get("total", D("0"))
    return total


# ---------- main display ----------


def main() -> None:
    print("=== BALANCES VIEWER ===")
    print()

    try:
        client = get_client()
    except Exception as e:
        print(f"Error: could not initialize Coinbase client: {e}")
        print("\nTip: close this window when done viewing balances.")
        return

    pfid = _resolve_pfid()
    accounts = _accounts_by_currency(client, pfid)
    if not accounts:
        print("No balances returned from client.get_accounts(portfolio_uuid=PFID).")
        print("\nTip: close this window when done viewing balances.")
        return

    non_zero: Dict[str, Dict[str, D]] = {
        cur: row
        for cur, row in accounts.items()
        if row.get("total", D("0")) != 0
    }

    if not non_zero:
        print("All balances are zero (no non-zero TOTAL rows).")
        print("\nTip: close this window when done viewing balances.")
        return

    sorted_items = sorted(non_zero.items(), key=lambda kv: kv[0])

    ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
    total_usd = _compute_total_usd(accounts)
    print(f"As of {ts} UTC   |   PFID: {pfid or '(not set)'}   |   Total USD (USD+USDC+USDT): {_fmt_amount(total_usd)}")
    print()

    print("CURRENCY    AVAILABLE        HOLD       TOTAL")
    print("---------------------------------------------")

    for cur, row in sorted_items:
        avail = _fmt_amount(row.get("available", D("0")))
        hold = _fmt_amount(row.get("hold", D("0")))
        total = _fmt_amount(row.get("total", D("0")))
        print(f"{cur:<8} {avail:>12} {hold:>12} {total:>12}")

    print("\nTip: close this window when done viewing balances.")


if __name__ == "__main__":
    main()
