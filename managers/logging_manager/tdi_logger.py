from __future__ import annotations

import json
import threading
import time
from pathlib import Path
from typing import Any, Dict, Optional

__all__ = ["write_snapshot", "write_error"]

_WRITE_LOCK = threading.Lock()


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def _snapshot_path(cfg: Optional[Dict[str, Any]] = None) -> Path:
    cfg = cfg or {}
    rel = str(cfg.get("TDI_SNAPSHOT_PATH") or "logs/tdi_snapshots.jsonl")
    p = Path(rel)
    if not p.is_absolute():
        p = _project_root() / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _ts_utc() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _append(path: Path, row: Dict[str, Any]) -> None:
    line = json.dumps(row, separators=(",", ":"), ensure_ascii=False)
    with _WRITE_LOCK:
        with open(path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def write_snapshot(cfg: Optional[Dict[str, Any]], payload: Dict[str, Any]) -> bool:
    try:
        if not isinstance(payload, dict):
            return False
        comps = payload.get("components") if isinstance(payload.get("components"), dict) else {}
        row: Dict[str, Any] = {
            "ts": payload.get("ts") or _ts_utc(),
            "tick": payload.get("tick"),
            "product_id": payload.get("product_id"),
            "price": payload.get("price"),
            "tdi_version": payload.get("tdi_version"),
            "tdi_score": payload.get("tdi_score"),
            "tdi_truth_score": payload.get("tdi_truth_score"),
            "tdi_reliability_adjustment": payload.get("tdi_reliability_adjustment"),
            "tdi_band": payload.get("tdi_band"),
            "top_reasons": payload.get("top_reasons") or [],
        }
        for name, value in comps.items():
            row[f"tdi_{name}"] = value
        for key in (
            "bot_score",
            "g24h_pct",
            "dmid_bps",
            "spr_bps",
            "tob_usd",
            "press",
            "trough_pct",
            "trough_n",
            "tape_fresh_ratio",
            "tape_spread_ok_ratio",
            "tape_press_ok_ratio",
            "tape_top_ratio",
            "tape_tob_usd_avg",
            "tape_sample_n",
            "tape_u0_streak",
            "tape_u0_cooldown",
            "symbol_cohort",
            "symbol_quality_score",
        ):
            if key in payload:
                row[key] = payload.get(key)
        _append(_snapshot_path(cfg), row)
        return True
    except Exception:
        return False


def write_error(
    cfg: Optional[Dict[str, Any]],
    product_id: str,
    error: Any,
    payload: Optional[Dict[str, Any]] = None,
) -> bool:
    try:
        row: Dict[str, Any] = {
            "ts": _ts_utc(),
            "product_id": str(product_id or ""),
            "event": "tdi_error",
            "tdi_version": "v1",
            "error": str(error),
        }
        if isinstance(payload, dict):
            if payload.get("tick") is not None:
                row["tick"] = payload.get("tick")
            if payload.get("price") is not None:
                row["price"] = payload.get("price")
        _append(_snapshot_path(cfg), row)
        return True
    except Exception:
        return False
