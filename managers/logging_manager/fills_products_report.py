#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fills_products_report.py

Quick diagnostic for what PnL snapshot actually sees in fills_all.json / fills_dump.json.

- Uses the same project-root detection and fill parsing logic as diag_pnl_snapshot.py
  (JSON list, {"fills": [...]}, NDJSON, or CSV:
   fee, liquidity, trade_id, price, product_id, fee2, side, size, time, order_id)

- Prints, per product_id:
    * number of fills
    * first timestamp
    * last timestamp
"""

from __future__ import annotations

import csv
import json
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _find_project_root() -> Path:
    """Walk up until we find a 'logs' directory; fallback to current file dir."""
    here = Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        if (cand / "logs").is_dir():
            return cand
    return here.parent


PROJECT_ROOT = _find_project_root()
LOGS_DIR = PROJECT_ROOT / "logs"

FILLS_ALL = PROJECT_ROOT / "fills_all.json"
FILLS_DUMP = PROJECT_ROOT / "fills_dump.json"


def _decode_bytes(raw: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="ignore")


def _safe_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if v != v:
            return None
        return v
    except (TypeError, ValueError):
        return None


def _load_fills_from_file(path: Path) -> List[Dict[str, Any]]:
    """
    Load fills from:
    - JSON array file (or {"fills": [...]})
    - NDJSON (one JSON object per line)
    - CSV in the format:
      fee, liquidity, trade_id, price, product_id, fee2, side, size, time, order_id
    """
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return []
    except OSError as exc:
        print(f"[WARN] Could not read fills file {path}: {exc}", file=sys.stderr)
        return []

    text = _decode_bytes(raw)

    # 1) Single JSON value (list or {"fills": [...]})
    try:
        data = json.loads(text)
        if isinstance(data, list):
            return [r for r in data if isinstance(r, dict)]
        if isinstance(data, dict):
            fills = data.get("fills")
            if isinstance(fills, list):
                return [r for r in fills if isinstance(r, dict)]
    except json.JSONDecodeError:
        pass

    # 2) NDJSON
    ndjson_fills: List[Dict[str, Any]] = []
    for line in text.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        if isinstance(obj, dict):
            ndjson_fills.append(obj)

    if ndjson_fills:
        return ndjson_fills

    # 3) CSV fallback
    csv_fills: List[Dict[str, Any]] = []
    reader = csv.reader(text.splitlines())
    for row in reader:
        # Expect at least:
        # fee, liquidity, trade_id, price, product_id, fee2, side, size, time, order_id
        if not row or len(row) < 8:
            continue

        # Skip header-ish lines
        if row[0].lower().startswith("fee") or row[3].lower().startswith("price"):
            continue

        product_id = (row[4] if len(row) > 4 else "").strip()
        side = (row[6] if len(row) > 6 else "").strip().upper()
        price = _safe_float(row[3] if len(row) > 3 else None)
        size = _safe_float(row[7] if len(row) > 7 else None)
        fee = _safe_float(row[0])
        time_str = (row[8] if len(row) > 8 else "").strip()

        if not product_id or side not in ("BUY", "SELL"):
            continue
        if price is None or size is None or size <= 0:
            continue

        csv_fills.append(
            {
                "product_id": product_id,
                "side": side,
                "price": price,
                "size": size,
                "fee": fee or 0.0,
                "time": time_str,
            }
        )

    if csv_fills:
        return csv_fills

    print(f"[WARN] Could not parse fills file {path} as JSON, NDJSON, or CSV", file=sys.stderr)
    return []


def _load_fills() -> Tuple[List[Dict[str, Any]], Optional[str]]:
    """
    Preferred: fills_all.json, fallback: fills_dump.json.
    Returns (fills, source_label).
    """
    for p in (FILLS_ALL, FILLS_DUMP):
        if p.exists():
            fills = _load_fills_from_file(p)
            if fills:
                return fills, str(p)
    return [], None


def main(argv: Optional[List[str]] = None) -> int:
    fills, src = _load_fills()
    if not fills:
        print("No fills loaded.")
        print("Looked for:")
        print(f"  - {FILLS_ALL}")
        print(f"  - {FILLS_DUMP}")
        return 0

    print("=== FILLS PRODUCTS REPORT ===")
    print(f"Source: {src}")
    print(f"Total fills loaded: {len(fills)}")
    print()

    by_pid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for r in fills:
        pid = (
            (r.get("product_id") or r.get("product") or r.get("pid") or "")
            .strip()
        )
        if not pid:
            continue
        by_pid[pid].append(r)

    if not by_pid:
        print("No product_id found in fills.")
        return 0

    print(f"{'pid':14s} {'fills':>7s} {'first_time':>26s} {'last_time':>26s}")
    print("-" * 80)

    def _get_time(row: Dict[str, Any]) -> str:
        t = row.get("time") or row.get("created_at") or ""
        return str(t)

    for pid in sorted(by_pid.keys()):
        rows = by_pid[pid]
        times = sorted(_get_time(r) for r in rows if _get_time(r))
        first = times[0] if times else ""
        last = times[-1] if times else ""
        print(
            f"{pid:14s} "
            f"{len(rows):7d} "
            f"{first:>26s} "
            f"{last:>26s}"
        )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
