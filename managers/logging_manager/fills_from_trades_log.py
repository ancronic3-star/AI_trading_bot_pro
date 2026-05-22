#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
fills_from_trades_log.py

Utility: scan trades.log and build a synthetic fills_all.json suitable
for diag_pnl_snapshot.py and pnl_report.py.

It looks for lines that mention fills (contain 'fill' / 'filled') and
tries to parse:

    - side: BUY / SELL
    - product_id: e.g. BTC-USD, DOGE-USD, SOL-USDC, etc.
    - qty / size: from fragments like 'qty~0.0012'
    - price: from fragments like 'px~65000.12' or 'price=65000.12'
    - timestamp: from a leading [YYYY-MM-DD HH:MM:SS ...] if present

Output:
    C:\ai_trading_bot_koko\fills_all.json

diag_pnl_snapshot.py prefers fills_all.json over fills_dump.json, so
once this file exists, menu option H will use it.
"""

from __future__ import annotations

import json
import os
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------

ROOT_DIR = Path(__file__).resolve().parents[2]
TRADES_LOG = ROOT_DIR / "trades.log"
FILLS_ALL = ROOT_DIR / "fills_all.json"


# ---------------------------------------------------------------------------
# Regex patterns (aligned with pnl_tracker.py)
# ---------------------------------------------------------------------------

SIDE_PAT = re.compile(r"\b(BUY|SELL)\b", re.IGNORECASE)
QTY_PAT = re.compile(r"qty[~=:\s]*([0-9.]+)", re.IGNORECASE)
PX_PAT = re.compile(r"(px|price)[~=:\s]*([0-9.]+)", re.IGNORECASE)

# Product IDs: e.g. BTC-USD, DOGE-USD, SOL-USDC, TAO-USD1, etc.
# Restrict to quote assets that behave like dollars.
PROD_PAT = re.compile(
    r"\b([A-Z0-9]+-(USD|USDC|USDT|USD1))\b",
    re.IGNORECASE,
)

# Timestamp at start of line: [2025-12-07 16:53:17] ...
TS_PAT = re.compile(r"\[([0-9]{4}-[0-9]{2}-[0-9]{2} [^]]+)\]")


def _safe_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    if v != v:  # NaN
        return None
    return v


def _parse_time(line: str) -> Optional[str]:
    """
    Extract a timestamp from '[YYYY-MM-DD ...]' if present and return an ISO-ish string.
    If parsing fails, we just return the raw bracket contents.
    """
    m = TS_PAT.search(line)
    if not m:
        return None
    raw = m.group(1).strip()
    # Best-effort normalization. If it looks like 'YYYY-MM-DD HH:MM:SS', normalize;
    # otherwise just return the raw string.
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M"):
        try:
            dt = datetime.strptime(raw, fmt)
            return dt.isoformat()
        except ValueError:
            continue
    return raw


def _parse_fill(line: str) -> Optional[Dict[str, Any]]:
    """
    Parse a single log line into a fill dict if possible.
    Expect something like:

        "[ts] ... BUY FILLED BTC-USD qty~0.0012 px~65000.12 ..."
        "[ts] ... SELL FILLED DOGE-USD qty=20.8681 price=0.24 ..."

    Returns None if required pieces cannot be found.
    """
    # Require 'fill' / 'filled' so we don't treat every order line as a fill.
    low = line.lower()
    if "fill" not in low and "filled" not in low:
        return None

    # side
    sm = SIDE_PAT.search(line)
    if not sm:
        return None
    side = sm.group(1).upper()

    # product_id: search after the side so we don't accidentally match other tokens
    prod = None
    pm = PROD_PAT.search(line[sm.end():])
    if pm:
        prod = pm.group(1).upper()

    if not prod:
        return None

    # qty and price
    qm = QTY_PAT.search(line)
    pm2 = PX_PAT.search(line)

    qty = _safe_float(qm.group(1)) if qm else None
    px = _safe_float(pm2.group(2)) if pm2 else None

    if qty is None or px is None or qty <= 0:
        return None

    # timestamp (optional)
    t = _parse_time(line)

    return {
        "product_id": prod,
        "side": side,
        "size": qty,
        "price": px,
        "fee": 0.0,  # we don't have accurate fee info in trades.log
        "time": t or "",
        "source": "trades.log",
    }


def main() -> int:
    if not TRADES_LOG.exists():
        print(f"[ERROR] trades.log not found at {TRADES_LOG}")
        return 1

    fills: List[Dict[str, Any]] = []
    by_pid: defaultdict[str, int] = defaultdict(int)

    print(f"=== FILLS FROM trades.log ===")
    print(f"Source: {TRADES_LOG}")

    with TRADES_LOG.open("r", encoding="utf-8", errors="replace") as fh:
        for line in fh:
            line = line.rstrip("\n")
            if not line:
                continue
            fill = _parse_fill(line)
            if not fill:
                continue
            fills.append(fill)
            by_pid[fill["product_id"]] += 1

    if not fills:
        print("No fills could be parsed from trades.log.")
        print("Check that your log lines contain 'BUY/SELL', 'qty~', and 'px~' or 'price='. ")
        return 0

    # Write JSON
    try:
        with FILLS_ALL.open("w", encoding="utf-8") as out:
            json.dump(fills, out, indent=2, sort_keys=True)
        print()
        print(f"Wrote {len(fills)} fills to {FILLS_ALL}")
    except OSError as exc:
        print(f"[ERROR] Could not write {FILLS_ALL}: {exc}")
        return 1

    # Summary by product
    print()
    print("pid              fills")
    print("-" * 40)
    for pid in sorted(by_pid.keys()):
        print(f"{pid:14s} {by_pid[pid]:6d}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
