#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Windowed PnL / history snapshot helper.

This script reuses managers.logging_manager.diag_pnl_snapshot to build the
per-product PnL, but applies a simple time-window filter on the fills before
aggregation. It is meant to be launched from the main menu (option H sub-menu).
"""

from __future__ import annotations

import argparse
import os
import sys
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------------
# Import base diag_pnl_snapshot (so we reuse all its PnL logic)
# ---------------------------------------------------------------------------

_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

try:
    from managers.logging_manager import diag_pnl_snapshot as base  # type: ignore
except Exception:  # pragma: no cover
    # Allow running directly from project root as:
    #   python managers/logging_manager/diag_pnl_snapshot_windowed.py
    try:
        import diag_pnl_snapshot as base  # type: ignore
    except Exception as exc:  # pragma: no cover
        print(f"[pnl_window] FATAL: cannot import diag_pnl_snapshot: {exc}")
        sys.exit(1)

WINDOW_CHOICES = ("1d", "7d", "30d", "90d", "all")


def _parse_fill_time(row: Dict[str, Any]) -> Optional[datetime]:
    """
    Best-effort parse of a fill row's timestamp.

    Accepts ISO-8601 with 'Z', with or without fractional seconds, or a plain
    'YYYY-mm-dd HH:MM:SS' fallback. Returns timezone-aware UTC datetimes.
    """
    ts = row.get("time") or row.get("created_at")
    if not ts:
        return None
    s = str(ts).strip()
    if not s:
        return None

    # Epoch seconds as a string (not expected, but cheap to support)
    if s.isdigit():
        try:
            return datetime.fromtimestamp(int(s), tz=timezone.utc)
        except Exception:
            pass

    # Handle common Coinbase-style ISO timestamps with trailing Z
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        return datetime.fromisoformat(s)
    except Exception:
        pass

    # Very small fallback set
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
        try:
            return datetime.strptime(s, fmt).replace(tzinfo=timezone.utc)  # type: ignore[attr-defined]
        except Exception:
            continue
    return None


def _window_to_since(window: str) -> Optional[datetime]:
    """
    Map a window string ("1d", "7d", "30d", "90d", "all") to a UTC cutoff.
    """
    window = (window or "all").lower()
    if window in ("all", "", "none"):
        return None
    days_map = {"1d": 1, "7d": 7, "30d": 30, "90d": 90}
    days = days_map.get(window)
    if not days:
        return None
    return datetime.now(timezone.utc) - timedelta(days=days)


def _filter_fills_by_window(
    fills: List[Dict[str, Any]],
    since_utc: Optional[datetime],
) -> List[Dict[str, Any]]:
    """
    Return only fills whose timestamp is >= since_utc.

    If since_utc is None or the timestamp is unparseable, the row is kept.
    """
    if since_utc is None:
        return fills
    out: List[Dict[str, Any]] = []
    for row in fills:
        t = _parse_fill_time(row)
        if t is None or t >= since_utc:
            out.append(row)
    return out


def main() -> int:
    ap = argparse.ArgumentParser(
        description="Windowed PnL / history snapshot (menu H sub-menu helper)."
    )
    ap.add_argument(
        "--window",
        choices=WINDOW_CHOICES,
        default="7d",
        help="Time window for fills-based PnL: 1d, 7d, 30d, 90d, or all.",
    )
    args = ap.parse_args()

    # Load all fills using the same helper the base script uses.
    try:
        fills, src_label = base._load_fills()  # type: ignore[attr-defined]
    except Exception as exc:
        print(f"[pnl_window] Failed to load fills: {exc}")
        return 1

    if not fills:
        print("[pnl_window] No fills available.")
        return 0

    since_utc = _window_to_since(args.window)
    fills_window = _filter_fills_by_window(fills, since_utc)

    # If filter wipes everything out, fall back to originals so the viewer
    # still shows something instead of an empty table.
    if not fills_window and since_utc is not None:
        print("[pnl_window] No fills in requested window; using full history instead.")
        fills_window = fills
        window_label = "all"
    else:
        window_label = args.window

    try:
        snap = base._build_pnl_from_fills(fills_window)  # type: ignore[attr-defined]
    except Exception as exc:
        print(f"[pnl_window] Failed to build PnL snapshot: {exc}")
        return 1

    # Tag snapshot with the window so future tooling can inspect it, even if
    # the pretty-printer ignores this key.
    if isinstance(snap, dict):
        snap = dict(snap)
        snap.setdefault("window", window_label)

    # Reuse the existing pretty-printer. We stuff the window label into the
    # "Source:" string so you can see it in the header without touching
    # diag_pnl_snapshot itself.
    src_for_header = src_label
    if src_label:
        src_for_header = f"{src_label} (window {window_label})"

    try:
        base.print_pnl_snapshot(snap, src_label=src_for_header)  # type: ignore[attr-defined]
    except Exception as exc:
        print(f"[pnl_window] Failed to print snapshot: {exc}")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
