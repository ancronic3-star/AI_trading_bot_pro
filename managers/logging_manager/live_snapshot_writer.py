from __future__ import annotations

import argparse
import csv
import io
import json
import math
import os
import re
import sys
import threading
import time
import zipfile
from bisect import bisect_right
from collections import defaultdict, deque
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, Iterable, List, Optional, Tuple
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from managers.auth_manager.auth_jwt import get_client

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DEFAULT_OUTPUT = PROJECT_ROOT / "live_snapshot.json"
DEFAULT_TRACKED_OUTPUT = PROJECT_ROOT / "tracked_account_snapshot.json"
DEFAULT_DECISION_REPLAY_OUTPUT = PROJECT_ROOT / "decision_replay_snapshot.json"
DEFAULT_WM3_SUPPORT_OUTPUT = PROJECT_ROOT / "wm3_support_snapshot.json"
DEFAULT_TRACKED_BASELINE = PROJECT_ROOT / "logs" / "tracked_account_baseline.json"
DEFAULT_TDI_PATH = PROJECT_ROOT / "logs" / "tdi_snapshots.jsonl"
DEFAULT_ACTIVITY_PATH = PROJECT_ROOT / "logs" / "activity_ticker.log"
DEFAULT_RUN_ACTIVE_PATH = PROJECT_ROOT / "logs" / "run_active.json"
DEFAULT_CYCLE_DIR = PROJECT_ROOT / "logs" / "analysis_cycle"

STABLES = {"USD", "USDC", "USDT", "USD1"}
SNAPSHOT_LOCK = threading.Lock()
DECISION_REPLAY_CACHE: Dict[str, Any] = {"built_at": 0.0, "activity_mtime": None, "tdi_mtime": None, "cycle_sig": None, "payload": {"generated_at": "", "rows": []}}
TRANSPARENT_LOG_CACHE: Dict[str, Any] = {"built_at": 0.0, "activity_mtime": None, "payload": {"generated_at": "", "engine_context": {}, "event_counts": {}, "events": [], "success_events": [], "last_tick_diag": None}}
TIMEFRAME_ORDER = ["1m", "5m", "15m", "30m", "1h", "2h", "4h", "6h", "1d", "3d", "1w", "1mo", "3mo", "6mo", "9mo", "1y"]
SELECTOR_TIMEFRAME_REQUESTED_ORDER = ["15m", "1h", "6h", "1d", "3d", "1w", "1mo", "3mo", "6mo", "9mo", "1y"]
TP_TARGET_LADDER = [2.0, 5.0, 10.0, 20.0, 50.0, 100.0, 150.0, 200.0, 300.0, 500.0]
SELECTOR_DERIVATION_RULES: Dict[str, Dict[str, Any]] = {
    "3d": {"primary": "1d", "secondary": "1w", "mode": "blend", "score_penalty": 6, "confidence_penalty": 8},
    "1mo": {"primary": "1mo", "secondary": "1w", "mode": "anchor", "score_penalty": 8, "confidence_penalty": 10},
    "3mo": {"primary": "1mo", "secondary": "1w", "mode": "anchor", "score_penalty": 12, "confidence_penalty": 16},
    "6mo": {"primary": "1mo", "secondary": "1w", "mode": "anchor", "score_penalty": 16, "confidence_penalty": 20},
    "9mo": {"primary": "1mo", "secondary": "1w", "mode": "anchor", "score_penalty": 20, "confidence_penalty": 24},
    "1y": {"primary": "1mo", "secondary": "1w", "mode": "anchor", "score_penalty": 24, "confidence_penalty": 28},
}
MM28_TP_SELECTOR_FORMULA_VERSION = "mm28_scanner_readiness_unified_v1"
SCANNER_SUPPORT_INTERVALS = ["15m", "30m", "1h", "2h", "4h", "6h", "1d", "1w"]
SCANNER_SELECTOR_DERIVED_WEIGHTS: Dict[str, List[Tuple[str, float]]] = {
    "3d": [("1d", 0.72), ("1w", 0.28)],
    "1mo": [("1w", 0.82), ("1d", 0.18)],
    "3mo": [("1w", 0.90), ("1d", 0.10)],
    "6mo": [("1w", 0.94), ("1d", 0.06)],
    "9mo": [("1w", 0.97), ("1d", 0.03)],
    "1y": [("1w", 1.00)],
}



def _to_plain(x: Any) -> Any:
    try:
        return json.loads(json.dumps(x, default=lambda o: getattr(o, "__dict__", {})))
    except Exception:
        return x


def _dec(x: Any, default: float = 0.0) -> float:
    try:
        if x is None or x == "":
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def _now_utc_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_settings() -> Dict[str, Any]:
    path = PROJECT_ROOT / "run_settings.json"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}


def _read_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return None


def _write_json_atomic(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)


