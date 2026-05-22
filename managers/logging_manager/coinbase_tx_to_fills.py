#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
coinbase_tx_to_fills.py

Convert a Coinbase "Raw transaction" CSV export (columns like:
    Transaction ID, Transaction Type, Date & time, Asset Acquired,
    Quantity Acquired (Bought, Received, etc),
    Cost Basis (incl. fees and/or spread) (USD),
    Data Source,
    Asset Disposed (Sold, Sent, etc),
    Quantity Disposed,
    Proceeds (excl. fees and/or spread) (USD)

into a fills_all.json file that diag_pnl_snapshot.py and
fills_products_report.py already know how to read.

Output format: JSON array of dicts with keys:

    product_id, side, price, size, fee, time

We currently treat only "Buy" and "Sell" rows to avoid double‑counting
the many "Credit", "Converted", and "Advanced trade trade" ledger rows.
"""

from __future__ import annotations

import argparse
import csv
import json
from pathlib import Path
from typing import Any, Dict, List


def _safe_float(x: str) -> float | None:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return v


def convert_rawtx_to_fills(src: Path) -> List[Dict[str, Any]]:
    fills: List[Dict[str, Any]] = []

    with src.open("r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            ttype = (row.get("Transaction Type") or "").strip()
            if ttype not in ("Buy", "Sell"):
                # Skip credits, rewards, conversions, portfolio transfers, etc.
                continue

            if ttype == "Buy":
                asset = (row.get("Asset Acquired") or "").strip()
                qty_str = (row.get("Quantity Acquired (Bought, Received, etc)") or "").strip()
                usd_str = (row.get("Cost Basis (incl. fees and/or spread) (USD)") or "").strip()
                side = "BUY"
            else:  # "Sell"
                asset = (row.get("Asset Disposed (Sold, Sent, etc)") or "").strip()
                qty_str = (row.get("Quantity Disposed") or "").strip()
                usd_str = (row.get("Proceeds (excl. fees and/or spread) (USD)") or "").strip()
                side = "SELL"

            if not asset or not qty_str or not usd_str:
                continue

            qty = _safe_float(qty_str)
            usd = _safe_float(usd_str)
            if qty is None or usd is None or qty <= 0 or usd <= 0:
                continue

            price = usd / qty
            time_str = (row.get("Date & time") or "").strip()
            if not time_str:
                time_str = ""

            fills.append(
                {
                    "product_id": f"{asset}-USD",
                    "side": side,
                    "size": qty,
                    "price": price,
                    "fee": 0.0,  # Cost basis includes fees; we don't double‑count here.
                    "time": time_str,
                }
            )

    return fills


def main() -> None:
    ap = argparse.ArgumentParser(description="Convert Coinbase Raw TX CSV to fills_all.json format.")
    ap.add_argument(
        "--src",
        type=Path,
        required=True,
        help="Path to Coinbase Raw transaction CSV (e.g. Coinbase-0-CB-RAWTX_.csv)",
    )
    ap.add_argument(
        "--out",
        type=Path,
        default=Path("fills_all.json"),
        help="Output JSON file path (default: fills_all.json in project root)",
    )
    args = ap.parse_args()

    fills = convert_rawtx_to_fills(args.src)
    if not fills:
        print(f"[WARN] No usable Buy/Sell rows found in {args.src}")
    else:
        print(f"[INFO] Parsed {len(fills)} Buy/Sell rows from {args.src}")

    # Make sure output directory exists
    if args.out.parent and not args.out.parent.exists():
        args.out.parent.mkdir(parents=True, exist_ok=True)

    args.out.write_text(json.dumps(fills, indent=2))
    print(f"[INFO] Wrote {len(fills)} fills to {args.out}")


if __name__ == "__main__":
    main()
