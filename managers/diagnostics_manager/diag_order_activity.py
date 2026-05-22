# managers/diagnostics_manager/diag_order_activity.py
# Diagnostics: pull recent order activity from Coinbase (Advanced Trade) and write JSONL + a readable summary.
#
# This script does NOT copy key files. It only reads COINBASE_KEY_FILE to authenticate for API calls.

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def _repo_root() -> Path:
    # <repo>/managers/diagnostics_manager/diag_order_activity.py -> parents: diagnostics_manager, managers, <repo>
    return Path(__file__).resolve().parents[2]


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _to_primitive(obj: Any) -> Any:
    """Best-effort conversion to JSON-serializable primitives."""
    if obj is None:
        return None
    if isinstance(obj, (str, int, float, bool)):
        return obj
    if isinstance(obj, dict):
        return {str(k): _to_primitive(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [_to_primitive(v) for v in obj]
    # SDK objects sometimes have to_dict()
    to_dict = getattr(obj, "to_dict", None)
    if callable(to_dict):
        try:
            return _to_primitive(to_dict())
        except Exception:
            pass
    # fall back to __dict__
    d = getattr(obj, "__dict__", None)
    if isinstance(d, dict):
        return {str(k): _to_primitive(v) for k, v in d.items() if not str(k).startswith("_")}
    return str(obj)


def _pick(d: Dict[str, Any], keys: Iterable[str]) -> Any:
    for k in keys:
        if k in d:
            return d.get(k)
    return None


def _parse_dt(v: Any) -> Optional[datetime]:
    if v is None:
        return None
    if isinstance(v, datetime):
        return v.astimezone(timezone.utc)
    if isinstance(v, (int, float)):
        try:
            return datetime.fromtimestamp(float(v), tz=timezone.utc)
        except Exception:
            return None
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return None
        # Common Coinbase formats: ISO8601 with Z or offset
        try:
            if s.endswith("Z"):
                s2 = s[:-1] + "+00:00"
                return datetime.fromisoformat(s2).astimezone(timezone.utc)
            return datetime.fromisoformat(s).astimezone(timezone.utc)
        except Exception:
            return None
    return None


def _extract_order_fields(o: Any) -> Dict[str, Any]:
    d = _to_primitive(o)
    if not isinstance(d, dict):
        return {"raw": d}

    created = _pick(d, ["created_time", "created_at", "createdTime", "time", "created"])
    updated = _pick(d, ["last_fill_time", "updated_time", "updated_at", "updatedTime", "update_time"])

    out = {
        "order_id": _pick(d, ["order_id", "orderId", "id"]),
        "client_order_id": _pick(d, ["client_order_id", "clientOrderId", "client_oid"]),
        "product_id": _pick(d, ["product_id", "productId", "product"]),
        "side": _pick(d, ["side", "order_side", "orderSide"]),
        "status": _pick(d, ["status", "order_status", "orderStatus"]),
        "created_time": created,
        "updated_time": updated,
        "price": _pick(d, ["price", "limit_price", "limitPrice"]),
        "size": _pick(d, ["size", "base_size", "baseSize", "quantity"]),
        "filled_size": _pick(d, ["filled_size", "filledSize", "filled_quantity", "filledQuantity"]),
        "average_filled_price": _pick(d, ["average_filled_price", "averageFilledPrice", "avg_filled_price"]),
    }

    # Keep full raw dict as well (useful when fields differ)
    out["_raw"] = d
    return out


def _list_orders(client: Any, order_status: str, product_id: Optional[str], limit: int) -> List[Any]:
    # Best effort: support varying SDK signatures
    try:
        return getattr(client.list_orders(order_status=[order_status], product_id=product_id, limit=limit), "orders", [])
    except TypeError:
        try:
            return getattr(client.list_orders(order_status=[order_status], product_id=product_id), "orders", [])
        except TypeError:
            # Some SDK versions use "status" instead of "order_status"
            try:
                return getattr(client.list_orders(status=[order_status], product_id=product_id, limit=limit), "orders", [])
            except TypeError:
                return getattr(client.list_orders(status=[order_status], product_id=product_id), "orders", [])


def _format_line(rec: Dict[str, Any]) -> str:
    created = _parse_dt(rec.get("created_time"))
    created_s = created.isoformat(timespec="seconds") if created else str(rec.get("created_time"))
    return (
        f"{created_s}  {rec.get('status')}  {rec.get('product_id')}  {rec.get('side')}  "
        f"px={rec.get('price')}  sz={rec.get('size')}  filled={rec.get('filled_size')}  "
        f"oid={rec.get('order_id')}"
    )


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--product-id", default=None, help="Optional product id (e.g. XRP-USD). If omitted, queries all products (may be slower).")
    ap.add_argument("--hours", type=float, default=24.0, help="How far back to consider results (best effort).")
    ap.add_argument("--limit", type=int, default=200, help="Max orders per status query.")
    ap.add_argument("--statuses", default="OPEN,CANCELLED,FILLED", help="Comma-separated statuses to query.")
    ap.add_argument("--out", required=True, help="Path to write JSONL output.")
    args = ap.parse_args(argv)

    repo_root = _repo_root()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    key_file = os.environ.get("COINBASE_KEY_FILE", "").strip()
    if not key_file:
        print("ERROR: COINBASE_KEY_FILE env var is not set.", file=sys.stderr)
        return 2

    # Import from the repo (uses installed coinbase SDK)
    from managers.auth_manager.auth_jwt import get_client  # type: ignore

    client = get_client(key_file)

    statuses = [s.strip().upper() for s in args.statuses.split(",") if s.strip()]
    cutoff = _utc_now() - timedelta(hours=float(args.hours))

    out_path = Path(args.out).expanduser().resolve()
    out_path.parent.mkdir(parents=True, exist_ok=True)

    records: List[Dict[str, Any]] = []
    errors: List[str] = []

    for st in statuses:
        try:
            orders = _list_orders(client, st, args.product_id, int(args.limit))
            for o in orders or []:
                rec = _extract_order_fields(o)
                rec["status_query"] = st
                records.append(rec)
        except Exception as e:
            errors.append(f"{st}: {type(e).__name__}: {e}")

    # Filter by created_time where possible
    filtered: List[Dict[str, Any]] = []
    for r in records:
        dt = _parse_dt(r.get("created_time"))
        if dt is None or dt >= cutoff:
            filtered.append(r)

    # Sort by created_time best-effort
    def _sort_key(r: Dict[str, Any]) -> Tuple[int, str]:
        dt = _parse_dt(r.get("created_time"))
        if dt is None:
            return (1, str(r.get("created_time") or ""))
        return (0, dt.isoformat())

    filtered.sort(key=_sort_key)

    # Write JSONL
    with out_path.open("w", encoding="utf-8") as f:
        meta = {
            "meta": True,
            "generated_utc": _utc_now().isoformat(timespec="seconds"),
            "product_id": args.product_id,
            "hours": args.hours,
            "limit": args.limit,
            "statuses": statuses,
            "cutoff_utc": cutoff.isoformat(timespec="seconds"),
            "errors": errors,
        }
        f.write(json.dumps(meta, ensure_ascii=False) + "\n")
        for r in filtered:
            f.write(json.dumps(_to_primitive(r), ensure_ascii=False) + "\n")

    # Human-readable summary to stdout
    print("COINBASE ORDER ACTIVITY (best effort)")
    print(f"generated_utc: {_utc_now().isoformat(timespec='seconds')}")
    print(f"product_id: {args.product_id or '(all)'}")
    print(f"cutoff_utc: {cutoff.isoformat(timespec='seconds')}")
    if errors:
        print("errors:")
        for e in errors:
            print(f"  - {e}")
    print("")
    print(f"records_written: {len(filtered)} -> {out_path}")
    print("")

    # Print last ~200 lines for quick view
    tail = filtered[-200:] if len(filtered) > 200 else filtered
    for r in tail:
        print(_format_line(r))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