def _normalize_iso_or_none(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        t2 = s[:-1] + "+00:00" if s.endswith("Z") else s
        dt = datetime.fromisoformat(t2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    except Exception:
        return s



def _median_or_none(values: Iterable[Any]) -> Optional[float]:
    nums: List[float] = []
    for value in values:
        try:
            if value is None or value == "":
                continue
            nums.append(float(value))
        except Exception:
            continue
    if not nums:
        return None
    nums.sort()
    mid = len(nums) // 2
    if len(nums) % 2:
        return float(nums[mid])
    return float((nums[mid - 1] + nums[mid]) / 2.0)


def _float_or_none(value: Any) -> Optional[float]:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except Exception:
        return None


def _sample_strength_from_count(count: Any) -> Optional[str]:
    try:
        n = int(count)
    except Exception:
        return None
    if n <= 0:
        return "none"
    if n < 3:
        return "thin"
    if n < 10:
        return "light"
    if n < 25:
        return "moderate"
    return "strong"


def _confidence_band_from_count(count: Any) -> Optional[str]:
    try:
        n = int(count)
    except Exception:
        return None
    if n <= 0:
        return None
    if n < 3:
        return "low"
    if n < 10:
        return "medium"
    return "high"


def _confidence_band_from_score(score: Any) -> Optional[str]:
    try:
        val = float(score)
    except Exception:
        return None
    if val >= 80.0:
        return "high"
    if val >= 50.0:
        return "medium"
    if val > 0.0:
        return "low"
    return None


def _normalize_target_key(value: Any) -> str:
    val = _float_or_none(value)
    return f"{float(val):.1f}" if val is not None else ""


def _readiness_from_support_state(state: Any) -> str:
    sval = str(state or "").strip().lower()
    if sval == "supported":
        return "ready"
    if sval == "watch":
        return "watch"
    if sval:
        return "blocked"
    return "blocked"


def _selector_phase_bonus(phase: Any) -> float:
    p = str(phase or "").strip().lower()
    if "lifting" in p:
        return 8.0
    if "descending" in p:
        return -10.0
    return 0.0


def _derive_target_fit_score_mm28(interval_row: Dict[str, Any], target_pct: float) -> Optional[float]:
    if not isinstance(interval_row, dict):
        return None
    avg_rebound = _float_or_none(interval_row.get("avg_rebound_pct"))
    if avg_rebound is None or avg_rebound <= 0:
        return None
    target = max(float(target_pct or 0.0), 0.0)
    confidence = _dec(interval_row.get("confidence"), 0.0)
    base_score = _dec(interval_row.get("score"), 0.0)
    qualified_troughs = max(0.0, _dec(interval_row.get("qualified_troughs"), 0.0))
    phase_bonus = _selector_phase_bonus(interval_row.get("phase"))
    trough_bonus = min(10.0, qualified_troughs * 1.25)
    if avg_rebound >= target:
        effective_floor = max(2.5, target)
        overshoot_penalty = ((avg_rebound - target) / effective_floor) * 100.0 if effective_floor > 0 else 0.0
        fit = max(0.0, 100.0 - overshoot_penalty)
    else:
        fit = (avg_rebound / max(target, 0.5)) * 100.0
    total = (fit * 0.55) + (confidence * 0.15) + (base_score * 0.20) + trough_bonus + phase_bonus
    return round(max(0.0, min(100.0, total)), 4)


def _selector_direct_support_scores_mm28(timeframes: Dict[str, Any], target_pct: float) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for tf in SCANNER_SUPPORT_INTERVALS:
        row = timeframes.get(tf) if isinstance(timeframes, dict) else None
        if not isinstance(row, dict):
            continue
        score = _derive_target_fit_score_mm28(row, target_pct)
        if score is None:
            continue
        source_kind = str(row.get("source_kind") or "live")
        out[tf] = {
            "tf": tf,
            "score": score,
            "confidence": _float_or_none(row.get("confidence")),
            "base_score": _float_or_none(row.get("score")),
            "avg_rebound_pct": _float_or_none(row.get("avg_rebound_pct")),
            "avg_drawdown_pct": _float_or_none(row.get("avg_drawdown_pct")),
            "qualified_troughs": int(_dec(row.get("qualified_troughs"), 0)),
            "phase": str(row.get("phase") or "") or None,
            "source_kind": source_kind,
            "interval_backing": "derived" if source_kind == "derived" else "live_backed",
            "provenance": "timeframes",
        }
    return out


def _selector_derived_score_mm28(base_scores: Dict[str, Dict[str, Any]], tf: str) -> Optional[Dict[str, Any]]:
    weights = SCANNER_SELECTOR_DERIVED_WEIGHTS.get(tf)
    if not weights:
        return None
    usable = [(base_scores.get(base_tf), weight, base_tf) for base_tf, weight in weights if isinstance(base_scores.get(base_tf), dict)]
    if not usable:
        return None
    weight_total = sum(weight for _, weight, _ in usable)
    if weight_total <= 0:
        return None
    score = sum(float(item.get("score") or 0.0) * weight for item, weight, _ in usable) / weight_total
    confidence_vals = [float(item.get("confidence") or 0.0) * weight for item, weight, _ in usable]
    confidence = sum(confidence_vals) / weight_total if confidence_vals else None
    primary = usable[0][0]
    return {
        "tf": tf,
        "score": round(float(score), 4),
        "confidence": round(float(confidence), 4) if confidence is not None else None,
        "base_score": None,
        "avg_rebound_pct": None,
        "avg_drawdown_pct": None,
        "qualified_troughs": None,
        "phase": primary.get("phase") if isinstance(primary, dict) else None,
        "source_kind": "derived",
        "interval_backing": "derived",
        "provenance": f"weighted_from_{'_'.join(base_tf for _, _, base_tf in usable)}",
    }


def _selector_scores_mm28(timeframes: Dict[str, Any], target_pct: float) -> Dict[str, Dict[str, Any]]:
    base_scores = _selector_direct_support_scores_mm28(timeframes, target_pct)
    out: Dict[str, Dict[str, Any]] = {}
    for tf in ["15m", "1h", "6h", "1d", "1w"]:
        row = base_scores.get(tf)
        if isinstance(row, dict):
            out[tf] = dict(row)
    for tf in ["3d", "1mo", "3mo", "6mo", "9mo", "1y"]:
        row = _selector_derived_score_mm28(base_scores, tf)
        if isinstance(row, dict):
            out[tf] = row
    return out


def _ranked_support_intervals_mm28(direct_scores: Dict[str, Dict[str, Any]]) -> List[Dict[str, Any]]:
    rows = [dict(v) for v in direct_scores.values() if isinstance(v, dict)]
    rows.sort(key=lambda item: (float(item.get("score") or 0.0), float(item.get("confidence") or 0.0), float(item.get("avg_rebound_pct") or 0.0), str(item.get("tf") or "")), reverse=True)
    return rows


def _build_tp_selector_contracts(coin: Dict[str, Any], support_coin: Dict[str, Any], default_target_key: str) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    timeframes = coin.get("timeframes") if isinstance(coin.get("timeframes"), dict) else {}
    support_tp = support_coin.get("tp_support") if isinstance(support_coin, dict) else {}
    if not isinstance(support_tp, dict):
        support_tp = {}
    base_ctx_stack = coin.get("ctx_stack") if isinstance(coin.get("ctx_stack"), list) else []
    base_readiness = str(coin.get("readiness") or "") if isinstance(coin, dict) else ""
    base_phase = None
    structure = coin.get("structure") if isinstance(coin.get("structure"), dict) else {}
    if isinstance(structure, dict):
        base_phase = structure.get("phase")

    by_target: Dict[str, Any] = {}
    for target in TP_TARGET_LADDER:
        target_key = _normalize_target_key(target)
        support_node = support_tp.get(target_key) if isinstance(support_tp.get(target_key), dict) else None
        selector_scores = _selector_scores_mm28(timeframes, float(target))
        direct_scores = _selector_direct_support_scores_mm28(timeframes, float(target))
        ranked_support = _ranked_support_intervals_mm28(direct_scores)
        best_interval = str((support_node or {}).get("best_interval") or (ranked_support[0].get("tf") if ranked_support else "") or "") or None
        confidence = _float_or_none((support_node or {}).get("confidence"))
        if confidence is None and best_interval and isinstance(direct_scores.get(best_interval), dict):
            confidence = _float_or_none(direct_scores[best_interval].get("confidence"))
        phase = (support_node or {}).get("phase") or (direct_scores.get(best_interval or "", {}) or {}).get("phase") or base_phase
        readiness = _readiness_from_support_state((support_node or {}).get("state")) if support_node else (base_readiness or "blocked")
        readiness_tone = readiness
        fit_status = None
        if support_node:
            state = str(support_node.get("state") or "").strip().lower()
            if state == "supported":
                fit_status = "fit"
            elif state == "watch":
                fit_status = "stretch"
            elif state:
                fit_status = "unsupported"
        support_intervals = [str(x) for x in ((support_node or {}).get("supporting_intervals") or []) if str(x)]
        if not support_intervals:
            support_intervals = [str(item.get("tf")) for item in ranked_support[:5] if item.get("tf")]
        nearest_interval = (support_node or {}).get("nearest_interval") or best_interval
        interval_backing = None
        if best_interval and isinstance(timeframes.get(best_interval), dict):
            interval_backing = "derived" if str((timeframes.get(best_interval) or {}).get("source_kind") or "live") == "derived" else "live_backed"
        reason = (support_node or {}).get("reason")
        if not reason:
            if best_interval and isinstance(direct_scores.get(best_interval), dict):
                drow = direct_scores.get(best_interval) or {}
                reason = f"MM28 selector score {drow.get('score')} at {best_interval} for target {target_key}%"
            else:
                reason = f"no support match for target {target_key}%"
        ctx_stack = []
        for item in ranked_support[:3]:
            ctx_stack.append({
                "tf": item.get("tf"),
                "score": item.get("score"),
                "phase": item.get("phase"),
                "interval_backing": item.get("interval_backing"),
            })
        if not ctx_stack:
            ctx_stack = list(base_ctx_stack)
        by_target[target_key] = {
            "selected_target_pct": float(target),
            "readiness": readiness,
            "readiness_tone": readiness_tone,
            "best_interval": best_interval,
            "support_intervals": support_intervals,
            "nearest_interval": nearest_interval,
            "confidence": confidence,
            "confidence_band": _confidence_band_from_score(confidence),
            "phase": phase,
            "reason": reason,
            "fit_status": fit_status,
            "fit_note": (support_node or {}).get("reason"),
            "interval_backing": interval_backing,
            "ctx_stack": ctx_stack,
            "selector_scores": {tf: (selector_scores.get(tf) or {}).get("score") for tf in SELECTOR_TIMEFRAME_REQUESTED_ORDER},
            "selector_score_rows": [selector_scores.get(tf) for tf in SELECTOR_TIMEFRAME_REQUESTED_ORDER if isinstance(selector_scores.get(tf), dict)],
            "support_score_rows": ranked_support,
            "source_path": "wm3_support" if support_node else "live_fallback",
            "formula_version": MM28_TP_SELECTOR_FORMULA_VERSION,
            "provenance": "live_snapshot_writer",
        }
    default_block = dict(by_target.get(default_target_key) or {}) if default_target_key and default_target_key in by_target else None
    if default_block and not default_block.get("selected_target_pct"):
        default_block["selected_target_pct"] = _float_or_none(default_target_key)
    return by_target, default_block


def _augment_support_snapshot_selector_blocks(support_payload: Dict[str, Any], live_payload: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    support_coins = support_payload.get("coins") if isinstance(support_payload, dict) else None
    live_coins = live_payload.get("coins") if isinstance(live_payload, dict) else None
    if not isinstance(support_coins, list) or not isinstance(live_coins, list):
        return support_payload
    live_by_pid: Dict[str, Dict[str, Any]] = {}
    for coin in live_coins:
        if isinstance(coin, dict):
            pid = str(coin.get("product_id") or "").upper()
            if pid:
                live_by_pid[pid] = coin
    default_target_key = _normalize_target_key(settings.get("TP_PCT"))
    for coin in support_coins:
        if not isinstance(coin, dict):
            continue
        pid = str(coin.get("product_id") or "").upper()
        live_coin = live_by_pid.get(pid) or {}
        tp_selector_by_target, tp_selector_default = _build_tp_selector_contracts(live_coin, coin, default_target_key)
        coin["tp_selector_by_target"] = tp_selector_by_target
        coin["tp_selector_default"] = tp_selector_default
    meta = support_payload.get("meta") if isinstance(support_payload.get("meta"), dict) else {}
    meta["tp_selector_formula_version"] = MM28_TP_SELECTOR_FORMULA_VERSION
    meta["default_tp_target_pct"] = _float_or_none(settings.get("TP_PCT"))
    support_payload["meta"] = meta
    return support_payload


def _phase_anchor_type(phase: Any) -> Optional[str]:
    p = str(phase or "").strip().lower()
    if not p:
        return None
    if "trough" in p or "support" in p or "lift" in p or "ascend" in p or "bottom" in p:
        return "trough"
    if "crest" in p or "descend" in p or "roll" in p or "top" in p or "fade" in p:
        return "crest"
    return None


def _days_since_iso(ts_value: Any, as_of: Optional[datetime]) -> Optional[float]:
    if as_of is None:
        return None
    dt = _parse_utc_ts(ts_value)
    if dt is None:
        return None
    delta = (as_of - dt).total_seconds() / 86400.0
    if delta < 0:
        return 0.0
    return float(delta)


def _phase_day_from_anchor(anchor_days: Optional[float]) -> Optional[int]:
    if anchor_days is None:
        return None
    try:
        return int(math.floor(float(anchor_days))) + 1
    except Exception:
        return None


def _flatten_ctx_labels(values: Any) -> List[str]:
    out: List[str] = []
    if isinstance(values, list):
        for item in values:
            if isinstance(item, dict):
                label = str(item.get("tf") or item.get("interval") or "").strip()
            else:
                label = str(item or "").strip()
            if label and label not in out:
                out.append(label)
    return out


def _dominant_factors(components: Dict[str, Any], top_reasons: List[str], limit: int = 3) -> List[str]:
    ordered: List[str] = []
    for reason in top_reasons or []:
        key = str(reason or "").strip()
        if key and key not in ordered:
            ordered.append(key)
    scored: List[Tuple[str, float]] = []
    for key, value in (components or {}).items():
        try:
            if value is None:
                continue
            scored.append((str(key), float(value)))
        except Exception:
            continue
    scored.sort(key=lambda item: (-item[1], item[0]))
    for key, _ in scored:
        if key and key not in ordered:
            ordered.append(key)
    return ordered[:max(1, int(limit))]


def _load_tracked_baseline(path: Path = DEFAULT_TRACKED_BASELINE) -> Dict[str, Any]:
    obj = _read_json(path) if path.exists() else None
    starting = _dec(obj.get("starting_equity") if isinstance(obj, dict) else None, 50.0)
    try:
        starting_f = round(float(starting if starting is not None else 50.0), 8)
    except Exception:
        starting_f = 50.0
    baseline = {
        "account_label": str((obj or {}).get("account_label") or "tracked_account") if isinstance(obj, dict) else "tracked_account",
        "starting_equity": starting_f,
        "baseline_start_time": _normalize_iso_or_none((obj or {}).get("baseline_start_time")) if isinstance(obj, dict) else None,
    }
    if not path.exists():
        try:
            _write_json_atomic(path, baseline)
        except Exception:
            pass
    return baseline


def _build_tracked_account_snapshot(snapshot: Dict[str, Any]) -> Dict[str, Any]:
    meta = snapshot.get("meta") if isinstance(snapshot, dict) else {}
    acct = snapshot.get("account") if isinstance(snapshot, dict) else {}
    generated_at = str((meta or {}).get("generated_at") or _now_utc_iso())
    current_equity = _dec((acct or {}).get("equity_usd"), 0.0) or 0.0
    held_positions_count = int((acct or {}).get("positions_count") or len(snapshot.get("positions") or []))

    baseline = _load_tracked_baseline(DEFAULT_TRACKED_BASELINE)
    starting_equity = _dec(baseline.get("starting_equity"), 50.0)
    starting_equity = round(float(starting_equity if starting_equity is not None else 50.0), 8)
    baseline_start_time = _normalize_iso_or_none(baseline.get("baseline_start_time"))
    account_label = str(baseline.get("account_label") or "tracked_account")

    unrealized_pnl: Optional[float] = None
    realized_pnl: Optional[float] = None
    recent_closed_trades: List[Dict[str, Any]] = []

    try:
        from managers.logging_manager import diag_pnl_snapshot as pnl_diag  # type: ignore

        pnl_snapshot, _ = pnl_diag._build_balance_anchored_snapshot()
        open_rows = pnl_snapshot.get("open") if isinstance(pnl_snapshot, dict) else {}
        if isinstance(open_rows, dict):
            vals: List[float] = []
            complete = True
            for row in open_rows.values():
                if not isinstance(row, dict) or row.get("unrealized_pnl_usd") is None:
                    complete = False
                    break
                vals.append(float(row.get("unrealized_pnl_usd") or 0.0))
            if complete:
                unrealized_pnl = round(sum(vals), 8)
        if unrealized_pnl is not None:
            realized_pnl = round((current_equity - starting_equity) - unrealized_pnl, 8)
    except Exception:
        unrealized_pnl = None
        realized_pnl = None

    equity_return_pct: Optional[float]
    if starting_equity > 0:
        equity_return_pct = round(((current_equity - starting_equity) / starting_equity) * 100.0, 8)
    else:
        equity_return_pct = None

    return {
        "generated_at": generated_at,
        "baseline_start_time": baseline_start_time,
        "account_label": account_label,
        "starting_equity": starting_equity,
        "current_equity": round(float(current_equity), 8),
        "realized_pnl": realized_pnl,
        "unrealized_pnl": unrealized_pnl,
        "equity_return_pct": equity_return_pct,
        "held_positions_count": held_positions_count,
        "last_updated": generated_at,
        "recent_closed_trades": recent_closed_trades,
    }




_LOCAL_TZ = datetime.now().astimezone().tzinfo or timezone.utc


def _tail_offset(path: Path, max_bytes: int = 64 * 1024 * 1024) -> int:
    try:
        size = path.stat().st_size
    except Exception:
        return 0
    off = size - int(max_bytes)
    return off if off > 0 else 0


def _read_tail_lines(path: Path, max_lines: int = 250000, max_bytes: int = 64 * 1024 * 1024) -> List[str]:
    try:
        off = _tail_offset(path, max_bytes=max_bytes)
        dq: Deque[str] = deque(maxlen=max(1, int(max_lines)))
        with open(path, 'r', encoding='utf-8', errors='ignore') as fh:
            fh.seek(off)
            if off > 0:
                try:
                    fh.readline()
                except Exception:
                    pass
            for line in fh:
                dq.append(line.rstrip('\n'))
        return list(dq)
    except Exception:
        return []


def _parse_utc_ts(value: Any) -> Optional[datetime]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    t2 = s[:-1] + '+00:00' if s.endswith('Z') else s
    try:
        dt = datetime.fromisoformat(t2)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        pass
    for fmt in ('%Y-%m-%dT%H:%M:%S', '%Y-%m-%d %H:%M:%S'):
        try:
            return datetime.strptime(s.replace('Z', ''), fmt).replace(tzinfo=timezone.utc)
        except Exception:
            pass
    return None


def _parse_local_bracket_ts(line: str) -> Optional[datetime]:
    try:
        if not line.startswith('['):
            return None
        i = line.find(']')
        if i <= 1:
            return None
        dt_local = datetime.strptime(line[1:i], '%Y-%m-%d %H:%M:%S').replace(tzinfo=_LOCAL_TZ)
        return dt_local.astimezone(timezone.utc)
    except Exception:
        return None


def _extract_json_after_tag(line: str, tag: str) -> Optional[Dict[str, Any]]:
    try:
        i = line.find(tag)
        if i == -1:
            return None
        payload = line[i + len(tag):].strip()
        if not payload:
            return None
        obj = json.loads(payload)
        return obj if isinstance(obj, dict) else None
    except Exception:
        return None


def _extract_pid_from_text(line: str) -> str:
    patterns = (
        r'\bpid=([A-Z0-9-]+)\b',
        r'\bproduct_id=([A-Z0-9-]+)\b',
        r'\b([A-Z0-9]+-USD)\b',
    )
    for pat in patterns:
        m = re.search(pat, line, flags=re.IGNORECASE)
        if m:
            try:
                return str(m.group(1) or '').upper()
            except Exception:
                return ''
    return ''


def _extract_price_from_text(line: str) -> Optional[float]:
    patterns = (
        r'\bfill_price=([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)\b',
        r'\bavg_price=([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)\b',
        r'\bavg_px=([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)\b',
        r'\bprice=([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)\b',
        r'\bpx=([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)\b',
    )
    for pat in patterns:
        m = re.search(pat, line, flags=re.IGNORECASE)
        if m:
            try:
                v = float(m.group(1))
                if v > 0:
                    return v
            except Exception:
                pass
    return None


def _extract_float_key_from_text(line: str, key: str) -> Optional[float]:
    try:
        m = re.search(rf'\b{re.escape(str(key))}=([0-9]*\.?[0-9]+(?:e-?[0-9]+)?)\b', line, flags=re.IGNORECASE)
        if not m:
            return None
        return float(m.group(1))
    except Exception:
        return None


def _extract_text_key_from_text(line: str, key: str) -> str:
    try:
        m = re.search(rf'\b{re.escape(str(key))}=([^\s]+)', line, flags=re.IGNORECASE)
        if not m:
            return ''
        return str(m.group(1) or '').strip()
    except Exception:
        return ''


def _extract_pipe_list_key_from_text(line: str, key: str) -> List[str]:
    raw = _extract_text_key_from_text(line, key)
    if not raw:
        return []
    try:
        return [str(x).strip() for x in str(raw).split('|') if str(x).strip()]
    except Exception:
        return []


def _load_tdi_rows_for_replay(path: Path, max_lines: int = 350000, max_bytes: int = 128 * 1024 * 1024) -> Tuple[Dict[str, Dict[str, Any]], Optional[float]]:
    buckets: Dict[str, Dict[str, Any]] = {}
    latest_epoch: Optional[float] = None
    if not path.exists():
        return buckets, latest_epoch
    for line in _read_tail_lines(path, max_lines=max_lines, max_bytes=max_bytes):
        try:
            d = json.loads(line)
        except Exception:
            continue
        if not isinstance(d, dict):
            continue
        pid = str(d.get('product_id') or '').strip().upper()
        ts = _parse_utc_ts(d.get('ts'))
        if not pid or ts is None:
            continue
        price = d.get('price')
        try:
            price_v = float(price) if price is not None else None
        except Exception:
            price_v = None
        reasons = d.get('top_reasons') if isinstance(d.get('top_reasons'), list) else []
        row = {
            'product_id': pid,
            'ts': ts.replace(microsecond=0).isoformat().replace('+00:00', 'Z'),
            'ts_dt': ts,
            'ts_epoch': ts.timestamp(),
            'price': price_v,
            'tdi_score': d.get('tdi_score'),
            'tdi_trough': d.get('tdi_trough'),
            'tdi_momentum': d.get('tdi_momentum'),
            'tdi_liquidity': d.get('tdi_liquidity'),
            'tdi_spread': d.get('tdi_spread'),
            'tdi_pressure': d.get('tdi_pressure'),
            'top_reasons': list(reasons),
            'ctx_stack': list(d.get('ctx_stack')) if isinstance(d.get('ctx_stack'), list) else [],
        }
        bucket = buckets.setdefault(pid, {'times': [], 'rows': []})
        bucket['times'].append(row['ts_epoch'])
        bucket['rows'].append(row)
        latest_epoch = row['ts_epoch'] if latest_epoch is None else max(latest_epoch, row['ts_epoch'])
    return buckets, latest_epoch


def _match_target_tp(tp_pct: Any) -> Optional[str]:
    try:
        tp = round(float(tp_pct), 1)
    except Exception:
        return None
    for target in (2.0, 6.2, 10.0):
        if abs(tp - target) <= 0.11:
            return f'{target:.1f}'
    return None


def _load_cycle_best_by_tp(cycle_dir: Path) -> Dict[str, Dict[str, Dict[str, Any]]]:
    out: Dict[str, Dict[str, Dict[str, Any]]] = {'2.0': {}, '6.2': {}, '10.0': {}}
    if not cycle_dir.exists():
        return out
    zips = sorted(cycle_dir.glob('mm25_cycle_map_*.zip'), key=lambda p: p.stat().st_mtime, reverse=True)
    have: set[str] = set()
    for zpath in zips:
        try:
            with zipfile.ZipFile(zpath, 'r') as zf:
                if 'cycle_structure_meta.json' not in zf.namelist():
                    continue
                with zf.open('cycle_structure_meta.json') as fh:
                    meta = json.load(io.TextIOWrapper(fh, encoding='utf-8'))
                tkey = _match_target_tp((meta or {}).get('tp_pct'))
                if not tkey or tkey in have:
                    continue
                mapping: Dict[str, Dict[str, Any]] = {}
                if 'cycle_structure_best_intervals.csv' in zf.namelist():
                    with zf.open('cycle_structure_best_intervals.csv') as fh:
                        text = io.TextIOWrapper(fh, encoding='utf-8')
                        for row in csv.DictReader(text):
                            pid = str(row.get('product_id') or '').upper()
                            if not pid:
                                continue
                            mapping[pid] = {
                                'interval': str(row.get('interval') or ''),
                                'current_phase': str(row.get('current_phase') or ''),
                                'qualified_troughs': int(_dec(row.get('qualified_troughs'), 0)),
                            }
                elif 'cycle_structure_best_intervals.json' in zf.namelist():
                    with zf.open('cycle_structure_best_intervals.json') as fh:
                        rows = json.load(io.TextIOWrapper(fh, encoding='utf-8'))
                    if isinstance(rows, list):
                        for row in rows:
                            if not isinstance(row, dict):
                                continue
                            pid = str(row.get('product_id') or '').upper()
                            if not pid:
                                continue
                            mapping[pid] = {
                                'interval': str(row.get('interval') or ''),
                                'current_phase': str(row.get('current_phase') or ''),
                                'qualified_troughs': int(_dec(row.get('qualified_troughs'), 0)),
                            }
                out[tkey] = mapping
                have.add(tkey)
                if len(have) == 3:
                    break
        except Exception:
            continue
    return out


def _build_decision_replay_snapshot(max_events: int = 1200, refresh_sec: float = 60.0) -> Dict[str, Any]:
    activity_path = DEFAULT_ACTIVITY_PATH
    tdi_path = DEFAULT_TDI_PATH
    cycle_dir = DEFAULT_CYCLE_DIR
    act_mtime = activity_path.stat().st_mtime if activity_path.exists() else None
    tdi_mtime = tdi_path.stat().st_mtime if tdi_path.exists() else None
    cycle_sig = None
    try:
        cycle_sig = tuple((p.name, p.stat().st_mtime) for p in sorted(cycle_dir.glob('mm25_cycle_map_*.zip'))[-6:])
    except Exception:
        cycle_sig = None
    now = time.time()
    cache = DECISION_REPLAY_CACHE
    if (
        cache.get('payload')
        and (now - float(cache.get('built_at') or 0.0) < float(refresh_sec))
        and cache.get('activity_mtime') == act_mtime
        and cache.get('tdi_mtime') == tdi_mtime
        and cache.get('cycle_sig') == cycle_sig
    ):
        return cache['payload']

    rows_out: List[Dict[str, Any]] = []
    if not activity_path.exists() or not tdi_path.exists():
        payload = {'generated_at': _now_utc_iso(), 'rows': rows_out}
        cache.update({'built_at': now, 'activity_mtime': act_mtime, 'tdi_mtime': tdi_mtime, 'cycle_sig': cycle_sig, 'payload': payload})
        return payload

    tdi_buckets, latest_epoch = _load_tdi_rows_for_replay(tdi_path)
    cycle_by_tp = _load_cycle_best_by_tp(cycle_dir)
    lines = _read_tail_lines(activity_path, max_lines=max(50000, int(max_events) * 1500), max_bytes=64 * 1024 * 1024)

    events: List[Dict[str, Any]] = []
    paper_by_pid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    exit_by_pid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)

    for line in lines:
        ts_dt = _parse_local_bracket_ts(line)
        if ts_dt is None:
            continue
        ts_iso = ts_dt.replace(microsecond=0).isoformat().replace('+00:00', 'Z')
        if '[PAPER_BUY_SIGNAL]' in line:
            d = _extract_json_after_tag(line, '[PAPER_BUY_SIGNAL]') or {}
            pid = str(d.get('product_id') or '').strip().upper()
            if not pid:
                continue
            evt = {
                'event': 'PAPER_BUY_SIGNAL',
                'product_id': pid,
                'ts_dt': ts_dt,
                'ts_epoch': ts_dt.timestamp(),
                'ts': ts_iso,
                'price': (_dec(d.get('price'), None) if d.get('price') is not None else None),
                'signal_score': d.get('bot_score', d.get('signal_score')),
                'blocked_by': d.get('blocked_by'),
                'trough_pct': d.get('trough_pct'),
                'trough_n': d.get('trough_n'),
                'ctx_stack': list(d.get('ctx_stack')) if isinstance(d.get('ctx_stack'), list) else [],
                'cycle_phase': str(d.get('cycle_phase') or d.get('ctx_phase') or ''),
            }
            events.append(evt)
            paper_by_pid[pid].append(evt)
        elif '[BUY_OK]' in line:
            pid = _extract_pid_from_text(line)
            if not pid:
                continue
            evt = {
                'event': 'BUY_OK',
                'product_id': pid,
                'ts_dt': ts_dt,
                'ts_epoch': ts_dt.timestamp(),
                'ts': ts_iso,
                'price': _extract_price_from_text(line),
                'tdi_score': _extract_float_key_from_text(line, 'tdi_score'),
                'tdi_min_buy_score': _extract_float_key_from_text(line, 'tdi_min_buy_score'),
                'top_drivers': _extract_pipe_list_key_from_text(line, 'tdi_top_reasons'),
                'ctx_stack': _extract_pipe_list_key_from_text(line, 'ctx_stack'),
                'cycle_phase': _extract_text_key_from_text(line, 'cycle_phase'),
            }
            events.append(evt)
        if ('[TP]' in line) or ('[SL]' in line) or ('[SELL_OK]' in line):
            pid = _extract_pid_from_text(line)
            if pid:
                exit_by_pid[pid].append({
                    'event': 'TP' if '[TP]' in line else ('SL' if '[SL]' in line else 'SELL_OK'),
                    'ts_dt': ts_dt,
                    'ts_epoch': ts_dt.timestamp(),
                    'ts': ts_iso,
                    'price': _extract_price_from_text(line),
                })

    events.sort(key=lambda x: x['ts_epoch'])
    for pid in list(paper_by_pid.keys()):
        paper_by_pid[pid].sort(key=lambda x: x['ts_epoch'])
    for pid in list(exit_by_pid.keys()):
        exit_by_pid[pid].sort(key=lambda x: x['ts_epoch'])

    if latest_epoch is not None:
        cutoff = latest_epoch - (36 * 3600.0)
        events = [e for e in events if e['ts_epoch'] >= cutoff]
    events = events[-max(1, int(max_events) * 2):]

    def _find_matched_signal(pid: str, entry_epoch: float) -> Optional[Dict[str, Any]]:
        seq = paper_by_pid.get(pid) or []
        if not seq:
            return None
        times = [e['ts_epoch'] for e in seq]
        idx = bisect_right(times, entry_epoch) - 1
        if idx < 0:
            return None
        evt = seq[idx]
        if entry_epoch - evt['ts_epoch'] > 1800.0:
            return None
        return evt

    for evt in events:
        pid = evt['product_id']
        bucket = tdi_buckets.get(pid)
        if not bucket:
            continue
        times = bucket['times']
        rows = bucket['rows']
        idx = bisect_right(times, evt['ts_epoch']) - 1
        if idx < 0:
            continue
        prior = rows[idx]
        entry_price = evt.get('price')
        if entry_price is None:
            entry_price = prior.get('price')
        try:
            entry_price_f = float(entry_price) if entry_price is not None else None
        except Exception:
            entry_price_f = None

        matched_signal = _find_matched_signal(pid, evt['ts_epoch']) if evt['event'] == 'BUY_OK' else None
        signal_ts = matched_signal.get('ts') if matched_signal else (evt['ts'] if evt['event'] == 'PAPER_BUY_SIGNAL' else None)
        signal_type = evt['event']
        entry_ts = evt['ts'] if evt['event'] == 'BUY_OK' else None
        ctx_stack = list(evt.get('ctx_stack') or [])
        if not ctx_stack:
            ctx_stack = list(prior.get('ctx_stack') or []) if isinstance(prior.get('ctx_stack'), list) else []
        cycle_phase = str(evt.get('cycle_phase') or '')
        event_top_drivers = list(evt.get('top_drivers') or [])

        def _future_row_after(epoch_target: float) -> Optional[Dict[str, Any]]:
            j = bisect_right(times, epoch_target - 1e-9)
            if j >= len(rows):
                return None
            return rows[j]

        outcomes: Dict[str, Optional[float]] = {}
        for label, minutes in (('1h_pct', 60.0), ('4h_pct', 240.0), ('24h_pct', 1440.0)):
            if entry_price_f is None or entry_price_f <= 0:
                outcomes[label] = None
                continue
            fr = _future_row_after(evt['ts_epoch'] + (minutes * 60.0))
            if not fr or fr.get('price') in (None, 0):
                outcomes[label] = None
                continue
            try:
                outcomes[label] = round(((float(fr['price']) - entry_price_f) / entry_price_f) * 100.0, 8)
            except Exception:
                outcomes[label] = None

        coverage_minutes = 0.0
        if times:
            coverage_minutes = max(0.0, (times[-1] - evt['ts_epoch']) / 60.0)
        tp_outcomes: Dict[str, Dict[str, Any]] = {}
        for tkey, tval in (('2.0', 2.0), ('6.2', 6.2), ('10.0', 10.0)):
            best_meta = (cycle_by_tp.get(tkey) or {}).get(pid) or {}
            hit: Optional[bool] = None
            hit_minutes: Optional[int] = None
            if entry_price_f is not None and entry_price_f > 0:
                threshold = entry_price_f * (1.0 + (tval / 100.0))
                for fr in rows[idx + 1:]:
                    price_f = fr.get('price')
                    if price_f is None:
                        continue
                    try:
                        if float(price_f) >= threshold:
                            hit = True
                            hit_minutes = int(round((fr['ts_epoch'] - evt['ts_epoch']) / 60.0))
                            break
                    except Exception:
                        continue
                if hit is None:
                    hit = False if coverage_minutes >= 1440.0 else None
            tp_outcomes[tkey] = {
                'hit': hit,
                'time_to_hit_minutes': hit_minutes,
                'best_interval': str(best_meta.get('interval') or ''),
            }

        exit_ts = None
        exit_price = None
        if evt['event'] == 'BUY_OK':
            for ex in exit_by_pid.get(pid) or []:
                if ex['ts_epoch'] >= evt['ts_epoch']:
                    exit_ts = ex['ts']
                    exit_price = ex.get('price')
                    if exit_price is None:
                        fr = _future_row_after(ex['ts_epoch'])
                        exit_price = fr.get('price') if fr else None
                    break

        row = {
            'product_id': pid,
            'signal_type': signal_type,
            'signal_ts': signal_ts,
            'entry_ts': entry_ts,
            'entry_price': round(float(entry_price_f), 8) if entry_price_f is not None else None,
            'tdi_score_at_entry': evt.get('tdi_score') if evt.get('tdi_score') is not None else prior.get('tdi_score'),
            'tdi_min_buy_score_at_entry': evt.get('tdi_min_buy_score'),
            'cycle_phase_at_entry': cycle_phase,
            'top_drivers': event_top_drivers if event_top_drivers else list(prior.get('top_reasons') or []),
            'ctx_stack_at_entry': ctx_stack,
            'outcomes': outcomes,
            'tp_outcomes': tp_outcomes,
            'exit_price': round(float(exit_price), 8) if exit_price is not None else None,
            'exit_ts': exit_ts,
            'confidence': None,
            'sample_size': None,
        }
        rows_out.append(row)

    rows_out.sort(key=lambda r: max(_parse_utc_ts(r.get('entry_ts') or '') or datetime.fromtimestamp(0, tz=timezone.utc), _parse_utc_ts(r.get('signal_ts') or '') or datetime.fromtimestamp(0, tz=timezone.utc)), reverse=True)
    rows_out = rows_out[:max(1, int(max_events))]
    payload = {'generated_at': _now_utc_iso(), 'rows': rows_out}
    cache.update({'built_at': now, 'activity_mtime': act_mtime, 'tdi_mtime': tdi_mtime, 'cycle_sig': cycle_sig, 'payload': payload})
    return payload


def _pid_alive(pid: Optional[int]) -> bool:
    try:
        if not pid:
            return False
        if os.name == "nt":
            import ctypes  # type: ignore
            kernel32 = ctypes.windll.kernel32
            PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
            handle = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, int(pid))
            if not handle:
                return False
            code = ctypes.c_ulong()
            ok = kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
            kernel32.CloseHandle(handle)
            return bool(ok) and int(code.value) == 259
        else:
            os.kill(int(pid), 0)
            return True
    except Exception:
        return False


def _bot_status(settings: Dict[str, Any]) -> Tuple[str, Optional[int], Optional[float]]:
    ra_path = Path(str(settings.get("RUN_ACTIVE_PATH") or DEFAULT_RUN_ACTIVE_PATH))
    if not ra_path.is_absolute():
        ra_path = PROJECT_ROOT / ra_path
    obj = _read_json(ra_path) if ra_path.exists() else None
    pid = None
    age_sec = None
    if isinstance(obj, dict):
        try:
            pid = int(obj.get("pid") or 0) or None
        except Exception:
            pid = None
        try:
            mtime = ra_path.stat().st_mtime
            age_sec = max(0.0, time.time() - mtime)
        except Exception:
            age_sec = None
    return ("running" if _pid_alive(pid) else "stopped"), pid, age_sec


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
            # Some client versions may not support limit/cursor kwargs consistently.
            try:
                raw = fn(portfolio_uuid=pfid) if pfid else fn()
            except Exception:
                break
        except Exception:
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


def _account_value_parts(a: Dict[str, Any]) -> Tuple[float, float, float]:
    av = a.get("available_balance") or {}
    hold = a.get("hold") or {}
    bal = a.get("balance") or {}
    available = _dec(av.get("value") if isinstance(av, dict) else av, 0.0)
    hold_v = _dec(hold.get("value") if isinstance(hold, dict) else hold, 0.0)
    total = _dec(bal.get("value") if isinstance(bal, dict) else bal, available + hold_v)
    if total <= 0.0:
        total = available + hold_v
    return max(0.0, available), max(0.0, hold_v), max(0.0, total)


def _load_latest_tdi(path: Path, tail_lines: int = 40000, history_points: int = 240) -> Tuple[Dict[str, Dict[str, Any]], Dict[str, Deque[Dict[str, Any]]]]:
    latest: Dict[str, Dict[str, Any]] = {}
    history: Dict[str, Deque[Dict[str, Any]]] = defaultdict(lambda: deque(maxlen=max(10, int(history_points or 240))))
    if not path.exists():
        return latest, history
    try:
        with open(path, "r", encoding="utf-8") as fh:
            lines = fh.readlines()[-tail_lines:]
    except Exception:
        return latest, history
    for line in lines:
        try:
            row = json.loads(line)
        except Exception:
            continue
        pid = str(row.get("product_id") or "").upper()
        if not pid:
            continue
        ts = row.get("ts")
        try:
            score = _dec(row.get("tdi_score"), None)
        except Exception:
            score = None
        if score is None:
            continue
        latest[pid] = row
        history[pid].append({
            "ts": ts,
            "tdi": row.get("tdi_score"),
            "price": row.get("price"),
        })
    return latest, history


def _find_latest_cycle_zip(cycle_dir: Path) -> Optional[Path]:
    if not cycle_dir.exists():
        return None
    zips = sorted(cycle_dir.glob("mm25_cycle_map_*.zip"), key=lambda p: p.stat().st_mtime)
    return zips[-1] if zips else None


def _find_latest_ctx_cache(cycle_dir: Path) -> Optional[Path]:
    if not cycle_dir.exists():
        return None
    caches = sorted(cycle_dir.glob("cycle_ctx_cache_tp_*.json"), key=lambda p: p.stat().st_mtime)
    return caches[-1] if caches else None


def _cycle_confidence(row: Dict[str, Any]) -> int:
    tp = _dec(row.get("tp_hit_rate_pct"), 0.0)
    adv = _dec(row.get("adverse_first_rate_pct"), 0.0)
    both = _dec(row.get("both_same_rate_pct"), 0.0)
    troughs = _dec(row.get("qualified_troughs"), 0.0)
    bars = _dec(row.get("bars"), 0.0)
    confidence = tp - (adv * 0.5) - (both * 0.5)
    if str(row.get("source") or "") == "synthetic_from_1d":
        confidence -= 5.0
        if troughs < 4:
            confidence -= 5.0
    if bars < 24:
        confidence -= 10.0
    return int(max(0.0, min(100.0, round(confidence))))





def _granularity_for_backfill(tf: Optional[str]) -> int:
    tf_s = str(tf or "").strip().lower()
    if tf_s in {"1m", "5m"}:
        return 300
    if tf_s in {"15m", "30m"}:
        return 900
    if tf_s in {"1h", "2h", "4h"}:
        return 3600
    if tf_s in {"6h", "1d"}:
        return 21600
    return 86400


def _backfill_lookback_candles(tf: Optional[str]) -> int:
    tf_s = str(tf or "").strip().lower()
    if tf_s in {"1m", "5m", "15m", "30m"}:
        return 240
    if tf_s in {"1h", "2h", "4h"}:
        return 240
    if tf_s in {"6h", "1d"}:
        return 180
    return 120


def _fetch_exchange_candles(pid: str, start_dt: datetime, end_dt: datetime, granularity: int) -> List[List[float]]:
    base = f"https://api.exchange.coinbase.com/products/{pid}/candles"
    qs = urlencode({
        "start": start_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "end": end_dt.astimezone(timezone.utc).isoformat().replace("+00:00", "Z"),
        "granularity": str(int(granularity)),
    })
    req = Request(base + "?" + qs, headers={"User-Agent": "mm28-live-snapshot-writer"})
    with urlopen(req, timeout=25) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    rows: List[List[float]] = []
    for row in data if isinstance(data, list) else []:
        try:
            rows.append([
                int(row[0]),
                float(row[1]),
                float(row[2]),
                float(row[3]),
                float(row[4]),
                float(row[5]) if len(row) > 5 else 0.0,
            ])
        except Exception:
            continue
    rows.sort(key=lambda item: item[0])
    return rows


def _fetch_candles_backfill(pid: str, tf: Optional[str], as_of: Optional[datetime], count_hint: int = 240) -> List[List[float]]:
    if not pid:
        return []
    dt_end = as_of if isinstance(as_of, datetime) else datetime.now(timezone.utc)
    gran = _granularity_for_backfill(tf)
    count = max(60, min(300, int(count_hint or _backfill_lookback_candles(tf))))
    dt_start = dt_end - timedelta(seconds=int(gran * count))
    try:
        return _fetch_exchange_candles(pid, dt_start, dt_end, gran)
    except Exception:
        return []


def _points_from_candles(candles: List[List[float]]) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    for row in candles or []:
        try:
            ts_epoch = int(row[0])
            close_px = float(row[4])
        except Exception:
            continue
        points.append({
            "ts": datetime.fromtimestamp(ts_epoch, tz=timezone.utc).isoformat().replace("+00:00", "Z"),
            "tdi": None,
            "price": round(close_px, 8),
        })
    return points


def _backfill_history_payload_from_candles(pid: str, history_payload: Dict[str, Any], best_interval: Optional[str], as_of: Optional[datetime]) -> Dict[str, Any]:
    out = dict(history_payload or {})
    existing_points = list(out.get("points") or [])
    existing_price_points = sum(1 for p in existing_points if isinstance(p, dict) and p.get("price") is not None)
    if existing_price_points >= 20:
        return out
    candles = _fetch_candles_backfill(pid, best_interval, as_of, count_hint=_backfill_lookback_candles(best_interval))
    if not candles:
        return out
    candle_points = _points_from_candles(candles)
    if not candle_points:
        return out

    existing_by_ts: Dict[str, Dict[str, Any]] = {}
    for item in existing_points:
        if not isinstance(item, dict):
            continue
        ts = _normalize_iso_or_none(item.get("ts"))
        if ts:
            existing_by_ts[ts] = dict(item)

    merged_points: List[Dict[str, Any]] = []
    for item in candle_points:
        ts = _normalize_iso_or_none(item.get("ts"))
        base = dict(item)
        if ts and ts in existing_by_ts:
            prev = existing_by_ts[ts]
            if prev.get("tdi") is not None:
                base["tdi"] = prev.get("tdi")
            if prev.get("price") is not None:
                base["price"] = prev.get("price")
        merged_points.append(base)

    out["points"] = merged_points
    out["price"] = [p.get("price") for p in merged_points if p.get("price") is not None]
    out["tdi"] = [p.get("tdi") for p in merged_points if p.get("tdi") is not None]
    out["count"] = len(merged_points)
    out["first_ts"] = merged_points[0].get("ts") if merged_points else None
    out["last_ts"] = merged_points[-1].get("ts") if merged_points else None
    dt_first = _parse_utc_ts(out.get("first_ts"))
    dt_last = _parse_utc_ts(out.get("last_ts"))
    if dt_first is not None and dt_last is not None:
        try:
            out["window_min"] = round(max(0.0, (dt_last - dt_first).total_seconds() / 60.0), 4)
        except Exception:
            pass
    out["has_price_history"] = bool(out.get("price"))
    out["has_tdi_history"] = bool(out.get("tdi"))
    prev_prov = str(out.get("provenance") or "").strip()
    out["provenance"] = "tdi_snapshots.jsonl+coinbase_exchange_candles" if prev_prov and prev_prov != "coinbase_exchange_candles" else "coinbase_exchange_candles"
    return out


def _backfill_structure_age_from_candles(pid: str, best_interval: Optional[str], current_phase: Any, existing: Dict[str, Any], current_price: Any, as_of: Optional[datetime]) -> Dict[str, Any]:
    out = dict(existing or {})
    has_anchors = bool(out.get("last_crest_ts")) or bool(out.get("last_trough_ts")) or (out.get("range_pct") is not None)
    if has_anchors:
        return out
    candles = _fetch_candles_backfill(pid, best_interval, as_of, count_hint=_backfill_lookback_candles(best_interval))
    if len(candles) < 8:
        return out

    trough_row = None
    crest_row = None
    try:
        trough_row = min(candles, key=lambda row: float(row[1]))
        crest_row = max(candles, key=lambda row: float(row[2]))
    except Exception:
        return out

    trough_ts = datetime.fromtimestamp(int(trough_row[0]), tz=timezone.utc).isoformat().replace("+00:00", "Z") if trough_row else None
    crest_ts = datetime.fromtimestamp(int(crest_row[0]), tz=timezone.utc).isoformat().replace("+00:00", "Z") if crest_row else None
    trough_price = round(float(trough_row[1]), 8) if trough_row else None
    crest_price = round(float(crest_row[2]), 8) if crest_row else None

    range_abs = None
    range_pct = None
    if crest_price is not None and trough_price is not None:
        try:
            range_abs = float(crest_price) - float(trough_price)
            if float(trough_price) > 0:
                range_pct = (range_abs / float(trough_price)) * 100.0
        except Exception:
            range_abs = None
            range_pct = None

    days_since_last_crest = _days_since_iso(crest_ts, as_of)
    days_since_last_trough = _days_since_iso(trough_ts, as_of)
    anchor_type = _phase_anchor_type(current_phase)
    anchor_days = days_since_last_trough if anchor_type == "trough" else days_since_last_crest if anchor_type == "crest" else None
    last_swing_type = None
    last_swing_ts = None
    if crest_ts and trough_ts:
        if _parse_utc_ts(crest_ts) >= _parse_utc_ts(trough_ts):
            last_swing_type = "crest"
            last_swing_ts = crest_ts
        else:
            last_swing_type = "trough"
            last_swing_ts = trough_ts

    out.update({
        "phase_day": _phase_day_from_anchor(anchor_days),
        "days_since_last_crest": round(days_since_last_crest, 4) if days_since_last_crest is not None else None,
        "days_since_last_trough": round(days_since_last_trough, 4) if days_since_last_trough is not None else None,
        "current_phase": str(current_phase or "") or out.get("current_phase"),
        "last_crest_ts": crest_ts,
        "last_trough_ts": trough_ts,
        "last_crest_price": crest_price,
        "last_trough_price": trough_price,
        "range_abs": round(float(range_abs), 8) if range_abs is not None else None,
        "range_pct": round(float(range_pct), 4) if range_pct is not None else None,
        "last_swing_type": last_swing_type,
        "last_swing_ts": last_swing_ts,
        "source_interval": str(best_interval or "") or out.get("source_interval"),
        "provenance": "candles_backfill",
        "sample_count": len(candles),
        "sample_strength": _sample_strength_from_count(len(candles)),
        "confidence_band": _confidence_band_from_count(len(candles)),
    })

    price_now = _float_or_none(current_price)
    if price_now is not None and crest_price is not None and price_now > 0:
        try:
            out["potential_to_next_crest_pct"] = round(((float(crest_price) - float(price_now)) / float(price_now)) * 100.0, 4)
            out["next_crest_est_price"] = crest_price
        except Exception:
            out["potential_to_next_crest_pct"] = None
            out["next_crest_est_price"] = crest_price
    elif crest_price is not None:
        out["potential_to_next_crest_pct"] = None
        out["next_crest_est_price"] = crest_price

    return out

def _load_cycle_map(cycle_dir: Path) -> Dict[str, Any]:
    def _entry_from_row(row: Dict[str, Any]) -> Dict[str, Any]:
        return {
            "tf": str(row.get("interval") or row.get("tf") or ""),
            "score": int(round(_dec(row.get("tp_hit_rate_pct", row.get("score")), 0.0))),
            "confidence": int(round(_dec(row.get("confidence"), _cycle_confidence(row)))),
            "phase": row.get("current_phase") or row.get("phase") or "",
            "bars": int(_dec(row.get("bars"), 0)),
            "qualified_troughs": int(_dec(row.get("qualified_troughs"), 0)),
            "source": row.get("source") or "",
            "avg_rebound_pct": _dec(row.get("avg_rebound_pct"), 0.0),
            "avg_drawdown_pct": _dec(row.get("avg_drawdown_pct"), 0.0),
            "median_min_to_tp": _dec(row.get("median_min_to_tp"), 0.0),
            "trough_to_crest_med_min": _dec(row.get("trough_to_crest_med_min"), 0.0),
            "crest_to_crest_med_min": _dec(row.get("crest_to_crest_med_min"), 0.0),
            "note": row.get("note") or "",
        }

    zpath = _find_latest_cycle_zip(cycle_dir)
    cpath = _find_latest_ctx_cache(cycle_dir)
    per_coin: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    best: Dict[str, Dict[str, Any]] = {}
    swings: Dict[str, Dict[str, List[Dict[str, Any]]]] = defaultdict(lambda: defaultdict(list))
    meta: Dict[str, Any] = {}

    if zpath:
        try:
            with zipfile.ZipFile(zpath, "r") as zf:
                if "cycle_structure_meta.json" in zf.namelist():
                    with zf.open("cycle_structure_meta.json") as fh:
                        try:
                            meta_obj = json.load(io.TextIOWrapper(fh, encoding="utf-8"))
                            if isinstance(meta_obj, dict):
                                meta = meta_obj
                        except Exception:
                            meta = {}
                if "cycle_structure_per_coin.csv" in zf.namelist():
                    with zf.open("cycle_structure_per_coin.csv") as fh:
                        text = io.TextIOWrapper(fh, encoding="utf-8")
                        for row in csv.DictReader(text):
                            pid = str(row.get("product_id") or "").upper()
                            if not pid:
                                continue
                            per_coin[pid].append(_entry_from_row(row))
                if "cycle_structure_best_intervals.csv" in zf.namelist():
                    with zf.open("cycle_structure_best_intervals.csv") as fh:
                        text = io.TextIOWrapper(fh, encoding="utf-8")
                        for row in csv.DictReader(text):
                            pid = str(row.get("product_id") or "").upper()
                            if pid:
                                best[pid] = row
                if "cycle_structure_swings.csv" in zf.namelist():
                    with zf.open("cycle_structure_swings.csv") as fh:
                        text = io.TextIOWrapper(fh, encoding="utf-8")
                        for row in csv.DictReader(text):
                            pid = str(row.get("product_id") or "").upper()
                            tf = str(row.get("interval") or row.get("tf") or "")
                            swing_type = str(row.get("type") or "").strip().lower()
                            ts_utc = _normalize_iso_or_none(row.get("ts_utc"))
                            if not pid or not tf or not swing_type or not ts_utc:
                                continue
                            swings[pid][tf].append({
                                "type": swing_type,
                                "ts_utc": ts_utc,
                                "price": _float_or_none(row.get("price")),
                                "source": str(row.get("source") or ""),
                                "swing_idx": int(_dec(row.get("swing_idx"), 0)),
                            })
        except Exception:
            per_coin = defaultdict(list)
            best = {}
            swings = defaultdict(lambda: defaultdict(list))
            meta = {}

    if cpath:
        try:
            obj = _read_json(cpath) or {}
            cache_all = obj.get("all_rows") if isinstance(obj, dict) else {}
            cache_best = obj.get("best_rows") if isinstance(obj, dict) else {}
            if isinstance(cache_all, dict):
                for pid, rows in cache_all.items():
                    pid_u = str(pid or "").upper()
                    if not pid_u or not isinstance(rows, list):
                        continue
                    merged_by_tf: Dict[str, Dict[str, Any]] = {}
                    for entry in per_coin.get(pid_u, []):
                        tf = str(entry.get("tf") or "")
                        if tf:
                            merged_by_tf[tf] = dict(entry)
                    for row in rows:
                        if not isinstance(row, dict):
                            continue
                        entry = _entry_from_row(row)
                        tf = str(entry.get("tf") or "")
                        if not tf:
                            continue
                        if tf not in merged_by_tf or int(entry.get("confidence") or 0) >= int(merged_by_tf[tf].get("confidence") or 0):
                            merged_by_tf[tf] = entry
                    if merged_by_tf:
                        per_coin[pid_u] = list(merged_by_tf.values())
            if isinstance(cache_best, dict):
                for pid, row in cache_best.items():
                    pid_u = str(pid or "").upper()
                    if pid_u and isinstance(row, dict) and pid_u not in best:
                        best[pid_u] = dict(row)
        except Exception:
            pass

    for pid, tf_map in list(swings.items()):
        for tf, rows in list(tf_map.items()):
            rows.sort(key=lambda item: (str(item.get("ts_utc") or ""), int(item.get("swing_idx") or 0)))

    for pid, rows in list(per_coin.items()):
        rows.sort(key=lambda r: (-int(r.get("confidence") or 0), -int(r.get("score") or 0), str(r.get("tf") or "")))
        if pid not in best and rows:
            best[pid] = {
                "product_id": pid,
                "interval": rows[0].get("tf"),
                "current_phase": rows[0].get("phase"),
                "tp_hit_rate_pct": rows[0].get("score"),
                "confidence": rows[0].get("confidence"),
            }

    default_tp_pct = _dec((meta or {}).get("tp_pct"), None)

    return {
        "zip": str(zpath) if zpath else None,
        "ctx_cache": str(cpath) if cpath else None,
        "meta": meta,
        "default_tp_pct": default_tp_pct,
        "per_coin": dict(per_coin),
        "best": best,
        "swings": {pid: dict(tf_map) for pid, tf_map in swings.items()},
    }



def _latest_feed(latest_tdi: Dict[str, Dict[str, Any]], cycle_map: Dict[str, Any], limit: int = 20) -> List[Dict[str, Any]]:
    rows = sorted(latest_tdi.values(), key=lambda r: str(r.get("ts") or ""), reverse=True)
    out: List[Dict[str, Any]] = []
    for row in rows[:limit]:
        pid = str(row.get("product_id") or "").upper()
        symbol = pid.split("-", 1)[0]
        comps = []
        for k in row.get("top_reasons") or []:
            kk = str(k)
            val = row.get(f"tdi_{kk}")
            if val is not None:
                comps.append(f"{kk[:3]}={int(round(_dec(val, 0))):d}")
        ctx_entries = cycle_map.get("per_coin", {}).get(pid, [])[:3]
        ctx = " | ".join([f"{e.get('tf')}^{int(e.get('confidence') or 0)}" for e in ctx_entries]) or "--"
        out.append({
            "ts": row.get("ts") or _now_utc_iso(),
            "symbol": symbol,
            "line": f"{symbol} TDI={int(round(_dec(row.get('tdi_score'), 0)))} {' '.join(comps)} ctx={ctx}".strip(),
        })
    return out


def _mark_prices(client: Any, product_ids: List[str], latest_tdi: Dict[str, Dict[str, Any]]) -> Tuple[Dict[str, Optional[float]], List[str]]:
    prices: Dict[str, Optional[float]] = {}
    skipped: List[str] = []
    product_ids = [str(x).upper() for x in product_ids if x]
    if not product_ids:
        return prices, skipped
    fn = getattr(client, "get_best_bid_ask", None)
    if callable(fn):
        for i in range(0, len(product_ids), 50):
            chunk = product_ids[i:i+50]
            try:
                raw = fn(product_ids=chunk)
                obj = _to_plain(raw)
                arr = obj.get("pricebooks") if isinstance(obj, dict) else []
                for pb in arr or []:
                    d = pb if isinstance(pb, dict) else _to_plain(pb)
                    pid = str(d.get("product_id") or "").upper()
                    bid = None
                    ask = None
                    bids = d.get("bids") or []
                    asks = d.get("asks") or []
                    if bids:
                        bid = _dec((bids[0] or {}).get("price") if isinstance(bids[0], dict) else None, None)
                    if asks:
                        ask = _dec((asks[0] or {}).get("price") if isinstance(asks[0], dict) else None, None)
                    mid = None
                    if bid is not None and ask is not None:
                        mid = (bid + ask) / 2.0
                    elif bid is not None:
                        mid = bid
                    elif ask is not None:
                        mid = ask
                    prices[pid] = mid
            except Exception:
                pass
    get_product = getattr(client, "get_product", None)
    for pid in product_ids:
        if pid in prices and prices[pid] is not None:
            continue
        try:
            if callable(get_product):
                obj = _to_plain(get_product(product_id=pid))
                price = _dec(obj.get("price"), None) if isinstance(obj, dict) else None
                if price is not None:
                    prices[pid] = price
                    continue
        except Exception:
            pass
        # fallback to latest tdi price
        row = latest_tdi.get(pid) or {}
        price = _dec(row.get("price"), None)
        if price is not None:
            prices[pid] = price
        else:
            prices[pid] = None
            skipped.append(pid)
    return prices, skipped


def _compute_account(client: Any, pfid: str, settings: Dict[str, Any], latest_tdi: Dict[str, Dict[str, Any]], cycle_map: Dict[str, Any]) -> Dict[str, Any]:
    accounts = list(_iter_accounts(client, pfid))
    cash_total = 0.0
    cash_available = 0.0
    positions_raw: List[Dict[str, Any]] = []
    for a in accounts:
        cur = str(a.get("currency") or a.get("asset") or "").upper()
        if not cur:
            continue
        avail, hold, total = _account_value_parts(a)
        if cur in STABLES:
            cash_total += total
            cash_available += avail
        else:
            if total > 0.0:
                positions_raw.append({"symbol": cur, "pair": f"{cur}-USD", "qty": total, "available": avail, "hold": hold})
    mark_prices, skipped = _mark_prices(client, [p["pair"] for p in positions_raw], latest_tdi)
    tp_pct = _dec(settings.get("TP_PCT"), 0.0)
    sl_pct = _dec(settings.get("SL_PCT"), 0.0)
    positions: List[Dict[str, Any]] = []
    equity = cash_total
    for p in positions_raw:
        pid = p["pair"]
        mark = mark_prices.get(pid)
        market_value = None if mark is None else round(p["qty"] * mark, 8)
        if market_value is not None:
            equity += market_value
        latest = latest_tdi.get(pid) or {}
        # Avg entry and pnl are intentionally left null in v1 unless derived elsewhere.
        pos = {
            "symbol": p["symbol"],
            "pair": pid,
            "side": "long",
            "qty": round(p["qty"], 8),
            "avg_entry": None,
            "mark_price": mark,
            "market_value_usd": market_value,
            "unrealized_pnl_usd": None,
            "unrealized_pnl_pct": None,
            "tp_price": None,
            "sl_price": None,
            "opened_at": None,
        }
        positions.append(pos)
    positions.sort(key=lambda x: (x.get("market_value_usd") is None, -(x.get("market_value_usd") or 0.0), x.get("pair") or ""))
    return {
        "account": {
            "equity_usd": round(equity, 8),
            "cash_usd": round(cash_available, 8),
            "positions_count": len(positions),
            "open_risk_count": len(positions),
        },
        "positions": positions,
        "skipped_marks": skipped,
    }


def _qualifier(tdi_row: Dict[str, Any], cycle_entries: List[Dict[str, Any]]) -> str:
    trough = _dec(tdi_row.get("tdi_trough"), 50.0)
    phase = str(cycle_entries[0].get("phase") or "") if cycle_entries else ""
    if trough >= 80 and ("lifting" in phase or "bottom" in phase):
        return "trough aligned"
    if "descending" in phase or "crest" in phase:
        return "crest risk"
    if trough >= 65:
        return "forming"
    return "mixed"


def _readiness(tdi_row: Dict[str, Any], cycle_entries: List[Dict[str, Any]]) -> str:
    score = _dec(tdi_row.get("tdi_score"), 0.0)
    phase = str(cycle_entries[0].get("phase") or "") if cycle_entries else ""
    if score >= 75 and ("lifting" in phase or "bottom" in phase or not phase):
        return "ready"
    if score >= 60:
        return "watch"
    return "blocked"


def _traction(tdi_row: Dict[str, Any]) -> str:
    reasons = [str(x) for x in (tdi_row.get("top_reasons") or []) if str(x)]
    return f"{reasons[0]}-led" if reasons else "mixed"


def _tf_phase_bucket(phase: str) -> str:
    p = str(phase or "").strip().lower()
    if not p:
        return "unknown"
    if "lift" in p or "ascend" in p or "trough" in p or "support" in p or "bottom" in p:
        return "supportive"
    if "mixed" in p or "neutral" in p:
        return "mixed"
    if "descend" in p or "crest" in p or "hostile" in p or "roll" in p:
        return "hostile"
    return "unknown"


def _tf_row_useful(row: Dict[str, Any]) -> bool:
    if not isinstance(row, dict):
        return False
    return (
        _dec(row.get("score"), 0.0) > 0.0
        or _dec(row.get("confidence"), 0.0) > 0.0
        or _dec(row.get("avg_rebound_pct"), 0.0) > 0.0
        or _dec(row.get("avg_drawdown_pct"), 0.0) > 0.0
    )


def _tf_metric_weighted(rows: List[Tuple[Dict[str, Any], float]], key: str) -> Optional[float]:
    num = 0.0
    den = 0.0
    for row, weight in rows:
        if not isinstance(row, dict):
            continue
        val = _dec(row.get(key), None)
        if val is None:
            continue
        num += float(val) * float(weight)
        den += float(weight)
    if den <= 0.0:
        return None
    return num / den


def _selector_phase(primary_phase: str, secondary_phase: str) -> str:
    pp = str(primary_phase or "").strip()
    sp = str(secondary_phase or "").strip()
    if pp and not sp:
        return pp
    if sp and not pp:
        return sp
    if pp == sp:
        return pp
    pb = _tf_phase_bucket(pp)
    sb = _tf_phase_bucket(sp)
    if pb == sb:
        return pp or sp
    return "mixed_derived"


def _selector_alias_row(base_tf: str, base_row: Dict[str, Any], target_tf: str, score_penalty: int, confidence_penalty: int, derivation_mode: str, source_note: str) -> Dict[str, Any]:
    score = max(0, int(round(_dec(base_row.get("score"), 0.0) - float(score_penalty))))
    confidence = max(0, int(round(_dec(base_row.get("confidence"), 0.0) - float(confidence_penalty))))
    return {
        "score": score,
        "confidence": confidence,
        "phase": str(base_row.get("phase") or "unknown"),
        "bars": int(_dec(base_row.get("bars"), 0.0)),
        "qualified_troughs": int(_dec(base_row.get("qualified_troughs"), 0.0)),
        "avg_rebound_pct": _dec(base_row.get("avg_rebound_pct"), 0.0),
        "avg_drawdown_pct": _dec(base_row.get("avg_drawdown_pct"), 0.0),
        "source_kind": "derived",
        "derived_from": [base_tf],
        "derivation_mode": derivation_mode,
        "source_note": source_note,
    }


def _extend_selector_timeframes(timeframes: Dict[str, Any]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for tf, row in (timeframes or {}).items():
        stf = str(tf or "").strip()
        if not stf or not isinstance(row, dict):
            continue
        cloned = dict(row)
        cloned.setdefault("source_kind", "live")
        cloned.setdefault("derived_from", [stf])
        cloned.setdefault("derivation_mode", "live")
        if "source_note" not in cloned:
            cloned["source_note"] = "live_backed_cycle_interval"
        out[stf] = cloned

    def _pick(tf_name: str, useful_only: bool = False) -> Optional[Dict[str, Any]]:
        row = out.get(tf_name)
        if not isinstance(row, dict):
            return None
        if useful_only and not _tf_row_useful(row):
            return None
        return row

    for target_tf, spec in SELECTOR_DERIVATION_RULES.items():
        existing = _pick(target_tf, useful_only=True)
        if existing is not None:
            continue

        primary_tf = str(spec.get("primary") or "")
        secondary_tf = str(spec.get("secondary") or "")
        mode = str(spec.get("mode") or "anchor")
        score_penalty = int(spec.get("score_penalty") or 0)
        confidence_penalty = int(spec.get("confidence_penalty") or 0)

        primary_row = _pick(primary_tf, useful_only=True)
        secondary_row = _pick(secondary_tf, useful_only=True)

        if mode == "blend" and primary_row is not None and secondary_row is not None:
            score = max(0, int(round((_dec(primary_row.get("score"), 0.0) * 0.6) + (_dec(secondary_row.get("score"), 0.0) * 0.4) - float(score_penalty))))
            confidence = max(0, int(round((_dec(primary_row.get("confidence"), 0.0) * 0.55) + (_dec(secondary_row.get("confidence"), 0.0) * 0.45) - float(confidence_penalty))))
            avg_rebound = _tf_metric_weighted([(primary_row, 0.65), (secondary_row, 0.35)], "avg_rebound_pct")
            avg_drawdown = _tf_metric_weighted([(primary_row, 0.65), (secondary_row, 0.35)], "avg_drawdown_pct")
            out[target_tf] = {
                "score": score,
                "confidence": confidence,
                "phase": _selector_phase(primary_row.get("phase"), secondary_row.get("phase")),
                "bars": int(max(_dec(primary_row.get("bars"), 0.0), _dec(secondary_row.get("bars"), 0.0))),
                "qualified_troughs": int(max(_dec(primary_row.get("qualified_troughs"), 0.0), _dec(secondary_row.get("qualified_troughs"), 0.0))),
                "avg_rebound_pct": float(avg_rebound) if avg_rebound is not None else 0.0,
                "avg_drawdown_pct": float(avg_drawdown) if avg_drawdown is not None else 0.0,
                "source_kind": "derived",
                "derived_from": [primary_tf, secondary_tf],
                "derivation_mode": "selector_blend",
                "source_note": f"derived_selector_interval_blend_from_{primary_tf}_{secondary_tf}",
            }
            continue

        base_tf = ""
        base_row = None
        if primary_row is not None:
            base_tf = primary_tf
            base_row = primary_row
        elif secondary_row is not None:
            base_tf = secondary_tf
            base_row = secondary_row
        else:
            raw_primary = _pick(primary_tf, useful_only=False)
            raw_secondary = _pick(secondary_tf, useful_only=False)
            if raw_primary is not None:
                base_tf = primary_tf
                base_row = raw_primary
            elif raw_secondary is not None:
                base_tf = secondary_tf
                base_row = raw_secondary

        if base_row is None:
            continue

        extra_conf_penalty = 0 if base_tf == primary_tf else 8
        extra_score_penalty = 0 if base_tf == primary_tf else 4
        out[target_tf] = _selector_alias_row(
            base_tf=base_tf,
            base_row=base_row,
            target_tf=target_tf,
            score_penalty=score_penalty + extra_score_penalty,
            confidence_penalty=confidence_penalty + extra_conf_penalty,
            derivation_mode="selector_alias",
            source_note=f"derived_selector_interval_alias_from_{base_tf}",
        )

    return out



def _pick_structure_age_source_interval(best_interval: Optional[str], cycle_map: Dict[str, Any], pid: str) -> Optional[str]:
    swings_by_tf = ((cycle_map or {}).get("swings") or {}).get(pid) or {}
    if best_interval and best_interval in swings_by_tf:
        return str(best_interval)
    if best_interval:
        best_base = str(best_interval)
        if best_base in swings_by_tf:
            return best_base
    entries = ((cycle_map or {}).get("per_coin") or {}).get(pid) or []
    for entry in entries:
        tf = str(entry.get("tf") or "")
        if tf and tf in swings_by_tf:
            return tf
    for tf in swings_by_tf.keys():
        if tf:
            return str(tf)
    return None


def _build_structure_age_for_coin(pid: str, best_interval: Optional[str], phase: Any, cycle_map: Dict[str, Any], as_of: Optional[datetime]) -> Dict[str, Any]:
    source_interval = _pick_structure_age_source_interval(best_interval, cycle_map, pid)
    swings_by_tf = ((cycle_map or {}).get("swings") or {}).get(pid) or {}
    rows = list((swings_by_tf.get(source_interval) or [])) if source_interval else []
    last_crest_ts = None
    last_trough_ts = None
    last_crest_price = None
    last_trough_price = None
    for row in rows:
        rtype = str(row.get("type") or "").strip().lower()
        ts_utc = _normalize_iso_or_none(row.get("ts_utc"))
        if not ts_utc:
            continue
        if rtype == "crest":
            last_crest_ts = ts_utc
            last_crest_price = _float_or_none(row.get("price"))
        elif rtype == "trough":
            last_trough_ts = ts_utc
            last_trough_price = _float_or_none(row.get("price"))

    days_since_last_crest = _days_since_iso(last_crest_ts, as_of)
    days_since_last_trough = _days_since_iso(last_trough_ts, as_of)
    anchor_type = _phase_anchor_type(phase)
    anchor_days = days_since_last_trough if anchor_type == "trough" else days_since_last_crest if anchor_type == "crest" else None

    range_abs = None
    range_pct = None
    if last_crest_price is not None and last_trough_price is not None:
        try:
            range_abs = float(last_crest_price) - float(last_trough_price)
            if float(last_trough_price) > 0:
                range_pct = (range_abs / float(last_trough_price)) * 100.0
        except Exception:
            range_abs = None
            range_pct = None

    last_swing_type = None
    last_swing_ts = None
    if rows:
        try:
            last_row = rows[-1]
            last_swing_type = str(last_row.get("type") or "").strip().lower() or None
            last_swing_ts = _normalize_iso_or_none(last_row.get("ts_utc"))
        except Exception:
            last_swing_type = None
            last_swing_ts = None

    return {
        "phase_day": _phase_day_from_anchor(anchor_days),
        "days_since_last_crest": round(days_since_last_crest, 4) if days_since_last_crest is not None else None,
        "days_since_last_trough": round(days_since_last_trough, 4) if days_since_last_trough is not None else None,
        "current_phase": str(phase or "") or None,
        "last_crest_ts": last_crest_ts,
        "last_trough_ts": last_trough_ts,
        "last_crest_price": round(float(last_crest_price), 8) if last_crest_price is not None else None,
        "last_trough_price": round(float(last_trough_price), 8) if last_trough_price is not None else None,
        "range_abs": round(float(range_abs), 8) if range_abs is not None else None,
        "range_pct": round(float(range_pct), 4) if range_pct is not None else None,
        "last_swing_type": last_swing_type,
        "last_swing_ts": last_swing_ts,
        "source_interval": source_interval,
        "provenance": "swing_map" if source_interval else None,
        "sample_count": len(rows) if rows else 0,
        "sample_strength": _sample_strength_from_count(len(rows) if rows else 0),
        "confidence_band": _confidence_band_from_count(len(rows) if rows else 0),
    }


def _build_cycle_default_recorded_tp_stats(cyc: List[Dict[str, Any]], target_pct: Optional[float]) -> Dict[str, Any]:
    if target_pct is None or not cyc:
        return {}
    best_row = None
    for row in cyc:
        if not isinstance(row, dict):
            continue
        if _dec(row.get("score"), None) is None and _dec(row.get("median_min_to_tp"), None) is None:
            continue
        best_row = row
        break
    if best_row is None:
        return {}
    observations = int(_dec(best_row.get("qualified_troughs"), 0))
    hit_rate = _dec(best_row.get("score"), None)
    hits = int(round((observations * float(hit_rate)) / 100.0)) if observations > 0 and hit_rate is not None else None
    median_min_to_hit = _dec(best_row.get("median_min_to_tp"), None)
    target_key = f"{float(target_pct):.1f}"
    return {
        target_key: {
            "hits": hits,
            "observations": observations if observations > 0 else 0,
            "hit_rate": round(float(hit_rate), 4) if hit_rate is not None else None,
            "median_time_to_hit_min": round(float(median_min_to_hit), 4) if median_min_to_hit is not None else None,
            "median_time_to_hit_hours": round(float(median_min_to_hit) / 60.0, 4) if median_min_to_hit is not None else None,
            "sample_count": observations if observations > 0 else 0,
            "sample_strength": _sample_strength_from_count(observations),
            "confidence_band": _confidence_band_from_count(observations),
            "best_interval": str(best_row.get("tf") or "") or None,
            "provenance": "cycle_map",
            "source": "cycle_map",
        }
    }


def _build_history_payload(hist: List[Dict[str, Any]]) -> Dict[str, Any]:
    points: List[Dict[str, Any]] = []
    for item in hist or []:
        if not isinstance(item, dict):
            continue
        ts_iso = _normalize_iso_or_none(item.get("ts"))
        tdi_val = _float_or_none(item.get("tdi"))
        price_val = _float_or_none(item.get("price"))
        if ts_iso is None and tdi_val is None and price_val is None:
            continue
        points.append({
            "ts": ts_iso,
            "tdi": round(float(tdi_val), 4) if tdi_val is not None else None,
            "price": round(float(price_val), 8) if price_val is not None else None,
        })

    first_ts = points[0].get("ts") if points else None
    last_ts = points[-1].get("ts") if points else None
    duration_min = None
    dt_first = _parse_utc_ts(first_ts)
    dt_last = _parse_utc_ts(last_ts)
    if dt_first is not None and dt_last is not None:
        try:
            duration_min = max(0.0, (dt_last - dt_first).total_seconds() / 60.0)
        except Exception:
            duration_min = None

    return {
        "tdi": [p.get("tdi") for p in points if p.get("tdi") is not None],
        "price": [p.get("price") for p in points if p.get("price") is not None],
        "points": points,
        "count": len(points),
        "first_ts": first_ts,
        "last_ts": last_ts,
        "window_min": round(float(duration_min), 4) if duration_min is not None else None,
        "has_tdi_history": any(p.get("tdi") is not None for p in points),
        "has_price_history": any(p.get("price") is not None for p in points),
        "provenance": "tdi_snapshots.jsonl",
    }



def _coin_rows(
    latest_tdi: Dict[str, Dict[str, Any]],
    history: Dict[str, Deque[Dict[str, Any]]],
    cycle_map: Dict[str, Any],
    positions: List[Dict[str, Any]],
    settings: Optional[Dict[str, Any]] = None,
    generated_at: Optional[str] = None,
) -> List[Dict[str, Any]]:
    pos_pairs = {str(p.get("pair") or "").upper() for p in positions}
    all_pairs = set(latest_tdi.keys()) | set(cycle_map.get("per_coin", {}).keys()) | set(cycle_map.get("best", {}).keys()) | pos_pairs
    out: List[Dict[str, Any]] = []
    settings = settings or {}
    as_of = _parse_utc_ts(generated_at) if generated_at else datetime.now(timezone.utc)
    threshold_used = _dec(settings.get("TDI_MIN_BUY_SCORE"), None)
    default_tp_pct = _dec(settings.get("TP_PCT"), cycle_map.get("default_tp_pct"))

    for pid in sorted(all_pairs):
        row = latest_tdi.get(pid) or {}
        cyc = cycle_map.get("per_coin", {}).get(pid, [])
        symbol = pid.split("-", 1)[0] if "-" in pid else pid
        components = {
            "liquidity": row.get("tdi_liquidity"),
            "trough": row.get("tdi_trough"),
            "pressure": row.get("tdi_pressure"),
            "spread": row.get("tdi_spread"),
            "momentum": row.get("tdi_momentum"),
        }
        timeframes: Dict[str, Any] = {}
        for e in cyc:
            tf = str(e.get("tf") or "")
            if not tf:
                continue
            timeframes[tf] = {
                "score": e.get("score"),
                "confidence": e.get("confidence"),
                "phase": e.get("phase"),
                "bars": e.get("bars"),
                "qualified_troughs": e.get("qualified_troughs"),
                "avg_rebound_pct": e.get("avg_rebound_pct"),
                "avg_drawdown_pct": e.get("avg_drawdown_pct"),
            }
        timeframes = _extend_selector_timeframes(timeframes)
        hist = list(history.get(pid) or [])
        best_interval = str(cyc[0].get("tf") or "") if cyc else None
        top_reasons = [str(x) for x in (row.get("top_reasons") or []) if str(x)]
        ctx_stack = [{"tf": e.get("tf"), "score": e.get("confidence"), "phase": e.get("phase")} for e in cyc[:3]]
        phase_now = cyc[0].get("phase") if cyc else None
        structure_age = _build_structure_age_for_coin(pid, best_interval, phase_now, cycle_map, as_of)
        structure_age = _backfill_structure_age_from_candles(pid, best_interval, phase_now, structure_age, row.get("price"), as_of)
        structure = {
            "phase": phase_now,
            "avg_drawdown_pct": cyc[0].get("avg_drawdown_pct") if cyc else None,
            "avg_rebound_pct": cyc[0].get("avg_rebound_pct") if cyc else None,
            "crest_to_crest_med_min": cyc[0].get("crest_to_crest_med_min") if cyc else None,
            "trough_to_crest_med_min": cyc[0].get("trough_to_crest_med_min") if cyc else None,
            "crest": structure_age.get("last_crest_price"),
            "trough": structure_age.get("last_trough_price"),
            "range_pct": structure_age.get("range_pct"),
            "range_abs": structure_age.get("range_abs"),
            "last_crest_ts": structure_age.get("last_crest_ts"),
            "last_trough_ts": structure_age.get("last_trough_ts"),
            "source_interval": structure_age.get("source_interval"),
            "potential_to_next_crest_pct": structure_age.get("potential_to_next_crest_pct"),
            "next_crest_est_price": structure_age.get("next_crest_est_price"),
            "note": cyc[0].get("note") if cyc else None,
        }
        history_payload = _build_history_payload(hist)
        history_payload = _backfill_history_payload_from_candles(pid, history_payload, best_interval, as_of)
        dominant_factors = _dominant_factors(components, top_reasons, limit=3)
        decision_why = {
            "tdi_score": row.get("tdi_score"),
            "threshold_used": round(float(threshold_used), 4) if threshold_used is not None else None,
            "top_reasons": top_reasons,
            "dominant_factors": dominant_factors,
            "best_interval": best_interval,
            "context_stack": ctx_stack,
            "qualifier": _qualifier(row, cyc),
            "traction": _traction(row),
        }
        coin = {
            "symbol": symbol,
            "pair": pid,
            "product_id": pid,
            "price": row.get("price"),
            "change_pct": row.get("g24h_pct"),
            "tdi": row.get("tdi_score"),
            "tdi_score": row.get("tdi_score"),
            "tdi_band": row.get("tdi_band"),
            "top_reasons": top_reasons,
            "best_interval": best_interval,
            "readiness": _readiness(row, cyc),
            "body": (cyc[0].get("phase") if cyc else row.get("tdi_band") or "unknown"),
            "traction": decision_why["traction"],
            "qualifier": decision_why["qualifier"],
            "ctx_stack": ctx_stack,
            "components": components,
            "timeframes": timeframes,
            "cycle_scores": [[str(e.get("tf") or "").upper(), e.get("confidence")] for e in cyc],
            "structure": structure,
            "structure_age": structure_age,
            "history": history_payload,
            "recorded_tp_stats": _build_cycle_default_recorded_tp_stats(cyc, default_tp_pct),
            "decision_why": decision_why,
            "replay": [],
        }
        out.append(coin)
    out.sort(key=lambda c: (_dec(c.get("tdi"), -1), _dec(c.get("price"), 0.0)), reverse=True)
    return out



def _tf_sort_key(tf: str) -> Tuple[int, str]:
    try:
        return (TIMEFRAME_ORDER.index(tf), tf)
    except ValueError:
        return (999, tf)


def _derive_structure_note(structure: Dict[str, Any]) -> str:
    note = str((structure or {}).get("note") or "").strip()
    if note:
        return note
    phase = str((structure or {}).get("phase") or "").strip()
    rebound = (structure or {}).get("avg_rebound_pct")
    drawdown = (structure or {}).get("avg_drawdown_pct")
    tr2cr = (structure or {}).get("trough_to_crest_med_min")
    cr2cr = (structure or {}).get("crest_to_crest_med_min")
    parts: List[str] = []
    if phase:
        parts.append(phase.replace("_", " "))
    try:
        if rebound is not None and drawdown is not None:
            parts.append(f"avg rebound {float(rebound):.2f}% / avg drawdown {float(drawdown):.2f}%")
        elif rebound is not None:
            parts.append(f"avg rebound {float(rebound):.2f}%")
        elif drawdown is not None:
            parts.append(f"avg drawdown {float(drawdown):.2f}%")
    except Exception:
        pass
    try:
        if tr2cr is not None and float(tr2cr) > 0:
            parts.append(f"trough→crest median {float(tr2cr):.0f} min")
        elif cr2cr is not None and float(cr2cr) > 0:
            parts.append(f"crest cadence {float(cr2cr):.0f} min")
    except Exception:
        pass
    return " | ".join([p for p in parts if p]).strip()



def _trim_replay_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    return {
        "product_id": row.get("product_id"),
        "signal_type": row.get("signal_type"),
        "signal_ts": row.get("signal_ts"),
        "entry_ts": row.get("entry_ts"),
        "entry_price": row.get("entry_price"),
        "tdi_score_at_entry": row.get("tdi_score_at_entry"),
        "tdi_min_buy_score_at_entry": row.get("tdi_min_buy_score_at_entry"),
        "cycle_phase_at_entry": row.get("cycle_phase_at_entry"),
        "top_drivers": row.get("top_drivers") or [],
        "ctx_stack_at_entry": row.get("ctx_stack_at_entry") or [],
        "outcomes": row.get("outcomes") or {},
        "tp_outcomes": row.get("tp_outcomes") or {},
        "exit_price": row.get("exit_price"),
        "exit_ts": row.get("exit_ts"),
        "confidence": row.get("confidence"),
        "sample_size": row.get("sample_size"),
    }


def _aggregate_replay_tp_stats(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    agg: Dict[str, Dict[str, Any]] = {}
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        tp_map = row.get("tp_outcomes") or {}
        if not isinstance(tp_map, dict):
            continue
        for target_key, outcome in tp_map.items():
            key = str(target_key or "").strip()
            if not key or not isinstance(outcome, dict):
                continue
            hit = outcome.get("hit")
            rec = agg.setdefault(key, {"hits": 0, "observations": 0, "times": []})
            if hit is True:
                rec["hits"] += 1
                rec["observations"] += 1
                t_hit = _dec(outcome.get("time_to_hit_minutes"), None)
                if t_hit is not None:
                    rec["times"].append(float(t_hit))
            elif hit is False:
                rec["observations"] += 1

    out: Dict[str, Any] = {}
    for key in sorted(agg.keys(), key=lambda item: float(item)):
        rec = agg[key]
        observations = int(rec.get("observations") or 0)
        hits = int(rec.get("hits") or 0)
        med = _median_or_none(rec.get("times") or [])
        out[key] = {
            "hits": hits,
            "observations": observations,
            "hit_rate": round((hits / observations) * 100.0, 4) if observations > 0 else None,
            "median_time_to_hit_min": round(float(med), 4) if med is not None else None,
            "median_time_to_hit_hours": round(float(med) / 60.0, 4) if med is not None else None,
            "sample_count": observations,
            "sample_strength": _sample_strength_from_count(observations),
            "confidence_band": _confidence_band_from_count(observations),
            "provenance": "decision_replay_snapshot.rows",
            "source": "replay",
        }
    return out


def _merge_recorded_tp_stats(existing_stats: Dict[str, Any], replay_stats: Dict[str, Any]) -> Dict[str, Any]:
    merged: Dict[str, Any] = {}
    for key in sorted(set((existing_stats or {}).keys()) | set((replay_stats or {}).keys()), key=lambda item: float(item)):
        if key in replay_stats and isinstance(replay_stats.get(key), dict):
            merged[key] = dict(replay_stats[key])
        elif key in existing_stats and isinstance(existing_stats.get(key), dict):
            merged[key] = dict(existing_stats[key])
    return merged


def _build_tp_lens_contracts(coin: Dict[str, Any], support_coin: Dict[str, Any], default_target_key: str) -> Tuple[Dict[str, Any], Optional[Dict[str, Any]]]:
    timeframes = coin.get("timeframes") if isinstance(coin.get("timeframes"), dict) else {}
    tp_support = support_coin.get("tp_support") if isinstance(support_coin, dict) else {}
    if not isinstance(tp_support, dict):
        return {}, None

    by_target: Dict[str, Any] = {}
    for target_key, support in tp_support.items():
        if not isinstance(support, dict):
            continue
        best_interval = str(support.get("best_interval") or "") or None
        source_kind = None
        if best_interval and isinstance(timeframes.get(best_interval), dict):
            source_kind = str((timeframes.get(best_interval) or {}).get("source_kind") or "live")
        fit_status = None
        state = str(support.get("state") or "").strip().lower()
        if state == "supported":
            fit_status = "fit"
        elif state == "watch":
            fit_status = "stretch"
        elif state:
            fit_status = "unsupported"
        interval_backing = "derived" if source_kind == "derived" else "live_backed" if source_kind else None
        support_intervals = [str(x) for x in (support.get("supporting_intervals") or []) if str(x)]
        confidence = _dec(support.get("confidence"), None)
        by_target[str(target_key)] = {
            "selected_target_pct": _dec(target_key, None),
            "best_interval": best_interval,
            "support_intervals": support_intervals,
            "nearest_interval": support.get("nearest_interval"),
            "confidence": confidence,
            "confidence_band": _confidence_band_from_score(confidence),
            "phase": support.get("phase"),
            "reason": support.get("reason"),
            "fit_status": fit_status,
            "fit_note": support.get("reason"),
            "interval_backing": interval_backing,
            "sample_count": len(support_intervals),
            "sample_strength": _sample_strength_from_count(len(support_intervals)),
            "provenance": "wm3_support_snapshot.coins[].tp_support",
        }

    default_block = None
    if default_target_key:
        if default_target_key in by_target:
            default_block = dict(by_target[default_target_key])
        else:
            default_block = {
                "selected_target_pct": _dec(default_target_key, None),
                "best_interval": None,
                "support_intervals": [],
                "nearest_interval": None,
                "confidence": None,
                "confidence_band": None,
                "phase": None,
                "reason": None,
                "fit_status": None,
                "fit_note": None,
                "interval_backing": None,
                "sample_count": 0,
                "sample_strength": "none",
                "provenance": "wm3_support_snapshot.coins[].tp_support",
            }
    return by_target, default_block


def _build_replay_proof(rows: List[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not rows:
        return None
    preferred = None
    for row in rows:
        if str(row.get("signal_type") or "").upper() == "BUY_OK":
            preferred = row
            break
    if preferred is None:
        preferred = rows[0]
    if not isinstance(preferred, dict):
        return None

    entry_context = _flatten_ctx_labels(preferred.get("ctx_stack_at_entry"))
    outcomes = preferred.get("outcomes") if isinstance(preferred.get("outcomes"), dict) else {}
    tp_outcomes_raw = preferred.get("tp_outcomes") if isinstance(preferred.get("tp_outcomes"), dict) else {}
    tp_outcomes: Dict[str, Any] = {}
    for key in sorted(tp_outcomes_raw.keys(), key=lambda item: float(item)):
        item = tp_outcomes_raw.get(key) or {}
        if not isinstance(item, dict):
            continue
        tp_outcomes[str(key)] = {
            "hit": item.get("hit"),
            "time_to_hit_min": item.get("time_to_hit_minutes"),
        }

    return {
        "signal_type": preferred.get("signal_type"),
        "signal_ts": preferred.get("signal_ts"),
        "entry_ts": preferred.get("entry_ts"),
        "entry_tdi": preferred.get("tdi_score_at_entry"),
        "threshold_at_entry": preferred.get("tdi_min_buy_score_at_entry"),
        "entry_interval": entry_context[0] if entry_context else None,
        "entry_context": entry_context,
        "top_reasons_at_entry": preferred.get("top_drivers") or [],
        "outcome_1h_pct": outcomes.get("1h_pct"),
        "outcome_4h_pct": outcomes.get("4h_pct"),
        "outcome_24h_pct": outcomes.get("24h_pct"),
        "tp_outcomes": tp_outcomes,
        "source_count": len(rows),
        "confidence": preferred.get("confidence"),
        "sample_count": preferred.get("sample_size"),
        "sample_strength": _sample_strength_from_count(preferred.get("sample_size") or 0),
        "confidence_band": _confidence_band_from_count(preferred.get("sample_size") or 0),
        "provenance": "decision_replay_snapshot.rows",
    }


def _augment_snapshot_contract_blocks(payload: Dict[str, Any], replay_payload: Dict[str, Any], support_payload: Dict[str, Any], settings: Dict[str, Any]) -> Dict[str, Any]:
    coins = payload.get("coins") if isinstance(payload, dict) else None
    if not isinstance(coins, list):
        return payload

    rows = replay_payload.get("rows") if isinstance(replay_payload, dict) else []
    replay_by_pid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if isinstance(rows, list):
        def _row_sort_key(r: Dict[str, Any]) -> str:
            return str(r.get("entry_ts") or r.get("signal_ts") or "")
        for row in rows:
            if not isinstance(row, dict):
                continue
            pid = str(row.get("product_id") or "").upper()
            if pid:
                replay_by_pid[pid].append(row)
        for pid, rws in replay_by_pid.items():
            rws.sort(key=_row_sort_key, reverse=True)

    support_by_pid: Dict[str, Dict[str, Any]] = {}
    if isinstance(support_payload, dict):
        for item in support_payload.get("coins") or []:
            if not isinstance(item, dict):
                continue
            pid = str(item.get("product_id") or "").upper()
            if pid:
                support_by_pid[pid] = item

    default_target_key = f"{_dec(settings.get('TP_PCT'), None):.1f}" if _dec(settings.get('TP_PCT'), None) is not None else ""
    for coin in coins:
        if not isinstance(coin, dict):
            continue
        pid = str(coin.get("product_id") or "").upper()
        rws = replay_by_pid.get(pid, [])
        replay_stats = _aggregate_replay_tp_stats(rws)
        existing_stats = coin.get("recorded_tp_stats") if isinstance(coin.get("recorded_tp_stats"), dict) else {}
        coin["recorded_tp_stats"] = _merge_recorded_tp_stats(existing_stats, replay_stats)

        support_coin = support_by_pid.get(pid) or {}
        tp_selector_by_target, tp_selector_default = _build_tp_selector_contracts(coin, support_coin, default_target_key)
        coin["tp_selector_by_target"] = tp_selector_by_target
        coin["tp_selector_default"] = tp_selector_default
        tp_lens_by_target, tp_lens_default = _build_tp_lens_contracts(coin, support_coin, default_target_key)
        coin["tp_lens_by_target"] = tp_lens_by_target
        coin["tp_lens_default"] = tp_lens_default
        coin["replay_proof"] = _build_replay_proof(rws)

    meta = payload.get("meta") if isinstance(payload, dict) else None
    if isinstance(meta, dict):
        meta["schema_version"] = "1.3.0"
        meta["default_tp_target_pct"] = _dec(settings.get("TP_PCT"), None)
        meta["tp_selector_formula_version"] = MM28_TP_SELECTOR_FORMULA_VERSION
        payload["meta"] = meta
    return payload


def _transparent_engine_context(settings: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "profile": str(settings.get("PROFILE") or settings.get("PORTFOLIO") or "") or None,
        "environment": "dry" if bool(settings.get("DRY", False)) else "live",
        "tp_target_pct": _float_or_none(settings.get("TP_PCT")),
        "supported_tp_targets": list(TP_TARGET_LADDER),
        "selector_timeframes": list(SELECTOR_TIMEFRAME_REQUESTED_ORDER),
        "rank_by_24h_pct": bool(settings.get("RANK_BY_24H_PCT", False)),
        "min_24h_pct": _float_or_none(settings.get("MIN_24H_PCT")),
        "trend_ticks": int(_dec(settings.get("TREND_TICKS"), 0)) if settings.get("TREND_TICKS") is not None else None,
        "trend_bps_min": _float_or_none(settings.get("TREND_BPS_MIN")),
        "min_dmid_bps": _float_or_none(settings.get("MIN_DMID_BPS")),
        "tdi_min_buy_score": _float_or_none(settings.get("TDI_MIN_BUY_SCORE")),
        "buy_confirm_ticks": int(_dec(settings.get("BUY_CONFIRM_TICKS"), 0)) if settings.get("BUY_CONFIRM_TICKS") is not None else None,
        "book_pressure_min": _float_or_none(settings.get("BOOK_PRESSURE_MIN")),
        "min_topbook_usd": _float_or_none(settings.get("MIN_TOPBOOK_USD")),
        "tick_sec": _float_or_none(settings.get("TICK_SEC")),
        "universe_mode": str(settings.get("UNIVERSE_MODE") or "") or None,
        "universe_top": int(_dec(settings.get("UNIVERSE_TOP"), 0)) if settings.get("UNIVERSE_TOP") is not None else None,
        "default_product_id": str(settings.get("DEFAULT_PRODUCT_ID") or "") or None,
        "tp_selector_formula_version": MM28_TP_SELECTOR_FORMULA_VERSION,
        "provenance": "run_settings.json",
    }



def _parse_text_kv_pairs(line: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    for match in re.finditer(r'\b([A-Za-z_]+)=([^\s]+)', line):
        try:
            out[str(match.group(1) or "").strip()] = str(match.group(2) or "").strip()
        except Exception:
            continue
    return out



def _transparent_result_label(event_type: str, pnl_pct: Optional[float]) -> Optional[str]:
    et = str(event_type or "").upper()
    if et == "TP":
        return "success"
    if et == "SL":
        return "loss"
    if et == "SELL_OK":
        if pnl_pct is None:
            return "closed"
        if pnl_pct > 0:
            return "success"
        if pnl_pct < 0:
            return "loss"
        return "flat"
    if et == "BUY_OK":
        return "opened"
    if et == "BUY_FAIL":
        return "rejected"
    return None



def _build_transparent_logging(payload: Dict[str, Any], settings: Dict[str, Any], max_events: int = 500, max_successes: int = 250, refresh_sec: float = 30.0) -> Dict[str, Any]:
    activity_path = DEFAULT_ACTIVITY_PATH
    act_mtime = activity_path.stat().st_mtime if activity_path.exists() else None
    now = time.time()
    cache = TRANSPARENT_LOG_CACHE
    if cache.get("payload") and (now - float(cache.get("built_at") or 0.0) < float(refresh_sec)) and cache.get("activity_mtime") == act_mtime:
        return cache.get("payload") or {}

    engine_context = _transparent_engine_context(settings)
    payload_out: Dict[str, Any] = {
        "generated_at": _now_utc_iso(),
        "engine_context": engine_context,
        "event_counts": {},
        "events": [],
        "success_events": [],
        "last_tick_diag": None,
        "history_scope_lines": 0,
        "provenance": "activity_ticker.log",
    }
    if not activity_path.exists():
        cache.update({"built_at": now, "activity_mtime": act_mtime, "payload": payload_out})
        return payload_out

    coin_by_pid: Dict[str, Dict[str, Any]] = {}
    for coin in payload.get("coins") or []:
        if isinstance(coin, dict):
            pid = str(coin.get("product_id") or "").upper()
            if pid:
                coin_by_pid[pid] = coin

    lines = _read_tail_lines(activity_path, max_lines=max(120000, int(max_events) * 400), max_bytes=64 * 1024 * 1024)
    counts: Dict[str, int] = defaultdict(int)
    events: List[Dict[str, Any]] = []
    success_events: List[Dict[str, Any]] = []
    last_tick_diag = None
    for line in lines:
        if "[tick_diag]" in line:
            last_tick_diag = line
        event_type = None
        for tag in ("BUY_OK", "BUY_FAIL", "SELL_OK", "TP", "SL"):
            if f"[{tag}]" in line:
                event_type = tag
                break
        if not event_type:
            continue
        counts[event_type] += 1
        ts_dt = _parse_local_bracket_ts(line)
        ts_iso = ts_dt.replace(microsecond=0).isoformat().replace("+00:00", "Z") if ts_dt is not None else None
        kv = _parse_text_kv_pairs(line)
        pid = _extract_pid_from_text(line) or None
        coin = coin_by_pid.get(str(pid or "").upper()) or {}
        structure = coin.get("structure") if isinstance(coin.get("structure"), dict) else {}
        pnl_pct = _float_or_none(kv.get("pnl_pct"))
        event = {
            "ts": ts_iso,
            "ts_local": line[1:20] if line.startswith("[") and len(line) >= 20 else None,
            "event_type": event_type,
            "product_id": pid,
            "oid": kv.get("oid"),
            "reason": kv.get("reason"),
            "src": kv.get("src"),
            "price": _extract_price_from_text(line),
            "entry_ref": _float_or_none(kv.get("entry_ref")),
            "exit_mid": _float_or_none(kv.get("exit_mid")),
            "tp": _float_or_none(kv.get("tp")),
            "sl": _float_or_none(kv.get("sl")),
            "pnl_pct": pnl_pct,
            "tdi_score": _float_or_none(kv.get("tdi_score")),
            "tdi_min_buy_score": _float_or_none(kv.get("tdi_min_buy_score")),
            "top_reasons": _extract_pipe_list_key_from_text(line, "tdi_top_reasons"),
            "current_best_interval": coin.get("best_interval") if isinstance(coin, dict) else None,
            "current_phase": structure.get("phase") if isinstance(structure, dict) else None,
            "current_readiness": coin.get("readiness") if isinstance(coin, dict) else None,
            "result_label": _transparent_result_label(event_type, pnl_pct),
            "goal_hit": True if event_type == "TP" else (True if event_type == "SELL_OK" and pnl_pct is not None and pnl_pct > 0 else False if event_type in ("SL", "SELL_OK") and pnl_pct is not None else None),
            "provenance": "activity_ticker.log",
        }
        events.append(event)
        if event.get("goal_hit") is True or event_type in ("TP", "SL"):
            success_events.append(dict(event))

    counts["events_total"] = len(events)
    counts["success_events_total"] = len(success_events)
    payload_out.update({
        "event_counts": dict(counts),
        "events": events[-max(1, int(max_events)):],
        "success_events": success_events[-max(1, int(max_successes)):],
        "last_tick_diag": last_tick_diag,
        "history_scope_lines": len(lines),
    })
    cache.update({"built_at": now, "activity_mtime": act_mtime, "payload": payload_out})
    return payload_out



def _augment_snapshot_for_wm3(payload: Dict[str, Any], replay_payload: Dict[str, Any]) -> Dict[str, Any]:
    coins = payload.get("coins") if isinstance(payload, dict) else None
    rows = replay_payload.get("rows") if isinstance(replay_payload, dict) else None
    replay_by_pid: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    if isinstance(rows, list):
        def _row_sort_key(r: Dict[str, Any]) -> str:
            return str(r.get("entry_ts") or r.get("signal_ts") or "")
        for r in rows:
            if not isinstance(r, dict):
                continue
            pid = str(r.get("product_id") or "").upper()
            if pid:
                replay_by_pid[pid].append(r)
        for pid, rws in replay_by_pid.items():
            rws.sort(key=_row_sort_key, reverse=True)

    if isinstance(coins, list):
        for coin in coins:
            if not isinstance(coin, dict):
                continue
            pid = str(coin.get("product_id") or "").upper()
            struct = coin.get("structure") if isinstance(coin.get("structure"), dict) else {}
            if struct:
                struct["note"] = _derive_structure_note(struct)
                coin["structure"] = struct
            tfs = coin.get("timeframes") if isinstance(coin.get("timeframes"), dict) else {}
            coin["available_timeframes"] = sorted(list(tfs.keys()), key=_tf_sort_key)
            rws = replay_by_pid.get(pid, [])
            coin["has_replay"] = bool(rws)
            coin["replay_count"] = len(rws)
            coin["replay"] = [_trim_replay_row(r) for r in rws[:8]]

    meta = payload.get("meta") if isinstance(payload, dict) else None
    if isinstance(meta, dict):
        meta["products_with_replay_count"] = len(replay_by_pid)
        meta["timeframe_history_available"] = False
        meta["timeframe_high_low_available"] = False
        payload["meta"] = meta
    return payload



def _build_wm3_support_snapshot(payload: Dict[str, Any], replay_payload: Dict[str, Any]) -> Dict[str, Any]:
    rows = replay_payload.get("rows") if isinstance(replay_payload, dict) else []
    replay_counts: Dict[str, int] = {}
    if isinstance(rows, list):
        for r in rows:
            if not isinstance(r, dict):
                continue
            pid = str(r.get("product_id") or "").upper()
            if pid:
                replay_counts[pid] = replay_counts.get(pid, 0) + 1

    internal_timeframe_order = list(TIMEFRAME_ORDER)
    internal_rank = {tf: idx for idx, tf in enumerate(internal_timeframe_order)}
    requested_selector_timeframes = list(SELECTOR_TIMEFRAME_REQUESTED_ORDER)
    requested_tp_targets = [float(v) for v in TP_TARGET_LADDER]

    actual_timeframes: set[str] = set()
    selector_live_backed: set[str] = set()
    selector_derived: set[str] = set()
    for coin in (payload.get("coins") or []):
        if not isinstance(coin, dict):
            continue
        tfs = coin.get("timeframes") if isinstance(coin.get("timeframes"), dict) else {}
        for tf, tfrow in tfs.items():
            stf = str(tf or "").strip()
            if not stf:
                continue
            actual_timeframes.add(stf)
            if stf in requested_selector_timeframes and isinstance(tfrow, dict):
                if str(tfrow.get("source_kind") or "live") == "derived":
                    selector_derived.add(stf)
                else:
                    selector_live_backed.add(stf)

    emitted_selector_timeframes = [tf for tf in requested_selector_timeframes if tf in actual_timeframes]
    selector_rank = {tf: idx for idx, tf in enumerate(emitted_selector_timeframes)}

    def _sort_internal_tfs(vals: List[str]) -> List[str]:
        vals = [str(v) for v in vals if v]
        return sorted(vals, key=lambda tf: (internal_rank.get(tf, 999), tf))

    def _selector_timeframes_for_coin(coin: Dict[str, Any]) -> List[str]:
        tfs = coin.get("timeframes") if isinstance(coin.get("timeframes"), dict) else {}
        return [tf for tf in emitted_selector_timeframes if tf in tfs]

    def _phase_bucket(phase: str) -> str:
        p = str(phase or "").strip().lower()
        if not p:
            return "unknown"
        if "lift" in p or "ascend" in p or "trough" in p or "support" in p or "bottom" in p:
            return "supportive"
        if "mixed" in p or "neutral" in p:
            return "mixed"
        if "descend" in p or "crest" in p or "hostile" in p or "roll" in p:
            return "hostile"
        return "unknown"

    def _build_tp_support(coin: Dict[str, Any]) -> Tuple[List[str], List[str], Dict[str, Any], Dict[str, str]]:
        tfs = coin.get("timeframes") if isinstance(coin.get("timeframes"), dict) else {}
        visible_targets: List[str] = []
        hidden_targets: List[str] = []
        visible_support: Dict[str, Any] = {}
        hidden_reasons: Dict[str, str] = {}

        for target in requested_tp_targets:
            target_key = f"{target:.1f}"
            candidates: List[Dict[str, Any]] = []
            nearest_tf = ""
            nearest_rebound = None

            for tf, tfrow in tfs.items():
                if not isinstance(tfrow, dict):
                    continue
                rebound = _dec(tfrow.get("avg_rebound_pct"), None)
                drawdown = _dec(tfrow.get("avg_drawdown_pct"), None)
                score = int(_dec(tfrow.get("score"), 0))
                confidence = int(_dec(tfrow.get("confidence"), 0))
                phase = str(tfrow.get("phase") or "")
                if rebound is None or rebound <= 0:
                    continue

                if nearest_rebound is None or rebound > nearest_rebound:
                    nearest_rebound = rebound
                    nearest_tf = str(tf)

                phase_bucket = _phase_bucket(phase)
                qualifies = rebound >= target and score > 0 and confidence > 0
                if not qualifies:
                    continue

                support_score = int(max(0, min(100, round((score * 0.55) + (confidence * 0.35) + (10 if phase_bucket == "supportive" else 0) - (10 if phase_bucket == "hostile" else 0)))))
                candidates.append({
                    "tf": str(tf),
                    "score": score,
                    "confidence": confidence,
                    "phase": phase,
                    "phase_bucket": phase_bucket,
                    "avg_rebound_pct": float(rebound),
                    "avg_drawdown_pct": float(drawdown) if drawdown is not None else None,
                    "support_score": support_score,
                })

            candidates = sorted(
                candidates,
                key=lambda r: (
                    -int(r.get("support_score") or 0),
                    -int(r.get("confidence") or 0),
                    -int(r.get("score") or 0),
                    internal_rank.get(str(r.get("tf") or ""), 999),
                ),
            )

            if candidates:
                best = candidates[0]
                state = "supported" if best["phase_bucket"] == "supportive" and best["score"] >= 80 and best["confidence"] >= 60 else "watch"
                reason = (
                    f'{best["tf"]} avg rebound {best["avg_rebound_pct"]:.2f}% >= target {target_key}%'
                    f' | phase {best["phase"] or "unknown"} | score {best["score"]} | confidence {best["confidence"]}'
                )
                visible_targets.append(target_key)
                visible_support[target_key] = {
                    "available": True,
                    "state": state,
                    "best_interval": best["tf"],
                    "phase": best["phase"],
                    "score": best["score"],
                    "confidence": best["confidence"],
                    "avg_rebound_pct": best["avg_rebound_pct"],
                    "avg_drawdown_pct": best["avg_drawdown_pct"],
                    "support_score": best["support_score"],
                    "supporting_intervals": _sort_internal_tfs([c["tf"] for c in candidates]),
                    "reason": reason,
                    "source_fields": ["timeframes", "best_interval", "ctx_stack"],
                    "nearest_interval": nearest_tf,
                    "nearest_avg_rebound_pct": float(nearest_rebound) if nearest_rebound is not None else None,
                }
            else:
                hidden_targets.append(target_key)
                if nearest_tf:
                    hidden_reasons[target_key] = (
                        f'no timeframe with nonzero score/confidence and avg_rebound_pct >= target {target_key}%'
                    )
                else:
                    hidden_reasons[target_key] = (
                        f'no timeframe rebound data currently available for target {target_key}%'
                    )

        return visible_targets, hidden_targets, visible_support, hidden_reasons

    coins_out: List[Dict[str, Any]] = []
    global_visible_targets: set[str] = set()
    for coin in (payload.get("coins") or []):
        if not isinstance(coin, dict):
            continue
        pid = str(coin.get("product_id") or "").upper()
        struct = coin.get("structure") if isinstance(coin.get("structure"), dict) else {}
        selector_tfs = _selector_timeframes_for_coin(coin)
        visible_targets, hidden_targets, visible_support, hidden_reasons = _build_tp_support(coin)
        global_visible_targets.update(visible_targets)
        timeframe_source_details = {
            tf: {
                "source_kind": str(((coin.get("timeframes") or {}).get(tf) or {}).get("source_kind") or "live"),
                "derived_from": list((((coin.get("timeframes") or {}).get(tf) or {}).get("derived_from") or [tf])),
                "derivation_mode": str(((coin.get("timeframes") or {}).get(tf) or {}).get("derivation_mode") or "live"),
                "source_note": str(((coin.get("timeframes") or {}).get(tf) or {}).get("source_note") or ""),
            }
            for tf in selector_tfs
        }
        coins_out.append({
            "product_id": pid,
            "available_timeframes": selector_tfs,
            "selector_timeframes": selector_tfs,
            "timeframe_source_details": timeframe_source_details,
            "canonical_timeframe_order": emitted_selector_timeframes,
            "timeframe_history_available": False,
            "timeframe_high_low_available": False,
            "has_replay": bool(replay_counts.get(pid, 0)),
            "replay_count": int(replay_counts.get(pid, 0)),
            "structure_note": str((struct or {}).get("note") or ""),
            "canonical_tp_relative_source": "tp_support",
            "tp_target_selection_available": True,
            "tp_relative_context_supported": True,
            "tp_relative_support_fields": ["tp_support", "best_interval", "timeframes", "ctx_stack"],
            "tp_targets": visible_targets,
            "hidden_tp_targets": hidden_targets,
            "tp_hidden_reasons": hidden_reasons,
            "tp_support": visible_support,
        })

    available_tp_targets = [f"{v:.1f}" for v in requested_tp_targets if f"{v:.1f}" in global_visible_targets]
    hidden_tp_targets = [f"{v:.1f}" for v in requested_tp_targets if f"{v:.1f}" not in global_visible_targets]

    return {
        "generated_at": _now_utc_iso(),
        "timeframe_selection": {
            "canonical_source": "coins[].timeframes",
            "requested_display_order": requested_selector_timeframes,
            "canonical_display_order": emitted_selector_timeframes,
            "internal_support_intervals": internal_timeframe_order,
            "live_backed_selector_intervals": [tf for tf in requested_selector_timeframes if tf in selector_live_backed],
            "derived_selector_intervals": [tf for tf in requested_selector_timeframes if tf in selector_derived],
            "full_history_available": False,
            "high_low_available": False,
            "notes": "Selector-facing timeframes are emitted through coins[].timeframes. Some longer windows are derived selector aliases/blends from real live-backed intervals and are marked per coin in timeframe_source_details. Internal support intervals may include additional ranges such as 30m/2h/4h for TP-fit analysis.",
        },
        "structure": {
            "note_mode": "derived_when_blank",
            "preferred_numeric_fields": [
                "structure.phase",
                "structure.avg_drawdown_pct",
                "structure.avg_rebound_pct",
                "structure.crest_to_crest_med_min",
                "structure.trough_to_crest_med_min",
            ],
        },
        "replay": {
            "source": "decision_replay_snapshot.rows",
            "products_with_replay": sorted(replay_counts.keys()),
            "replay_counts_by_product": replay_counts,
            "derive_from_unique_product_id": True,
        },
        "tp_relative": {
            "canonical_source": "coins[].tp_support",
            "support_fields": ["tp_support", "best_interval", "timeframes", "ctx_stack"],
            "dedicated_field_available": True,
            "selector_available": True,
            "ui_governance_allowed": {
                "main_scanner_tdi_interpretation": False,
                "readiness_state": True,
                "tp_relative_context_panel": True,
                "coin_detail_interval_fit": True,
                "scanner_ordering": True,
                "replay_interpretation": False,
            },
            "notes": "TP support is derived from real timeframe metrics (avg_rebound_pct, score, confidence, phase). It may drive readiness, TP-relative context, interval-fit, and selector ordering, but not main scanner TDI meaning or replay meaning.",
        },
        "tp_target_selection": {
            "available": True,
            "requested_tp_targets": [f"{v:.1f}" for v in requested_tp_targets],
            "available_tp_targets": available_tp_targets,
            "hidden_tp_targets": hidden_tp_targets,
            "canonical_source": "coins[].tp_support",
            "minimum_contract_available": True,
            "notes": "Targets are emitted only when at least one coin has a real interval with nonzero rebound, nonzero score/confidence, and avg_rebound_pct >= target. Strong supportive phases surface as state=supported; weaker or hostile-fit intervals remain visible as state=watch.",
        },
        "body_depth_tiers_available": False,
        "classification_available": False,
        "coins": coins_out,
    }


def build_snapshot() -> Dict[str, Any]:
    settings = _load_settings()
    profile = str(settings.get("PROFILE") or settings.get("PORTFOLIO") or "")
    pfid = str(os.environ.get("PFID") or settings.get("PFID") or "")
    status, pid, heartbeat_age = _bot_status(settings)

    tdi_latest, tdi_history = _load_latest_tdi(DEFAULT_TDI_PATH)
    cycle_map = _load_cycle_map(DEFAULT_CYCLE_DIR)

    client = get_client()
    acct = _compute_account(client, pfid, settings, tdi_latest, cycle_map)
    generated_at = _now_utc_iso()
    coins = _coin_rows(tdi_latest, tdi_history, cycle_map, acct["positions"], settings=settings, generated_at=generated_at)
    feed = _latest_feed(tdi_latest, cycle_map, limit=20)

    env_name = "dry" if bool(settings.get("DRY", False)) else "live"
    selected_pid = str(settings.get("DEFAULT_PRODUCT_ID") or "")
    selected_coin = selected_pid.split("-", 1)[0] if selected_pid else ""

    out = {
        "meta": {
            "schema_version": "1.2.0",
            "generated_at": generated_at,
            "source": "koko-bot",
            "environment": env_name,
            "portfolio": profile,
            "bot_status": status,
            "heartbeat_age_sec": round(float(heartbeat_age or 0.0), 2) if heartbeat_age is not None else None,
            "universe_count": int(settings.get("UNIVERSE_TOP") or 0),
            "selected_coin": selected_coin,
            "pfid": pfid,
            "run_pid": pid,
            "cycle_map_zip": cycle_map.get("zip"),
            "cycle_ctx_cache": cycle_map.get("ctx_cache"),
            "skipped_mark_products": acct.get("skipped_marks") or [],
        },
        "account": acct["account"],
        "feed": feed,
        "positions": acct["positions"],
        "coins": coins,
    }
    transparent_logging = _build_transparent_logging(out, settings)
    account_block = out.get("account") if isinstance(out.get("account"), dict) else {}
    account_block["transparent_logging"] = transparent_logging
    out["account"] = account_block
    meta_block = out.get("meta") if isinstance(out.get("meta"), dict) else {}
    history_counts = [int(((coin.get("history") or {}).get("count") or 0)) for coin in coins if isinstance(coin, dict)]
    meta_block["coin_history_available"] = any(count > 0 for count in history_counts)
    meta_block["coin_history_points_max"] = max(history_counts) if history_counts else 0
    meta_block["transparent_logging_available"] = True
    out["meta"] = meta_block
    return out




def write_snapshot(path: Path, tracked_path: Optional[Path] = None, replay_path: Optional[Path] = None, wm3_support_path: Optional[Path] = None) -> Tuple[Path, Optional[Path], Optional[Path], Optional[Path]]:
    settings = _load_settings()
    replay_payload = _build_decision_replay_snapshot()

    # Keep decision replay fresh even when account/API-backed snapshot work is
    # temporarily degraded (for example by Coinbase 429s).
    if replay_path is not None:
        with SNAPSHOT_LOCK:
            _write_json_atomic(replay_path, replay_payload)

    payload = build_snapshot()
    payload = _augment_snapshot_for_wm3(payload, replay_payload)
    wm3_support_payload = _build_wm3_support_snapshot(payload, replay_payload)
    wm3_support_payload = _augment_support_snapshot_selector_blocks(wm3_support_payload, payload, settings)
    payload = _augment_snapshot_contract_blocks(payload, replay_payload, wm3_support_payload, settings)
    tracked_payload = _build_tracked_account_snapshot(payload)

    with SNAPSHOT_LOCK:
        _write_json_atomic(path, payload)
        if tracked_path is not None:
            _write_json_atomic(tracked_path, tracked_payload)
        if wm3_support_path is not None:
            _write_json_atomic(wm3_support_path, wm3_support_payload)
    return path, tracked_path, replay_path, wm3_support_path


def main(argv: Optional[List[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="MM26 live snapshot writer (read-only sidecars)")
    ap.add_argument("--output", default=str(DEFAULT_OUTPUT), help="Output live snapshot path")
    ap.add_argument("--tracked-output", default=str(DEFAULT_TRACKED_OUTPUT), help="Output tracked account snapshot path")
    ap.add_argument("--decision-replay-output", default=str(DEFAULT_DECISION_REPLAY_OUTPUT), help="Output decision replay snapshot path")
    ap.add_argument("--wm3-support-output", default=str(DEFAULT_WM3_SUPPORT_OUTPUT), help="Output WM3 support snapshot path")
    ap.add_argument("--interval", type=float, default=5.0, help="Refresh interval seconds")
    ap.add_argument("--once", action="store_true", help="Write one snapshot and exit")
    args = ap.parse_args(argv)

    out = Path(args.output)
    if not out.is_absolute():
        out = PROJECT_ROOT / out

    tracked_out = Path(args.tracked_output)
    if not tracked_out.is_absolute():
        tracked_out = PROJECT_ROOT / tracked_out

    replay_out = Path(args.decision_replay_output)
    if not replay_out.is_absolute():
        replay_out = PROJECT_ROOT / replay_out

    wm3_support_out = Path(args.wm3_support_output)
    if not wm3_support_out.is_absolute():
        wm3_support_out = PROJECT_ROOT / wm3_support_out

    if args.once:
        path, tracked_path, replay_path, wm3_support_path = write_snapshot(out, tracked_out, replay_out, wm3_support_out)
        print(f"CREATED: {path}", flush=True)
        if tracked_path is not None:
            print(f"CREATED: {tracked_path}", flush=True)
        if replay_path is not None:
            print(f"CREATED: {replay_path}", flush=True)
        if wm3_support_path is not None:
            print(f"CREATED: {wm3_support_path}", flush=True)
        return 0

    print(f"LIVE SNAPSHOT WRITER -> {out}", flush=True)
    print(f"TRACKED ACCOUNT WRITER -> {tracked_out}", flush=True)
    print(f"DECISION REPLAY WRITER -> {replay_out}", flush=True)
    while True:
        try:
            path, tracked_path, replay_path, wm3_support_path = write_snapshot(out, tracked_out, replay_out, wm3_support_out)
            print(f"UPDATED: {path} @ {_now_utc_iso()}", flush=True)
            if tracked_path is not None:
                print(f"UPDATED: {tracked_path} @ {_now_utc_iso()}", flush=True)
            if replay_path is not None:
                print(f"UPDATED: {replay_path} @ {_now_utc_iso()}", flush=True)
            if wm3_support_path is not None:
                print(f"UPDATED: {wm3_support_path} @ {_now_utc_iso()}", flush=True)
        except KeyboardInterrupt:
            return 0
        except Exception as e:
            print(f"ERROR: {type(e).__name__}: {e}", flush=True)
        time.sleep(max(1.0, float(args.interval or 5.0)))


if __name__ == "__main__":
    raise SystemExit(main())
