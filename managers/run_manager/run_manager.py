# C:\ai_trading_bot_koko\managers\run_manager\run_manager.py
# v1.11.0 — maker-only, continuation-gated autobuys, dynamic universe wiring
# Guards: LIMIT-only; buys post_only=True; no reduce_only here.
# Gates: 24h gainer strength, short-horizon continuation confirmation,
#        spread/topbook sanity, and simple anti-overtrade protection.

from __future__ import annotations

import csv
import io
import json
import os
import sys
import time
import calendar
import socket
import subprocess
import threading
import uuid
import zipfile
import faulthandler
from collections import deque

from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# MM16_SL_GRACE
_LAST_BUY_TICK: Dict[str, int] = {}  # pid -> last BUY tick

# MM24_PAPER_BUY_SIGNAL (per-pid throttled log of would-buy signals blocked by constraints)
_PAPER_SIG_LAST_TICK: Dict[str, int] = {}  # pid -> last tick logged

_DRY_PNL_LOCK = threading.Lock()
_DRY_PNL_STATE: Dict[str, Any] = {"loaded": False, "open": {}, "summary": {}}



# MM24_TROUGH_GATE: rolling trough position gate using sampled mids (DRY-safe)
_TROUGH_SAMPLES: Dict[str, Any] = {}  # pid -> deque[(tick, mid_float)]
_TROUGH_LAST_SAMPLE_TICK: Dict[str, int] = {}  # pid -> last tick sampled

# MM24_ATTACHED_EXIT_SELL_OK: track attached TP/SL entries and emit SELL_OK when the base position disappears
# (exchange-managed exit; bot may not place a SELL order itself).
_ATTACHED_OPEN: Dict[str, Dict[str, Any]] = {}  # pid -> info dict
_ATTACHED_OPEN_LOCK = threading.Lock()

# MM25_INTERVAL_AWARE_TROUGH_CONTEXT: cache latest TP-matched cycle-map rows and keep a dynamic
# per-coin interval-confidence stack. This is DRY-only context; it does not touch LIVE execution.
_CYCLE_CTX_CACHE: Dict[str, Any] = {
    "src": "",
    "mtime": 0.0,
    "tp_pct": None,
    "loaded_at": 0.0,
    "best_rows": {},
    "all_rows": {},
    "meta": {},
}
_CYCLE_STACK_STATE: Dict[str, Any] = {}
_CYCLE_CTX_AUTO_BEST: Dict[str, Dict[str, Any]] = {}
_CYCLE_CTX_AUTO_ALL: Dict[str, List[Dict[str, Any]]] = {}
_CYCLE_AUTO_QUEUE: deque[str] = deque()
_CYCLE_AUTO_PENDING: set[str] = set()
_CYCLE_AUTO_FAIL_TS: Dict[str, float] = {}
_CYCLE_AUTO_CFG: Dict[str, Any] = {}
_CYCLE_AUTO_LOCK = threading.Lock()
_CYCLE_AUTO_THREAD: Optional[threading.Thread] = None
_CYCLE_CTX_PERSIST: Dict[str, Any] = {"tp_pct": None, "loaded_at": 0.0, "path": ""}

# Tape-quality memory is used to keep data-starved names from repeatedly polluting
# the dry campaign with pseudo-strategy rejects. This is DRY-safe input hygiene.
_TAPE_QUALITY_STATE: Dict[str, Any] = {}  # pid -> deque[dict]
_TAPE_U0_STREAK: Dict[str, int] = {}  # pid -> consecutive stale/empty tape ticks
_TAPE_U0_COOLDOWN_UNTIL: Dict[str, int] = {}  # pid -> tick until temporarily skipped
_TAPE_RECOVERY_STREAK: Dict[str, int] = {}  # pid -> consecutive healthy tape ticks after u0 starvation
_SYMBOL_RELIABILITY_STATE: Dict[str, Any] = {}  # pid -> deque[dict]
_SYMBOL_RELIABILITY_QUARANTINE_UNTIL: Dict[str, int] = {}  # pid -> tick until symbol is quarantined
_SYMBOL_RELIABILITY_QUARANTINE_REASON: Dict[str, str] = {}  # pid -> dominant infra reason family
_TDI_SNAPSHOT_FAILS: int = 0



def _pct_points(x: Any, default: float = 0.0) -> float:
    try:
        v = float(x)
        if 0.0 < abs(v) <= 1.0:
            v *= 100.0
        return float(v)
    except Exception:
        return float(default)


def _safe_float(v: Any, default: float = 0.0) -> float:
    try:
        return float(v)
    except Exception:
        return float(default)


def _safe_int(v: Any, default: int = 0) -> int:
    try:
        return int(v)
    except Exception:
        return int(default)


def _u_dyn_symbol_cohort(pid: str) -> str:
    try:
        if u_dyn and hasattr(u_dyn, "LAST_COHORT_BY_PID"):
            cohort = str((u_dyn.LAST_COHORT_BY_PID or {}).get(str(pid or "").strip().upper()) or "").strip().lower()
            if cohort:
                return cohort
    except Exception:
        pass
    return "standard"


def _u_dyn_symbol_quality(pid: str) -> float:
    try:
        if u_dyn and hasattr(u_dyn, "LAST_TAPE_QUALITY_BY_PID"):
            return float((u_dyn.LAST_TAPE_QUALITY_BY_PID or {}).get(str(pid or "").strip().upper(), 0.0) or 0.0)
    except Exception:
        pass
    return 0.0


def _tape_quality_history(pid: str, lookback_ticks: int) -> deque:
    hist = _TAPE_QUALITY_STATE.get(pid)
    maxlen = max(24, int(lookback_ticks) * 2)
    if not isinstance(hist, deque) or hist.maxlen != maxlen:
        hist = deque(list(hist or []), maxlen=maxlen)
        _TAPE_QUALITY_STATE[pid] = hist
    return hist


def _symbol_reliability_history(pid: str, lookback_ticks: int) -> deque:
    hist = _SYMBOL_RELIABILITY_STATE.get(pid)
    maxlen = max(32, int(lookback_ticks) * 2)
    if not isinstance(hist, deque) or hist.maxlen != maxlen:
        hist = deque(list(hist or []), maxlen=maxlen)
        _SYMBOL_RELIABILITY_STATE[pid] = hist
    return hist


def _reliability_reason_family(reason: Any) -> str:
    text = str(reason or "").strip().lower()
    if text.startswith("preq_q_"):
        text = text[len("preq_q_"):]
    if text in {"u0", "u0_now", "u0_cd", "preq_fresh"}:
        return "u0"
    if text == "preq_hist":
        return "hist"
    if text == "preq_tobq":
        return "tobq"
    if text == "preq_spread":
        return "spread"
    if text == "preq_press":
        return "press"
    return text or "infra"


def _symbol_reliability_snapshot(pid: str, cfg: Dict[str, Any], t: Optional[int] = None) -> Dict[str, Any]:
    lookback = max(12, _safe_int(cfg.get("SYMBOL_RELIABILITY_LOOKBACK_TICKS", 90), 90))
    hist = _symbol_reliability_history(pid, lookback)
    sample = list(hist)[-lookback:]
    n = len(sample)
    infra_rows = [row for row in sample if bool(row.get("infra"))]
    infra_hits = len(infra_rows)
    infra_counts: Dict[str, int] = {}
    for row in infra_rows:
        fam = _reliability_reason_family(row.get("reason"))
        infra_counts[fam] = int(infra_counts.get(fam, 0) or 0) + 1
    dominant_reason = ""
    dominant_hits = 0
    if infra_counts:
        dominant_reason, dominant_hits = sorted(
            infra_counts.items(),
            key=lambda kv: (int(kv[1] or 0), kv[0]),
            reverse=True,
        )[0]
    infra_share = (float(infra_hits) / float(n)) if n > 0 else 0.0
    dominant_share = (float(dominant_hits) / float(infra_hits)) if infra_hits > 0 else 0.0
    quarantine_until = _safe_int(_SYMBOL_RELIABILITY_QUARANTINE_UNTIL.get(pid, -1), -1)
    quarantined = bool(t is not None and quarantine_until >= int(t))
    quarantine_reason = str(_SYMBOL_RELIABILITY_QUARANTINE_REASON.get(pid, "") or dominant_reason or "").strip().lower()
    return {
        "symbol_reliability_sample_n": int(n),
        "symbol_reliability_infra_hits": int(infra_hits),
        "symbol_reliability_infra_share": float(infra_share),
        "symbol_reliability_dominant_reason": dominant_reason,
        "symbol_reliability_dominant_share": float(dominant_share),
        "symbol_quarantined": quarantined,
        "symbol_quarantine_until": int(quarantine_until),
        "symbol_quarantine_reason": quarantine_reason,
    }


def _record_symbol_reliability(
    pid: str,
    cfg: Dict[str, Any],
    t: int,
    reason: str,
    allowed: bool,
) -> Dict[str, Any]:
    lookback = max(12, _safe_int(cfg.get("SYMBOL_RELIABILITY_LOOKBACK_TICKS", 90), 90))
    hist = _symbol_reliability_history(pid, lookback)
    reason_text = str(reason or "").strip().lower()
    family = _reliability_reason_family(reason_text) if reason_text else ""
    # Bootstrap/history gaps and local u0 cooldown/freshness misses are transient gate states.
    # They should not accumulate as long-horizon infrastructure debt that later blocks eligibility.
    transient_noninfra_reasons = {"u0_now", "u0_cd", "preq_hist", "preq_fresh"}
    infra_family = "" if reason_text in transient_noninfra_reasons else family
    hist.append(
        {
            "tick": int(t),
            "allowed": bool(allowed),
            "infra": bool((not allowed) and infra_family),
            "reason": infra_family or reason_text or family,
        }
    )

    quarantine_until = _safe_int(_SYMBOL_RELIABILITY_QUARANTINE_UNTIL.get(pid, -1), -1)
    if quarantine_until >= 0 and int(t) > quarantine_until:
        _SYMBOL_RELIABILITY_QUARANTINE_UNTIL.pop(pid, None)
        _SYMBOL_RELIABILITY_QUARANTINE_REASON.pop(pid, None)

    snap = _symbol_reliability_snapshot(pid, cfg, t)
    if not bool(cfg.get("SYMBOL_RELIABILITY_QUARANTINE_ENABLED", True)):
        return snap

    min_samples = max(8, _safe_int(cfg.get("SYMBOL_RELIABILITY_MIN_SAMPLES", 16), 16))
    min_hits = max(4, _safe_int(cfg.get("SYMBOL_RELIABILITY_MIN_INFRA_HITS", 10), 10))
    max_share = max(0.35, min(0.95, _safe_float(cfg.get("SYMBOL_RELIABILITY_MAX_INFRA_SHARE", 0.58), 0.58)))
    quarantine_ticks = max(20, _safe_int(cfg.get("SYMBOL_RELIABILITY_QUARANTINE_TICKS", 180), 180))

    if (
        not bool(snap.get("symbol_quarantined"))
        and int(snap.get("symbol_reliability_sample_n", 0) or 0) >= min_samples
        and int(snap.get("symbol_reliability_infra_hits", 0) or 0) >= min_hits
        and float(snap.get("symbol_reliability_infra_share", 0.0) or 0.0) >= max_share
    ):
        q_reason = str(snap.get("symbol_reliability_dominant_reason") or family or "infra").strip().lower()
        _SYMBOL_RELIABILITY_QUARANTINE_UNTIL[pid] = int(t) + quarantine_ticks
        _SYMBOL_RELIABILITY_QUARANTINE_REASON[pid] = q_reason
        snap = _symbol_reliability_snapshot(pid, cfg, t)
    return snap


def _tape_quality_snapshot(pid: str, cfg: Dict[str, Any], t: Optional[int] = None) -> Dict[str, Any]:
    lookback = max(6, _safe_int(cfg.get("TAPE_QUALITY_LOOKBACK_TICKS", 18), 18))
    hist = _tape_quality_history(pid, lookback)
    sample = list(hist)[-lookback:]
    n = len(sample)
    latest = sample[-1] if sample else {}
    fresh_now = bool(sample[-1].get("fresh")) if sample else False
    fresh_ratio = (sum(1 for row in sample if row.get("fresh")) / float(n)) if n > 0 else 0.0
    spread_ok_ratio = (sum(1 for row in sample if row.get("spread_ok")) / float(n)) if n > 0 else 0.0
    press_ok_ratio = (sum(1 for row in sample if row.get("press_ok")) / float(n)) if n > 0 else 0.0
    top_ratio_avg = (sum(float(row.get("top_ratio", 0.0) or 0.0) for row in sample) / float(n)) if n > 0 else 0.0
    tob_usd_avg = (sum(float(row.get("tob_usd", 0.0) or 0.0) for row in sample) / float(n)) if n > 0 else 0.0
    cohort = str(sample[-1].get("cohort") or _u_dyn_symbol_cohort(pid) or "standard").strip().lower() if sample else _u_dyn_symbol_cohort(pid)
    quality_score = float(sample[-1].get("quality_score", _u_dyn_symbol_quality(pid)) or _u_dyn_symbol_quality(pid) or 0.0) if sample else _u_dyn_symbol_quality(pid)
    cooldown_until = _safe_int(_TAPE_U0_COOLDOWN_UNTIL.get(pid, -1), -1)
    u0_streak = _safe_int(_TAPE_U0_STREAK.get(pid, 0), 0)
    snap = {
        "fresh_now": fresh_now,
        "fresh_ratio": float(fresh_ratio),
        "spread_ok_ratio": float(spread_ok_ratio),
        "press_ok_ratio": float(press_ok_ratio),
        "top_ratio_avg": float(top_ratio_avg),
        "tob_usd_avg": float(tob_usd_avg),
        "current_top_ratio": float(latest.get("top_ratio", 0.0) or 0.0),
        "current_tob_usd": float(latest.get("tob_usd", 0.0) or 0.0),
        "current_spr_bps": float(latest.get("spr_bps", 0.0) or 0.0),
        "current_spread_ok": bool(latest.get("spread_ok", False)),
        "current_press": float(latest.get("press", 0.5) or 0.5),
        "current_press_ok": bool(latest.get("press_ok", False)),
        "sample_n": int(n),
        "u0_streak": int(u0_streak),
        "recovery_streak": int(_safe_int(_TAPE_RECOVERY_STREAK.get(pid, 0), 0)),
        "u0_cooldown": bool(t is not None and cooldown_until >= int(t)),
        "u0_cooldown_until": int(cooldown_until),
        "symbol_cohort": cohort or "standard",
        "symbol_quality_score": float(quality_score),
    }
    try:
        snap.update(_symbol_reliability_snapshot(pid, cfg, t))
    except Exception:
        pass
    return snap


def _record_tape_quality(pid: str, m: Optional[Dict[str, Any]], cfg: Dict[str, Any], t: int) -> Dict[str, Any]:
    if not isinstance(m, dict):
        return _tape_quality_snapshot(pid, cfg, t)

    lookback = max(6, _safe_int(cfg.get("TAPE_QUALITY_LOOKBACK_TICKS", 18), 18))
    min_topbook_usd = max(1.0, _safe_float(cfg.get("MIN_TOPBOOK_USD", 50.0), 50.0))
    max_spr_bps = max(1.0, _cfg_max_spr_bps(cfg))
    spread_frac_cap = max(0.20, _safe_float(cfg.get("TAPE_QUALITY_MAX_SPREAD_FRACTION", 0.75), 0.75))
    min_press = max(0.01, _safe_float(cfg.get("TAPE_QUALITY_MIN_PRESSURE", 0.08), 0.08))
    u0_streak_ticks = max(1, _safe_int(cfg.get("U0_REJECT_STREAK_TICKS", 3), 3))
    u0_cooldown_ticks = max(1, _safe_int(cfg.get("U0_SYMBOL_COOLDOWN_TICKS", 30), 30))
    recovery_clear_ticks = max(1, _safe_int(cfg.get("U0_RECOVERY_CLEAR_TICKS", 2), 2))
    recovery_clear_top_ratio = max(0.25, _safe_float(cfg.get("U0_RECOVERY_CLEAR_TOP_RATIO", 0.60), 0.60))
    recovery_require_press = bool(cfg.get("U0_RECOVERY_CLEAR_REQUIRE_PRESS", False))

    tob_usd = _safe_float(m.get("tob", m.get("tob_usd", 0.0)), 0.0)
    spr_bps = _safe_float(m.get("spr_bps", 0.0), 0.0)
    press = _safe_float(m.get("press", 0.5), 0.5)
    mid = _safe_float(m.get("mid", 0.0), 0.0)

    # Keep quote freshness separate from liquidity quality. A live quote with a
    # weak/zero top-of-book should fail the TOB gate, not be misclassified as a
    # stale-data `u0` event that poisons reliability and cooldown state.
    fresh = bool(mid > 0.0 and spr_bps >= 0.0)
    top_ratio = tob_usd / float(min_topbook_usd) if min_topbook_usd > 0.0 else 0.0
    spread_ok = bool(spr_bps <= (max_spr_bps * spread_frac_cap))
    press_ok = bool(press >= min_press)
    recovery_ok = bool(fresh and spread_ok and top_ratio >= recovery_clear_top_ratio and (press_ok or not recovery_require_press))
    cohort = _u_dyn_symbol_cohort(pid)
    quality_score = _u_dyn_symbol_quality(pid)

    hist = _tape_quality_history(pid, lookback)
    hist.append(
        {
            "tick": int(t),
            "fresh": bool(fresh),
            "top_ratio": float(top_ratio),
            "tob_usd": float(tob_usd),
            "spr_bps": float(spr_bps),
            "spread_ok": bool(spread_ok),
            "press_ok": bool(press_ok),
            "cohort": cohort,
            "quality_score": float(quality_score),
        }
    )

    if fresh:
        _TAPE_U0_STREAK[pid] = 0
        _TAPE_RECOVERY_STREAK[pid] = (_safe_int(_TAPE_RECOVERY_STREAK.get(pid, 0), 0) + 1) if recovery_ok else 0
    else:
        streak = _safe_int(_TAPE_U0_STREAK.get(pid, 0), 0) + 1
        _TAPE_U0_STREAK[pid] = streak
        _TAPE_RECOVERY_STREAK[pid] = 0
        if streak >= u0_streak_ticks:
            _TAPE_U0_COOLDOWN_UNTIL[pid] = max(_safe_int(_TAPE_U0_COOLDOWN_UNTIL.get(pid, -1), -1), int(t) + u0_cooldown_ticks)

    cooldown_until = _safe_int(_TAPE_U0_COOLDOWN_UNTIL.get(pid, -1), -1)
    if cooldown_until >= 0 and _safe_int(_TAPE_RECOVERY_STREAK.get(pid, 0), 0) >= recovery_clear_ticks:
        _TAPE_U0_COOLDOWN_UNTIL.pop(pid, None)
        _TAPE_U0_STREAK[pid] = 0
    elif fresh and cooldown_until >= 0 and int(t) > cooldown_until:
        _TAPE_U0_COOLDOWN_UNTIL.pop(pid, None)

    return _tape_quality_snapshot(pid, cfg, t)


def _market_flow_snapshot(
    cfg: Dict[str, Any],
    m: Optional[Dict[str, Any]],
    tape_info: Optional[Dict[str, Any]] = None,
    cycle_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    tape = dict(tape_info or {})
    cycle = dict(cycle_info or {})

    try:
        min_topbook_usd = max(1.0, float(cfg.get("MIN_TOPBOOK_USD", 50.0) or 50.0))
    except Exception:
        min_topbook_usd = 50.0
    try:
        max_spr_bps = max(1.0, float(_cfg_max_spr_bps(cfg)))
    except Exception:
        max_spr_bps = 60.0
    try:
        trend_floor = max(1.0, float(cfg.get("TREND_BPS_MIN", 1.0) or 1.0))
    except Exception:
        trend_floor = 1.0

    if isinstance(m, dict):
        tob_usd = _safe_float(m.get("tob", m.get("tob_usd", tape.get("current_tob_usd", 0.0))), 0.0)
        spr_bps = _safe_float(m.get("spr_bps", tape.get("current_spr_bps", 0.0)), 0.0)
        press = _safe_float(m.get("press", tape.get("current_press", 0.5)), 0.5)
        dmid_bps = _safe_float(m.get("dmid_bps", m.get("dmid", 0.0)), 0.0)
    else:
        tob_usd = _safe_float(tape.get("current_tob_usd", 0.0), 0.0)
        spr_bps = _safe_float(tape.get("current_spr_bps", 0.0), 0.0)
        press = _safe_float(tape.get("current_press", 0.5), 0.5)
        dmid_bps = 0.0

    fresh_now = bool(tape.get("fresh_now"))
    fresh_ratio = _safe_float(tape.get("fresh_ratio", 0.0), 0.0)
    quality_score = _safe_float(tape.get("symbol_quality_score", 0.0), 0.0)
    tob_ratio = tob_usd / float(min_topbook_usd) if min_topbook_usd > 0.0 else 0.0
    spread_health = max(0.0, 1.0 - min(1.0, spr_bps / max_spr_bps))
    press_health = max(0.0, min(1.0, press))
    momentum_push = max(0.0, min(1.0, dmid_bps / max(trend_floor * 4.0, 4.0)))
    pullback_cushion = max(0.0, 1.0 - min(1.0, abs(min(0.0, dmid_bps)) / max(trend_floor * 3.0, 3.0)))

    cycle_phase = str(cycle.get("phase") or "").strip().lower()
    cycle_allow = bool(cycle.get("allow"))
    cycle_block = bool(cycle.get("block"))
    bullish_cycle = cycle_phase in ("lifting_from_trough", "bottoming") or cycle_allow
    bearish_cycle = cycle_phase in ("descending_from_crest", "rolling_over") or cycle_block

    flow_score = (
        (18.0 if fresh_now else 0.0)
        + (fresh_ratio * 20.0)
        + (min(1.5, tob_ratio) / 1.5 * 18.0)
        + (spread_health * 14.0)
        + (press_health * 14.0)
        + (momentum_push * 10.0)
        + (pullback_cushion * 3.0)
        + (quality_score * 0.12)
    )
    if bullish_cycle:
        flow_score += 6.0
    if bearish_cycle:
        flow_score -= 8.0
    flow_score = max(0.0, min(100.0, flow_score))

    trend_up = dmid_bps >= max(1.0, trend_floor * 0.5)
    mild_pullback = dmid_bps >= -max(3.0, trend_floor * 1.5)
    tight_now = spr_bps <= max_spr_bps * 0.65
    book_live = tob_ratio >= 0.60
    pressure_live = press >= max(0.08, _safe_float(cfg.get("TAPE_QUALITY_MIN_PRESSURE", 0.08), 0.08))
    pressure_strong = press >= 0.18

    regime = "fragile"
    if flow_score >= 72.0 and trend_up and pressure_strong and book_live and tight_now:
        regime = "ride"
    elif flow_score >= 68.0 and bullish_cycle and mild_pullback and book_live and tight_now:
        regime = "pullback"
    elif flow_score >= 62.0 and trend_up and book_live:
        regime = "breakout"
    elif flow_score >= 55.0 and fresh_now and tight_now:
        regime = "float"

    soft_ready = regime in {"ride", "pullback", "breakout"} and flow_score >= _safe_float(
        cfg.get("FLOW_SURF_PREENTRY_MIN_SCORE", 68.0), 68.0
    )
    return {
        "flow_score": round(float(flow_score), 2),
        "flow_regime": regime,
        "flow_bullish_cycle": bool(bullish_cycle),
        "flow_bearish_cycle": bool(bearish_cycle),
        "flow_tob_ratio": float(tob_ratio),
        "flow_spread_health": round(float(spread_health * 100.0), 2),
        "flow_pressure_health": round(float(press_health * 100.0), 2),
        "flow_momentum_push": round(float(momentum_push * 100.0), 2),
        "flow_soft_ready": bool(soft_ready),
        "flow_current_book_live": bool(book_live),
        "flow_current_spread_live": bool(tight_now),
        "flow_current_press_live": bool(pressure_live),
    }


def _tape_recovery_override_allows(
    cfg: Dict[str, Any],
    tape_info: Optional[Dict[str, Any]],
    reason_family: str,
) -> bool:
    tape = dict(tape_info or {})
    family = _reliability_reason_family(reason_family)
    if family not in {"u0", "hist"}:
        return False
    if not bool(cfg.get("TAPE_RECOVERY_OVERRIDE_ENABLED", True)):
        return False
    if bool(tape.get("symbol_quarantined")) or not bool(tape.get("fresh_now")):
        return False

    min_fresh_ratio = max(0.35, min(0.95, _safe_float(cfg.get("TAPE_RECOVERY_OVERRIDE_MIN_FRESH_RATIO", 0.50), 0.50)))
    min_top_ratio = max(0.35, _safe_float(cfg.get("TAPE_RECOVERY_OVERRIDE_MIN_TOP_RATIO", 0.75), 0.75))
    min_quality = max(0.0, _safe_float(cfg.get("TAPE_RECOVERY_OVERRIDE_MIN_QUALITY", 55.0), 55.0))
    min_flow_score = max(0.0, _safe_float(cfg.get("TAPE_RECOVERY_OVERRIDE_MIN_FLOW_SCORE", 56.0), 56.0))
    bootstrap_min_samples = max(
        3,
        _safe_int(
            cfg.get(
                "TAPE_RECOVERY_OVERRIDE_MIN_SAMPLES",
                max(3, _safe_int(cfg.get("TAPE_QUALITY_MIN_SAMPLES", 6), 6) // 2),
            ),
            max(3, _safe_int(cfg.get("TAPE_QUALITY_MIN_SAMPLES", 6), 6) // 2),
        ),
    )

    if _safe_int(tape.get("sample_n", 0), 0) < bootstrap_min_samples:
        return False

    fresh_ratio = _safe_float(tape.get("fresh_ratio", 0.0), 0.0)
    top_ratio = max(_safe_float(tape.get("current_top_ratio", 0.0), 0.0), _safe_float(tape.get("top_ratio_avg", 0.0), 0.0))
    quality_score = _safe_float(tape.get("symbol_quality_score", 0.0), 0.0)
    flow_score = _safe_float(tape.get("flow_score", 0.0), 0.0)
    recovery_streak = _safe_int(tape.get("recovery_streak", 0), 0)

    if fresh_ratio < min_fresh_ratio or top_ratio < min_top_ratio:
        return False
    if not bool(tape.get("current_spread_ok", False)):
        return False
    if quality_score < min_quality or flow_score < min_flow_score:
        return False
    if family == "u0" and bool(tape.get("u0_cooldown")) and recovery_streak < 1:
        return False
    return True


def _preentry_tape_gate_allows(
    cfg: Dict[str, Any],
    pid: str,
    m: Optional[Dict[str, Any]],
    t: int,
    tape_info: Optional[Dict[str, Any]] = None,
    tdi_payload: Optional[Dict[str, Any]] = None,
    cycle_payload: Optional[Dict[str, Any]] = None,
) -> tuple[bool, str, Dict[str, Any]]:
    tape = dict(tape_info or _record_tape_quality(pid, m, cfg, t) or {})
    if not bool(cfg.get("TAPE_QUALITY_PREENTRY_ENABLED", True)):
        return True, "", tape

    def _reject(reason: str) -> tuple[bool, str, Dict[str, Any]]:
        try:
            tape.update(_record_symbol_reliability(pid, cfg, t, reason, allowed=False))
        except Exception:
            pass
        return False, reason, tape

    def _allow() -> tuple[bool, str, Dict[str, Any]]:
        try:
            tape.update(_record_symbol_reliability(pid, cfg, t, "", allowed=True))
        except Exception:
            pass
        return True, "", tape

    cohort = str(tape.get("symbol_cohort") or "standard").strip().lower()
    cohort_scale = {"prime": 0.92, "standard": 1.0, "speculative": 1.10}.get(cohort, 1.0)
    min_samples = max(4, _safe_int(cfg.get("TAPE_QUALITY_MIN_SAMPLES", 6), 6))
    min_fresh_ratio = max(0.20, min(0.95, _safe_float(cfg.get("TAPE_QUALITY_MIN_FRESH_RATIO", 0.55), 0.55) * cohort_scale))
    min_top_ratio = max(0.25, _safe_float(cfg.get("TAPE_QUALITY_MIN_TOPBOOK_RATIO", 0.65), 0.65) * cohort_scale)
    min_spread_ok_ratio = max(0.25, _safe_float(cfg.get("TAPE_QUALITY_MIN_SPREAD_OK_RATIO", 0.55), 0.55) / cohort_scale)
    min_press_ok_ratio = max(0.20, _safe_float(cfg.get("TAPE_QUALITY_MIN_PRESS_OK_RATIO", 0.45), 0.45) / cohort_scale)
    flow = _market_flow_snapshot(cfg, m, tape, cycle_payload)
    tape.update(flow)

    if bool(tape.get("symbol_quarantined")):
        family = _reliability_reason_family(tape.get("symbol_quarantine_reason"))
        return _reject(f"preq_q_{family}")
    if bool(tape.get("u0_cooldown")):
        if _tape_recovery_override_allows(cfg, tape, "u0"):
            tape["tape_recovery_override"] = True
            tape["tape_recovery_override_reason"] = "u0_cd"
            _TAPE_U0_COOLDOWN_UNTIL[pid] = 0
        else:
            return _reject("u0_cd")
    if not bool(tape.get("fresh_now")):
        return _reject("u0_now")
    if _safe_int(tape.get("sample_n", 0), 0) < min_samples:
        if _tape_recovery_override_allows(cfg, tape, "hist"):
            tape["tape_recovery_override"] = True
            tape["tape_recovery_override_reason"] = "preq_hist"
        else:
            return _reject("preq_hist")

    soft_failures: List[str] = []
    if _safe_float(tape.get("fresh_ratio", 0.0), 0.0) < min_fresh_ratio:
        soft_failures.append("preq_fresh")
    if _safe_float(tape.get("top_ratio_avg", 0.0), 0.0) < min_top_ratio:
        soft_failures.append("preq_tobq")
    if _safe_float(tape.get("spread_ok_ratio", 0.0), 0.0) < min_spread_ok_ratio:
        soft_failures.append("preq_spread")
    if _safe_float(tape.get("press_ok_ratio", 0.0), 0.0) < min_press_ok_ratio:
        soft_failures.append("preq_press")
    if not soft_failures:
        return _allow()

    try:
        tdi_score_now = float((tdi_payload or {}).get("tdi_score", 0.0) or 0.0)
    except Exception:
        tdi_score_now = 0.0
    try:
        tdi_truth_now = float((tdi_payload or {}).get("tdi_truth_score", 0.0) or 0.0)
    except Exception:
        tdi_truth_now = 0.0
    try:
        tdi_flow_floor = float((tdi_payload or {}).get("tdi_flow_floor", 0.0) or 0.0)
    except Exception:
        tdi_flow_floor = 0.0

    max_soft_fails = max(0, _safe_int(cfg.get("FLOW_SURF_PREENTRY_MAX_SOFT_FAILS", 1), 1))
    flow_soft_ready = bool(tape.get("flow_soft_ready"))
    flow_regime = str(tape.get("flow_regime") or "").strip().lower()
    current_book_live = bool(tape.get("flow_current_book_live"))
    current_spread_live = bool(tape.get("flow_current_spread_live"))
    current_press_live = bool(tape.get("flow_current_press_live"))
    current_ok = current_book_live and current_spread_live and current_press_live
    truth_gate = max(tdi_score_now, tdi_truth_now, tdi_flow_floor)
    truth_gate_min = _safe_float(cfg.get("FLOW_SURF_PREENTRY_TDI_MIN", 68.0), 68.0)

    if (
        flow_soft_ready
        and current_ok
        and flow_regime in {"ride", "pullback", "breakout"}
        and len(soft_failures) <= max_soft_fails
        and truth_gate >= truth_gate_min
    ):
        tape["flow_preentry_override"] = True
        tape["flow_preentry_override_reasons"] = "|".join(soft_failures)
        return _allow()

    return _reject(str(soft_failures[0]))


def _symbol_reliability_eligibility_allows(
    cfg: Dict[str, Any],
    pid: str,
    m: Optional[Dict[str, Any]],
    t: int,
    tape_info: Optional[Dict[str, Any]] = None,
) -> tuple[bool, str, Dict[str, Any]]:
    tape = dict(tape_info or _record_tape_quality(pid, m, cfg, t) or {})
    if not bool(cfg.get("SYMBOL_RELIABILITY_ELIGIBILITY_ENABLED", True)):
        return True, "", tape
    tape.update(_market_flow_snapshot(cfg, m, tape, None))

    min_samples = max(
        8,
        _safe_int(
            cfg.get(
                "SYMBOL_RELIABILITY_ELIGIBILITY_MIN_SAMPLES",
                cfg.get("SYMBOL_RELIABILITY_MIN_SAMPLES", 16),
            ),
            _safe_int(cfg.get("SYMBOL_RELIABILITY_MIN_SAMPLES", 16), 16),
        ),
    )
    max_infra_share = max(
        0.20,
        min(
            0.90,
            _safe_float(
                cfg.get(
                    "SYMBOL_RELIABILITY_ELIGIBILITY_MAX_INFRA_SHARE",
                    min(_safe_float(cfg.get("SYMBOL_RELIABILITY_MAX_INFRA_SHARE", 0.62), 0.62), 0.40),
                ),
                min(_safe_float(cfg.get("SYMBOL_RELIABILITY_MAX_INFRA_SHARE", 0.62), 0.62), 0.40),
            ),
        ),
    )
    recovery_max_infra_share = max(
        max_infra_share,
        min(
            0.95,
            _safe_float(
                cfg.get(
                    "SYMBOL_RELIABILITY_ELIGIBILITY_RECOVERY_MAX_INFRA_SHARE",
                    max(max_infra_share, 0.55),
                ),
                max(max_infra_share, 0.55),
            ),
        ),
    )

    family = _reliability_reason_family(
        tape.get("symbol_quarantine_reason") or tape.get("symbol_reliability_dominant_reason")
    )
    if bool(tape.get("symbol_quarantined")):
        return False, f"elig_q_{family or 'infra'}", tape

    sample_n = _safe_int(tape.get("symbol_reliability_sample_n", 0), 0)
    if sample_n < min_samples:
        return True, "", tape

    infra_share = _safe_float(tape.get("symbol_reliability_infra_share", 0.0), 0.0)
    if infra_share >= max_infra_share:
        if (
            family in {"u0", "hist"}
            and infra_share <= recovery_max_infra_share
            and _tape_recovery_override_allows(cfg, tape, family)
        ):
            tape["symbol_reliability_recovery_override"] = True
            tape["symbol_reliability_recovery_override_reason"] = family
            return True, "", tape
        return False, f"elig_q_{family or 'infra'}", tape

    return True, "", tape


def _symbol_reliability_rank_tuple(
    tape_info: Optional[Dict[str, Any]],
    eligible: bool,
    source_index: int,
) -> tuple:
    tape = dict(tape_info or {})
    return (
        0 if eligible else 1,
        float(tape.get("symbol_reliability_infra_share", 1.0) or 1.0),
        0 if bool(tape.get("symbol_quarantined")) else 1,
        -float(tape.get("fresh_ratio", 0.0) or 0.0),
        -float(tape.get("symbol_quality_score", 0.0) or 0.0),
        -float(tape.get("top_ratio_avg", 0.0) or 0.0),
        int(source_index),
    )


def _candidate_pool_limit(cfg: Dict[str, Any], top_n: int) -> int:
    top_n = max(1, int(top_n))
    pool_mult = max(1, _safe_int(cfg.get("SYMBOL_RELIABILITY_ELIGIBILITY_POOL_MULT", 2), 2))
    return max(top_n, top_n * pool_mult)


def _cycle_ctx_enabled(cfg: Dict[str, Any]) -> bool:
    try:
        if not bool(cfg.get("DRY", False)):
            return False
    except Exception:
        return False
    try:
        return bool(cfg.get("CYCLE_CONTEXT_DRY", True))
    except Exception:
        return True


def _cycle_ctx_display_enabled(cfg: Dict[str, Any]) -> bool:
    try:
        return bool(cfg.get("CYCLE_CONTEXT_DISPLAY", True))
    except Exception:
        return True


def _cycle_ctx_target_tp(cfg: Dict[str, Any]) -> float:
    return round(_pct_points(cfg.get("TP_PCT", 0.0), 0.0), 3)


def _cycle_ctx_switch_margin(cfg: Dict[str, Any]) -> float:
    try:
        return max(2.0, float(cfg.get("CYCLE_CONTEXT_SWITCH_MARGIN", 8.0) or 8.0))
    except Exception:
        return 8.0


def _cycle_interval_minutes(interval: str) -> int:
    table = {
        "1m": 1,
        "5m": 5,
        "15m": 15,
        "30m": 30,
        "1h": 60,
        "2h": 120,
        "4h": 240,
        "6h": 360,
        "1d": 1440,
        "1w": 10080,
        "1mo": 43200,
    }
    return int(table.get(str(interval or "").strip(), 0))


def _cycle_phase_stance(phase: str) -> str:
    phase = str(phase or "unknown").strip()
    if phase in ("lifting_from_trough", "bottoming"):
        return "bull"
    if phase in ("descending_from_crest", "rolling_over"):
        return "bear"
    return "neutral"


def _cycle_phase_symbol(phase: str) -> str:
    phase = str(phase or "unknown").strip()
    return {
        "lifting_from_trough": "^",
        "bottoming": "v",
        "descending_from_crest": "x",
        "rolling_over": "~",
    }.get(phase, "?")


def _cycle_bucket(interval: str) -> str:
    mins = _cycle_interval_minutes(interval)
    if mins <= 120:
        return "short"
    if mins <= 360:
        return "mid"
    return "long"


def _read_json_file(path_json: str) -> Any:
    with open(path_json, "r", encoding="utf-8") as f:
        return json.load(f)


def _read_csv_file(path_csv: str) -> List[Dict[str, Any]]:
    with open(path_csv, "r", encoding="utf-8", newline="") as f:
        return [dict(r) for r in csv.DictReader(f)]


def _read_json_zip(zf: zipfile.ZipFile, name: str) -> Any:
    with zf.open(name) as f:
        return json.load(f)


def _read_csv_zip(zf: zipfile.ZipFile, name: str) -> List[Dict[str, Any]]:
    with zf.open(name) as f:
        txt = io.TextIOWrapper(f, encoding="utf-8", newline="")
        return [dict(r) for r in csv.DictReader(txt)]


def _cycle_ctx_pick_latest(root: str, target_tp: float) -> Tuple[str, float, Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]:
    analysis_dir = os.path.join(root, "logs", "analysis_cycle")
    if not os.path.isdir(analysis_dir):
        return ("", 0.0, {}, [], [])

    candidates: List[Tuple[float, str, Dict[str, Any], List[Dict[str, Any]], List[Dict[str, Any]]]] = []

    try:
        for name in os.listdir(analysis_dir):
            if not str(name).startswith("mm25_cycle_map_"):
                continue
            pack_dir = os.path.join(analysis_dir, str(name))
            if not os.path.isdir(pack_dir):
                continue
            meta_path = os.path.join(pack_dir, "cycle_structure_meta.json")
            best_path = os.path.join(pack_dir, "cycle_structure_best_intervals.json")
            all_path = os.path.join(pack_dir, "cycle_structure_per_coin.csv")
            if not (os.path.exists(meta_path) and os.path.exists(best_path)):
                continue
            try:
                meta = _read_json_file(meta_path)
                best_rows = _read_json_file(best_path)
                all_rows = _read_csv_file(all_path) if os.path.exists(all_path) else []
                meta_tp = round(_pct_points((meta or {}).get("tp_pct", 0.0), 0.0), 3)
                if abs(meta_tp - float(target_tp)) > 0.05:
                    continue
                mtime = max(os.path.getmtime(meta_path), os.path.getmtime(best_path), os.path.getmtime(all_path) if os.path.exists(all_path) else 0.0)
                candidates.append((mtime, pack_dir, meta if isinstance(meta, dict) else {}, best_rows if isinstance(best_rows, list) else [], all_rows if isinstance(all_rows, list) else []))
            except Exception:
                continue
    except Exception:
        pass

    if not candidates:
        try:
            for name in os.listdir(analysis_dir):
                if not (str(name).startswith("mm25_cycle_map_") and str(name).lower().endswith(".zip")):
                    continue
                zip_path = os.path.join(analysis_dir, str(name))
                try:
                    with zipfile.ZipFile(zip_path, "r") as zf:
                        meta = _read_json_zip(zf, "cycle_structure_meta.json")
                        best_rows = _read_json_zip(zf, "cycle_structure_best_intervals.json")
                        try:
                            all_rows = _read_csv_zip(zf, "cycle_structure_per_coin.csv")
                        except Exception:
                            all_rows = []
                    meta_tp = round(_pct_points((meta or {}).get("tp_pct", 0.0), 0.0), 3)
                    if abs(meta_tp - float(target_tp)) > 0.05:
                        continue
                    mtime = os.path.getmtime(zip_path)
                    candidates.append((mtime, zip_path, meta if isinstance(meta, dict) else {}, best_rows if isinstance(best_rows, list) else [], all_rows if isinstance(all_rows, list) else []))
                except Exception:
                    continue
        except Exception:
            pass

    if not candidates:
        return ("", 0.0, {}, [], [])
    mtime, src, meta, best_rows, all_rows = sorted(candidates, key=lambda x: x[0])[-1]
    return (str(src), float(mtime), meta if isinstance(meta, dict) else {}, best_rows if isinstance(best_rows, list) else [], all_rows if isinstance(all_rows, list) else [])


def _cycle_ctx_persist_path(root: str, target_tp: float) -> str:
    safe = str(target_tp).replace(".", "p")
    return os.path.join(root, "logs", "analysis_cycle", f"cycle_ctx_cache_tp_{safe}.json")


def _cycle_ctx_persist_load(root: str, target_tp: float) -> None:
    path_json = _cycle_ctx_persist_path(root, target_tp)
    if not os.path.exists(path_json):
        return
    try:
        with open(path_json, "r", encoding="utf-8") as f:
            obj = json.load(f)
        if not isinstance(obj, dict):
            return
        best = obj.get("best_rows") or {}
        all_rows = obj.get("all_rows") or {}
        state = obj.get("stack_state") or {}
        if isinstance(best, dict):
            for pid, row in best.items():
                pid_u = str(pid or "").strip().upper()
                if pid_u and isinstance(row, dict):
                    _CYCLE_CTX_AUTO_BEST[pid_u] = dict(row)
        if isinstance(all_rows, dict):
            for pid, rows in all_rows.items():
                pid_u = str(pid or "").strip().upper()
                if pid_u and isinstance(rows, list):
                    _CYCLE_CTX_AUTO_ALL[pid_u] = [dict(r) for r in rows if isinstance(r, dict)]
        if isinstance(state, dict):
            for pid, row in state.items():
                pid_u = str(pid or "").strip().upper()
                if pid_u and isinstance(row, dict):
                    _CYCLE_STACK_STATE[pid_u] = dict(row)
        _CYCLE_CTX_PERSIST["tp_pct"] = target_tp
        _CYCLE_CTX_PERSIST["loaded_at"] = time.time()
        _CYCLE_CTX_PERSIST["path"] = path_json
    except Exception:
        return


def _cycle_ctx_persist_save(root: str, target_tp: float) -> None:
    path_json = _cycle_ctx_persist_path(root, target_tp)
    try:
        os.makedirs(os.path.dirname(path_json), exist_ok=True)
        obj = {
            "saved_at": time.time(),
            "tp_pct": target_tp,
            "best_rows": _CYCLE_CTX_AUTO_BEST,
            "all_rows": _CYCLE_CTX_AUTO_ALL,
            "stack_state": _CYCLE_STACK_STATE,
        }
        tmp = path_json + ".tmp"
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False)
        os.replace(tmp, path_json)
        _CYCLE_CTX_PERSIST["tp_pct"] = target_tp
        _CYCLE_CTX_PERSIST["loaded_at"] = time.time()
        _CYCLE_CTX_PERSIST["path"] = path_json
    except Exception:
        return


def _cycle_ctx_load(cfg: Dict[str, Any]) -> None:
    if not _cycle_ctx_display_enabled(cfg):
        _CYCLE_CTX_CACHE["best_rows"] = {}
        _CYCLE_CTX_CACHE["all_rows"] = {}
        _CYCLE_CTX_CACHE["meta"] = {}
        _CYCLE_CTX_CACHE["src"] = ""
        try:
            _CYCLE_CTX_AUTO_BEST.clear()
            _CYCLE_CTX_AUTO_ALL.clear()
            _CYCLE_STACK_STATE.clear()
        except Exception:
            pass
        return
    now = time.time()
    try:
        last = float(_CYCLE_CTX_CACHE.get("loaded_at", 0.0) or 0.0)
    except Exception:
        last = 0.0
    target_tp = _cycle_ctx_target_tp(cfg)
    cache_tp = _CYCLE_CTX_CACHE.get("tp_pct")
    if (now - last) < 60.0 and (_CYCLE_CTX_CACHE.get("best_rows") or _CYCLE_CTX_CACHE.get("all_rows")) and cache_tp == target_tp:
        return

    src, mtime, meta, best_rows, all_rows = _cycle_ctx_pick_latest(ROOT, target_tp)
    try:
        if _CYCLE_CTX_PERSIST.get("tp_pct") != target_tp or not _CYCLE_CTX_AUTO_BEST:
            _cycle_ctx_persist_load(ROOT, target_tp)
    except Exception:
        pass
    best_by_pid: Dict[str, Dict[str, Any]] = {}
    for row in best_rows or []:
        try:
            pid = str((row or {}).get("product_id") or "").strip().upper()
        except Exception:
            pid = ""
        if pid:
            best_by_pid[pid] = dict(row or {})
    all_by_pid: Dict[str, List[Dict[str, Any]]] = {}
    for row in all_rows or []:
        try:
            pid = str((row or {}).get("product_id") or "").strip().upper()
        except Exception:
            pid = ""
        if not pid:
            continue
        all_by_pid.setdefault(pid, []).append(dict(row or {}))

    _CYCLE_CTX_CACHE["src"] = src
    _CYCLE_CTX_CACHE["mtime"] = mtime
    _CYCLE_CTX_CACHE["tp_pct"] = target_tp
    _CYCLE_CTX_CACHE["loaded_at"] = now
    _CYCLE_CTX_CACHE["best_rows"] = best_by_pid
    _CYCLE_CTX_CACHE["all_rows"] = all_by_pid
    _CYCLE_CTX_CACHE["meta"] = meta if isinstance(meta, dict) else {}


def _cycle_ctx_best_rows(cfg: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    _cycle_ctx_load(cfg)
    rows = dict(_CYCLE_CTX_CACHE.get("best_rows", {}) or {})
    try:
        rows.update(_CYCLE_CTX_AUTO_BEST or {})
    except Exception:
        pass
    return rows


def _cycle_ctx_all_rows(cfg: Dict[str, Any]) -> Dict[str, List[Dict[str, Any]]]:
    _cycle_ctx_load(cfg)
    rows = dict(_CYCLE_CTX_CACHE.get("all_rows", {}) or {})
    try:
        for pid, rlist in (_CYCLE_CTX_AUTO_ALL or {}).items():
            rows[str(pid)] = list(rlist or [])
    except Exception:
        pass
    return rows


def _cycle_ctx_autofill_enabled(cfg: Dict[str, Any]) -> bool:
    try:
        return _cycle_ctx_display_enabled(cfg) and bool(cfg.get("CYCLE_CONTEXT_AUTOFILL", True))
    except Exception:
        return False


def _cycle_ctx_autofill_bars(cfg: Dict[str, Any]) -> int:
    try:
        return max(120, min(240, int(cfg.get("CYCLE_CONTEXT_AUTOFILL_BARS", 180) or 180)))
    except Exception:
        return 180


def _cycle_ctx_autofill_min_swing(cfg: Dict[str, Any]) -> float:
    try:
        val = float(cfg.get("CYCLE_CONTEXT_AUTOFILL_MIN_SWING_PCT", 0.0) or 0.0)
    except Exception:
        val = 0.0
    if val > 0.0:
        return float(val)
    tp = _cycle_ctx_target_tp(cfg)
    return max(0.5, round(tp / 2.0, 2))


def _cycle_ctx_autofill_min_bars(cfg: Dict[str, Any]) -> int:
    try:
        return max(2, min(6, int(cfg.get("CYCLE_CONTEXT_AUTOFILL_MIN_BARS", 2) or 2)))
    except Exception:
        return 2


def _cycle_ctx_autofill_compute(cfg: Dict[str, Any], pid: str) -> None:
    pid_u = str(pid or "").strip().upper()
    if not pid_u:
        return
    try:
        from managers.logging_manager import diag_trough_wait_score as _cy  # type: ignore
    except Exception:
        return

    target_tp = _cycle_ctx_target_tp(cfg)
    adverse_pct = _pct_points(cfg.get("SL_PCT", 0.0), 0.0)
    bars_per_interval = _cycle_ctx_autofill_bars(cfg)
    min_swing_pct = _cycle_ctx_autofill_min_swing(cfg)
    min_bars = _cycle_ctx_autofill_min_bars(cfg)

    rows: List[Dict[str, Any]] = []
    daily: List[List[float]] = []
    base_intervals = [x for x in list(getattr(_cy, "_INTERVALS", []) or []) if _cycle_interval_minutes(str(x[0])) >= 15]
    if not base_intervals:
        return

    for interval_name, fetch_gran, agg_size, source_kind in base_intervals:
        candles: List[List[float]] = []
        fetch_bars = int(bars_per_interval) * max(1, int(agg_size))
        try:
            base_candles = _cy._fetch_candles_by_count(pid_u, int(fetch_gran), int(fetch_bars))
            candles = _cy._aggregate_candles(base_candles, int(agg_size)) if int(agg_size) > 1 else list(base_candles)
            if len(candles) > int(bars_per_interval):
                candles = candles[-int(bars_per_interval):]
        except Exception:
            candles = []
        if interval_name == "1d":
            daily = list(candles)
        summary, _ = _cy._analyze_cycle_interval(
            pid_u,
            str(interval_name),
            candles,
            tp_pct=float(target_tp),
            adverse_pct=float(adverse_pct),
            min_swing_pct=float(min_swing_pct),
            min_bars=int(min_bars),
            source_kind=str(source_kind),
        )
        if isinstance(summary, dict):
            rows.append(dict(summary))

    if daily:
        try:
            weekly = _cy._aggregate_candles(daily, 7)
            summary, _ = _cy._analyze_cycle_interval(
                pid_u,
                "1w",
                weekly,
                tp_pct=float(target_tp),
                adverse_pct=float(adverse_pct),
                min_swing_pct=float(min_swing_pct),
                min_bars=max(1, int(min_bars)),
                source_kind="synthetic_from_1d",
            )
            if isinstance(summary, dict):
                rows.append(dict(summary))
        except Exception:
            pass

    scored: List[Dict[str, Any]] = []
    for row in rows:
        rr = dict(row or {})
        rr["confidence"] = round(_cycle_row_confidence(rr, target_tp), 2)
        scored.append(rr)
    if not scored:
        return

    scored.sort(key=lambda r: (-_safe_float(r.get("confidence"), 0.0), _cycle_interval_minutes(str(r.get("interval") or ""))))
    best = dict(scored[0])
    with _CYCLE_AUTO_LOCK:
        _CYCLE_CTX_AUTO_ALL[pid_u] = list(scored)
        _CYCLE_CTX_AUTO_BEST[pid_u] = dict(best)
    try:
        _cycle_ctx_persist_save(ROOT, target_tp)
    except Exception:
        pass


def _cycle_ctx_autofill_worker() -> None:
    global _CYCLE_AUTO_THREAD
    while True:
        with _CYCLE_AUTO_LOCK:
            pid = _CYCLE_AUTO_QUEUE.popleft() if _CYCLE_AUTO_QUEUE else None
            cfg = dict(_CYCLE_AUTO_CFG or {})
        if not pid:
            break
        try:
            _cycle_ctx_autofill_compute(cfg, str(pid))
            _CYCLE_AUTO_FAIL_TS.pop(str(pid), None)
        except Exception:
            _CYCLE_AUTO_FAIL_TS[str(pid)] = time.time()
        finally:
            with _CYCLE_AUTO_LOCK:
                _CYCLE_AUTO_PENDING.discard(str(pid))
        time.sleep(0.10)
    with _CYCLE_AUTO_LOCK:
        _CYCLE_AUTO_THREAD = None


def _cycle_ctx_autofill_request(cfg: Dict[str, Any], pid: str) -> None:
    global _CYCLE_AUTO_THREAD
    pid_u = str(pid or "").strip().upper()
    if not pid_u or not _cycle_ctx_autofill_enabled(cfg):
        return
    try:
        if (_cycle_ctx_all_rows(cfg).get(pid_u) or _cycle_ctx_best_rows(cfg).get(pid_u)):
            return
    except Exception:
        pass
    now = time.time()
    if (now - _safe_float(_CYCLE_AUTO_FAIL_TS.get(pid_u), 0.0)) < 120.0:
        return
    with _CYCLE_AUTO_LOCK:
        _CYCLE_AUTO_CFG.clear()
        _CYCLE_AUTO_CFG.update(dict(cfg or {}))
        if pid_u in _CYCLE_AUTO_PENDING:
            return
        _CYCLE_AUTO_PENDING.add(pid_u)
        _CYCLE_AUTO_QUEUE.append(pid_u)
        if _CYCLE_AUTO_THREAD is None or (not _CYCLE_AUTO_THREAD.is_alive()):
            _CYCLE_AUTO_THREAD = threading.Thread(target=_cycle_ctx_autofill_worker, name="cycle-ctx-autofill", daemon=True)
            _CYCLE_AUTO_THREAD.start()


def _cycle_ctx_for_pid(cfg: Dict[str, Any], pid: str) -> Optional[Dict[str, Any]]:
    rows = _cycle_ctx_best_rows(cfg)
    if not rows:
        return None
    try:
        return rows.get(str(pid).strip().upper())
    except Exception:
        return None


def _cycle_row_confidence(row: Dict[str, Any], target_tp: float) -> float:
    tp_hit = _safe_float((row or {}).get("tp_hit_rate_pct"), 0.0)
    adverse = _safe_float((row or {}).get("adverse_first_rate_pct"), 0.0)
    both = _safe_float((row or {}).get("both_same_rate_pct"), 0.0)
    rebound = _safe_float((row or {}).get("avg_rebound_pct"), 0.0)
    qtr = _safe_int((row or {}).get("qualified_troughs"), 0)
    swings = _safe_int((row or {}).get("swings"), 0)
    bars = _safe_int((row or {}).get("bars"), 0)
    med_tp = _safe_float((row or {}).get("median_min_to_tp"), 0.0)
    tr2cr = _safe_float((row or {}).get("trough_to_crest_med_min"), 0.0)
    phase = str((row or {}).get("current_phase") or "unknown").strip()
    source = str((row or {}).get("source") or "").strip()

    tp_ratio = 0.0
    if target_tp > 0.0:
        tp_ratio = max(0.0, min(120.0, (rebound / max(0.25, float(target_tp))) * 100.0))
    support = max(0.0, min(100.0, (qtr * 12.0) + max(0.0, float(swings - 5)) * 2.0))
    time_score = 50.0
    if med_tp > 0.0 and tr2cr > 0.0:
        ratio = med_tp / max(1.0, tr2cr)
        if ratio <= 0.25:
            time_score = 95.0
        elif ratio <= 0.50:
            time_score = 80.0
        elif ratio <= 0.75:
            time_score = 65.0
        elif ratio <= 1.00:
            time_score = 55.0
        else:
            time_score = max(15.0, 55.0 - min(40.0, (ratio - 1.0) * 20.0))
    phase_bonus = {
        "lifting_from_trough": 18.0,
        "bottoming": 8.0,
        "descending_from_crest": -22.0,
        "rolling_over": -12.0,
    }.get(phase, 0.0)
    source_penalty = 0.0
    if source == "synthetic_from_1d":
        source_penalty += 12.0
    elif source == "synthetic_from_1h":
        source_penalty += 5.0
    if bars < 60:
        source_penalty += 8.0
    conf = (0.45 * tp_hit) + (0.20 * (100.0 - adverse)) + (0.15 * tp_ratio) + (0.10 * support) + (0.10 * time_score) + phase_bonus - source_penalty - (0.15 * both)
    return max(0.0, min(100.0, float(conf)))


def _cycle_ctx_stack_for_pid(cfg: Dict[str, Any], pid: str) -> Optional[Dict[str, Any]]:
    pid_u = str(pid or "").strip().upper()
    if not pid_u:
        return None
    rows = list((_cycle_ctx_all_rows(cfg).get(pid_u) or []))
    if not rows:
        best = _cycle_ctx_for_pid(cfg, pid_u)
        if best:
            rows = [best]
    if not rows:
        return None

    target_tp = _cycle_ctx_target_tp(cfg)
    stack: List[Dict[str, Any]] = []
    for row in rows:
        interval = str((row or {}).get("interval") or "").strip()
        if not interval:
            continue
        phase = str((row or {}).get("current_phase") or "unknown").strip()
        item = dict(row or {})
        item["interval"] = interval
        item["phase"] = phase
        item["stance"] = _cycle_phase_stance(phase)
        item["bucket"] = _cycle_bucket(interval)
        item["confidence"] = round(_cycle_row_confidence(item, target_tp), 2)
        stack.append(item)
    if not stack:
        return None
    stack.sort(key=lambda r: (-_safe_float(r.get("confidence"), 0.0), _cycle_interval_minutes(str(r.get("interval") or ""))))

    dominant = dict(stack[0])
    prev = _CYCLE_STACK_STATE.get(pid_u)
    margin = _cycle_ctx_switch_margin(cfg)
    if isinstance(prev, dict):
        prev_interval = str(prev.get("interval") or "").strip()
        if prev_interval and dominant.get("interval") != prev_interval:
            prev_item = next((dict(x) for x in stack if str(x.get("interval") or "").strip() == prev_interval), None)
            if prev_item is not None and _safe_float(dominant.get("confidence"), 0.0) < (_safe_float(prev_item.get("confidence"), 0.0) + margin):
                dominant = prev_item
                dominant["retained"] = True
    _CYCLE_STACK_STATE[pid_u] = {
        "interval": dominant.get("interval"),
        "confidence": _safe_float(dominant.get("confidence"), 0.0),
        "phase": dominant.get("phase"),
        "updated_at": time.time(),
    }
    try:
        if _CYCLE_CTX_AUTO_BEST:
            _cycle_ctx_persist_save(ROOT, target_tp)
    except Exception:
        pass

    bull_total = sum(_safe_float(x.get("confidence"), 0.0) for x in stack if x.get("stance") == "bull")
    bear_total = sum(_safe_float(x.get("confidence"), 0.0) for x in stack if x.get("stance") == "bear")
    long_bull = sum(_safe_float(x.get("confidence"), 0.0) for x in stack if x.get("bucket") in ("mid", "long") and x.get("stance") == "bull")
    long_bear = sum(_safe_float(x.get("confidence"), 0.0) for x in stack if x.get("bucket") in ("mid", "long") and x.get("stance") == "bear")
    short_bull = sum(_safe_float(x.get("confidence"), 0.0) for x in stack if x.get("bucket") == "short" and x.get("stance") == "bull")
    short_bear = sum(_safe_float(x.get("confidence"), 0.0) for x in stack if x.get("bucket") == "short" and x.get("stance") == "bear")

    dom_conf = _safe_float(dominant.get("confidence"), 0.0)
    dom_stance = str(dominant.get("stance") or "neutral")
    dom_bucket = str(dominant.get("bucket") or "long")

    stability_block = (long_bear >= 45.0) and (long_bear > (long_bull + 8.0))
    agile_allow = (dom_bucket == "short") and (dom_stance == "bull") and (long_bear <= (long_bull + 5.0))
    confidence_live = dom_conf >= 40.0
    block = confidence_live and (stability_block or ((dom_stance == "bear") and (bear_total > (bull_total + 5.0))))
    allow = confidence_live and (dom_stance == "bull") and (((dom_bucket in ("mid", "long")) and (bull_total >= bear_total)) or agile_allow)

    top_stack: List[Dict[str, Any]] = []
    for item in stack[:3]:
        top_stack.append({
            "interval": str(item.get("interval") or ""),
            "phase": str(item.get("phase") or "unknown"),
            "stance": str(item.get("stance") or "neutral"),
            "bucket": str(item.get("bucket") or "long"),
            "confidence": round(_safe_float(item.get("confidence"), 0.0), 2),
        })

    return {
        "interval": str(dominant.get("interval") or ""),
        "phase": str(dominant.get("phase") or "unknown"),
        "source": str(dominant.get("source") or ""),
        "tp_hit_rate_pct": round(_safe_float(dominant.get("tp_hit_rate_pct"), 0.0), 2),
        "qualified_troughs": _safe_int(dominant.get("qualified_troughs"), 0),
        "confidence": round(dom_conf, 2),
        "dominant_bucket": dom_bucket,
        "dominant_stance": dom_stance,
        "retained": bool(dominant.get("retained")),
        "allow": bool(allow),
        "block": bool(block),
        "bull_total": round(bull_total, 2),
        "bear_total": round(bear_total, 2),
        "long_bull": round(long_bull, 2),
        "long_bear": round(long_bear, 2),
        "short_bull": round(short_bull, 2),
        "short_bear": round(short_bear, 2),
        "top_stack": top_stack,
        "cache_source": str(_CYCLE_CTX_CACHE.get("src") or ""),
    }


def _cycle_ctx_for_pid_dynamic(cfg: Dict[str, Any], pid: str) -> Optional[Dict[str, Any]]:
    try:
        ctx = _cycle_ctx_stack_for_pid(cfg, pid)
        if ctx:
            return ctx
    except Exception:
        pass
    try:
        _cycle_ctx_autofill_request(cfg, pid)
    except Exception:
        pass
    return None


def _cycle_ctx_brief(cfg: Dict[str, Any], pid: str) -> str:
    ctx = _cycle_ctx_for_pid_dynamic(cfg, pid)
    if not isinstance(ctx, dict) or not ctx:
        return "--"

    def _fmt(item: Dict[str, Any]) -> str:
        interval = str((item or {}).get('interval') or '--')
        phase = str((item or {}).get('phase') or '')
        conf = int(round(_safe_float((item or {}).get('confidence'), 0.0)))
        return f"{interval}{_cycle_phase_symbol(phase)}{conf:>3}"

    stack = list(ctx.get("top_stack") or [])
    if not stack:
        stack = [ctx]

    parts: List[str] = []
    seen: set[str] = set()
    for item in stack:
        interval = str((item or {}).get('interval') or '').strip()
        if not interval or interval in seen:
            continue
        seen.add(interval)
        parts.append(_fmt(item))
        if len(parts) >= 3:
            break

    if not parts:
        return "--"
    return "|".join(parts)


def _fmt_pid_ticker(pid: str, base_w: int = 18, quote_w: int = 4) -> str:
    s = str(pid or "").strip().upper()
    if not s:
        return "".ljust(base_w + 1 + quote_w)
    if "-" not in s:
        total_w = base_w + 1 + quote_w
        if len(s) > total_w:
            s = s[: max(1, total_w - 3)] + "..."
        return f"{s:<{total_w}}"
    base, quote = s.rsplit("-", 1)
    if len(base) > base_w:
        base = base[: max(1, base_w - 3)] + "..."
    return f"{base:<{base_w}}-{quote:>{quote_w}}"


def _cycle_ctx_phase_gate(cfg: Dict[str, Any], pid: str) -> Optional[Dict[str, Any]]:
    ctx = _cycle_ctx_for_pid_dynamic(cfg, pid)
    if isinstance(ctx, dict) and ctx:
        return ctx
    row = _cycle_ctx_for_pid(cfg, pid)
    if not isinstance(row, dict) or not row:
        return None
    interval = str(row.get("interval") or "").strip()
    phase = str(row.get("current_phase") or "unknown").strip()
    source = str(row.get("source") or "").strip()
    tp_hit = _safe_float(row.get("tp_hit_rate_pct"), 0.0)
    qtr = _safe_int(row.get("qualified_troughs"), 0)
    allow = phase in ("lifting_from_trough", "bottoming")
    block = phase in ("descending_from_crest", "rolling_over")
    conf = round(_cycle_row_confidence(row, _cycle_ctx_target_tp(cfg)), 2)
    return {
        "interval": interval,
        "phase": phase,
        "source": source,
        "tp_hit_rate_pct": round(tp_hit, 2),
        "qualified_troughs": qtr,
        "confidence": conf,
        "dominant_bucket": _cycle_bucket(interval),
        "dominant_stance": _cycle_phase_stance(phase),
        "allow": bool(allow),
        "block": bool(block),
        "bull_total": conf if allow else 0.0,
        "bear_total": conf if block else 0.0,
        "top_stack": [{
            "interval": interval,
            "phase": phase,
            "stance": _cycle_phase_stance(phase),
            "bucket": _cycle_bucket(interval),
            "confidence": conf,
        }],
    }

def _cycle_tp_fast_gate_enabled(cfg: Dict[str, Any]) -> bool:
    try:
        return _cycle_ctx_enabled(cfg) and bool(cfg.get("CYCLE_TP_FAST_GATE", True))
    except Exception:
        return False


def _cycle_tp_fast_intervals(cfg: Dict[str, Any]) -> List[str]:
    raw = str(cfg.get("CYCLE_TP_FAST_INTERVALS", "15m,30m,1h,2h") or "").strip()
    out: List[str] = []
    seen: set[str] = set()
    for part in raw.replace("|", ",").split(","):
        tf = str(part or "").strip()
        if not tf or tf in seen:
            continue
        seen.add(tf)
        out.append(tf)
    return out or ["15m", "30m", "1h", "2h"]


def _cycle_tp_fast_support_gate(cfg: Dict[str, Any], pid: str) -> Optional[Dict[str, Any]]:
    if not _cycle_tp_fast_gate_enabled(cfg):
        return None
    pid_u = str(pid or "").strip().upper()
    if not pid_u:
        return None

    rows = list((_cycle_ctx_all_rows(cfg).get(pid_u) or []))
    if not rows:
        best = _cycle_ctx_for_pid(cfg, pid_u)
        if isinstance(best, dict) and best:
            rows = [best]
    if not rows:
        return {
            "allow": True,
            "block": False,
            "reason": "ctx_unavailable",
            "available": False,
            "target_tp_pct": round(_cycle_ctx_target_tp(cfg), 3),
            "fast_intervals": _cycle_tp_fast_intervals(cfg),
            "supporting_intervals": [],
        }

    target_tp = round(_cycle_ctx_target_tp(cfg), 3)
    fast_intervals = _cycle_tp_fast_intervals(cfg)
    fast_set = set(fast_intervals)
    candidates: List[Dict[str, Any]] = []

    for row in rows:
        interval = str((row or {}).get("interval") or "").strip()
        if not interval:
            continue
        rebound = _safe_float((row or {}).get("avg_rebound_pct"), -1.0)
        if rebound < target_tp:
            continue
        phase = str((row or {}).get("current_phase") or "unknown").strip()
        tp_hit = round(_safe_float((row or {}).get("tp_hit_rate_pct"), 0.0), 2)
        qtr = _safe_int((row or {}).get("qualified_troughs"), 0)
        conf = round(_cycle_row_confidence(row, target_tp), 2)
        phase_bonus = 10 if _cycle_phase_stance(phase) == "bull" else (-10 if _cycle_phase_stance(phase) == "bear" else 0)
        support_score = int(max(0, min(100, round((conf * 0.70) + (tp_hit * 0.20) + (min(qtr, 5) * 2.0) + phase_bonus))))
        candidates.append({
            "interval": interval,
            "phase": phase,
            "tp_hit_rate_pct": tp_hit,
            "qualified_troughs": qtr,
            "confidence": conf,
            "avg_rebound_pct": round(rebound, 3),
            "support_score": support_score,
            "stance": _cycle_phase_stance(phase),
        })

    candidates.sort(key=lambda r: (
        -int(r.get("support_score") or 0),
        -_safe_float(r.get("confidence"), 0.0),
        -_safe_float(r.get("tp_hit_rate_pct"), 0.0),
        _cycle_interval_minutes(str(r.get("interval") or "")),
    ))

    if not candidates:
        return {
            "allow": False,
            "block": True,
            "reason": "unsupported",
            "available": True,
            "target_tp_pct": target_tp,
            "fast_intervals": fast_intervals,
            "supporting_intervals": [],
        }

    best_any = dict(candidates[0])
    best_fast = next((dict(r) for r in candidates if str(r.get("interval") or "") in fast_set), None)
    best_interval = str(best_any.get("interval") or "")
    allow = best_interval in fast_set
    reason = "fast_supported" if allow else "slow_only"

    return {
        "allow": bool(allow),
        "block": not bool(allow),
        "reason": reason,
        "available": True,
        "target_tp_pct": target_tp,
        "fast_intervals": fast_intervals,
        "best_interval": best_interval,
        "best_phase": best_any.get("phase"),
        "best_tp_hit_rate_pct": best_any.get("tp_hit_rate_pct"),
        "best_qualified_troughs": best_any.get("qualified_troughs"),
        "best_confidence": best_any.get("confidence"),
        "best_avg_rebound_pct": best_any.get("avg_rebound_pct"),
        "best_support_score": best_any.get("support_score"),
        "best_stance": best_any.get("stance"),
        "supporting_intervals": [str(r.get("interval") or "") for r in candidates],
        "fast_best_interval": str((best_fast or {}).get("interval") or ""),
        "fast_best_phase": (best_fast or {}).get("phase"),
        "fast_best_tp_hit_rate_pct": (best_fast or {}).get("tp_hit_rate_pct"),
        "fast_best_qualified_troughs": (best_fast or {}).get("qualified_troughs"),
        "fast_best_confidence": (best_fast or {}).get("confidence"),
        "fast_best_avg_rebound_pct": (best_fast or {}).get("avg_rebound_pct"),
        "fast_best_support_score": (best_fast or {}).get("support_score"),
        "fast_best_stance": (best_fast or {}).get("stance"),
    }


def _trough_params(cfg: Dict[str, Any]) -> Tuple[int, int, float, int]:
    """Returns (lookback_ticks, sample_every_ticks, trough_pct_max, min_samples)."""
    try:
        tick_sec = float(cfg.get('TICK_SEC', 3.0) or 3.0)
    except Exception:
        tick_sec = 3.0
    if tick_sec <= 0:
        tick_sec = 1.0
    try:
        look_sec = float(cfg.get('TROUGH_LOOKBACK_SEC', 7200.0) or 7200.0)
    except Exception:
        look_sec = 7200.0
    try:
        sample_sec = float(cfg.get('TROUGH_SAMPLE_SEC', 60.0) or 60.0)
    except Exception:
        sample_sec = 60.0
    try:
        pct_max = float(cfg.get('TROUGH_PCT_MAX', 0.0) or 0.0)
    except Exception:
        pct_max = 0.0
    try:
        min_samples = int(cfg.get('TROUGH_MIN_SAMPLES', 10) or 10)
    except Exception:
        min_samples = 10

    look_ticks = int(round(look_sec / tick_sec)) if look_sec > 0 else 0
    if look_ticks < 5:
        look_ticks = 5
    sample_ticks = int(round(sample_sec / tick_sec)) if sample_sec > 0 else 1
    if sample_ticks < 1:
        sample_ticks = 1
    if min_samples < 1:
        min_samples = 1
    return look_ticks, sample_ticks, pct_max, min_samples


def _trough_update(cfg: Dict[str, Any], pid: str, t: int, mid: float) -> None:
    try:
        look_ticks, sample_ticks, pct_max, _min_samples = _trough_params(cfg)
    except Exception:
        return
    # disabled unless 0 < pct_max < 1
    if not (0.0 < float(pct_max) < 1.0):
        return
    if mid <= 0:
        return
    pid = str(pid)
    last = int(_TROUGH_LAST_SAMPLE_TICK.get(pid, -999999))
    if (t - last) < int(sample_ticks):
        return
    _TROUGH_LAST_SAMPLE_TICK[pid] = int(t)
    dq = _TROUGH_SAMPLES.get(pid)
    if dq is None:
        dq = deque()
        _TROUGH_SAMPLES[pid] = dq
    dq.append((int(t), float(mid)))
    cutoff = int(t) - int(look_ticks)
    while dq and int(dq[0][0]) < cutoff:
        dq.popleft()
    # hard cap (prune oldest) to avoid unbounded growth in edge cases
    try:
        cap = int((int(look_ticks) / max(1, int(sample_ticks))) + 10)
        while len(dq) > cap:
            dq.popleft()
    except Exception:
        pass


def _trough_compute(cfg: Dict[str, Any], pid: str, t: int, mid: float) -> Tuple[Optional[float], Optional[float], Optional[float], int]:
    """Returns (trough_pct, lo, hi, n). trough_pct in [0..1], where 0 is window low."""
    try:
        look_ticks, _sample_ticks, pct_max, min_samples = _trough_params(cfg)
    except Exception:
        return (None, None, None, 0)
    if not (0.0 < float(pct_max) < 1.0):
        return (None, None, None, 0)
    pid = str(pid)
    dq = _TROUGH_SAMPLES.get(pid)
    if not dq:
        return (None, None, None, 0)
    cutoff = int(t) - int(look_ticks)
    while dq and int(dq[0][0]) < cutoff:
        dq.popleft()
    n = int(len(dq))
    if n < int(min_samples):
        return (None, None, None, n)
    lo = float('inf')
    hi = float('-inf')
    try:
        for _tt, _m in dq:
            v = float(_m)
            if v < lo:
                lo = v
            if v > hi:
                hi = v
    except Exception:
        return (None, None, None, n)
    if not (hi > lo):
        return (None, lo, hi, n)
    pct = (float(mid) - lo) / (hi - lo)
    if pct < 0.0:
        pct = 0.0
    if pct > 1.0:
        pct = 1.0
    return (pct, lo, hi, n)


def _paper_sig_enabled(cfg: Dict[str, Any]) -> bool:
    try:
        return bool(cfg.get('PAPER_SIGNAL_LOG', True))
    except Exception:
        return True


def _paper_sig_gap_ticks(cfg: Dict[str, Any]) -> int:
    try:
        g = int(cfg.get('PAPER_SIGNAL_MIN_TICK_GAP', 60) or 60)
    except Exception:
        g = 60
    return 1 if g < 1 else g


def _paper_sig_should_log(cfg: Dict[str, Any], pid: str, t: int) -> bool:
    if not _paper_sig_enabled(cfg):
        return False
    gap = _paper_sig_gap_ticks(cfg)
    last = int(_PAPER_SIG_LAST_TICK.get(str(pid), -999999))
    if (t - last) < gap:
        return False
    _PAPER_SIG_LAST_TICK[str(pid)] = int(t)
    return True


def _paper_buy_signal(
    cfg: Dict[str, Any],
    t: int,
    pid: str,
    score: Any,
    m: Dict[str, Any],
    idea_state: Optional[Dict[str, Any]],
    blocked_by: str,
    extra: Optional[Dict[str, Any]] = None,
) -> None:
    # Emit a single [PAPER_BUY_SIGNAL] line to activity log (best-effort).
    try:
        if not _paper_sig_should_log(cfg, pid, t):
            return
        base = ''
        try:
            base = str(pid).split('-')[0].upper()
        except Exception:
            base = ''

        payload: Dict[str, Any] = {
            'ts_utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            'tick': int(t),
            'product_id': str(pid),
            'base': base,
            'mid': float(m.get('mid', 0) or 0),
            'score': float(score) if score is not None else 0.0,
            'spr_bps': float(m.get('spr_bps', 0) or 0),
            'tob_usd': float(m.get('tob', 0) or 0),
            'press': float(m.get('press', 0) or 0),
            'dmid_bps': float(m.get('dmid_bps', 0) or 0),
            'blocked_by': str(blocked_by or ''),
            'cfg': {
                'DRY': bool(cfg.get('DRY', False)),
                'AUTO_TRADE': bool(cfg.get('AUTO_TRADE', True)),
                'Z_BUY': cfg.get('Z_BUY', None),
                'BUY_CONFIRM_TICKS': cfg.get('BUY_CONFIRM_TICKS', None),
                'TREND_BPS_MIN': cfg.get('TREND_BPS_MIN', None),
                'TP_PCT': cfg.get('TP_PCT', None),
                'SL_PCT': cfg.get('SL_PCT', None),
            },
        }

        if isinstance(idea_state, dict):
            payload['idea'] = {
                'streak': int(idea_state.get('streak', 0) or 0),
                'pnl_bps': float(idea_state.get('pnl_bps', 0.0) or 0.0),
                'dd_bps': float(idea_state.get('dd_bps', 0.0) or 0.0),
            }

        if isinstance(extra, dict) and extra:
            payload.update(extra)

        _dry_pnl_open_from_payload(cfg, payload)
        _activity(cfg, f"[PAPER_BUY_SIGNAL] {json.dumps(payload, separators=(',',':'))}")
    except Exception:
        return


def _dry_pnl_enabled(cfg: Dict[str, Any]) -> bool:
    try:
        return bool(cfg.get("DRY", False)) and bool(cfg.get("DRY_PNL_LEDGER", True))
    except Exception:
        return False


def _dry_pnl_path(cfg: Dict[str, Any], key: str, default_rel: str) -> Path:
    raw = str(cfg.get(key) or default_rel)
    p = Path(raw)
    if not p.is_absolute():
        p = Path(ROOT) / p
    return p


def _dry_pnl_paths(cfg: Dict[str, Any]) -> Tuple[Path, Path, Path]:
    return (
        _dry_pnl_path(cfg, "DRY_PNL_LEDGER_PATH", "logs/dry_pnl_ledger.jsonl"),
        _dry_pnl_path(cfg, "DRY_PNL_STATE_PATH", "logs/dry_pnl_state.json"),
        _dry_pnl_path(cfg, "DRY_PNL_SUMMARY_PATH", "logs/dry_pnl_score.json"),
    )


def _dry_pnl_summary_default() -> Dict[str, Any]:
    return {
        "opened": 0,
        "closed": 0,
        "blocked_open": 0,
        "quarantined": 0,
        "wins": 0,
        "losses": 0,
        "realized_pnl_bps": 0.0,
        "realized_pnl_usd": 0.0,
        "unrealized_pnl_bps": 0.0,
        "unrealized_pnl_usd": 0.0,
        "marked_count": 0,
        "positive_open_count": 0,
        "negative_open_count": 0,
        "open_count": 0,
        "last_event_ts_utc": "",
        "last_mark_ts_utc": "",
        "last_mark_tick": 0,
    }


def _dry_pnl_utc_now() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _dry_pnl_epoch_from_ts(ts_text: Any) -> float:
    try:
        return float(calendar.timegm(time.strptime(str(ts_text or ""), "%Y-%m-%dT%H:%M:%SZ")))
    except Exception:
        return 0.0


def _dry_pnl_recent_stats_from_ledger(cfg: Dict[str, Any], max_bytes: int = 262144) -> Dict[str, Dict[str, Any]]:
    stats: Dict[str, Dict[str, Any]] = {}
    try:
        ledger_path, _, _ = _dry_pnl_paths(cfg)
        if not ledger_path.exists():
            return stats
        size = ledger_path.stat().st_size
        with open(ledger_path, "rb") as fh:
            fh.seek(max(0, size - int(max_bytes)))
            lines = fh.read().decode("utf-8", errors="ignore").splitlines()
        for line in lines:
            try:
                event = json.loads(line)
            except Exception:
                continue
            if not isinstance(event, dict) or event.get("type") != "close":
                continue
            pid = str(event.get("product_id") or "").strip().upper()
            if not pid:
                continue
            row = stats.setdefault(pid, {"closed": 0, "wins": 0, "losses": 0, "pnl_usd": 0.0, "pnl_bps": 0.0})
            pnl_usd = _safe_float(event.get("pnl_usd"), 0.0)
            pnl_bps = _safe_float(event.get("pnl_bps"), 0.0)
            row["closed"] = int(row.get("closed", 0) or 0) + 1
            row["pnl_usd"] = round(float(row.get("pnl_usd", 0.0) or 0.0) + pnl_usd, 8)
            row["pnl_bps"] = round(float(row.get("pnl_bps", 0.0) or 0.0) + pnl_bps, 4)
            if pnl_usd > 0.0:
                row["wins"] = int(row.get("wins", 0) or 0) + 1
            elif pnl_usd < 0.0:
                row["losses"] = int(row.get("losses", 0) or 0) + 1
    except Exception:
        return stats
    return stats


def _dry_pnl_load(cfg: Dict[str, Any]) -> None:
    if _DRY_PNL_STATE.get("loaded"):
        return
    _, state_path, _ = _dry_pnl_paths(cfg)
    state: Dict[str, Any] = {"open": {}, "summary": _dry_pnl_summary_default(), "quarantine": {}, "stats": {}}
    try:
        if state_path.exists():
            loaded = json.loads(state_path.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                state["open"] = loaded.get("open") if isinstance(loaded.get("open"), dict) else {}
                state["quarantine"] = loaded.get("quarantine") if isinstance(loaded.get("quarantine"), dict) else {}
                state["stats"] = loaded.get("stats") if isinstance(loaded.get("stats"), dict) else {}
                summary = _dry_pnl_summary_default()
                if isinstance(loaded.get("summary"), dict):
                    summary.update(loaded.get("summary") or {})
                state["summary"] = summary
    except Exception:
        state = {"open": {}, "summary": _dry_pnl_summary_default(), "quarantine": {}, "stats": {}}
    try:
        ledger_stats = _dry_pnl_recent_stats_from_ledger(cfg)
        if ledger_stats:
            merged = state.setdefault("stats", {})
            if isinstance(merged, dict):
                merged.update(ledger_stats)
    except Exception:
        pass
    _DRY_PNL_STATE.clear()
    _DRY_PNL_STATE.update(state)
    _DRY_PNL_STATE["loaded"] = True
    try:
        ledger_path, state_path, summary_path = _dry_pnl_paths(cfg)
        if not state_path.exists() or not summary_path.exists():
            _dry_pnl_write_state(cfg)
        if not ledger_path.exists():
            ledger_path.parent.mkdir(parents=True, exist_ok=True)
            ledger_path.touch()
    except Exception:
        pass
    try:
        _dry_pnl_prune_loaded_stale_open(cfg)
    except Exception:
        pass


def _dry_pnl_write_state(cfg: Dict[str, Any]) -> None:
    try:
        _, state_path, summary_path = _dry_pnl_paths(cfg)
        state_path.parent.mkdir(parents=True, exist_ok=True)
        summary_path.parent.mkdir(parents=True, exist_ok=True)
        summary = dict(_DRY_PNL_STATE.get("summary") or _dry_pnl_summary_default())
        summary["open_count"] = len(_DRY_PNL_STATE.get("open") or {})
        state = {
            "open": _DRY_PNL_STATE.get("open") or {},
            "quarantine": _DRY_PNL_STATE.get("quarantine") or {},
            "stats": _DRY_PNL_STATE.get("stats") or {},
            "summary": summary,
        }
        tmp_state = state_path.with_suffix(state_path.suffix + ".tmp")
        tmp_summary = summary_path.with_suffix(summary_path.suffix + ".tmp")
        tmp_state.write_text(json.dumps(state, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        tmp_summary.write_text(json.dumps(summary, separators=(",", ":"), sort_keys=True), encoding="utf-8")
        os.replace(str(tmp_state), str(state_path))
        os.replace(str(tmp_summary), str(summary_path))
    except Exception:
        return


def _dry_pnl_append(cfg: Dict[str, Any], event: Dict[str, Any]) -> None:
    try:
        ledger_path, _, _ = _dry_pnl_paths(cfg)
        ledger_path.parent.mkdir(parents=True, exist_ok=True)
        with open(ledger_path, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(event, separators=(",", ":"), sort_keys=True) + "\n")
    except Exception:
        return


def _dry_pnl_prune_loaded_stale_open(cfg: Dict[str, Any]) -> None:
    open_rows = _DRY_PNL_STATE.setdefault("open", {})
    if not isinstance(open_rows, dict) or not open_rows:
        return
    stale_age_min = _safe_float(cfg.get("DRY_PNL_STALE_MAX_MIN", 240.0), 240.0)
    stale_max_bps = _safe_float(cfg.get("DRY_PNL_STALE_EXIT_MAX_BPS", 0.0), 0.0)
    if stale_age_min <= 0.0:
        return
    now = time.time()
    now_utc = _dry_pnl_utc_now()
    summary = _DRY_PNL_STATE.setdefault("summary", _dry_pnl_summary_default())
    stats = _DRY_PNL_STATE.setdefault("stats", {})
    changed = False
    for pid, pos in list(open_rows.items()):
        if not isinstance(pos, dict):
            continue
        entry_ts = _dry_pnl_epoch_from_ts(pos.get("entry_ts_utc"))
        age_min = ((now - entry_ts) / 60.0) if entry_ts > 0.0 else 0.0
        pnl_bps = _safe_float(pos.get("last_pnl_bps"), 0.0)
        if age_min < stale_age_min or pnl_bps > stale_max_bps:
            continue
        entry = _safe_float(pos.get("entry_mid"), 0.0)
        event = {
            "type": "close",
            "product_id": str(pid),
            "exit_reason": "stale_loaded",
            "exit_ts_utc": now_utc,
            "exit_tick": _safe_int(summary.get("last_mark_tick"), 0),
            "exit_mid": float(_safe_float(pos.get("last_mid"), entry)),
            "entry_mid": float(entry),
            "pnl_bps": round(float(pnl_bps), 4),
            "pnl_usd": round(float(_safe_float(pos.get("last_pnl_usd"), 0.0)), 8),
            "notional_usd": _safe_float(pos.get("notional_usd"), _dry_pnl_notional_usd(cfg)),
            "entry_ts_utc": pos.get("entry_ts_utc"),
            "entry_tick": pos.get("entry_tick"),
        }
        open_rows.pop(pid, None)
        summary["closed"] = int(summary.get("closed", 0) or 0) + 1
        if float(event.get("pnl_bps") or 0.0) > 0.0:
            summary["wins"] = int(summary.get("wins", 0) or 0) + 1
        elif float(event.get("pnl_bps") or 0.0) < 0.0:
            summary["losses"] = int(summary.get("losses", 0) or 0) + 1
        if isinstance(stats, dict):
            srow = stats.setdefault(str(pid), {"closed": 0, "wins": 0, "losses": 0, "pnl_usd": 0.0, "pnl_bps": 0.0})
            srow["closed"] = int(srow.get("closed", 0) or 0) + 1
            if float(event.get("pnl_usd") or 0.0) > 0.0:
                srow["wins"] = int(srow.get("wins", 0) or 0) + 1
            elif float(event.get("pnl_usd") or 0.0) < 0.0:
                srow["losses"] = int(srow.get("losses", 0) or 0) + 1
            srow["pnl_usd"] = round(float(srow.get("pnl_usd", 0.0) or 0.0) + float(event.get("pnl_usd") or 0.0), 8)
            srow["pnl_bps"] = round(float(srow.get("pnl_bps", 0.0) or 0.0) + float(event.get("pnl_bps") or 0.0), 4)
        summary["realized_pnl_bps"] = round(float(summary.get("realized_pnl_bps", 0.0) or 0.0) + float(event.get("pnl_bps") or 0.0), 4)
        summary["realized_pnl_usd"] = round(float(summary.get("realized_pnl_usd", 0.0) or 0.0) + float(event.get("pnl_usd") or 0.0), 8)
        summary["last_event_ts_utc"] = now_utc
        _dry_pnl_append(cfg, event)
        changed = True
    if changed:
        summary["open_count"] = len(open_rows)
        _dry_pnl_write_state(cfg)


def _dry_pnl_notional_usd(cfg: Dict[str, Any]) -> float:
    return max(0.0, _safe_float(cfg.get("SOLDIER_USD", 10.0), 10.0))


def _dry_pnl_profit_protect_reason(cfg: Dict[str, Any], pos: Dict[str, Any], pnl_bps: float, age_min: float) -> str:
    if not bool(cfg.get("DRY_PNL_PROFIT_PROTECT_ENABLED", False)):
        return ""
    min_age = _safe_float(cfg.get("DRY_PNL_PROFIT_PROTECT_MIN_AGE_MIN", 0.0), 0.0)
    if age_min < min_age:
        return ""
    peak_bps = _safe_float(pos.get("peak_pnl_bps"), pnl_bps)
    min_peak_bps = _safe_float(cfg.get("DRY_PNL_PROFIT_PROTECT_MIN_PEAK_BPS", 40.0), 40.0)
    giveback_bps = abs(_safe_float(cfg.get("DRY_PNL_PROFIT_PROTECT_GIVEBACK_BPS", 25.0), 25.0))
    retain_bps = _safe_float(cfg.get("DRY_PNL_PROFIT_PROTECT_RETAIN_BPS", 5.0), 5.0)
    if giveback_bps <= 0.0:
        return ""
    if peak_bps >= min_peak_bps and pnl_bps >= retain_bps and pnl_bps <= (peak_bps - giveback_bps):
        return "profit_protect"
    return ""


def _dry_pnl_pid_has_positive_expectancy(pid: str, cfg: Dict[str, Any]) -> bool:
    stats = _DRY_PNL_STATE.get("stats") if isinstance(_DRY_PNL_STATE.get("stats"), dict) else {}
    row = stats.get(str(pid or "").strip().upper()) if isinstance(stats, dict) else None
    if not isinstance(row, dict):
        return False
    min_closed = max(1, _safe_int(cfg.get("DRY_PNL_MIN_CLOSED_FOR_EXPECTANCY", 1), 1))
    min_pnl_usd = _safe_float(cfg.get("DRY_PNL_MIN_EXPECTANCY_USD", 0.01), 0.01)
    min_avg_bps = _safe_float(cfg.get("DRY_PNL_MIN_EXPECTANCY_AVG_BPS", 1.0), 1.0)
    closed = _safe_int(row.get("closed"), 0)
    wins = _safe_int(row.get("wins"), 0)
    losses = _safe_int(row.get("losses"), 0)
    pnl_usd = _safe_float(row.get("pnl_usd"), 0.0)
    pnl_bps = _safe_float(row.get("pnl_bps"), 0.0)
    avg_bps = pnl_bps / float(max(1, closed))
    return bool(
        closed >= min_closed
        and pnl_usd >= min_pnl_usd
        and avg_bps >= min_avg_bps
        and wins > 0
        and wins > losses
    )


def _dry_pnl_entry_block_reason(cfg: Dict[str, Any], pid: str) -> str:
    summary = _DRY_PNL_STATE.get("summary") if isinstance(_DRY_PNL_STATE.get("summary"), dict) else {}
    open_rows = _DRY_PNL_STATE.get("open") if isinstance(_DRY_PNL_STATE.get("open"), dict) else {}
    quarantine = _DRY_PNL_STATE.get("quarantine") if isinstance(_DRY_PNL_STATE.get("quarantine"), dict) else {}
    pid = str(pid or "").strip().upper()
    now_ts = time.time()
    q_row = quarantine.get(pid) if isinstance(quarantine.get(pid), dict) else {}
    q_until = _safe_float((q_row or {}).get("until_ts"), 0.0) if isinstance(q_row, dict) else 0.0
    if q_until > now_ts:
        q_reason = str((q_row or {}).get("reason") or "")
        can_override = bool(
            cfg.get("DRY_PNL_ALLOW_EXPECTANCY_QUARANTINE_OVERRIDE", True)
            and q_reason in {"stale", "stale_unmarked", "stale_last_mark"}
            and _dry_pnl_pid_has_positive_expectancy(pid, cfg)
        )
        if not can_override:
            return "quarantine"
    max_open = _safe_int(cfg.get("DRY_PNL_MAX_OPEN_POSITIONS", 12), 12)
    if max_open > 0 and len(open_rows or {}) >= max_open:
        return "max_open"
    realized_usd = _safe_float(summary.get("realized_pnl_usd"), 0.0)
    unrealized_usd = _safe_float(summary.get("unrealized_pnl_usd"), 0.0)
    net_usd = realized_usd + unrealized_usd
    neg_open = _safe_int(summary.get("negative_open_count"), 0)
    pos_open = _safe_int(summary.get("positive_open_count"), 0)
    max_negative_share = _safe_float(cfg.get("DRY_PNL_MAX_NEGATIVE_OPEN_SHARE"), 0.0)
    if max_negative_share > 0.0 and neg_open > 0:
        open_count = max(1, _safe_int(summary.get("open_count"), len(open_rows or {})))
        negative_share = float(neg_open) / float(open_count)
        if negative_share > max_negative_share:
            can_override_negative_share = bool(
                cfg.get("DRY_PNL_ALLOW_EXPECTANCY_OVERRIDE_NEGATIVE_OPEN_SHARE", True)
                and _dry_pnl_pid_has_positive_expectancy(pid, cfg)
            )
            if not can_override_negative_share:
                return "negative_open_share"
    basket_negative = bool(unrealized_usd < 0.0 or neg_open > pos_open)
    net_negative = bool(net_usd < 0.0 and bool(cfg.get("DRY_PNL_BLOCK_NEW_WHEN_NET_NEGATIVE", True)))
    if basket_negative and bool(cfg.get("DRY_PNL_BLOCK_NEW_WHEN_UNREALIZED_NEGATIVE", True)):
        return "basket_negative"
    if net_negative:
        if net_negative and bool(cfg.get("DRY_PNL_HARD_BLOCK_WHEN_NET_NEGATIVE", True)):
            return "net_negative"
        if bool(cfg.get("DRY_PNL_REQUIRE_POSITIVE_EXPECTANCY_WHEN_NEGATIVE", True)):
            if not _dry_pnl_pid_has_positive_expectancy(pid, cfg):
                if net_negative and bool(cfg.get("DRY_PNL_ALLOW_SCOUT_WHEN_NET_NEGATIVE", False)) and not open_rows:
                    return ""
                return "net_negative_no_expectancy" if net_negative else "basket_negative_no_expectancy"
        else:
            return "net_negative" if net_negative else "basket_negative"
    return ""


def _dry_pnl_record_blocked_open(cfg: Dict[str, Any], pid: str, payload: Dict[str, Any], reason: str) -> None:
    now_utc = _dry_pnl_utc_now()
    summary = _DRY_PNL_STATE.setdefault("summary", _dry_pnl_summary_default())
    summary["blocked_open"] = int(summary.get("blocked_open", 0) or 0) + 1
    summary["last_event_ts_utc"] = now_utc
    _dry_pnl_append(cfg, {
        "type": "blocked_open",
        "product_id": str(pid or "").strip().upper(),
        "reason": str(reason or ""),
        "ts_utc": now_utc,
        "tick": _safe_int(payload.get("tick"), 0),
        "mid": _safe_float(payload.get("mid"), 0.0),
        "score": _safe_float(payload.get("score"), 0.0),
    })
    _dry_pnl_write_state(cfg)


def _dry_pnl_open_from_payload(cfg: Dict[str, Any], payload: Dict[str, Any]) -> None:
    if not _dry_pnl_enabled(cfg) or str(payload.get("blocked_by") or "").lower() != "dry":
        return
    pid = str(payload.get("product_id") or "").strip().upper()
    entry_mid = _safe_float(payload.get("mid"), 0.0)
    if not pid or entry_mid <= 0.0:
        return
    with _DRY_PNL_LOCK:
        _dry_pnl_load(cfg)
        open_rows = _DRY_PNL_STATE.setdefault("open", {})
        if pid in open_rows:
            return
        block_reason = _dry_pnl_entry_block_reason(cfg, pid)
        if block_reason:
            _dry_pnl_record_blocked_open(cfg, pid, payload, block_reason)
            return
        now_utc = _dry_pnl_utc_now()
        row = {
            "product_id": pid,
            "entry_ts_utc": str(payload.get("ts_utc") or now_utc),
            "entry_tick": _safe_int(payload.get("tick"), 0),
            "entry_mid": float(entry_mid),
            "score": _safe_float(payload.get("score"), 0.0),
            "tp_pct": _pct_points(cfg.get("DRY_PNL_TP_PCT", cfg.get("TP_PCT", 0.0)), 0.0),
            "sl_pct": _pct_points(cfg.get("DRY_PNL_SL_PCT", cfg.get("SL_PCT", 0.0)), 0.0),
            "notional_usd": _dry_pnl_notional_usd(cfg),
        }
        open_rows[pid] = row
        summary = _DRY_PNL_STATE.setdefault("summary", _dry_pnl_summary_default())
        summary["opened"] = int(summary.get("opened", 0) or 0) + 1
        summary["last_event_ts_utc"] = now_utc
        _dry_pnl_append(cfg, {"type": "open", **row})
        _dry_pnl_write_state(cfg)


def _dry_pnl_quarantine_pid(cfg: Dict[str, Any], pid: str, reason: str) -> None:
    try:
        mins = max(1.0, _safe_float(cfg.get("DRY_PNL_QUARANTINE_MIN", 720.0), 720.0))
        until_ts = time.time() + (mins * 60.0)
        quarantine = _DRY_PNL_STATE.setdefault("quarantine", {})
        if isinstance(quarantine, dict):
            quarantine[str(pid or "").strip().upper()] = {
                "reason": str(reason or ""),
                "until_ts": float(until_ts),
                "until_utc": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(until_ts)),
            }
        summary = _DRY_PNL_STATE.setdefault("summary", _dry_pnl_summary_default())
        summary["quarantined"] = int(summary.get("quarantined", 0) or 0) + 1
    except Exception:
        return


def _dry_pnl_mark_from_rows(cfg: Dict[str, Any], t: int, rows: Any) -> None:
    if not _dry_pnl_enabled(cfg):
        return
    with _DRY_PNL_LOCK:
        _dry_pnl_load(cfg)
    if isinstance(rows, dict):
        iterable_rows = []
        for pid_key, metric_row in rows.items():
            if isinstance(metric_row, dict):
                item = dict(metric_row)
                item.setdefault("product_id", pid_key)
                iterable_rows.append(item)
        rows = iterable_rows
    if not isinstance(rows, list):
        return
    mids: Dict[str, float] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("product_id") or row.get("pid") or row.get("symbol") or "").strip().upper()
        mid = _safe_float(row.get("mid"), 0.0)
        if pid and mid > 0.0:
            mids[pid] = mid
    if not mids:
        return
    with _DRY_PNL_LOCK:
        open_rows = _DRY_PNL_STATE.setdefault("open", {})
        if not open_rows:
            summary = _DRY_PNL_STATE.setdefault("summary", _dry_pnl_summary_default())
            summary["open_count"] = 0
            summary["marked_count"] = 0
            summary["unrealized_pnl_bps"] = 0.0
            summary["unrealized_pnl_usd"] = 0.0
            summary["positive_open_count"] = 0
            summary["negative_open_count"] = 0
            _dry_pnl_write_state(cfg)
            return
        summary = _DRY_PNL_STATE.setdefault("summary", _dry_pnl_summary_default())
        now_utc = _dry_pnl_utc_now()
        closed: List[Tuple[str, Dict[str, Any]]] = []
        unrealized_bps_total = 0.0
        unrealized_usd_total = 0.0
        marked_count = 0
        positive_count = 0
        negative_count = 0
        for pid, pos in list(open_rows.items()):
            mid = mids.get(pid)
            if mid is None or mid <= 0.0:
                continue
            entry = _safe_float(pos.get("entry_mid"), 0.0)
            if entry <= 0.0:
                continue
            pnl_bps = ((float(mid) - entry) / entry) * 10000.0
            notional = _safe_float(pos.get("notional_usd"), _dry_pnl_notional_usd(cfg))
            pnl_usd = notional * (pnl_bps / 10000.0)
            pos["last_mid"] = float(mid)
            pos["last_mark_tick"] = int(t)
            pos["last_mark_ts_utc"] = now_utc
            pos["last_pnl_bps"] = round(float(pnl_bps), 4)
            pos["last_pnl_usd"] = round(float(pnl_usd), 8)
            prior_peak_bps = _safe_float(pos.get("peak_pnl_bps"), pnl_bps)
            if "peak_pnl_bps" not in pos or pnl_bps > prior_peak_bps:
                pos["peak_pnl_bps"] = round(float(pnl_bps), 4)
                pos["peak_pnl_usd"] = round(float(pnl_usd), 8)
                pos["peak_mid"] = float(mid)
                pos["peak_tick"] = int(t)
                pos["peak_ts_utc"] = now_utc
            unrealized_bps_total += float(pnl_bps)
            unrealized_usd_total += float(pnl_usd)
            marked_count += 1
            if pnl_bps >= 0.0:
                positive_count += 1
            else:
                negative_count += 1
            stored_tp_bps = _safe_float(pos.get("tp_pct"), 0.0)
            cfg_tp_bps = _pct_points(cfg.get("DRY_PNL_TP_PCT", cfg.get("TP_PCT", 0.0)), 0.0)
            tp_candidates = [v for v in (stored_tp_bps, cfg_tp_bps) if v > 0.0]
            tp_bps = min(tp_candidates) if tp_candidates else 0.0
            stored_sl_bps = abs(_safe_float(pos.get("sl_pct"), 0.0))
            cfg_sl_bps = abs(_pct_points(cfg.get("DRY_PNL_SL_PCT", cfg.get("SL_PCT", 0.0)), 0.0))
            sl_candidates = [v for v in (stored_sl_bps, cfg_sl_bps) if v > 0.0]
            sl_bps = -min(sl_candidates) if sl_candidates else 0.0
            reason = ""
            summary_now = _DRY_PNL_STATE.get("summary") if isinstance(_DRY_PNL_STATE.get("summary"), dict) else {}
            basket_negative = bool(_safe_float(summary_now.get("unrealized_pnl_usd"), 0.0) < 0.0)
            net_negative = bool((_safe_float(summary_now.get("realized_pnl_usd"), 0.0) + _safe_float(summary_now.get("unrealized_pnl_usd"), 0.0)) < 0.0)
            force_age = _safe_float(cfg.get("DRY_PNL_FORCE_LOSS_MIN_AGE_MIN", 45.0), 45.0)
            force_bps = _safe_float(cfg.get("DRY_PNL_FORCE_LOSS_MAX_BPS", -75.0), -75.0)
            entry_ts = _dry_pnl_epoch_from_ts(pos.get("entry_ts_utc"))
            age_min = ((time.time() - entry_ts) / 60.0) if entry_ts > 0.0 else 0.0
            if (
                bool(cfg.get("DRY_PNL_FORCE_CLOSE_LOSERS_WHEN_BASKET_NEGATIVE", True))
                and net_negative
                and pnl_bps <= force_bps
                and age_min >= force_age
            ):
                reason = "loss_trim"
            elif tp_bps > 0.0 and pnl_bps >= tp_bps:
                reason = "tp"
            elif sl_bps < 0.0 and pnl_bps <= sl_bps:
                reason = "sl"
            else:
                reason = _dry_pnl_profit_protect_reason(cfg, pos, float(pnl_bps), float(age_min))
                if not reason:
                    max_age_min = _safe_float(cfg.get("DRY_PNL_STALE_MAX_MIN", 240.0), 240.0)
                    stale_max_bps = _safe_float(cfg.get("DRY_PNL_STALE_EXIT_MAX_BPS", 0.0), 0.0)
                    if max_age_min > 0.0 and age_min >= max_age_min and pnl_bps <= stale_max_bps:
                        reason = "stale"
                    else:
                        if bool(cfg.get("DRY_PNL_FORCE_CLOSE_LOSERS_WHEN_BASKET_NEGATIVE", True)) and (basket_negative or net_negative):
                            if age_min >= force_age and pnl_bps <= force_bps:
                                reason = "loss_trim"
            if not reason:
                continue
            event = {
                "type": "close",
                "product_id": pid,
                "exit_reason": reason,
                "exit_ts_utc": now_utc,
                "exit_tick": int(t),
                "exit_mid": float(mid),
                "entry_mid": entry,
                "pnl_bps": round(float(pnl_bps), 4),
                "pnl_usd": round(float(pnl_usd), 8),
                "notional_usd": notional,
                "entry_ts_utc": pos.get("entry_ts_utc"),
                "entry_tick": pos.get("entry_tick"),
            }
            for optional_key in ("peak_pnl_bps", "peak_pnl_usd", "peak_mid", "peak_tick", "peak_ts_utc"):
                if optional_key in pos:
                    event[optional_key] = pos.get(optional_key)
            closed.append((pid, event))
        stale_unmarked_max_min = _safe_float(cfg.get("DRY_PNL_UNMARKED_STALE_MAX_MIN", 360.0), 360.0)
        if stale_unmarked_max_min > 0.0:
            for pid, pos in list(open_rows.items()):
                if pid in mids:
                    continue
                entry_ts = _dry_pnl_epoch_from_ts(pos.get("entry_ts_utc"))
                age_min = ((time.time() - entry_ts) / 60.0) if entry_ts > 0.0 else 0.0
                last_pnl_bps = _safe_float(pos.get("last_pnl_bps"), None)
                last_pnl_usd = _safe_float(pos.get("last_pnl_usd"), None)
                last_mid = _safe_float(pos.get("last_mid"), 0.0)
                has_last_mark = bool(last_pnl_bps is not None and last_pnl_usd is not None and last_mid > 0.0)
                if has_last_mark:
                    stale_max_bps = _safe_float(cfg.get("DRY_PNL_STALE_EXIT_MAX_BPS", 0.0), 0.0)
                    stale_age_min = _safe_float(cfg.get("DRY_PNL_STALE_MAX_MIN", 240.0), 240.0)
                    summary_now = _DRY_PNL_STATE.get("summary") if isinstance(_DRY_PNL_STATE.get("summary"), dict) else {}
                    net_negative = bool((_safe_float(summary_now.get("realized_pnl_usd"), 0.0) + _safe_float(summary_now.get("unrealized_pnl_usd"), 0.0)) < 0.0)
                    close_last_mark_loss = bool(
                        cfg.get("DRY_PNL_FORCE_CLOSE_LOSERS_WHEN_BASKET_NEGATIVE", True)
                        and net_negative
                        and float(last_pnl_bps) < 0.0
                    )
                    profit_protect_last_mark = bool(
                        _dry_pnl_profit_protect_reason(cfg, pos, float(last_pnl_bps), float(age_min))
                    )
                    if (
                        profit_protect_last_mark
                        or close_last_mark_loss
                        or (stale_age_min > 0.0 and age_min >= stale_age_min and float(last_pnl_bps) <= stale_max_bps)
                    ):
                        notional = _safe_float(pos.get("notional_usd"), _dry_pnl_notional_usd(cfg))
                        exit_reason = "profit_protect"
                        if not profit_protect_last_mark:
                            exit_reason = "loss_trim" if close_last_mark_loss else "stale_last_mark"
                        event = {
                            "type": "close",
                            "product_id": pid,
                            "exit_reason": exit_reason,
                            "exit_ts_utc": now_utc,
                            "exit_tick": int(t),
                            "exit_mid": float(last_mid),
                            "entry_mid": _safe_float(pos.get("entry_mid"), 0.0),
                            "pnl_bps": round(float(last_pnl_bps), 4),
                            "pnl_usd": round(float(last_pnl_usd), 8),
                            "notional_usd": notional,
                            "entry_ts_utc": pos.get("entry_ts_utc"),
                            "entry_tick": pos.get("entry_tick"),
                        }
                        for optional_key in ("peak_pnl_bps", "peak_pnl_usd", "peak_mid", "peak_tick", "peak_ts_utc"):
                            if optional_key in pos:
                                event[optional_key] = pos.get(optional_key)
                        closed.append((pid, event))
                        continue
                    unrealized_bps_total += float(last_pnl_bps)
                    unrealized_usd_total += float(last_pnl_usd)
                    marked_count += 1
                    if float(last_pnl_bps) >= 0.0:
                        positive_count += 1
                    else:
                        negative_count += 1
                    continue
                if age_min < stale_unmarked_max_min:
                    continue
                entry = _safe_float(pos.get("entry_mid"), 0.0)
                notional = _safe_float(pos.get("notional_usd"), _dry_pnl_notional_usd(cfg))
                event = {
                    "type": "close",
                    "product_id": pid,
                    "exit_reason": "stale_unmarked",
                    "exit_ts_utc": now_utc,
                    "exit_tick": int(t),
                    "exit_mid": entry,
                    "entry_mid": entry,
                    "pnl_bps": 0.0,
                    "pnl_usd": 0.0,
                    "notional_usd": notional,
                    "entry_ts_utc": pos.get("entry_ts_utc"),
                    "entry_tick": pos.get("entry_tick"),
                }
                closed.append((pid, event))
        summary["open_count"] = len(open_rows)
        summary["marked_count"] = int(marked_count)
        summary["unrealized_pnl_bps"] = round(float(unrealized_bps_total), 4)
        summary["unrealized_pnl_usd"] = round(float(unrealized_usd_total), 8)
        summary["positive_open_count"] = int(positive_count)
        summary["negative_open_count"] = int(negative_count)
        summary["last_mark_ts_utc"] = now_utc
        summary["last_mark_tick"] = int(t)
        if not closed:
            _dry_pnl_write_state(cfg)
            return
        for pid, event in closed:
            open_rows.pop(pid, None)
            summary["closed"] = int(summary.get("closed", 0) or 0) + 1
            if float(event.get("pnl_bps") or 0.0) > 0.0:
                summary["wins"] = int(summary.get("wins", 0) or 0) + 1
            elif float(event.get("pnl_bps") or 0.0) < 0.0:
                summary["losses"] = int(summary.get("losses", 0) or 0) + 1
            stats = _DRY_PNL_STATE.setdefault("stats", {})
            if isinstance(stats, dict):
                srow = stats.setdefault(pid, {"closed": 0, "wins": 0, "losses": 0, "pnl_usd": 0.0, "pnl_bps": 0.0})
                srow["closed"] = int(srow.get("closed", 0) or 0) + 1
                if float(event.get("pnl_usd") or 0.0) > 0.0:
                    srow["wins"] = int(srow.get("wins", 0) or 0) + 1
                elif float(event.get("pnl_usd") or 0.0) < 0.0:
                    srow["losses"] = int(srow.get("losses", 0) or 0) + 1
                srow["pnl_usd"] = round(float(srow.get("pnl_usd", 0.0) or 0.0) + float(event.get("pnl_usd") or 0.0), 8)
                srow["pnl_bps"] = round(float(srow.get("pnl_bps", 0.0) or 0.0) + float(event.get("pnl_bps") or 0.0), 4)
            if (
                str(event.get("exit_reason") or "") in {"sl", "stale", "stale_unmarked", "stale_last_mark", "loss_trim"}
                and float(event.get("pnl_usd") or 0.0) < 0.0
            ):
                _dry_pnl_quarantine_pid(cfg, pid, str(event.get("exit_reason") or ""))
            summary["realized_pnl_bps"] = round(float(summary.get("realized_pnl_bps", 0.0) or 0.0) + float(event.get("pnl_bps") or 0.0), 4)
            summary["realized_pnl_usd"] = round(float(summary.get("realized_pnl_usd", 0.0) or 0.0) + float(event.get("pnl_usd") or 0.0), 8)
            summary["last_event_ts_utc"] = now_utc
            _dry_pnl_append(cfg, event)
        summary["open_count"] = len(open_rows)
        _dry_pnl_write_state(cfg)



# MM16_GET_HELPER
def _get(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


# Ensure project root is importable when run as a script:
#   python managers\\run_manager\\run_manager.py --console
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from managers.config_manager.settings import load_settings

# Prefer package import; fall back to root-level auth_jwt.py
try:
    from managers.auth_manager.auth_jwt import get_client
except ImportError:  # pragma: no cover - direct run fallback
    from auth_jwt import get_client  # type: ignore[no-redef]

from managers.strategy_manager import strategy_core as strat
from managers.strategy_manager import tdi_score
from managers.logging_manager import tdi_logger
from managers.orders_manager import orders_place as orders
from managers.orders_manager import exit_engine  # used for TP handoff
from managers.orders_manager import limit_maker
from managers.orders_manager import stop_loss  # MM16 soft stop-loss


# Dynamic universe (PEPE / WIF / TRUMP, etc.) – best effort.
try:  # pragma: no cover - import can fail harmlessly
    from managers.universe_manager import universe_dynamic as u_dyn
except Exception:  # noqa: E722
    u_dyn = None  # type: ignore[assignment]

D = Decimal



# ---------- MM19_UNI_CACHE ----------
_UNI_CACHE: Dict[str, Any] = {}
# ---------- /MM19_UNI_CACHE ----------

# ---------- small utils ----------

def _D(x: Any) -> D:
    if isinstance(x, D):
        return x
    try:
        return D(str(x))
    except (InvalidOperation, Exception):
        return D("0")


def _ok(resp: Any) -> bool:
    if isinstance(resp, dict):
        if resp.get("ok") is True or resp.get("success") is True:
            return True
        r = resp.get("response")
        if isinstance(r, dict) and r.get("success") is True:
            return True
    return False


def _fmt_bp(x: Any) -> str:
    try:
        return f"{_D(x):>5.1f}"
    except Exception:
        return "  0.0"


def _utc_hms() -> str:
    try:
        from datetime import UTC, datetime

        return datetime.now(UTC).strftime("%H:%M:%S")
    except Exception:
        from datetime import datetime

        return datetime.utcnow().strftime("%H:%M:%S")


def _write_run_active(path: str) -> None:
    try:
        parent = os.path.dirname(path) or "."
        os.makedirs(parent, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(json.dumps({"pid": os.getpid(), "ts": _utc_hms()}))
    except Exception:
        # best-effort only
        pass


# ---------- Activity ticker + async maintenance ----------
_ACTIVITY_WRITE_LOCK = threading.Lock()  # serialize log writes
_MAINT_LOCK = threading.Lock()           # held while async maintenance runs
_ACTIVITY_TICKER_PID: Optional[int] = None

# Offline / network backoff (travel-safe): when the Coinbase REST API is unreachable,
# pause maintenance + trading briefly instead of spamming errors or making risky changes.
_OFFLINE_UNTIL_TS: float = 0.0
_OFFLINE_BACKOFF_SEC: float = 0.0
_OFFLINE_FAILS: int = 0
_LAST_OFFLINE_LOG_TS: float = 0.0



def _activity_log_path(cfg: Dict[str, Any]) -> Path:
    """Return path to the activity ticker log file."""
    p = str(cfg.get("ACTIVITY_LOG_PATH") or "logs/activity_ticker.log")
    try:
        path = Path(p)
        if not path.is_absolute():
            path = Path(ROOT) / path
        path.parent.mkdir(parents=True, exist_ok=True)
        return path
    except Exception:
        # last-resort: repo-root logs
        path = Path(ROOT) / "logs" / "activity_ticker.log"
        path.parent.mkdir(parents=True, exist_ok=True)
        return path


def _activity(cfg: Dict[str, Any], msg: str) -> None:
    """Append a single line to activity log (safe; never raises)."""
    try:
        ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        line = f"[{ts}] {msg}".rstrip() + "\n"
        path = _activity_log_path(cfg)
        with _ACTIVITY_WRITE_LOCK:
            with open(path, "a", encoding="utf-8") as f:
                f.write(line)
    except Exception:
        return


def _cfg_max_spr_bps(cfg: Dict[str, Any]) -> float:
    try:
        max_spr_bps = float(cfg.get("MAX_SPR_BPS", 0) or 0)
    except Exception:
        max_spr_bps = 0.0
    if max_spr_bps <= 0.0:
        try:
            max_spr_bps = float(cfg.get("MAX_SPREAD_PCT", 0.6) or 0.6) * 100.0
        except Exception:
            max_spr_bps = 60.0
    if max_spr_bps <= 0.0:
        max_spr_bps = 60.0
    return float(max_spr_bps)


def _tdi_context(
    cfg: Dict[str, Any],
    pid: str,
    score: Any,
    m: Dict[str, Any],
    tick: Optional[int] = None,
    pct24: Optional[float] = None,
    trough_info: Optional[Dict[str, Any]] = None,
    cycle_info: Optional[Dict[str, Any]] = None,
    tape_info: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    trough_info = dict(trough_info or {})
    cycle_info = dict(cycle_info or {})
    tape_info = dict(tape_info or _tape_quality_snapshot(pid, cfg, tick))
    flow_info = _market_flow_snapshot(cfg, m, tape_info, cycle_info)
    mid = float(m.get("mid", 0) or 0) if isinstance(m, dict) else 0.0
    out = {
        "tick": int(tick) if tick is not None else None,
        "product_id": str(pid),
        "price": float(mid),
        "bot_score": float(score) if score is not None else 0.0,
        "dmid_bps": float(m.get("dmid_bps", m.get("dmid", 0)) or 0) if isinstance(m, dict) else 0.0,
        "spr_bps": float(m.get("spr_bps", 0) or 0) if isinstance(m, dict) else 0.0,
        "tob_usd": float(m.get("tob", m.get("tob_usd", 0)) or 0) if isinstance(m, dict) else 0.0,
        "press": float(m.get("press", 0.5) or 0.5) if isinstance(m, dict) else 0.5,
        "g24h_pct": float(pct24) if pct24 is not None else None,
        "trough_pct": trough_info.get("trough_pct"),
        "trough_n": trough_info.get("trough_n"),
        "max_spr_bps": _cfg_max_spr_bps(cfg),
        "min_topbook_usd": float(cfg.get("MIN_TOPBOOK_USD", 50.0) or 50.0),
        "tape_fresh_ratio": float(tape_info.get("fresh_ratio", 0.0) or 0.0),
        "tape_spread_ok_ratio": float(tape_info.get("spread_ok_ratio", 0.0) or 0.0),
        "tape_press_ok_ratio": float(tape_info.get("press_ok_ratio", 0.0) or 0.0),
        "tape_top_ratio": float(tape_info.get("top_ratio_avg", 0.0) or 0.0),
        "tape_tob_usd_avg": float(tape_info.get("tob_usd_avg", 0.0) or 0.0),
        "tape_sample_n": int(tape_info.get("sample_n", 0) or 0),
        "tape_u0_streak": int(tape_info.get("u0_streak", 0) or 0),
        "tape_u0_cooldown": bool(tape_info.get("u0_cooldown", False)),
        "symbol_cohort": str(tape_info.get("symbol_cohort") or "standard"),
        "symbol_quality_score": float(tape_info.get("symbol_quality_score", 0.0) or 0.0),
        "symbol_reliability_sample_n": int(tape_info.get("symbol_reliability_sample_n", 0) or 0),
        "symbol_infra_hits": int(tape_info.get("symbol_reliability_infra_hits", 0) or 0),
        "symbol_infra_share": float(tape_info.get("symbol_reliability_infra_share", 0.0) or 0.0),
        "symbol_reliability_dominant_reason": str(tape_info.get("symbol_reliability_dominant_reason") or ""),
        "symbol_quarantined": bool(tape_info.get("symbol_quarantined", False)),
        "symbol_quarantine_reason": str(tape_info.get("symbol_quarantine_reason") or ""),
        "flow_score": float(flow_info.get("flow_score", 0.0) or 0.0),
        "flow_regime": str(flow_info.get("flow_regime") or ""),
        "flow_bullish_cycle": bool(flow_info.get("flow_bullish_cycle", False)),
        "flow_bearish_cycle": bool(flow_info.get("flow_bearish_cycle", False)),
        "flow_tob_ratio": float(flow_info.get("flow_tob_ratio", 0.0) or 0.0),
        "flow_spread_health": float(flow_info.get("flow_spread_health", 0.0) or 0.0),
        "flow_pressure_health": float(flow_info.get("flow_pressure_health", 0.0) or 0.0),
        "flow_momentum_push": float(flow_info.get("flow_momentum_push", 0.0) or 0.0),
    }
    if cycle_info:
        out.update({
            "cycle_interval": cycle_info.get("interval"),
            "cycle_phase": cycle_info.get("phase"),
            "cycle_confidence": cycle_info.get("confidence"),
            "cycle_tp_hit_rate_pct": cycle_info.get("tp_hit_rate_pct"),
            "cycle_qualified_troughs": cycle_info.get("qualified_troughs"),
            "cycle_support_score": cycle_info.get("support_score"),
            "cycle_bucket": cycle_info.get("dominant_bucket"),
            "cycle_stance": cycle_info.get("dominant_stance"),
            "cycle_bull_total": cycle_info.get("bull_total"),
            "cycle_bear_total": cycle_info.get("bear_total"),
            "cycle_allow": cycle_info.get("allow"),
            "cycle_block": cycle_info.get("block"),
            "cycle_top_stack": cycle_info.get("top_stack"),
        })
    return out


def _tdi_compute(
    cfg: Dict[str, Any],
    pid: str,
    score: Any,
    m: Dict[str, Any],
    tick: Optional[int] = None,
    pct24: Optional[float] = None,
    trough_info: Optional[Dict[str, Any]] = None,
    cycle_info: Optional[Dict[str, Any]] = None,
    tape_info: Optional[Dict[str, Any]] = None,
) -> Optional[Dict[str, Any]]:
    base = _tdi_context(
        cfg,
        pid,
        score,
        m,
        tick=tick,
        pct24=pct24,
        trough_info=trough_info,
        cycle_info=cycle_info,
        tape_info=tape_info,
    )
    try:
        payload = tdi_score.compute_tdi(base)
    except Exception as e:
        tdi_logger.write_error(cfg, str(pid), e, payload=base)
        return None
    if not isinstance(payload, dict):
        return None
    out = dict(base)
    out.update(payload)
    return out


def _tdi_preview_text(payload: Optional[Dict[str, Any]]) -> str:
    if not isinstance(payload, dict):
        return f"{'--':>6}  {'-':<27}"
    try:
        score = int(round(float(payload.get("tdi_score", 0) or 0)))
    except Exception:
        score = 0
    comps = payload.get("components") if isinstance(payload.get("components"), dict) else {}
    abbr = {"trough": "tro", "momentum": "mom", "liquidity": "liq", "spread": "spr", "pressure": "prs", "quality": "qlt"}
    bits: List[str] = []
    for name in payload.get("top_reasons") or []:
        if len(bits) >= 3:
            break
        key = str(name)
        try:
            sval = int(round(float(comps.get(key, 0) or 0)))
        except Exception:
            sval = 0
        bits.append(f"{abbr.get(key, key[:3]):>3}={sval:>3}")
    tail = " ".join(bits) if bits else "-"
    return f"{score:>6}  {tail:<27}"


def _tdi_snapshot_path(cfg: Dict[str, Any]) -> Path:
    rel = str(cfg.get("TDI_SNAPSHOT_PATH") or "logs/tdi_snapshots.jsonl")
    p = Path(rel)
    if not p.is_absolute():
        p = Path(ROOT) / p
    p.parent.mkdir(parents=True, exist_ok=True)
    return p


def _tdi_snapshot_self_heal(cfg: Dict[str, Any], reason: str = "write_fail") -> bool:
    path = _tdi_snapshot_path(cfg)
    rolled = None
    try:
        if path.exists():
            stamp = time.strftime("%Y%m%d_%H%M%S", time.localtime())
            rolled = path.with_name(f"{path.stem}_{reason}_{stamp}{path.suffix}")
            try:
                os.replace(path, rolled)
            except Exception:
                rolled = None
                with open(path, "w", encoding="utf-8"):
                    pass
        else:
            with open(path, "w", encoding="utf-8"):
                pass
        size_mb = 0.0
        try:
            if rolled is not None and rolled.exists():
                size_mb = float(rolled.stat().st_size) / (1024.0 * 1024.0)
        except Exception:
            size_mb = 0.0
        _activity(
            cfg,
            f"[tdi_snapshot] self-heal reason={reason} path={str(path)}"
            + (f" rolled={str(rolled)} size_mb={size_mb:.1f}" if rolled is not None else ""),
        )
        return True
    except Exception as e:
        try:
            _activity(cfg, f"[tdi_snapshot] self-heal_failed reason={reason} err={type(e).__name__}:{e}")
        except Exception:
            pass
        return False


def _tdi_log_snapshot(cfg: Dict[str, Any], payload: Optional[Dict[str, Any]]) -> None:
    global _TDI_SNAPSHOT_FAILS
    if not isinstance(payload, dict):
        return
    try:
        ok = bool(tdi_logger.write_snapshot(cfg, payload))
    except Exception:
        ok = False
    if ok:
        _TDI_SNAPSHOT_FAILS = 0
        return
    _TDI_SNAPSHOT_FAILS += 1
    if _TDI_SNAPSHOT_FAILS == 1 or (_TDI_SNAPSHOT_FAILS % 10) == 0:
        try:
            _activity(cfg, f"[tdi_snapshot] write_failed count={_TDI_SNAPSHOT_FAILS}")
        except Exception:
            pass
    if _TDI_SNAPSHOT_FAILS < 3:
        return
    if not _tdi_snapshot_self_heal(cfg, "append_fail"):
        return
    try:
        ok = bool(tdi_logger.write_snapshot(cfg, payload))
    except Exception:
        ok = False
    if ok:
        _TDI_SNAPSHOT_FAILS = 0
        try:
            _activity(cfg, "[tdi_snapshot] write_recovered")
        except Exception:
            pass


def _g24h_gate_allows(
    cfg: Dict[str, Any],
    pct24: Optional[float],
    tdi_payload: Optional[Dict[str, Any]] = None,
    cycle_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    try:
        if not bool(cfg.get("GAINERS_ONLY", True)):
            return True
    except Exception:
        return True

    try:
        min_24h_pct = float(cfg.get("MIN_24H_PCT", 2.0) or 2.0)
    except Exception:
        min_24h_pct = 2.0

    try:
        pct24_f = float(pct24)
    except Exception:
        return True

    if pct24_f >= min_24h_pct:
        return True

    payload = tdi_payload if isinstance(tdi_payload, dict) else {}
    cycle = cycle_payload if isinstance(cycle_payload, dict) else {}

    phase = str(payload.get("cycle_phase") or cycle.get("phase") or "").strip().lower()
    bullish = bool(
        phase in ("lifting_from_trough", "bottoming")
        or cycle.get("allow")
    )
    try:
        relief_score_min = float(cfg.get("G24H_RELIEF_TDI_SCORE_MIN", 60.0) or 60.0)
    except Exception:
        relief_score_min = 60.0

    try:
        tdi_score = float(payload.get("tdi_score", 0.0) or 0.0)
    except Exception:
        tdi_score = 0.0
    try:
        truth_score = float(payload.get("tdi_truth_score", 0.0) or 0.0)
    except Exception:
        truth_score = 0.0
    try:
        continuation_floor = float(payload.get("tdi_continuation_floor", 0.0) or 0.0)
    except Exception:
        continuation_floor = 0.0

    try:
        dmid_bps = float(payload.get("dmid_bps", 0.0) or 0.0)
    except Exception:
        dmid_bps = 0.0
    try:
        pressure = float(payload.get("press", 0.0) or 0.0) * 100.0
    except Exception:
        pressure = 0.0

    tape_bullish = dmid_bps > 0.0 and pressure >= 60.0
    if not (bullish or tape_bullish):
        return False

    return max(tdi_score, truth_score, continuation_floor) >= relief_score_min


def _tob_gate_allows(
    cfg: Dict[str, Any],
    m: Optional[Dict[str, Any]],
    tdi_payload: Optional[Dict[str, Any]] = None,
    cycle_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    if not isinstance(m, dict):
        return False
    try:
        tob_usd = float(m.get("tob", m.get("tob_usd", 0.0)) or 0.0)
    except Exception:
        tob_usd = 0.0
    try:
        min_tob_usd = float(cfg.get("MIN_TOPBOOK_USD", 50.0) or 50.0)
    except Exception:
        min_tob_usd = 50.0
    if tob_usd >= min_tob_usd:
        return True

    try:
        dmid_bps = float(m.get("dmid_bps", m.get("dmid", 0.0)) or 0.0)
    except Exception:
        dmid_bps = 0.0
    try:
        pressure = float(m.get("press", 0.5) or 0.5)
    except Exception:
        pressure = 0.5
    try:
        spr_bps = float(m.get("spr_bps", 0.0) or 0.0)
    except Exception:
        spr_bps = 0.0
    try:
        max_spr_bps = _cfg_max_spr_bps(cfg)
    except Exception:
        max_spr_bps = 60.0
    try:
        min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 0.0) or 0.0)
    except Exception:
        min_dmid_bps = 0.0

    payload = tdi_payload if isinstance(tdi_payload, dict) else {}
    cycle = cycle_payload if isinstance(cycle_payload, dict) else {}
    try:
        tdi_score = float(payload.get("tdi_score", 0.0) or 0.0)
    except Exception:
        tdi_score = 0.0
    try:
        cycle_support = float(cycle.get("support_score", 0.0) or 0.0)
    except Exception:
        cycle_support = 0.0
    cycle_phase = str(payload.get("cycle_phase") or cycle.get("phase") or "").strip().lower()

    # Strong tape can tolerate a lighter near-threshold book than the global floor.
    # Keep a real floor so truly thin names still fail here.
    hard_floor = max(20.0, min_tob_usd * 0.4)
    strong_dmid = dmid_bps >= max(min_dmid_bps + 1.0, 4.0)
    strong_press = pressure >= 0.18
    tight_enough = spr_bps <= max_spr_bps * 0.6
    truth_ok = tdi_score >= 66.0 or cycle_support >= 55.0 or cycle_phase == "lifting_from_trough"
    return tob_usd >= hard_floor and strong_dmid and strong_press and tight_enough and truth_ok


def _tdi_min_buy_score(
    cfg: Dict[str, Any],
    m: Optional[Dict[str, Any]],
    tdi_payload: Optional[Dict[str, Any]] = None,
    cycle_payload: Optional[Dict[str, Any]] = None,
) -> float:
    try:
        base_min_score = min(float(cfg.get("TDI_MIN_BUY_SCORE", 70.0) or 70.0), 70.0)
    except Exception:
        base_min_score = 70.0
    if not isinstance(m, dict):
        return base_min_score

    payload = tdi_payload if isinstance(tdi_payload, dict) else {}
    cycle = cycle_payload if isinstance(cycle_payload, dict) else {}
    try:
        tob_usd = float(m.get("tob", m.get("tob_usd", 0.0)) or 0.0)
    except Exception:
        tob_usd = 0.0
    try:
        dmid_bps = float(m.get("dmid_bps", m.get("dmid", 0.0)) or 0.0)
    except Exception:
        dmid_bps = 0.0
    try:
        pressure = float(m.get("press", 0.5) or 0.5)
    except Exception:
        pressure = 0.5
    try:
        spr_bps = float(m.get("spr_bps", 0.0) or 0.0)
    except Exception:
        spr_bps = 0.0
    try:
        max_spr_bps = _cfg_max_spr_bps(cfg)
    except Exception:
        max_spr_bps = 60.0
    try:
        min_tob_usd = float(cfg.get("MIN_TOPBOOK_USD", 50.0) or 50.0)
    except Exception:
        min_tob_usd = 50.0
    try:
        min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 0.0) or 0.0)
    except Exception:
        min_dmid_bps = 0.0
    try:
        truth_score = float(payload.get("tdi_truth_score", 0.0) or 0.0)
    except Exception:
        truth_score = 0.0
    try:
        flow_score = float(payload.get("flow_score", 0.0) or 0.0)
    except Exception:
        flow_score = 0.0
    flow_regime = str(payload.get("flow_regime") or "").strip().lower()
    try:
        flow_floor = float(payload.get("tdi_flow_floor", 0.0) or 0.0)
    except Exception:
        flow_floor = 0.0
    try:
        cycle_support = float(cycle.get("support_score", 0.0) or 0.0)
    except Exception:
        cycle_support = 0.0
    try:
        top_reasons = [str(x).strip().lower() for x in (payload.get("top_reasons") or []) if str(x).strip()]
    except Exception:
        top_reasons = []
    cycle_phase = str(payload.get("cycle_phase") or cycle.get("phase") or "").strip().lower()

    strong_tape = (
        tob_usd >= max(min_tob_usd * 1.0, 60.0)
        and dmid_bps >= max(min_dmid_bps + 1.5, 4.0)
        and spr_bps <= max_spr_bps * 0.50
        and pressure >= 0.05
    )
    market_truth_ok = (
        "momentum" in top_reasons
        and ("liquidity" in top_reasons or "pressure" in top_reasons)
        and tob_usd >= max(min_tob_usd * 2.0, 120.0)
        and dmid_bps >= max(min_dmid_bps + 4.0, 8.0)
    )
    truth_ok = (
        ("momentum" in top_reasons or "pressure" in top_reasons)
        and (
            truth_score >= 60.0
            or cycle_support >= 55.0
            or cycle_phase == "lifting_from_trough"
            or market_truth_ok
        )
    )
    if flow_regime == "ride" and flow_score >= 74.0 and max(truth_score, flow_floor, cycle_support) >= 66.0:
        return max(_safe_float(cfg.get("FLOW_SURF_RIDE_TDI_MIN", 52.0), 52.0), base_min_score - 18.0)
    if flow_regime in {"pullback", "breakout"} and flow_score >= 68.0 and max(truth_score, flow_floor, cycle_support) >= 62.0:
        return max(_safe_float(cfg.get("FLOW_SURF_PULLBACK_TDI_MIN", 56.0), 56.0), base_min_score - 14.0)
    if strong_tape and truth_ok:
        return max(56.0, base_min_score - 14.0)
    return base_min_score


def _dmid_gate_allows(
    cfg: Dict[str, Any],
    m: Optional[Dict[str, Any]],
    tdi_payload: Optional[Dict[str, Any]] = None,
    cycle_payload: Optional[Dict[str, Any]] = None,
) -> bool:
    if not isinstance(m, dict):
        return False
    try:
        dmid_bps = float(m.get("dmid_bps", m.get("dmid", 0.0)) or 0.0)
    except Exception:
        dmid_bps = 0.0
    try:
        min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 0.0) or 0.0)
    except Exception:
        min_dmid_bps = 0.0
    if dmid_bps >= min_dmid_bps:
        return True

    try:
        tob_usd = float(m.get("tob", m.get("tob_usd", 0.0)) or 0.0)
    except Exception:
        tob_usd = 0.0
    try:
        pressure = float(m.get("press", 0.5) or 0.5)
    except Exception:
        pressure = 0.5
    try:
        spr_bps = float(m.get("spr_bps", 0.0) or 0.0)
    except Exception:
        spr_bps = 0.0
    try:
        max_spr_bps = _cfg_max_spr_bps(cfg)
    except Exception:
        max_spr_bps = 60.0
    try:
        min_tob_usd = float(cfg.get("MIN_TOPBOOK_USD", 50.0) or 50.0)
    except Exception:
        min_tob_usd = 50.0
    try:
        trend_bps_min = float(cfg.get("TREND_BPS_MIN", 12.0) or 12.0)
    except Exception:
        trend_bps_min = 12.0

    payload = tdi_payload if isinstance(tdi_payload, dict) else {}
    cycle = cycle_payload if isinstance(cycle_payload, dict) else {}
    try:
        tdi_score = float(payload.get("tdi_score", 0.0) or 0.0)
    except Exception:
        tdi_score = 0.0
    try:
        truth_score = float(payload.get("tdi_truth_score", 0.0) or 0.0)
    except Exception:
        truth_score = 0.0
    try:
        continuation_floor = float(payload.get("tdi_continuation_floor", 0.0) or 0.0)
    except Exception:
        continuation_floor = 0.0
    try:
        cycle_support = float(cycle.get("support_score", 0.0) or 0.0)
    except Exception:
        cycle_support = 0.0
    cycle_phase = str(payload.get("cycle_phase") or cycle.get("phase") or "").strip().lower()

    mild_pullback_floor = min_dmid_bps - max(6.0, trend_bps_min * 0.90)
    strong_tape = (
        tob_usd >= max(min_tob_usd * 1.0, 60.0)
        and pressure >= 0.12
        and spr_bps <= max_spr_bps * 0.6
    )
    truth_ok = (
        max(tdi_score, truth_score, continuation_floor) >= 66.0
        or cycle_support >= 58.0
        or cycle_phase == "lifting_from_trough"
    )
    return dmid_bps >= mild_pullback_floor and strong_tape and truth_ok


def _is_net_down_err(e: BaseException) -> bool:
    """Heuristic: True if exception looks like DNS / connectivity / timeout failure."""
    s = repr(e)
    markers = (
        'NameResolutionError',
        'getaddrinfo failed',
        'Failed to resolve',
        'Temporary failure in name resolution',
        'Max retries exceeded',
        'NewConnectionError',
        'ConnectionError',
        'ConnectTimeout',
        'ReadTimeout',
        'Read timed out',
        'timed out',
        'RemoteDisconnected',
        'Connection aborted',
        'WinError 11001',
        'WinError 10060',
        'WinError 10054',
    )
    return any(m in s for m in markers)


def _offline_active() -> bool:
    global _OFFLINE_UNTIL_TS
    try:
        return (_OFFLINE_UNTIL_TS or 0.0) > 0 and _now_ts() < float(_OFFLINE_UNTIL_TS)
    except Exception:
        return False


def _offline_note(cfg: Dict[str, Any], msg: str) -> None:
    """Log a message at most once every OFFLINE_LOG_EVERY_SEC while offline."""
    global _LAST_OFFLINE_LOG_TS
    now = _now_ts()
    every = float(cfg.get('OFFLINE_LOG_EVERY_SEC', 30.0) or 30.0)
    if every < 1.0:
        every = 1.0
    if (now - float(_LAST_OFFLINE_LOG_TS or 0.0)) >= every:
        _LAST_OFFLINE_LOG_TS = now
        _activity(cfg, msg)


def _offline_trip(cfg: Dict[str, Any], source: str, e: BaseException) -> None:
    """Enter offline mode with exponential-ish backoff."""
    global _OFFLINE_UNTIL_TS, _OFFLINE_BACKOFF_SEC, _OFFLINE_FAILS
    now = _now_ts()
    min_s = float(cfg.get('OFFLINE_BACKOFF_MIN_SEC', 15.0) or 15.0)
    max_s = float(cfg.get('OFFLINE_BACKOFF_MAX_SEC', 300.0) or 300.0)
    mult = float(cfg.get('OFFLINE_BACKOFF_MULT', 1.7) or 1.7)
    if min_s < 1.0:
        min_s = 1.0
    if max_s < min_s:
        max_s = min_s
    if mult < 1.0:
        mult = 1.0

    if float(_OFFLINE_BACKOFF_SEC or 0.0) <= 0.0:
        _OFFLINE_BACKOFF_SEC = min_s
    else:
        _OFFLINE_BACKOFF_SEC = min(max_s, max(min_s, float(_OFFLINE_BACKOFF_SEC) * mult))

    _OFFLINE_FAILS = int(_OFFLINE_FAILS or 0) + 1
    _OFFLINE_UNTIL_TS = now + float(_OFFLINE_BACKOFF_SEC)

    # Keep the log compact; details are still captured in [maint_fatal].
    short = repr(e)
    if len(short) > 240:
        short = short[:240] + '…'
    _offline_note(cfg, f'[offline] source={source} fails={_OFFLINE_FAILS} backoff_s={float(_OFFLINE_BACKOFF_SEC):.1f} err={short}')


def _offline_clear(cfg: Dict[str, Any], source: str = 'maint') -> None:
    global _OFFLINE_UNTIL_TS, _OFFLINE_BACKOFF_SEC, _OFFLINE_FAILS
    try:
        was = float(_OFFLINE_UNTIL_TS or 0.0)
    except Exception:
        was = 0.0
    if was > 0.0 and int(_OFFLINE_FAILS or 0) > 0:
        _activity(cfg, f'[online] source={source} offline_fails={int(_OFFLINE_FAILS or 0)}')
    _OFFLINE_UNTIL_TS = 0.0
    _OFFLINE_BACKOFF_SEC = 0.0
    _OFFLINE_FAILS = 0




# -----------------------
# FILTER DIAGNOSTICS (MM18)
# -----------------------

def _diag_enabled(cfg: Dict[str, Any]) -> bool:
    try:
        return bool(cfg.get('FILTER_DIAG', True))
    except Exception:
        return True

def _diag_every_ticks(cfg: Dict[str, Any]) -> int:
    try:
        n = int(cfg.get('FILTER_DIAG_EVERY_TICKS', 1) or 1)
        return max(1, n)
    except Exception:
        return 1

def _diag_inc(d: Dict[str, int], k: str, n: int = 1) -> None:
    try:
        d[k] = int(d.get(k, 0) or 0) + int(n)
    except Exception:
        d[k] = 1

def _diag_fmt_counts(d: Dict[str, int], max_items: int = 8) -> str:
    if not d:
        return ''
    try:
        items = sorted(d.items(), key=lambda kv: (-int(kv[1] or 0), str(kv[0])))
    except Exception:
        items = list(d.items())
    items = items[:max_items]
    return ','.join([f"{k}:{v}" for k, v in items])

def _diag_universe_last() -> Dict[str, Any]:
    # Prefer run_manager's own snapshot (always available), but fall back
    # to universe_dynamic.LAST_DIAG if that module provides richer details.
    try:
        if isinstance(_LAST_UNIVERSE_DIAG, dict) and _LAST_UNIVERSE_DIAG:
            return dict(_LAST_UNIVERSE_DIAG)
    except Exception:
        pass
    try:
        if u_dyn and hasattr(u_dyn, 'LAST_DIAG') and isinstance(u_dyn.LAST_DIAG, dict):
            return u_dyn.LAST_DIAG
    except Exception:
        pass
    return {}



# ---------- MM19_HANG_GUARD ----------
_HANG_FH = None  # file handle kept open for faulthandler output

def _hang_guard_start(cfg: Dict[str, Any]) -> None:
    """Start a watchdog that dumps Python thread stacks periodically.
    Purpose: diagnose startup hangs before tick 1 without external tools.
    Controlled by cfg['HANG_DUMP_SEC'] (default 30). Set <=0 to disable.
    """
    global _HANG_FH
    try:
        sec = float(cfg.get("HANG_DUMP_SEC", 30.0))
        if sec <= 0:
            return
        p = cfg.get("HANG_DUMP_PATH") or f"logs/hang_dump_{os.getpid()}.log"
        path = Path(str(p))
        if not path.is_absolute():
            path = Path(ROOT) / path
        path.parent.mkdir(parents=True, exist_ok=True)
        _HANG_FH = open(path, "a", encoding="utf-8", buffering=1)
        try:
            faulthandler.enable(file=_HANG_FH, all_threads=True)
        except Exception:
            pass
        try:
            faulthandler.dump_traceback_later(sec, repeat=True, file=_HANG_FH)
        except Exception:
            pass
        try:
            _activity(cfg, f"[hang_guard] enabled sec={sec} path={str(path)}")
        except Exception:
            pass
    except Exception:
        return

def _hang_guard_cancel(cfg: Dict[str, Any]) -> None:
    """Cancel periodic stack dumps once the tick loop is confirmed alive."""
    try:
        if bool(cfg.get("HANG_GUARD_KEEP", False)):
            try:
                _activity(cfg, "[hang_guard] keep_enabled")
            except Exception:
                pass
            return
        faulthandler.cancel_dump_traceback_later()
        try:
            _activity(cfg, "[hang_guard] cancelled")
        except Exception:
            pass
    except Exception:
        return
# ---------- /MM19_HANG_GUARD ----------

def _spawn_activity_ticker(cfg: Dict[str, Any]) -> None:
    """Spawn an activity-ticker tail window (Windows only)."""
    global _ACTIVITY_TICKER_PID
    try:
        if not bool(cfg.get("ACTIVITY_TICKER", True)):
            return
        if os.environ.get("MM_ACTIVITY_TICKER_CHILD"):
            return
        if os.name != "nt":
            return
        script = (Path(__file__).resolve().parents[1] / "diagnostics_manager" / "activity_ticker.py")
        if not script.exists():
            return
        log_path = str(_activity_log_path(cfg))
        title = str(cfg.get("ACTIVITY_TICKER_TITLE") or "MM18 Activity")
        env = os.environ.copy()
        env["MM_ACTIVITY_TICKER_CHILD"] = "1"
        env["MM_ACTIVITY_LOG_PATH"] = log_path
        env["MM_ACTIVITY_TITLE"] = title
        try:
            CREATE_NEW_CONSOLE = subprocess.CREATE_NEW_CONSOLE  # type: ignore[attr-defined]
        except Exception:
            CREATE_NEW_CONSOLE = 0x00000010
        p = subprocess.Popen(
            [sys.executable, "-X", "utf8", "-u", str(script), "--path", log_path, "--title", title],
            env=env,
            creationflags=CREATE_NEW_CONSOLE,
        )
        _ACTIVITY_TICKER_PID = int(getattr(p, "pid", 0) or 0) or None
        _activity(cfg, f"[activity_ticker] spawned pid={_ACTIVITY_TICKER_PID} path={log_path}")
    except Exception:
        return


def _best_bid_ask_batch(client, product_ids: List[str]) -> Dict[str, D]:
    """Batch get mid prices for product_ids; returns pid -> mid."""
    out: Dict[str, D] = {}
    if not product_ids:
        return out

    # Chunk to avoid overly large payloads.
    def chunks(xs: List[str], n: int) -> List[List[str]]:
        return [xs[i:i+n] for i in range(0, len(xs), n)]

    for ch in chunks(product_ids, 50):
        try:
            bb = client.get_best_bid_ask(product_ids=ch)
        except Exception:
            continue
        pbs = bb.get("pricebooks") if isinstance(bb, dict) else _mm16_inv_get(bb, "pricebooks", None)
        if not pbs:
            pbs = bb.get("data") if isinstance(bb, dict) else _mm16_inv_get(bb, "data", None)
        if not pbs:
            continue
        for pb in (pbs or []):
            try:
                pid = str(_mm16_inv_get(pb, "product_id", "") or _mm16_inv_get(pb, "productId", "") or "").upper()
                if not pid:
                    continue
                bids = _mm16_inv_get(pb, "bids", []) or []
                asks = _mm16_inv_get(pb, "asks", []) or []
                b0 = bids[0] if bids else None
                a0 = asks[0] if asks else None
                if not b0 or not a0:
                    continue
                bid = float(_mm16_inv_get(b0, "price", 0) or 0)
                ask = float(_mm16_inv_get(a0, "price", 0) or 0)
                if bid <= 0 or ask <= 0:
                    continue
                out[pid] = _D((bid + ask) / 2.0)
            except Exception:
                continue
    return out


def _maintenance_should_run(cfg: Dict[str, Any], t: int) -> bool:
    every = int(cfg.get("MAINT_EVERY_TICKS", 2) or 2)
    if every < 1:
        every = 1
    return (t % every) == 0



# MM24_ATTACHED_EXIT_SELL_OK: emit SELL_OK when an attached TP/SL position disappears from holdings.
def _attached_exit_check(cfg: Dict[str, Any], t: int, client: Any, metrics: Dict[str, Any], held_bases_all: set) -> None:
    try:
        if not bool(cfg.get("EXIT_ATTACHED_TPSL", False)):
            return
    except Exception:
        return
    try:
        with _ATTACHED_OPEN_LOCK:
            items = list(_ATTACHED_OPEN.items())
    except Exception:
        items = []
    if not items:
        return

    closed = []
    for pid, info in items:
        try:
            base = str(pid).split("-")[0].upper()
        except Exception:
            base = ""
        if base and base not in held_bases_all:
            closed.append((pid, info))
    if not closed:
        return

    # Pull mids for exit classification (best-effort).
    mids: Dict[str, D] = {}
    try:
        for pid, _info in closed:
            m = metrics.get(pid)
            if isinstance(m, dict):
                mid = _D(m.get("mid", 0))
                if mid > 0:
                    mids[pid] = mid
    except Exception:
        pass

    missing = [pid for pid, _info in closed if pid not in mids]
    if missing:
        try:
            mids.update(_best_bid_ask_batch(client, missing))
        except Exception:
            pass

    for pid, info in closed:
        mid_d = mids.get(pid, D("0"))
        exit_mid = float(mid_d) if mid_d and mid_d > 0 else 0.0
        try:
            entry_ref = float(info.get("entry_ref") or 0.0)
        except Exception:
            entry_ref = 0.0
        try:
            tp_price = float(info.get("tp") or 0.0)
        except Exception:
            tp_price = 0.0
        try:
            sl_price = float(info.get("sl") or 0.0)
        except Exception:
            sl_price = 0.0
        oid = str(info.get("oid") or "")

        pnl_pct = None
        if entry_ref > 0 and exit_mid > 0:
            try:
                pnl_pct = (exit_mid / entry_ref - 1.0) * 100.0
            except Exception:
                pnl_pct = None

        reason = "EXIT"
        try:
            if tp_price > 0 and exit_mid > 0 and exit_mid >= (tp_price * 0.998):
                reason = "TP"
            elif sl_price > 0 and exit_mid > 0 and exit_mid <= (sl_price * 1.002):
                reason = "SL"
        except Exception:
            pass

        if pnl_pct is None:
            _activity(cfg, f"[SELL_OK] pid={pid} src=attached_exit reason={reason} entry_ref={entry_ref} exit_mid={exit_mid} tp={tp_price} sl={sl_price} oid={oid}")
        else:
            _activity(cfg, f"[SELL_OK] pid={pid} src=attached_exit reason={reason} pnl_pct={pnl_pct:.2f} entry_ref={entry_ref} exit_mid={exit_mid} tp={tp_price} sl={sl_price} oid={oid}")

        try:
            with _ATTACHED_OPEN_LOCK:
                _ATTACHED_OPEN.pop(pid, None)
        except Exception:
            pass

def _schedule_maintenance(cfg: Dict[str, Any], t: int, metrics: Dict[str, Any]) -> bool:
    """Run TP/SL inventory maintenance off-thread to keep ticker timing stable."""
    if not bool(cfg.get("MAINT_ASYNC", True)):
        return False
    if _offline_active() and bool(cfg.get("OFFLINE_PAUSE_MAINT", True)):
        return False
    if not _maintenance_should_run(cfg, t):
        return False

    # Only one in-flight maintenance thread.
    if not _MAINT_LOCK.acquire(blocking=False):
        return False

    th = threading.Thread(
        target=_maintenance_worker,
        args=(cfg, int(t), dict(metrics) if isinstance(metrics, dict) else {}),
        daemon=True,
    )
    th.start()
    return True


def _maintenance_worker(cfg: Dict[str, Any], t: int, metrics: Dict[str, Any]) -> None:
    """Worker body for async maintenance. Releases _MAINT_LOCK."""
    try:
        started = _now_ts()
        _activity(cfg, f"[maint_start] tick={t}")
        c = get_client()

        # Gather holdings (available+hold) per currency; prefer PFID scoped, but keep fallbacks.
        pfid = os.environ.get("PFID", "").strip() or str(cfg.get("PFID") or "").strip()

        try:
            resp = c.get_accounts(portfolio_uuid=pfid, limit=250) if pfid else c.get_accounts(limit=250)
        except TypeError:
            resp = c.get_accounts(portfolio_uuid=pfid) if pfid else c.get_accounts()

        accs = resp.get("accounts") if isinstance(resp, dict) else _mm16_inv_get(resp, "accounts", [])
        accs = accs or []

        dust = float(_D(cfg.get("POSITION_DUST", "0.00000010")))
        rows: List[Tuple[str, float]] = []
        for a in accs:
            try:
                a_pfid = str((_mm16_inv_get(a, "retail_portfolio_id", "") or _mm16_inv_get(a, "portfolio_uuid", "") or "") or "")
                if pfid and a_pfid and a_pfid != pfid:
                    continue
                cur = str((_mm16_inv_get(a, "currency", "") or "")).upper()
                if not cur or cur in ("USD", "USDC", "USDT", "FX"):
                    continue
                ab = _mm16_inv_get(a, "available_balance", None)
                hv = _mm16_inv_get(a, "hold", None)
                av = float(_mm16_inv_get(ab, "value", 0) if ab is not None else 0)
                hd = float(_mm16_inv_get(hv, "value", 0) if hv is not None else 0)
                tot = av + hd
                if tot > dust:
                    rows.append((cur, tot))
            except Exception:
                continue        # MM24_ATTACHED_EXIT_SELL_OK: detect attached exits (base disappeared) and emit SELL_OK.
        n_orphan = 0
        try:
            held_bases_all = set([cur for (cur, _tot) in rows])
            _attached_exit_check(cfg, t, c, metrics, held_bases_all)
            n_orphan = _cancel_orphan_sell_brackets(c, cfg, held_bases_all)
        except Exception:
            pass

# Maintenance must cover held positions; do NOT cap by INV_MAX_PIDS (that's a buy diversification cap).
        rows_total = len(rows)

        # Hard safety cap to avoid runaway work if many tiny balances exist.
        maint_cap = 120
        if maint_cap > 0 and rows_total > maint_cap:
            try:
                pids_all = [f"{cur}-USD" for (cur, _tot) in rows]
                mids_all = _best_bid_ask_batch(c, pids_all)
                scored = []
                for cur, tot in rows:
                    pid2 = f"{cur}-USD"
                    mid2 = mids_all.get(pid2, D("0"))
                    usd2 = float(mid2 * D(str(tot)))
                    scored.append((cur, tot, usd2))
                scored.sort(key=lambda x: x[2], reverse=True)
                rows = [(cur, tot) for (cur, tot, _usd) in scored[:maint_cap]]
            except Exception:
                rows.sort(key=lambda x: x[1], reverse=True)
                rows = rows[:maint_cap]

        pids = [f"{cur}-USD" for (cur, _tot) in rows]
        if not pids:
            mm30_tp, mm30_sl, mm30_exit = _mm30_attached_exit_drain(cfg)
            _activity(cfg, f"[maint_done] tick={t} held=0/{rows_total} tp={mm30_tp} sl={mm30_sl} orphan_cancel=0 skip_mid=0 attached_exit={mm30_exit} dur=0.00s")
            return

        # Mid prices: use metrics snapshot if available, otherwise batch best_bid_ask.
        mids: Dict[str, D] = {}
        try:
            for pid in pids:
                m = metrics.get(pid)
                if isinstance(m, dict):
                    mid = _D(m.get("mid", 0))
                    if mid > 0:
                        mids[pid] = mid
        except Exception:
            pass

        missing = [pid for pid in pids if pid not in mids]
        if missing:
            mids.update(_best_bid_ask_batch(c, missing))

        n_tp = 0
        n_sl = 0
        n_skip = 0

        sell_at_loss = bool(cfg.get("SELL_AT_LOSS", True))
        grace = int(cfg.get("SL_GRACE_TICKS", 10))

        for pid in pids:
            mid = mids.get(pid, D("0"))
            if mid <= 0:
                n_skip += 1
                continue

            # Stop-loss (optional).
            if sell_at_loss:
                try:
                    if (t - int(_LAST_BUY_TICK.get(pid, -999999))) < grace:
                        slr = {"action": "skip_grace"}
                    else:
                        slr = stop_loss.check_and_exit(c, pid, cfg, None)
                    if isinstance(slr, dict) and slr.get("action") == "stop_loss":
                        _SL_REENTRY_LAST_STOP[pid] = time.time()
                        n_sl += 1
                        _activity(cfg, f"[SL] {pid} action=stop_loss")
                        continue
                except Exception as e:
                    if _is_net_down_err(e):
                        _offline_trip(cfg, 'maint_sl', e)
                        raise
                    _activity(cfg, f"[SL_ERR] {pid} err={e}")
                    # fallthrough to TP attempt

            # Ensure TP.
            try:
                r = exit_engine.ensure_tp_for_product(c, pid, cfg, mid)
                if isinstance(r, dict) and r.get("action") in ("place", "replace", "cancel"):
                    n_tp += 1
                    err = r.get("error")
                    if err:
                        _activity(cfg, f"[TP] {pid} action={r.get('action')} err={err}")
                    else:
                        _activity(cfg, f"[TP] {pid} action={r.get('action')}")
            except Exception as e:
                if _is_net_down_err(e):
                    _offline_trip(cfg, 'maint_tp', e)
                    raise
                _activity(cfg, f"[TP_ERR] {pid} err={e}")

        _offline_clear(cfg, 'maint')

        dur = _now_ts() - started
        mm30_tp, mm30_sl, mm30_exit = _mm30_attached_exit_drain(cfg)
        n_tp += mm30_tp
        n_sl += mm30_sl
        _activity(cfg, f"[maint_done] tick={t} held={len(pids)}/{rows_total} tp={n_tp} sl={n_sl} orphan_cancel={n_orphan} skip_mid={n_skip} attached_exit={mm30_exit} dur={dur:.2f}s")
    except Exception as e:
        try:
            if _is_net_down_err(e):
                _offline_trip(cfg, 'maint', e)
            _activity(cfg, f"[maint_fatal] tick={t} err={repr(e)}")
        except Exception:
            pass
    finally:
        try:
            _MAINT_LOCK.release()
        except Exception:
            pass



# ---------- order adapter (keeps maker) ----------

def _place_order_adaptive(
    product_id: str,
    side: str,
    size: str,
    size_type: str,
    cfg: Dict[str, Any],
    limit_price: Optional[str] = None,
    post_only: bool = True,
    client_order_id: Optional[str] = None,
    client: Any = None,
) -> Dict[str, Any]:
    """
    Adapter over orders.place_order, tolerant of signature changes.
    Always tries to keep LIMIT + post_only when requested.
    """
    cfg = cfg or {}
    try:
        # Preferred kw path
        return orders.place_order(
            client=client,
            product_id=product_id,
            side=side,
            size=size,
            size_type=size_type,
            limit_price=limit_price,
            post_only=post_only,
            settings=cfg,
        )
    except TypeError as e:
        msg = str(e)
        # positional fallbacks
        for args in (
            (product_id, side, size, size_type, limit_price, post_only),
            (product_id, side, size, size_type),
        ):
            try:
                return orders.place_order(*args)
            except TypeError:
                continue
        return {"ok": False, "error": f"place_order signature mismatch: {msg}"}
    except Exception as e:
        return {"ok": False, "error": f"place_order failed: {e}"}


# ---------- MM16_TICKER_PNL_V3 ----------
# In-ticker PnL block printed every N ticks (top 8 by USD value)

_TP_ENTRY_CACHE: Dict[str, Tuple[float, D]] = {}
_POS_CACHE: Dict[str, Tuple[float, D]] = {}
_POS_SPLIT_CACHE: Dict[str, Tuple[float, Any]] = {}
_MID_CACHE: Dict[str, Tuple[float, D]] = {}
_BAD_PIDS: Dict[str, float] = {}

def _now_ts() -> float:
    try:
        return time.time()
    except Exception:
        return 0.0

def _entry_vwap_cached(client, pid: str, cfg: Dict[str, Any]) -> D:
    ttl = float(cfg.get("ENTRY_CACHE_SEC", 300))
    now = _now_ts()
    try:
        ts, v = _TP_ENTRY_CACHE.get(pid, (0.0, D("0")))
        if v > 0 and (now - float(ts)) <= ttl:
            return v
    except Exception:
        pass
    try:
        resp = client.get_fills(product_id=pid, limit=200)
    except Exception:
        return D("0")
    fills = resp.get("fills") if isinstance(resp, dict) else getattr(resp, "fills", None)
    if fills is None:
        fills = resp if isinstance(resp, list) else []
    if not isinstance(fills, list):
        fills = []
    tot_sz = D("0")
    tot_notional = D("0")
    for f in fills:
        side = str((f.get("side") if isinstance(f, dict) else getattr(f, "side", "")) or "").upper()
        if side not in ("BUY", "B"):
            continue
        try:
            sz = _D((f.get("size") if isinstance(f, dict) else getattr(f, "size", None)) or (f.get("base_size") if isinstance(f, dict) else getattr(f, "base_size", None)) or 0)
            px = _D((f.get("price") if isinstance(f, dict) else getattr(f, "price", None)) or (f.get("average_price") if isinstance(f, dict) else getattr(f, "average_price", None)) or 0)
        except Exception:
            continue
        if sz <= 0 or px <= 0:
            continue
        tot_sz += sz
        tot_notional += sz * px
    if tot_sz <= 0 or tot_notional <= 0:
        return D("0")
    vwap = tot_notional / tot_sz
    _TP_ENTRY_CACHE[pid] = (now, vwap)
    return vwap

def _accounts_positions(client, cfg: Dict[str, Any]) -> Dict[str, D]:
    ttl = float(cfg.get("POS_CACHE_SEC", 20))
    now = _now_ts()
    key = "ALL"
    try:
        ts, cached = _POS_CACHE.get(key, (0.0, None))
        if cached is not None and (now - float(ts)) <= ttl:
            return cached
    except Exception:
        pass

    pfid = os.environ.get("PFID", "").strip() or str(cfg.get("PFID") or "").strip()
    # Ignore tiny dust positions when computing held_bases / INV_MAX_PIDS (prevents false inv_cap).
    try:
        dust = _D(cfg.get("POSITION_DUST", "0.00000010"))
    except Exception:
        dust = D("0")

    out: Dict[str, D] = {}
    try:
        try:
            resp = client.get_accounts(portfolio_uuid=pfid, limit=250) if pfid else client.get_accounts(limit=250)
        except TypeError:
            resp = client.get_accounts(portfolio_uuid=pfid) if pfid else client.get_accounts()
    except Exception:
        _POS_CACHE[key] = (now, out)
        return out
    accs = resp.get("accounts") if isinstance(resp, dict) else getattr(resp, "accounts", [])
    accs = accs or []
    for a in accs:
        try:
            a_pfid = str((a.get("retail_portfolio_id") if isinstance(a, dict) else getattr(a, "retail_portfolio_id", "")) or (a.get("portfolio_uuid") if isinstance(a, dict) else getattr(a, "portfolio_uuid", "")) or "")
            if pfid and a_pfid and a_pfid != pfid:
                continue
            cur = str((a.get("currency") if isinstance(a, dict) else getattr(a, "currency", "")) or "").upper()
            if not cur or cur in ("USD", "USDC", "USDT", "FX"):
                continue
            ab = a.get("available_balance") if isinstance(a, dict) else getattr(a, "available_balance", None)
            hv = a.get("hold") if isinstance(a, dict) else getattr(a, "hold", None)
            av = _D((ab.get("value") if isinstance(ab, dict) else getattr(ab, "value", None)) or 0) if ab is not None else D("0")
            hd = _D((hv.get("value") if isinstance(hv, dict) else getattr(hv, "value", None)) or 0) if hv is not None else D("0")
            tot = av + hd
            if tot > dust:
                out[cur] = out.get(cur, D("0")) + tot
        except Exception:
            continue
    _POS_CACHE[key] = (now, out)
    return out


def _accounts_positions_split(client, cfg: Dict[str, Any]) -> Dict[str, Any]:
    """Return base -> (available, hold) for non-USD assets in this PFID."""
    ttl = float(cfg.get("POS_CACHE_SEC", 20))
    now = _now_ts()
    key = "ALL"
    try:
        ts, cached = _POS_SPLIT_CACHE.get(key, (0.0, None))
        if cached is not None and (now - float(ts)) <= ttl:
            return cached
    except Exception:
        pass

    pfid = os.environ.get("PFID", "").strip() or str(cfg.get("PFID") or "").strip()
    # Ignore dust so split holdings reflect meaningful positions.
    try:
        dust = _D(cfg.get("POSITION_DUST", "0.00000010"))
    except Exception:
        dust = D("0")

    out: Dict[str, Any] = {}
    try:
        try:
            resp = client.get_accounts(portfolio_uuid=pfid, limit=250) if pfid else client.get_accounts(limit=250)
        except TypeError:
            resp = client.get_accounts(portfolio_uuid=pfid) if pfid else client.get_accounts()
    except Exception:
        _POS_SPLIT_CACHE[key] = (now, out)
        return out

    accs = resp.get("accounts") if isinstance(resp, dict) else getattr(resp, "accounts", [])
    accs = accs or []
    for a in accs:
        try:
            a_pfid = str(
                (a.get("retail_portfolio_id") if isinstance(a, dict) else getattr(a, "retail_portfolio_id", ""))
                or (a.get("portfolio_uuid") if isinstance(a, dict) else getattr(a, "portfolio_uuid", ""))
                or ""
            )
            if pfid and a_pfid and a_pfid != pfid:
                continue
            cur = str((a.get("currency") if isinstance(a, dict) else getattr(a, "currency", "")) or "").upper()
            if not cur or cur in ("USD", "USDC", "USDT", "FX"):
                continue
            ab = a.get("available_balance") if isinstance(a, dict) else getattr(a, "available_balance", None)
            hv = a.get("hold") if isinstance(a, dict) else getattr(a, "hold", None)
            av = _D((ab.get("value") if isinstance(ab, dict) else getattr(ab, "value", None)) or 0) if ab is not None else D("0")
            hd = _D((hv.get("value") if isinstance(hv, dict) else getattr(hv, "value", None)) or 0) if hv is not None else D("0")
            if (av + hd) > 0:
                out[cur] = (av, hd)
        except Exception:
            continue

    _POS_SPLIT_CACHE[key] = (now, out)
    return out


def _mid_for_pid(client, pid: str, cfg: Dict[str, Any]) -> D:
    pid = str(pid or "").upper()
    if not pid or pid in _BAD_PIDS:
        return D("0")
    ttl = float(cfg.get("MID_CACHE_SEC", 10))
    now = _now_ts()
    try:
        ts, v = _MID_CACHE.get(pid, (0.0, D("0")))
        if v > 0 and (now - float(ts)) <= ttl:
            return v
    except Exception:
        pass
    try:
        resp = client.get_best_bid_ask(product_ids=[pid])
    except Exception:
        _BAD_PIDS[pid] = now
        return D("0")
    pbs = resp.get("pricebooks") if isinstance(resp, dict) else getattr(resp, "pricebooks", None)
    if not pbs:
        pbs = resp.get("data") if isinstance(resp, dict) else getattr(resp, "data", None)
    if not pbs or not isinstance(pbs, list):
        _BAD_PIDS[pid] = now
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
            mid = (bid + ask) / D("2")
            _MID_CACHE[pid] = (now, mid)
            return mid
    except Exception:
        pass
    return D("0")

def _maybe_print_pnl_block(c: coinbase.RESTClient, cfg: Dict[str, Any], t: int) -> None:
    """Periodically print a full holdings PnL table.

    MM18: If ACTIVITY_TICKER is enabled and MARKET_TICKER_MINIMAL=True, route this output
    to the activity log so the market ticker stays clean and timely.
    """
    every = int(cfg.get("PNL_TICKER_EVERY", 20) or 0)
    if every <= 0:
        return
    if (t != 1) and (t % every != 0):
        return

    to_activity = bool(cfg.get("PNL_TO_ACTIVITY", True))
    minimal = bool(cfg.get("MARKET_TICKER_MINIMAL", True))

    # If minimal mode is on and activity logging is off, suppress entirely.
    if minimal and not to_activity:
        return

    pos = _accounts_positions(c, cfg)
    if not pos:
        return

    dust = _D(cfg.get("POSITION_DUST", "0.00000010"))
    rows: List[Tuple[str, D, D, D]] = []  # (pid, amt, usd, pnl%)

    for base, amt in pos.items():
        base_u = str(base).upper()
        # ignore cash/stables
        if base_u in ("USD", "USDC", "USDT"):
            continue
        # hotfix: FX-USD isn't a tradable Coinbase product_id; skip to prevent 400
        if base_u in ("FX",):
            continue
        if _D(amt) <= dust:
            continue

        pid = f"{base_u}-USD"
        mid = _mid_for_pid(c, pid, cfg)
        if mid <= 0:
            continue
        entry = _entry_vwap_cached(c, pid, cfg)
        pnl_pct = D("0")
        if entry > 0:
            pnl_pct = (mid - entry) / entry * D("100")
        usd = _D(amt) * mid
        rows.append((pid, _D(amt), usd, pnl_pct))

    if not rows:
        return

    rows.sort(key=lambda r: float(r[2]), reverse=True)

    def _fmt_amt(a: D) -> str:
        try:
            return f"{float(a):.8f}".rstrip("0").rstrip(".")
        except Exception:
            return str(a)

    def _fmt_usd(u: D) -> str:
        try:
            return f"{float(u):.2f}"
        except Exception:
            return str(u)

    def _fmt_pct(p: D) -> str:
        try:
            return f"{float(p):.2f}"
        except Exception:
            return str(p)

    half = (len(rows) + 1) // 2
    left = rows[:half]
    right = rows[half:]

    out: List[str] = []
    out.append("PNL (all holdings)  pid  amt  usd  pnl%")
    out.append(
        f"{'pid':<12}{'amt':>14}{'usd':>10}{'pnl%':>8}    "
        f"{'pid':<12}{'amt':>14}{'usd':>10}{'pnl%':>8}"
    )

    for i in range(max(len(left), len(right))):
        a = left[i] if i < len(left) else None
        b = right[i] if i < len(right) else None
        if a and b:
            out.append(
                f"{a[0]:<12}{_fmt_amt(a[1]):>14}{_fmt_usd(a[2]):>10}{_fmt_pct(a[3]):>8}    "
                f"{b[0]:<12}{_fmt_amt(b[1]):>14}{_fmt_usd(b[2]):>10}{_fmt_pct(b[3]):>8}"
            )
        elif a:
            out.append(f"{a[0]:<12}{_fmt_amt(a[1]):>14}{_fmt_usd(a[2]):>10}{_fmt_pct(a[3]):>8}")
        elif b:
            out.append(f"{b[0]:<12}{_fmt_amt(b[1]):>14}{_fmt_usd(b[2]):>10}{_fmt_pct(b[3]):>8}")

    block = "\n".join(out)

    if to_activity:
        _activity(cfg, block)

    if not minimal:
        print(block)
def _best_bid_ask_row(x: Any) -> Tuple[D, D, D, D]:
    """
    Returns bid_px, ask_px, bid_sz, ask_sz from a pricebook-like object.
    """

    def _get(o, k):
        if isinstance(o, dict):
            return o.get(k)
        return getattr(o, k, None)

    bid_px = ask_px = bid_sz = ask_sz = D("0")
    try:
        b = x["bids"][0] if isinstance(x, dict) else (getattr(x, "bids", []) or [])[0]
        a = x["asks"][0] if isinstance(x, dict) else (getattr(x, "asks", []) or [])[0]
        bp = _get(b, "price")
        ap = _get(a, "price")
        bs = _get(b, "size") or _get(b, "quantity")
        asz = _get(a, "size") or _get(a, "quantity")
        bid_px, ask_px = _D(bp), _D(ap)
        bid_sz, ask_sz = _D(bs or 0), _D(asz or 0)
    except Exception:
        pass
    return bid_px, ask_px, bid_sz, ask_sz


def _book_metrics(c, pid: str) -> Tuple[D, D, D, D]:
    """
    Returns: mid, spread_bps, tob_usd, book_pressure [0..1]
    Uses get_best_bid_ask for consistent sizes.
    """
    try:
        r = c.get_best_bid_ask(product_ids=[pid])
        pb_list = None
        if isinstance(r, dict):
            pb_list = r.get("pricebooks") or r.get("data")
        else:
            pb_list = getattr(r, "pricebooks", None) or getattr(r, "data", None)
        if not pb_list:
            return D("0"), D("0"), D("0"), D("0.5")
        pb = pb_list[0]
    except Exception:
        return D("0"), D("0"), D("0"), D("0.5")

    bid, ask, bs, asz = _best_bid_ask_row(pb)
    if bid <= 0 or ask <= 0:
        return D("0"), D("0"), D("0"), D("0.5")

    mid = (bid + ask) / D("2")
    spr_bps = (ask - bid) / mid * D("10000")
    bid_usd = bs * bid
    ask_usd = asz * ask
    # MM31 TOB relief: using the weaker side only is too brittle for lift-off names
    # that momentarily lean one side of the top level. A geometric-mean depth keeps
    # extreme one-sided books penalized while stopping near-threshold asymmetry from
    # falsely choking otherwise valid candidates.
    try:
        tob_usd = (bid_usd * ask_usd).sqrt() if bid_usd > 0 and ask_usd > 0 else min(bid_usd, ask_usd)
    except Exception:
        tob_usd = min(bid_usd, ask_usd)
    press = ((bs - asz) / (bs + asz) + D("1")) / D("2") if (bs + asz) > 0 else D("0.5")
    return mid, spr_bps, tob_usd, press


# ---------- strategy plumbing ----------

# cache dynamic universe for a short TTL to avoid hammering the API
_UNI_CACHE: Dict[str, Tuple[float, List[str]]] = {}
_LAST_UNIVERSE_DIAG: Dict[str, Any] = {}  # updated each _universe() call


# ---------- position-aware buy gate (skip if already holding base) ----------
_POS_CACHE: Dict[str, Tuple[float, D]] = {}  # base -> (ts, total_base)

def _base_position_cached(client, base: str, cfg: Dict[str, Any]) -> D:
    """Return total base (available+hold) for BASE across accounts (PFID-filtered if possible), cached.

    NOTE: Uses paginated get_accounts(portfolio_uuid=PFID) to avoid 'USD=0' / missing accounts when only first page is fetched.
    """
    b = str(base or "").upper()
    if not b:
        return D("0")
    ttl = float(cfg.get("POS_CACHE_SEC", 20))
    now = time.time()
    try:
        ts, val = _POS_CACHE.get(b, (0.0, D("0")))
        if now - float(ts) <= ttl:
            return val
    except Exception:
        pass

    pfid = os.environ.get("PFID", "").strip() or str(cfg.get("PFID") or "").strip()
    total = D("0")
    try:
        cursor = None
        while True:
            try:
                if pfid:
                    resp = client.get_accounts(portfolio_uuid=pfid, cursor=cursor) if cursor else client.get_accounts(portfolio_uuid=pfid)
                else:
                    resp = client.get_accounts(cursor=cursor) if cursor else client.get_accounts()
            except TypeError:
                # Some SDK versions use starting_after
                if pfid:
                    resp = client.get_accounts(portfolio_uuid=pfid, starting_after=cursor) if cursor else client.get_accounts(portfolio_uuid=pfid)
                else:
                    resp = client.get_accounts(starting_after=cursor) if cursor else client.get_accounts()

            accounts = resp.get("accounts") if isinstance(resp, dict) else getattr(resp, "accounts", [])
            accounts = accounts or []
            for a in accounts:
                if not a:
                    continue
                try:
                    cur = str((a.get("currency") if isinstance(a, dict) else getattr(a, "currency", "")) or "").upper()
                    if cur != b:
                        continue
                    ab = (a.get("available_balance") if isinstance(a, dict) else getattr(a, "available_balance", None))
                    hv = (a.get("hold") if isinstance(a, dict) else getattr(a, "hold", None))
                    av = (ab.get("value") if isinstance(ab, dict) else getattr(ab, "value", ab)) if ab is not None else 0
                    hd = (hv.get("value") if isinstance(hv, dict) else getattr(hv, "value", hv)) if hv is not None else 0
                    total += _D(av) + _D(hd)
                except Exception:
                    continue

            has_next = bool(resp.get("has_next")) if isinstance(resp, dict) else bool(getattr(resp, "has_next", False))
            cursor = (resp.get("cursor") if isinstance(resp, dict) else getattr(resp, "cursor", None)) if has_next else None
            if not has_next or not cursor:
                break
    except Exception:
        total = D("0")

    _POS_CACHE[b] = (now, total)
    return total

# ---------- USD availability cache (avoid repeated get_accounts calls inside the buy loop) ----------
_USD_AVAIL_CACHE: Dict[str, Tuple[float, float]] = {}  # pfid_or_blank -> (ts, usd_available)

def _usd_available(client, pfid: str) -> float:
    """Return available USD (not including hold) across accounts (PFID-filtered if possible).

    Cached for a short TTL to avoid hammering get_accounts inside the candidate loop.
    """
    key = (pfid or "").strip() or "_"
    ttl = 5.0  # seconds
    now = time.time()

    try:
        ts, val = _USD_AVAIL_CACHE.get(key, (0.0, 0.0))
        if now - float(ts) <= ttl:
            return float(val)
    except Exception:
        pass

    avail = 0.0
    cursor = None
    try:
        while True:
            try:
                if pfid:
                    resp = client.get_accounts(portfolio_uuid=pfid, cursor=cursor) if cursor else client.get_accounts(portfolio_uuid=pfid)
                else:
                    resp = client.get_accounts(cursor=cursor) if cursor else client.get_accounts()
            except TypeError:
                # Some SDK versions use starting_after
                if pfid:
                    resp = client.get_accounts(portfolio_uuid=pfid, starting_after=cursor) if cursor else client.get_accounts(portfolio_uuid=pfid)
                else:
                    resp = client.get_accounts(starting_after=cursor) if cursor else client.get_accounts()

            accounts = resp.get("accounts") if isinstance(resp, dict) else getattr(resp, "accounts", [])
            accounts = accounts or []
            for a in accounts:
                if not a:
                    continue
                try:
                    cur = str((a.get("currency") if isinstance(a, dict) else getattr(a, "currency", "")) or "").upper()
                    if cur != "USD":
                        continue
                    ab = (a.get("available_balance") if isinstance(a, dict) else getattr(a, "available_balance", None))
                    av = (ab.get("value") if isinstance(ab, dict) else getattr(ab, "value", ab)) if ab is not None else 0
                    try:
                        avail += float(av)
                    except Exception:
                        avail += float(str(av) or "0")
                except Exception:
                    continue

            has_next = bool(resp.get("has_next")) if isinstance(resp, dict) else bool(getattr(resp, "has_next", False))
            cursor = (resp.get("cursor") if isinstance(resp, dict) else getattr(resp, "cursor", None)) if has_next else None
            if not has_next or not cursor:
                break
    except Exception:
        avail = 0.0

    _USD_AVAIL_CACHE[key] = (now, float(avail))
    return float(avail)

# ---------- Entry price cache (avoid repeated get_fills calls inside the buy loop) ----------
_ENTRY_PX_CACHE: Dict[str, Tuple[float, float]] = {}  # pid -> (ts, entry_px)

def _entry_px_cached(client, pid: str, cfg: Dict[str, Any]) -> float:
    """Return most-recent BUY fill price for pid (best-effort), cached for ENTRY_CACHE_SEC."""
    key = str(pid or "").upper()
    if not key:
        return 0.0
    try:
        ttl = float(cfg.get("ENTRY_CACHE_SEC", 180.0) or 180.0)
    except Exception:
        ttl = 180.0
    now = time.time()
    try:
        ts, px = _ENTRY_PX_CACHE.get(key, (0.0, 0.0))
        if (now - float(ts)) <= ttl and float(px) > 0.0:
            return float(px)
    except Exception:
        pass

    px = 0.0
    try:
        ent = exit_engine.recent_buy_entry(client, key)
        if ent and len(ent) >= 1:
            px = float(ent[0])
    except Exception:
        px = 0.0

    _ENTRY_PX_CACHE[key] = (now, float(px))
    return float(px)

def _has_position(client, product_id: str, cfg: Dict[str, Any]) -> bool:
    """True if base position exceeds dust threshold."""
    pid = str(product_id or "").upper()
    base = pid.split("-", 1)[0] if "-" in pid else pid
    dust = _D(cfg.get("POSITION_DUST", "0.00000010"))
    return _base_position_cached(client, base, cfg) > dust

def _soldiers_held(client, product_id: str, mid: D, cfg: Dict[str, Any]) -> int:
    """Approximate how many 'soldiers' are currently allocated to a pid based on holdings notional.

    This is intentionally fill-agnostic: it uses current base_total * mid and divides by SOLDIER_USD.
    We clamp MAX_SOLDIERS_PER_PID to >=5 elsewhere per user requirement.
    """
    try:
        pid = str(product_id or "").upper()
        base = pid.split("-", 1)[0] if "-" in pid else pid
        dust = _D(cfg.get("POSITION_DUST", "0.00000010"))
        base_tot = _base_position_cached(client, base, cfg)
        if base_tot <= dust:
            return 0
        if mid is None:
            return 0
        mid = _D(mid)
        if mid <= _D("0"):
            return 0
        soldier_usd = _D(cfg.get("SOLDIER_USD", "10"))
        if soldier_usd <= _D("0"):
            soldier_usd = _D("10")
        usd_notional = base_tot * mid
        # floor
        n = int(usd_notional / soldier_usd)
        return max(0, n)
    except Exception:
        return 0

def _universe(c, cfg: Dict, diag: Optional[Dict[str, Any]] = None) -> List[str]:
    global _LAST_UNIVERSE_DIAG

    key = str(cfg.get('UNIVERSE_MODE', 'TOP') or 'TOP')
    ttl = float(cfg.get('UNIVERSE_TTL_SEC', 30.0) or 30.0)
    now = time.time()

    # cache
    try:
        if key in _UNI_CACHE:
            ts, cached = _UNI_CACHE[key]
            if (now - float(ts)) < ttl:
                _LAST_UNIVERSE_DIAG = {
                    'ts': now,
                    'mode': key,
                    'source': 'cache',
                    'uni_out': len(cached or []),
                }
                if isinstance(diag, dict):
                    diag.update(_LAST_UNIVERSE_DIAG)
                return cached
    except Exception:
        pass

    # dynamic universe
    try:
        if u_dyn:
            try:
                out = u_dyn.build_universe(c, cfg, diag=diag)
            except TypeError:
                out = u_dyn.build_universe(c, cfg)
            out = list(out or [])
            # optional cap
            try:
                out = out[: int(cfg.get('UNIVERSE_TOP_N', len(out)) or len(out))]
            except Exception:
                pass

            _UNI_CACHE[key] = (now, out)
            _LAST_UNIVERSE_DIAG = {
                'ts': now,
                'mode': key,
                'source': 'dynamic',
                'uni_out': len(out),
            }
            if isinstance(diag, dict):
                diag.update(_LAST_UNIVERSE_DIAG)
            return out
    except Exception:
        # fall through to static universe
        pass

    # static / fallback universe
    out = cfg.get('UNIVERSE_LIST', []) or []
    src = 'settings_list'
    if not out:
        majors = cfg.get('UNIVERSE_MAJORS', ['BTC-USD', 'ETH-USD', 'SOL-USD', 'XRP-USD', 'DOGE-USD'])
        out = majors
        src = 'majors_fallback'

    out = list(out or [])
    _UNI_CACHE[key] = (now, out)
    _LAST_UNIVERSE_DIAG = {
        'ts': now,
        'mode': key,
        'source': src,
        'uni_out': len(out),
    }
    if isinstance(diag, dict):
        diag.update(_LAST_UNIVERSE_DIAG)
    return out

def _scores(c, cfg: Dict) -> List[Tuple[str, D]]:
    """
    Attempts several call shapes to strat.get_action_scores and normalizes output to [(pid, score)].
    """
    u = _universe(c, cfg)
    cand: List[Dict[str, Any]] = []

    for call in (
        lambda: strat.get_action_scores(client=c, settings=cfg, universe=u),
        lambda: strat.get_action_scores(client=c, settings=cfg),
        lambda: strat.get_action_scores(settings=cfg, universe=u),
        lambda: strat.get_action_scores(),
    ):
        try:
            r = call()
            if isinstance(r, list):
                cand = r
                break
        except Exception:
            continue

    out: List[Tuple[str, D]] = []
    for it in cand:
        pid = str(it.get("product_id") or it.get("pid") or "").upper()
        sc = _D(it.get("score") or it.get("signal") or 0)
        if pid:
            out.append((pid, sc))
    return out


def _soldier(cfg: Dict) -> D:
    return _D(cfg.get("SOLDIER_USD", 2))


def _print_header(cfg: Dict) -> None:
    chips = [
        f"[MIN_TOPBOOK_USD>={_D(cfg.get('MIN_TOPBOOK_USD', 1)):.2f}]",
        f"[MAX_SPREAD_PCT<={_D(cfg.get('MAX_SPREAD_PCT', 40)):.4f}]",
        f"[MIN_VOL_USD24H_M>={_D(cfg.get('MIN_1M_VOL', 0)):.2f}]",
        f"[COOLDOWN={int(cfg.get('COOLDOWN_TICKS', 0))}]",
        f"[AUTO_TRADE={'ON' if cfg.get('AUTO_TRADE') else 'OFF'}]",
        f"[MIN_DMID_BPS>={_D(cfg.get('MIN_DMID_BPS', 3)):.1f}]",
        f"[BP_MIN>={_D(cfg.get('BOOK_PRESSURE_MIN', 0.55)):.2f}]",
    ]
    print(
        f"{_utc_hms()} MODE={'LIVE' if not cfg.get('DRY') else 'DRY'} "
        f"DEFAULT_PRODUCT_ID={cfg.get('DEFAULT_PRODUCT_ID', 'XRP-USD')} "
        f"PORTFOLIO={cfg.get('PORTFOLIO', 'KOKO')} "
        f"PFID={os.environ.get('PFID', '')}  "
        f"UNIVERSE_MODE={cfg.get('UNIVERSE_MODE', 'TOP')} "
        f"TOP_N={cfg.get('TOP_N', 40)}"
    )
    print(" ".join(chips))
    print(f"{'pid':<23}{'score':>9}{'rk':>5}{'volM':>9}{'dmid%':>7}{'spr(bp)':>7}{'TDI':>8}  {'drivers':<27}{'ctx':>28}")


# ---------- MM16_TICKER_PNL ----------
# Cached helpers for in-ticker PnL/Usd readout (printed every N ticks)

_ENTRY_VWAP_CACHE: Dict[str, Tuple[float, D]] = {}
_POS_CACHE: Dict[str, Tuple[float, D]] = {}
_POS_SPLIT_CACHE: Dict[str, Tuple[float, Any]] = {}

def _entry_vwap_cached(client, pid: str, cfg: Dict[str, Any]) -> D:
    ttl = float(cfg.get("ENTRY_CACHE_SEC", 300))
    now = time.time()
    try:
        ts, v = _ENTRY_VWAP_CACHE.get(pid, (0.0, D("0")))
        if v > 0 and (now - float(ts)) <= ttl:
            return v
    except Exception:
        pass

    try:
        resp = client.get_fills(product_id=pid, limit=200)
    except Exception:
        return D("0")

    fills = resp.get("fills") if isinstance(resp, dict) else getattr(resp, "fills", None)
    if fills is None:
        fills = resp if isinstance(resp, list) else []
    if not isinstance(fills, list):
        fills = []

    tot_sz = D("0")
    tot_notional = D("0")
    for f in fills:
        side = str((f.get("side") if isinstance(f, dict) else getattr(f, "side", "")) or "").upper()
        if side not in ("BUY", "B"):
            continue
        try:
            sz = _D((f.get("size") if isinstance(f, dict) else getattr(f, "size", None)) or (f.get("base_size") if isinstance(f, dict) else getattr(f, "base_size", None)) or 0)
            px = _D((f.get("price") if isinstance(f, dict) else getattr(f, "price", None)) or (f.get("average_price") if isinstance(f, dict) else getattr(f, "average_price", None)) or 0)
        except Exception:
            continue
        if sz <= 0 or px <= 0:
            continue
        tot_sz += sz
        tot_notional += sz * px

    if tot_sz <= 0 or tot_notional <= 0:
        return D("0")

    vwap = tot_notional / tot_sz
    _ENTRY_VWAP_CACHE[pid] = (now, vwap)
    return vwap

def _base_total_cached(client, base: str, cfg: Dict[str, Any]) -> D:
    ttl = float(cfg.get("POS_CACHE_SEC", 20))
    now = time.time()
    b = str(base or "").upper()
    if not b:
        return D("0")
    try:
        ts, v = _POS_CACHE.get(b, (0.0, D("0")))
        if v > 0 and (now - float(ts)) <= ttl:
            return v
    except Exception:
        pass

    pfid = os.environ.get("PFID", "").strip() or str(cfg.get("PFID") or "").strip()
    total = D("0")
    try:
        try:
            resp = client.get_accounts(portfolio_uuid=pfid, limit=250) if pfid else client.get_accounts(limit=250)
        except TypeError:
            resp = client.get_accounts(portfolio_uuid=pfid) if pfid else client.get_accounts()
        accs = resp.get("accounts") if isinstance(resp, dict) else getattr(resp, "accounts", [])
        accs = accs or []
        for a in accs:
            try:
                a_pfid = str((a.get("retail_portfolio_id") if isinstance(a, dict) else getattr(a, "retail_portfolio_id", "")) or (a.get("portfolio_uuid") if isinstance(a, dict) else getattr(a, "portfolio_uuid", "")) or "")
                if pfid and a_pfid and a_pfid != pfid:
                    continue
                cur = str((a.get("currency") if isinstance(a, dict) else getattr(a, "currency", "")) or "").upper()
                if cur != b:
                    continue
                ab = a.get("available_balance") if isinstance(a, dict) else getattr(a, "available_balance", None)
                hv = a.get("hold") if isinstance(a, dict) else getattr(a, "hold", None)
                av = _D((ab.get("value") if isinstance(ab, dict) else getattr(ab, "value", None)) or 0) if ab is not None else D("0")
                hd = _D((hv.get("value") if isinstance(hv, dict) else getattr(hv, "value", None)) or 0) if hv is not None else D("0")
                total += av + hd
            except Exception:
                continue
    except Exception:
        total = D("0")

    _POS_CACHE[b] = (now, total)
    return total

def _maybe_print_pnl(c: coinbase.RESTClient, cfg: Dict[str, Any], metrics: Dict[str, Any], t: int) -> None:
    """Periodically print PnL for held positions among the current candidates.

    MM18: If ACTIVITY_TICKER is enabled and MARKET_TICKER_MINIMAL=True, route this output
    to the activity log so the market ticker stays clean and timely.
    """
    every = int(cfg.get("PNL_TICKER_EVERY", 10) or 0)
    if every <= 0:
        return
    if (t != 1) and (t % every != 0):
        return
    if not metrics:
        return

    to_activity = bool(cfg.get("PNL_TO_ACTIVITY", True))
    minimal = bool(cfg.get("MARKET_TICKER_MINIMAL", True))

    if minimal and not to_activity:
        return

    pos = _accounts_positions(c, cfg)
    if not pos:
        return

    dust = _D(cfg.get("POSITION_DUST", "0.00000010"))
    rows: List[Tuple[str, D, D, D]] = []  # (pid, amt, pnl%, usd)

    for pid, m in metrics.items():
        try:
            base = pid.split("-", 1)[0]
            amt = _base_total_cached(pos, base)
            if amt <= dust:
                continue
            mid = _D(m.get("mid", 0))
            entry = _entry_vwap_cached(c, pid, cfg)
            if entry <= 0 or mid <= 0:
                continue
            pnl_pct = (mid - entry) / entry * D("100")
            usd = amt * mid
            rows.append((pid, amt, pnl_pct, usd))
        except Exception:
            continue

    if not rows:
        return

    rows.sort(key=lambda r: float(r[3]), reverse=True)

    out: List[str] = []
    out.append("PNL (held positions among candidates)")
    out.append(f"{'pid':<20}{'amt':>14}{'pnl%':>10}{'usd':>14}")

    for pid, amt, pnl_pct, usd in rows[:8]:
        out.append(f"{pid:<20}{str(amt):>14}{float(pnl_pct):>10.2f}{float(usd):>14.2f}")

    block = "\n".join(out)

    if to_activity:
        _activity(cfg, block)

    if not minimal:
        print(block)
def _mm16_inv_get(obj, name, default=None):
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)

def _mm16_inventory_holdings(client, cfg: Dict[str, Any], t: int) -> None:
    try:
        on_start = bool(cfg.get("TP_INVENTORY_ON_START", False))
        every = int(cfg.get("TP_INVENTORY_EVERY_TICKS", 0))
        if not on_start and every <= 0:
            return
        if not ( (on_start and t == 1) or (every > 0 and (t % every) == 0) ):
            return

        max_pids = int(cfg.get("INV_MAX_PIDS", 12))
        if max_pids <= 0:
            return

        pfid = os.environ.get("PFID", "").strip() or str(cfg.get("PFID") or "").strip()

        # gather positions (available+hold) per currency
        try:
            try:
                resp = client.get_accounts(portfolio_uuid=pfid, limit=250) if pfid else client.get_accounts(limit=250)
            except TypeError:
                resp = client.get_accounts(portfolio_uuid=pfid) if pfid else client.get_accounts()
        except Exception:
            return
        accs = resp.get("accounts") if isinstance(resp, dict) else _mm16_inv_get(resp, "accounts", [])
        accs = accs or []

        pos = {}  # base -> total
        for a in accs:
            try:
                a_pfid = str((_mm16_inv_get(a, "retail_portfolio_id", "") or _mm16_inv_get(a, "portfolio_uuid", "") or "") or "")
                if pfid and a_pfid and a_pfid != pfid:
                    continue
                cur = str((_mm16_inv_get(a, "currency", "") or "")).upper()
                if not cur or cur in ("USD","USDC","USDT"):
                    continue
                ab = _mm16_inv_get(a, "available_balance", None)
                hv = _mm16_inv_get(a, "hold", None)
                av = _mm16_inv_get(ab, "value", 0) if ab is not None else 0
                hd = _mm16_inv_get(hv, "value", 0) if hv is not None else 0
                try:
                    tot = float(av) + float(hd)
                except Exception:
                    continue
                if tot > 0:
                    pos[cur] = pos.get(cur, 0.0) + tot
            except Exception:
                continue

        # Build candidate pids and estimate USD value with a quick best_bid_ask per pid
        rows = []
        for base, amt in pos.items():
            if base == "FX":
                continue
            pid = f"{base}-USD"
            try:
                bb = client.get_best_bid_ask(product_ids=[pid])
                pbs = bb.get("pricebooks") if isinstance(bb, dict) else _mm16_inv_get(bb, "pricebooks", None)
                if not pbs:
                    pbs = bb.get("data") if isinstance(bb, dict) else _mm16_inv_get(bb, "data", None)
                if not pbs:
                    continue
                pb = pbs[0]
                bids = _mm16_inv_get(pb, "bids", []) or []
                asks = _mm16_inv_get(pb, "asks", []) or []
                b0 = bids[0] if bids else None
                a0 = asks[0] if asks else None
                if not b0 or not a0:
                    continue
                bid = float(_mm16_inv_get(b0, "price", 0) or 0)
                ask = float(_mm16_inv_get(a0, "price", 0) or 0)
                if bid <= 0 or ask <= 0:
                    continue
                mid = (bid + ask) / 2.0
                usd_val = amt * mid
                rows.append((usd_val, pid, mid))
            except Exception:
                continue

        if not rows:
            return

        rows.sort(reverse=True, key=lambda r: r[0])
        rows = rows[:max_pids]

        n = 0
        n_sl = 0
        n_tp = 0

        for usd_val, pid, mid in rows:
            n += 1
            # stop-loss first
            try:
                grace = int(cfg.get("SL_GRACE_TICKS", 10))
                if (t - int(_LAST_BUY_TICK.get(pid, -999999))) < grace:
                    slr = {"action": "skip_grace"}
                else:
                    slr = stop_loss.check_and_exit(client, pid, cfg, None)
                if isinstance(slr, dict) and slr.get("action") == "stop_loss":
                    _SL_REENTRY_LAST_STOP[pid] = time.time()
                    n_sl += 1
                    continue
            except Exception:
                pass

            # ensure TP
            try:
                r = exit_engine.ensure_tp_for_product(client, pid, cfg, mid)
                if isinstance(r, dict) and (r.get("action") in ("place","replace")):
                    n_tp += 1
            except Exception:
                pass

        msg = f"[inventory_holdings] tick={t} checked={n} sl={n_sl} tp={n_tp}"
        if bool(cfg.get("ACTIVITY_TICKER", True)):
            _activity(cfg, msg)
        else:
            print(msg)
    except Exception:
        return

# ---------- MM16_INV_HOLDINGS ----------# ---------- MM16_SMART_BUY ----------
_BUY_STATE: Dict[str, Dict[str, Any]] = {}
_HOLD_FLOW_STATE: Dict[str, Dict[str, Any]] = {}
_ROLLOVER_EXIT_LAST_ATTEMPT: Dict[str, float] = {}

def _flow_state_get(store: Dict[str, Dict[str, Any]], pid: str) -> Dict[str, Any]:
    s = store.get(pid)
    if not isinstance(s, dict):
        s = {"mids": [], "confirm": 0, "last_tick": -1}
        store[pid] = s
    return s

def _sb_get(pid: str) -> Dict[str, Any]:
    return _flow_state_get(_BUY_STATE, pid)

def _hold_flow_get(pid: str) -> Dict[str, Any]:
    return _flow_state_get(_HOLD_FLOW_STATE, pid)

# ---------- MM18_SL_REENTRY_BLOCK ----------
_SL_REENTRY_LAST_STOP = {}  # pid -> last stop time (unix seconds)

def _stop_loss_reentry_block(pid, cfg, t):
    """Return True if re-entry should be blocked after a recent stop-loss.

    Uses wall-clock time (time.time()) for the cooldown window. Falls back to
    tick-based math only if the stored value looks like an older tick counter.
    """
    try:
        cool = float(cfg.get('SL_REENTRY_COOLDOWN_SEC', 0) or 0)
        if cool <= 0:
            return False
        last = _SL_REENTRY_LAST_STOP.get(pid)
        if last is None:
            return False

        # Back-compat: older builds stored last-stop as a tick counter.
        if isinstance(last, int) and isinstance(t, int) and last > 0 and t >= last:
            tick_sec = float(cfg.get('TICK_SEC', 1) or 1)
            if tick_sec <= 0:
                tick_sec = 1.0
            elapsed = (float(t) - float(last)) * tick_sec
        else:
            elapsed = time.time() - float(last)

        return elapsed >= 0 and elapsed < cool
    except Exception:
        return False

# ---------- MM18_SL_REENTRY_BLOCK ----------

def _continuation_update(
    store: Dict[str, Dict[str, Any]],
    pid: str,
    mid: D,
    dmid_bps: float,
    book_press: Optional[float],
    cfg: Dict[str, Any],
    t: int,
    allow_relief: bool = False,
) -> bool:
    confirm_n = int(cfg.get("BUY_CONFIRM_TICKS", 3))
    trend_n = int(cfg.get("TREND_TICKS", 5))
    trend_bps_min = float(cfg.get("TREND_BPS_MIN", 5.0))
    min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 0.0))
    if confirm_n < 1:
        confirm_n = 1
    if trend_n < 2:
        trend_n = 2

    st = _flow_state_get(store, pid)
    mids = st.get("mids") if isinstance(st.get("mids"), list) else []
    try:
        m = float(mid)
    except Exception:
        m = 0.0
    if m > 0:
        mids.append(m)
    if len(mids) > trend_n:
        mids = mids[-trend_n:]
    st["mids"] = mids

    deltas_bps: List[float] = []
    for i in range(1, len(mids)):
        base = float(mids[i - 1] or 0.0)
        last = float(mids[i] or 0.0)
        if base > 0.0 and last > 0.0:
            deltas_bps.append(((last - base) / base) * 10000.0)

    trend_bps = 0.0
    if len(mids) >= trend_n:
        base = float(mids[0] or 0.0)
        last = float(mids[-1] or 0.0)
        if base > 0.0 and last > 0.0:
            trend_bps = ((last - base) / base) * 10000.0

    last_step_bps = float(deltas_bps[-1]) if deltas_bps else float(dmid_bps or 0.0)
    prior_step_bps = float(deltas_bps[-2]) if len(deltas_bps) >= 2 else last_step_bps
    positive_steps = sum(1 for step in deltas_bps if step > 0.0)
    cooling = bool(deltas_bps) and (last_step_bps <= -1.5 and prior_step_bps <= -1.5)
    press_floor = max(0.01, float(cfg.get("BOOK_PRESSURE_MIN", 0.55)))
    try:
        press_now = float(book_press if book_press is not None else 0.5)
    except Exception:
        press_now = 0.5

    trend_ok = len(mids) >= trend_n and trend_bps >= trend_bps_min
    dmid_ok = float(dmid_bps or 0.0) >= min_dmid_bps
    pressing_now = (
        last_step_bps >= max(min_dmid_bps - 10.0, -10.0)
        and prior_step_bps >= -58.0
    )
    pressure_relief_ok = bool(
        press_now >= press_floor
        and last_step_bps >= max(min_dmid_bps - 12.0, -12.0)
        and prior_step_bps >= -64.0
    )
    step_ok = positive_steps >= max(1, len(deltas_bps) - 19)
    relief_ok = False
    if allow_relief and len(deltas_bps) >= 1:
        # Buy-side continuation should tolerate one deeper pullback when the
        # aggregate move is still lifting and the latest step has re-accelerated.
        # Held rollover remains stricter because it does not use the relief path.
        relief_trend_bps = max(trend_bps_min * 0.05, 0.5)
        relief_last_bps = max(min_dmid_bps - 4.5, -4.5)
        relief_prior_floor = -max(24.0, trend_bps_min * 2.5)
        relief_ok = bool(
            trend_bps >= relief_trend_bps
            and last_step_bps >= relief_last_bps
            and positive_steps >= max(1, len(deltas_bps) - 19)
            and prior_step_bps >= relief_prior_floor
            and not (last_step_bps <= -3.0 and prior_step_bps <= -2.0)
        )
    relief_ok = bool(relief_ok or (allow_relief and pressure_relief_ok and not cooling))
    sig_ok = (trend_ok and dmid_ok and pressing_now and step_ok and (not cooling)) or relief_ok

    if sig_ok:
        st["confirm"] = int(st.get("confirm", 0)) + 1
    else:
        st["confirm"] = 0

    st["last_tick"] = t
    st["trend_bps"] = float(trend_bps)
    st["last_step_bps"] = float(last_step_bps)
    st["cooling"] = bool(cooling)
    st["positive_steps"] = int(positive_steps)
    st["press_now"] = float(press_now)
    st["pressure_relief_ok"] = bool(pressure_relief_ok)
    st["relief_ok"] = bool(relief_ok)
    return int(st["confirm"]) >= confirm_n

def _sb_update(pid: str, mid: D, dmid_bps: float, book_press: Optional[float], cfg: Dict[str, Any], t: int) -> bool:
    return _continuation_update(_BUY_STATE, pid, mid, dmid_bps, book_press, cfg, t, allow_relief=True)

def _held_rollover_signal(pid: str, mid: D, dmid_bps: float, cfg: Dict[str, Any], t: int) -> Dict[str, Any]:
    sig_ok = _continuation_update(_HOLD_FLOW_STATE, pid, mid, dmid_bps, cfg, t)
    st = _hold_flow_get(pid)
    mids = st.get("mids") if isinstance(st.get("mids"), list) else []
    try:
        trend_n = int(cfg.get("TREND_TICKS", 5) or 5)
    except Exception:
        trend_n = 5
    if trend_n < 2:
        trend_n = 2
    try:
        min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 0.0) or 0.0)
    except Exception:
        min_dmid_bps = 0.0
    trend_bps = float(st.get("trend_bps", 0.0) or 0.0)
    last_step_bps = float(st.get("last_step_bps", float(dmid_bps or 0.0)) or 0.0)
    cooling = bool(st.get("cooling", False))
    enough_history = len(mids) >= trend_n
    broken = bool(
        enough_history
        and (not sig_ok)
        and (cooling or last_step_bps < min_dmid_bps or trend_bps < 0.0)
    )
    return {
        "sig_ok": bool(sig_ok),
        "broken": bool(broken),
        "enough_history": bool(enough_history),
        "trend_bps": float(trend_bps),
        "last_step_bps": float(last_step_bps),
        "dmid_bps": float(dmid_bps or 0.0),
        "cooling": bool(cooling),
        "positive_steps": int(st.get("positive_steps", 0) or 0),
    }

def _clear_position_caches(base: str = "") -> None:
    try:
        _POS_CACHE.clear()
    except Exception:
        pass
    try:
        _POS_SPLIT_CACHE.clear()
    except Exception:
        pass
    try:
        _USD_AVAIL_CACHE.clear()
    except Exception:
        pass
    if base:
        try:
            _POS_CACHE.pop(str(base).upper(), None)
        except Exception:
            pass

def _rollover_exit_attempt_allowed(pid: str, cfg: Dict[str, Any]) -> bool:
    try:
        cd = float(cfg.get("BUY_GLOBAL_COOLDOWN_SEC", 30.0) or 30.0)
    except Exception:
        cd = 30.0
    if cd < 10.0:
        cd = 10.0
    last = float(_ROLLOVER_EXIT_LAST_ATTEMPT.get(pid, 0.0) or 0.0)
    return (time.time() - last) >= cd

def _cancel_open_sell_orders_for_pid(client: Any, pid: str) -> int:
    try:
        resp = exit_engine._list_open_orders(client, pid)
        items = exit_engine._iter_orders(resp)
    except Exception:
        items = []
    sell_ids: List[str] = []
    for o in (items or []):
        try:
            side = str(
                (o.get("side") if isinstance(o, dict) else getattr(o, "side", ""))
                or (o.get("order_side") if isinstance(o, dict) else getattr(o, "order_side", ""))
                or ""
            ).upper()
            if side != "SELL":
                continue
            oid = str(
                (o.get("order_id") if isinstance(o, dict) else getattr(o, "order_id", ""))
                or (o.get("orderId") if isinstance(o, dict) else getattr(o, "orderId", ""))
                or ""
            )
            if oid:
                sell_ids.append(oid)
        except Exception:
            continue
    if not sell_ids:
        return 0
    try:
        exit_engine._cancel_order_ids(client, sell_ids)
    except Exception:
        return 0
    return len(sell_ids)

def _market_rollover_exit(client: Any, pid: str, cfg: Dict[str, Any], rollover: Dict[str, Any]) -> Dict[str, Any]:
    base = str(pid or "").split("-", 1)[0].upper()
    if not base:
        return {"ok": False, "reason": "bad_pid"}
    try:
        dust = _D(cfg.get("POSITION_DUST", "0.00000010"))
    except Exception:
        dust = D("0")

    def _read_split() -> Tuple[D, D, D]:
        pos_split_local = _accounts_positions_split(client, cfg) or {}
        av_hd_local = pos_split_local.get(base)
        if isinstance(av_hd_local, (tuple, list)):
            av_local = av_hd_local[0] if len(av_hd_local) > 0 else D("0")
            hd_local = av_hd_local[1] if len(av_hd_local) > 1 else D("0")
        else:
            av_local = av_hd_local or D("0")
            hd_local = D("0")
        av_local_d = av_local if isinstance(av_local, D) else _D(av_local or 0)
        hd_local_d = hd_local if isinstance(hd_local, D) else _D(hd_local or 0)
        return av_local_d, hd_local_d, (av_local_d + hd_local_d)

    av_d, hd_d, total_d = _read_split()
    if total_d <= dust:
        return {"ok": False, "reason": "no_position"}

    canceled = 0
    if hd_d > 0 or av_d <= dust:
        canceled = _cancel_open_sell_orders_for_pid(client, pid)
        if canceled > 0:
            # Coinbase balance releases can lag briefly after we cancel attached exits.
            # Poll a few short times so we don't misclassify a real held position as unavailable.
            for wait_s in (0.20, 0.35, 0.50):
                time.sleep(wait_s)
                _clear_position_caches(base)
                av_d, hd_d, total_d = _read_split()
                if av_d > dust or total_d <= dust:
                    break

    sell_amt = av_d
    if sell_amt <= dust and total_d > dust:
        # If the balance API still reports the position in hold right after cancel,
        # use the full owned amount for the rollover exit attempt instead of bailing out early.
        sell_amt = total_d
    if sell_amt <= dust:
        return {"ok": False, "reason": "no_available_after_cancel", "cancelled_sells": canceled}

    try:
        _pi, bi = limit_maker._get_increments(client, pid)
    except Exception:
        bi = D("0.000001")
    sell_size = limit_maker._q(_D(sell_amt), bi)
    if _D(sell_size) <= dust:
        return {"ok": False, "reason": "dust", "cancelled_sells": canceled}

    cid = str(uuid.uuid4())
    _ROLLOVER_EXIT_LAST_ATTEMPT[pid] = time.time()
    if bool(cfg.get("DRY", False)):
        _activity(
            cfg,
            f"[ROLLOVER_EXIT] pid={pid} dry=1 cid={cid} size={sell_size} "
            f"trend_bps={float(rollover.get('trend_bps', 0.0)):.2f} "
            f"last_step_bps={float(rollover.get('last_step_bps', 0.0)):.2f} "
            f"dmid_bps={float(rollover.get('dmid_bps', 0.0)):.2f} "
            f"cooling={int(bool(rollover.get('cooling', False)))} cancel_sells={canceled}"
        )
        return {"ok": True, "action": "dry", "cid": cid, "size": sell_size, "cancelled_sells": canceled}

    try:
        resp = limit_maker._market_sell(client, pid, base_size=sell_size, client_order_id=cid)
        _clear_position_caches(base)
        _activity(
            cfg,
            f"[ROLLOVER_EXIT] pid={pid} cid={cid} size={sell_size} "
            f"trend_bps={float(rollover.get('trend_bps', 0.0)):.2f} "
            f"last_step_bps={float(rollover.get('last_step_bps', 0.0)):.2f} "
            f"dmid_bps={float(rollover.get('dmid_bps', 0.0)):.2f} "
            f"cooling={int(bool(rollover.get('cooling', False)))} cancel_sells={canceled}"
        )
        return {"ok": True, "action": "market_sell", "cid": cid, "size": sell_size, "cancelled_sells": canceled, "resp": resp}
    except Exception as e:
        err = str(e or "")
        if "limit only mode" not in err.lower():
            raise

    bid_px = None
    ask_px = None
    fallback_px = None
    fallback_src = ""
    try:
        bid_px, ask_px, _bid_sz, _ask_sz = _best_bid_ask_row((client.get_best_bid_ask(product_ids=[pid]).get("pricebooks") or [{}])[0])
    except Exception:
        bid_px = None
        ask_px = None
    if bid_px and _D(bid_px) > 0:
        fallback_px = _D(bid_px)
        fallback_src = "best_bid"
    elif ask_px and _D(ask_px) > 0:
        # LIMIT_ONLY venues can briefly expose an ask without a usable bid.
        # Keep the rollover path alive by reusing the same live book snapshot.
        fallback_px = _D(ask_px)
        fallback_src = "best_ask"
    else:
        try:
            mid_px = _mid_for_pid(client, pid, cfg)
        except Exception:
            mid_px = D("0")
        if mid_px > 0:
            fallback_px = _D(mid_px)
            fallback_src = "mid_cache"
    if not fallback_px or _D(fallback_px) <= 0:
        return {"ok": False, "reason": "limit_only_no_bid", "cancelled_sells": canceled}
    try:
        px_inc, _base_inc = limit_maker._get_increments(client, pid)
    except Exception:
        px_inc = D("0.01")
    fallback_px = _D(limit_maker._q(_D(fallback_px), px_inc))
    if fallback_px <= 0:
        return {"ok": False, "reason": "limit_only_bad_fallback_px", "cancelled_sells": canceled}

    fallback = _place_order_adaptive(
        product_id=pid,
        side='SELL',
        size=sell_size,
        size_type='BASE',
        cfg=cfg,
        limit_price=str(fallback_px),
        post_only=False,
        client=client,
    )
    if not bool(fallback.get('ok')):
        return {"ok": False, "reason": str(fallback.get('error') or fallback.get('message') or 'limit_only_fallback_failed'), "cancelled_sells": canceled}

    _clear_position_caches(base)
    _activity(
        cfg,
        f"[ROLLOVER_EXIT] pid={pid} cid={str(fallback.get('client_order_id') or fallback.get('order_id') or cid)} size={sell_size} "
        f"limit_only_fallback=1 fallback_src={fallback_src} fallback_px={str(fallback_px)} "
        f"trend_bps={float(rollover.get('trend_bps', 0.0)):.2f} "
        f"last_step_bps={float(rollover.get('last_step_bps', 0.0)):.2f} "
        f"dmid_bps={float(rollover.get('dmid_bps', 0.0)):.2f} "
        f"cooling={int(bool(rollover.get('cooling', False)))} cancel_sells={canceled}"
    )
    return {"ok": True, "action": "limit_only_sell", "cid": cid, "size": sell_size, "cancelled_sells": canceled, "resp": fallback}

def _maybe_rollover_exit_held_positions(client: Any, cfg: Dict[str, Any], t: int, metrics: Dict[str, Dict[str, D]]) -> bool:
    try:
        grace = int(cfg.get("SL_GRACE_TICKS", 10) or 10)
    except Exception:
        grace = 10
    try:
        dust = _D(cfg.get("POSITION_DUST", "0.00000010"))
    except Exception:
        dust = D("0")

    try:
        pos_split = _accounts_positions_split(client, cfg) or {}
    except Exception:
        pos_split = {}
    if not pos_split:
        return False

    broken_rows: List[Tuple[float, float, str, Dict[str, Any]]] = []
    for base, av_hd in (pos_split or {}).items():
        try:
            pid = f"{str(base).upper()}-USD"
            if not _rollover_exit_attempt_allowed(pid, cfg):
                continue
            if (t - int(_LAST_BUY_TICK.get(pid, -999999))) < grace:
                continue
            if isinstance(av_hd, (tuple, list)):
                av = av_hd[0] if len(av_hd) > 0 else D("0")
                hd = av_hd[1] if len(av_hd) > 1 else D("0")
            else:
                av = av_hd or D("0")
                hd = D("0")
            total = (av if isinstance(av, D) else _D(av or 0)) + (hd if isinstance(hd, D) else _D(hd or 0))
            if total <= dust:
                continue

            m = metrics.get(pid)
            if not isinstance(m, dict) or _D(m.get("mid", 0)) <= 0:
                mid, spr_bps, tob, press = _book_metrics(client, pid)
                st = _hold_flow_get(pid)
                mids = st.get("mids") if isinstance(st.get("mids"), list) else []
                prev = _D(mids[-1]) if mids else D("0")
                dmid_bps = ((mid - prev) / prev * D("10000")) if prev > 0 else D("0")
                m = {
                    "mid": mid,
                    "spr_bps": spr_bps,
                    "tob": tob,
                    "press": press,
                    "dmid_bps": dmid_bps,
                }
                metrics[pid] = m

            mid = _D(m.get("mid", 0))
            if mid <= 0:
                continue
            dmid_bps = float(m.get("dmid_bps", m.get("dmid", 0)) or 0.0)
            rollover = _held_rollover_signal(pid, mid, dmid_bps, cfg, t)
            if not bool(rollover.get("broken", False)):
                continue

            entry_px = float(_entry_px_cached(client, pid, cfg) or 0.0)
            pnl_pct = 0.0
            if entry_px > 0.0:
                pnl_pct = ((float(mid) - entry_px) / entry_px) * 100.0
            broken_rows.append((float(pnl_pct), float(rollover.get("last_step_bps", 0.0) or 0.0), pid, rollover))
        except Exception:
            continue

    if not broken_rows:
        return False

    broken_rows.sort(key=lambda row: (float(row[0]), float(row[1]), str(row[2])))
    pnl_pct, _last_step, pid, rollover = broken_rows[0]
    try:
        resp = _market_rollover_exit(client, pid, cfg, rollover)
    except Exception as e:
        _activity(cfg, f"[ROLLOVER_EXIT_FAIL] pid={pid} err={e}")
        return False
    if not bool(resp.get("ok")):
        _activity(
            cfg,
            f"[ROLLOVER_EXIT_FAIL] pid={pid} reason={resp.get('reason') or 'exit_failed'} "
            f"trend_bps={float(rollover.get('trend_bps', 0.0)):.2f} "
            f"last_step_bps={float(rollover.get('last_step_bps', 0.0)):.2f} "
            f"dmid_bps={float(rollover.get('dmid_bps', 0.0)):.2f} "
            f"cooling={int(bool(rollover.get('cooling', False)))}"
        )
        return False
    _activity(
        cfg,
        f"[ROLLOVER_EXIT_OK] pid={pid} pnl_pct={float(pnl_pct):.2f} "
        f"trend_bps={float(rollover.get('trend_bps', 0.0)):.2f} "
        f"last_step_bps={float(rollover.get('last_step_bps', 0.0)):.2f} "
        f"dmid_bps={float(rollover.get('dmid_bps', 0.0)):.2f} "
        f"cooling={int(bool(rollover.get('cooling', False)))}"
    )
    return True

# ---------- MM16_SMART_BUY ----------# ---------- MM16_NEXT_CANDIDATE_FALLBACK ----------
# When a BUY attempt fails (e.g., Coinbase 500), do not stall the entire tick.
# Mark the pid in a short cooldown and try the next best candidate in the same tick.

_BUY_FAIL_COOLDOWN_UNTIL: Dict[str, float] = {}

# Global buy pacing: prevent burst-buying many symbols in one tick when multiple pass.
_GLOBAL_BUY_STATE: Dict[str, float] = {'until': 0.0}




# Global rotation pacing: when at INV_MAX_PIDS, optionally rotate out of a loser to free one slot.
_GLOBAL_ROTATE_STATE: Dict[str, float] = {'until': 0.0}

def _rotate_cooldown_active(now_ts: float) -> bool:
    try:
        return float(_GLOBAL_ROTATE_STATE.get('until', 0.0)) > float(now_ts)
    except Exception:
        return False

def _set_rotate_cooldown(cfg: Dict[str, Any], now_ts: float) -> None:
    try:
        sec = float(cfg.get('ROTATE_COOLDOWN_SEC', 300.0))
    except Exception:
        sec = 300.0
    _GLOBAL_ROTATE_STATE['until'] = float(now_ts) + max(0.0, sec)

def _buy_fail_cooldown_active(pid: str, now_ts: float) -> bool:
    try:
        return float(_BUY_FAIL_COOLDOWN_UNTIL.get(pid, 0.0)) > float(now_ts)
    except Exception:
        return False

def _mark_buy_fail(pid: str, cfg: Dict[str, Any], err: Any) -> None:
    try:
        cd = float(cfg.get("BUY_FAIL_COOLDOWN_SEC", 180))
    except Exception:
        cd = 180.0
    now = time.time()
    _BUY_FAIL_COOLDOWN_UNTIL[str(pid)] = now + cd
    try:
        msg = str(err)
    except Exception:
        msg = "err"
    print(f"[buy_fail] pid={pid} cooldown_sec={cd} err={msg[:120]}")
# ---------- MM19_ROTATE_AT_CAP ----------
def _rotate_free_slot_at_cap(
    c: Any,
    cfg: Dict[str, Any],
    held_bases: set,
    new_pid: str,
    new_score: float,
    now_ts: float,
) -> bool:
    """When INV_MAX_PIDS is reached and a strong new candidate appears, sell one held pid to free a slot.

    Behavior:
    - Sells ONE entire base position (closest thing to freeing a slot) using a SELL limit at best bid (post_only=False).
    - Uses a cooldown (ROTATE_COOLDOWN_SEC, default 300s) to avoid repeated churn.
    - Excludes bases in ROTATE_EXCLUDE_BASES (defaults to majors/stables).
    """
    try:
        if not bool(cfg.get('ROTATE_AT_INV_CAP', False)):
            return False
    except Exception:
        return False

    if _rotate_cooldown_active(now_ts):
        return False

    try:
        rot_min = float(cfg.get('ROTATE_MIN_SCORE', 0.70) or 0.0)
    except Exception:
        rot_min = 0.70
    try:
        if float(new_score) < float(rot_min):
            return False
    except Exception:
        return False

    new_pid = str(new_pid or '').upper()
    new_base = new_pid.split('-', 1)[0] if '-' in new_pid else new_pid

    # default excludes: majors + stables
    exclude = set(['USD','USDC','USDT','BTC','ETH','XRP','CBETH'])
    try:
        user_ex = cfg.get('ROTATE_EXCLUDE_BASES', None)
        if isinstance(user_ex, list):
            exclude.update({str(x).upper() for x in user_ex})
    except Exception:
        pass
    exclude.add(new_base)

    # Pull positions (base -> (available, hold)), then pick a loser to sell
    try:
        pos_split = _accounts_positions_split(c, cfg)
    except Exception:
        pos_split = {}

    try:
        min_usd = float(cfg.get('ROTATE_MIN_USD', cfg.get('SOLDIER_USD', 10.0)) or 0.0)
    except Exception:
        min_usd = 10.0

    try:
        allow_cancel_sells = bool(cfg.get('ALLOW_CANCEL_SELLS', False))
    except Exception:
        allow_cancel_sells = False

    candidates: List[Tuple[float, float, str, str, D]] = []  # (pnl_pct, usd_notional, pid, base, amt)

    for base, av_hd in (pos_split or {}).items():
        try:
            b = str(base).upper()
            if (not b) or (b in exclude):
                continue
            if held_bases and (b not in held_bases):
                continue
            if not av_hd:
                continue
            if isinstance(av_hd, (tuple, list)):
                av = av_hd[0] if len(av_hd) > 0 else D("0")
                hd = av_hd[1] if len(av_hd) > 1 else D("0")
            else:
                av = av_hd
                hd = D("0")
            av_d = av if isinstance(av, D) else _D(av)
            hd_d = hd if isinstance(hd, D) else _D(hd)
            total_d = av_d + hd_d
            if total_d <= 0:
                continue
            # If inventory is held by open orders, we can only rotate it when cancels are allowed.
            if hd_d > 0 and (not allow_cancel_sells):
                continue
            amt_d = total_d
            pid = f"{b}-USD"
            if pid == new_pid:
                continue

            mid, spr_bps, tob_usd, press = _book_metrics(c, pid)
            if mid <= 0:
                continue
            usd_notional = float(mid * amt_d)
            if usd_notional < float(min_usd):
                continue

            entry = _entry_vwap_cached(c, pid, cfg)
            pnl_pct = 0.0
            if entry and entry > 0:
                pnl_pct = float((mid - entry) / entry * D('100'))

            candidates.append((pnl_pct, usd_notional, pid, b, amt_d))
        except Exception:
            continue

    if not candidates:
        return False

    # Prefer selling worst PnL; if all green, sell smallest notional
    losers = [x for x in candidates if x[0] < 0.0]
    if losers:
        losers.sort(key=lambda t: (t[0], t[1]))  # most negative pnl first
        pnl_pct, usd_notional, sell_pid, sell_base, sell_amt = losers[0]
    else:
        candidates.sort(key=lambda t: (t[1], t[0]))  # smallest notional first
        pnl_pct, usd_notional, sell_pid, sell_base, sell_amt = candidates[0]

    # If the chosen position is held by open TP orders, cancel SELL orders first (only if allowed),
    # then re-read the available balance so the rotate SELL can succeed.
    if allow_cancel_sells:
        try:
            pos_now = _accounts_positions_split(c, cfg) or {}
            av_hd_now = pos_now.get(sell_base, None)
            if isinstance(av_hd_now, (tuple, list)):
                av_now = av_hd_now[0] if len(av_hd_now) > 0 else D("0")
                hd_now = av_hd_now[1] if len(av_hd_now) > 1 else D("0")
            else:
                av_now = av_hd_now
                hd_now = D("0")
            av_now_d = av_now if isinstance(av_now, D) else _D(av_now or 0)
            hd_now_d = hd_now if isinstance(hd_now, D) else _D(hd_now or 0)

            if hd_now_d > 0:
                try:
                    open_orders = exit_engine._list_orders_open(c, sell_pid, limit=200)
                except Exception:
                    open_orders = []
                sell_ids: List[str] = []
                for o in (open_orders or []):
                    try:
                        side = str(o.get("side") or o.get("order_side") or "").upper()
                        if side != "SELL":
                            continue
                        oid = str(o.get("order_id") or "")
                        if oid:
                            sell_ids.append(oid)
                    except Exception:
                        continue
                if sell_ids:
                    cr = exit_engine._cancel_order_ids(c, sell_ids)
                    _activity(cfg, f"[ROTATE] cancel_sells pid={sell_pid} n={len(sell_ids)} ok={bool(cr.get('ok'))}")
                # refresh available after cancel
                pos_now2 = _accounts_positions_split(c, cfg) or {}
                av_hd_now2 = pos_now2.get(sell_base, None)
                if isinstance(av_hd_now2, (tuple, list)):
                    av2 = av_hd_now2[0] if len(av_hd_now2) > 0 else D("0")
                    hd2 = av_hd_now2[1] if len(av_hd_now2) > 1 else D("0")
                else:
                    av2 = av_hd_now2
                    hd2 = D("0")
                av2_d = av2 if isinstance(av2, D) else _D(av2 or 0)
                hd2_d = hd2 if isinstance(hd2, D) else _D(hd2 or 0)
                # Only proceed if inventory is now free (or partially free); sell available only
                if av2_d > 0:
                    sell_amt = av2_d
                if hd2_d > 0:
                    # still held; let the rotate attempt fail fast in this tick
                    pass
        except Exception:
            pass

    # Get best bid for sell price
    bid_px = None
    try:
        r = c.get_best_bid_ask(product_ids=[sell_pid])
        pb_list = r.get('pricebooks') if isinstance(r, dict) else getattr(r, 'pricebooks', None)
        if not pb_list and isinstance(r, dict):
            pb_list = r.get('data')
        if pb_list:
            bid, ask, bs, asz = _best_bid_ask_row(pb_list[0])
            if bid and bid > 0:
                bid_px = str(bid)
    except Exception:
        bid_px = None

    size_str = str(sell_amt)
    resp = _place_order_adaptive(
        product_id=sell_pid,
        side='SELL',
        size=size_str,
        size_type='BASE',
        cfg=cfg,
        limit_price=bid_px,      # sell at bid to free funds (can execute immediately)
        post_only=False,
        client=c,
    )
    ok = bool(resp.get('ok'))
    if ok:
        _activity(cfg, f"[ROTATE] sell_ok pid={sell_pid} usd~{usd_notional:.2f} pnl%={pnl_pct:.2f} new={new_pid} score={float(new_score):.4f}")
    else:
        err = resp.get('error') or 'SELL_FAILED'
        _activity(cfg, f"[ROTATE_FAIL] pid={sell_pid} err={err} new={new_pid} score={float(new_score):.4f}")
    _set_rotate_cooldown(cfg, now_ts)
    return ok

# ---------- MM16_NEXT_CANDIDATE_FALLBACK ----------

# ---------- MM16_IDEA_STATE ----------
# Virtual probe / idea memory: require a candidate to "prove itself" over time before first entry.
# Settings:
#   IDEA_STREAK_MIN (int, default 3)    : consecutive qualifying ticks required
#   IDEA_PNL_BPS_MIN (float, default 10): required improvement from first-qualified mid in bps
#   IDEA_EXPIRE_TICKS (int, default 20) : if not seen for this many ticks, reset idea

_IDEA_STATE: Dict[str, Dict[str, Any]] = {}

def _idea_get(pid: str) -> Dict[str, Any]:
    s = _IDEA_STATE.get(pid)
    if not isinstance(s, dict):
        s = {
            "first_tick": -1,
            "first_mid": D("0"),
            "last_tick": -999999,
            "streak": 0,
            "max_mid": D("0"),
            "pnl_bps": 0.0,
            "dd_bps": 0.0,
            "last_log_tick": -999999,
        }
        _IDEA_STATE[pid] = s
    return s

def _idea_update(pid: str, mid: D, t: int, cfg: Dict[str, Any]) -> Dict[str, Any]:

    # MM18_IDEA_CFG_DEFAULT

    if cfg is None: cfg = {}
    pid = str(pid)
    s = _idea_get(pid)
    expire = int(cfg.get("IDEA_EXPIRE_TICKS", 20) or 20)
    if expire < 1:
        expire = 1

    # expire/reset if not seen recently or bad mid
    if mid <= 0 or (t - int(s.get("last_tick", -999999))) > expire:
        s["first_tick"] = t
        s["first_mid"] = mid
        s["last_tick"] = t
        s["streak"] = 1
        s["max_mid"] = mid
        s["pnl_bps"] = 0.0
        s["dd_bps"] = 0.0
        return s

    # consecutive streak
    if int(s.get("last_tick", -999999)) == (t - 1):
        s["streak"] = int(s.get("streak", 0)) + 1
    else:
        # new idea segment
        s["first_tick"] = t
        s["first_mid"] = mid
        s["streak"] = 1
        s["max_mid"] = mid

    s["last_tick"] = t

    first_mid = s.get("first_mid", D("0"))
    if isinstance(first_mid, (int, float)):
        first_mid = D(str(first_mid))
    if first_mid and first_mid > 0:
        s["pnl_bps"] = float((mid - first_mid) / first_mid * D("10000"))
    else:
        s["pnl_bps"] = 0.0

    max_mid = s.get("max_mid", D("0"))
    if isinstance(max_mid, (int, float)):
        max_mid = D(str(max_mid))
    if mid > max_mid:
        s["max_mid"] = mid
        max_mid = mid
    if max_mid and max_mid > 0:
        s["dd_bps"] = float((mid - max_mid) / max_mid * D("10000"))
    else:
        s["dd_bps"] = 0.0

    return s

def _idea_gate_ok(idea: Dict[str, Any], cfg: Dict[str, Any]) -> tuple[bool, str]:
    """Returns (ok, note). Note is used for skip logging when ok is False."""
    need_streak = int(cfg.get("IDEA_STREAK_MIN", 3) or 3)
    need_bps = float(cfg.get("IDEA_PNL_BPS_MIN", 10.0) or 10.0)
    if need_streak < 1:
        need_streak = 1

    # allow disabling by setting negative bps
    try:
        streak = int(idea.get("streak", 0))
    except Exception:
        streak = 0
    try:
        pnl_bps = float(idea.get("pnl_bps", 0.0))
    except Exception:
        pnl_bps = 0.0

    ok = (streak >= need_streak) and (pnl_bps >= need_bps)
    if ok:
        return True, "ok"
    return False, f"idea_gate streak={streak}/{need_streak} pnl_bps={pnl_bps:.1f}/{need_bps:.1f}"
# ---------- MM16_IDEA_STATE ----------

# ---------- MM16_GAINERS_MODE ----------
# Public 24h stats via Coinbase Exchange endpoint /products/<pid>/stats
# Used to rank/filter candidates so we buy gainers (up coins), not decliners.
import urllib.request, urllib.error, json as _json

_STATS_CACHE: Dict[str, Tuple[float, float]] = {}  # pid -> (ts, pct24 last-known-good)

def _gainer_24h_pct(pid: str, cfg: Dict[str, Any]) -> float:
    pid = str(pid or "")
    if not bool(cfg.get("PUBLIC_STATS_HTTP", True)):
        try:
            return float((_STATS_CACHE.get(pid, (0.0, 0.0)) or (0.0, 0.0))[1])
        except Exception:
            return 0.0
    try:
        ttl = float(cfg.get("STATS_TTL_SEC", 60) or 60)
    except Exception:
        ttl = 60.0
    now = time.time()
    prev_ts = 0.0
    prev_v = 0.0
    try:
        prev_ts, prev_v = _STATS_CACHE.get(pid, (0.0, 0.0))
        if (now - float(prev_ts)) <= ttl:
            return float(prev_v)
    except Exception:
        pass
    try:
        url = f"https://api.exchange.coinbase.com/products/{pid}/stats"
        req = urllib.request.Request(url, headers={"User-Agent":"Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=float(cfg.get("PUBLIC_STATS_TIMEOUT_SEC", 3.0) or 3.0)) as resp:
            data = resp.read().decode("utf-8")
        d = _json.loads(data)
        o = float(d.get("open", 0) or 0)
        last = float(d.get("last", 0) or 0)
        if o > 0 and last > 0:
            pct24 = ((last / o) - 1.0) * 100.0
            _STATS_CACHE[pid] = (now, pct24)
            return float(pct24)
        if float(prev_ts) > 0.0:
            _STATS_CACHE[pid] = (now, float(prev_v))
            return float(prev_v)
        return 0.0
    except Exception:
        if float(prev_ts) > 0.0:
            _STATS_CACHE[pid] = (now, float(prev_v))
            return float(prev_v)
        return 0.0
# ---------- MM16_GAINERS_MODE ----------# ---------- MM16_BUY_STALE_CANCEL ----------
_BUY_OPEN_SWEEP_LAST: float = 0.0
_ORPHAN_BRACKET_SWEEP_LAST: float = 0.0

def _parse_iso_ts(s: str) -> float:
    try:
        from datetime import datetime
        ss = (s or "").strip()
        if not ss:
            return 0.0
        if ss.endswith("Z"):
            ss = ss[:-1] + "+00:00"
        return datetime.fromisoformat(ss).timestamp()
    except Exception:
        return 0.0

# MM30_ATTACHED_EXIT_SURFACING_COOLDOWN_V1
_MM30_ATTACHED_EXIT_PRIMED = False
_MM30_ATTACHED_EXIT_SEEN_KEYS = set()
_MM30_ATTACHED_EXIT_PENDING = []
_MM30_ATTACHED_EXIT_LAST_SL_TS = {}


def _mm30_attached_exit_refresh(cfg: Dict[str, Any]) -> None:
    global _MM30_ATTACHED_EXIT_PRIMED, _MM30_ATTACHED_EXIT_SEEN_KEYS, _MM30_ATTACHED_EXIT_PENDING, _MM30_ATTACHED_EXIT_LAST_SL_TS
    try:
        import os as _os
        import re as _re
        from datetime import datetime as _dt
        path = str(cfg.get("ACTIVITY_LOG_PATH") or "logs/activity_ticker.log")
        if not path:
            return
        if not _os.path.isabs(path):
            try:
                path = _os.path.join(ROOT, path)
            except Exception:
                pass
        if not _os.path.exists(path):
            return
        max_bytes = 1024 * 1024
        with open(path, "rb") as _fh:
            _fh.seek(0, 2)
            _size = _fh.tell()
            _fh.seek(max(0, _size - max_bytes))
            _blob = _fh.read()
        text = _blob.decode("utf-8", "replace")
        pat = _re.compile(r'^\[(?P<ts>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\] \[SELL_OK\] pid=(?P<pid>\S+) src=attached_exit reason=(?P<reason>TP|SL|EXIT)\b.*?(?:\boid=(?P<oid>\S+))?', _re.M)
        found = []
        for m in pat.finditer(text):
            ts_text = m.group("ts")
            pid = str(m.group("pid") or "")
            reason = str(m.group("reason") or "")
            oid = str(m.group("oid") or "")
            if not pid or not reason:
                continue
            key = f"{pid}|{reason}|{oid or ts_text}"
            try:
                ts_epoch = _dt.strptime(ts_text, "%Y-%m-%d %H:%M:%S").timestamp()
            except Exception:
                ts_epoch = 0.0
            found.append((key, pid, reason, oid, ts_text, ts_epoch))
        if not found:
            _MM30_ATTACHED_EXIT_PRIMED = True
            return
        if not _MM30_ATTACHED_EXIT_PRIMED:
            for key, pid, reason, oid, ts_text, ts_epoch in found:
                _MM30_ATTACHED_EXIT_SEEN_KEYS.add(key)
                if reason == "SL" and ts_epoch > 0:
                    prev = float(_MM30_ATTACHED_EXIT_LAST_SL_TS.get(pid, 0.0) or 0.0)
                    if ts_epoch > prev:
                        _MM30_ATTACHED_EXIT_LAST_SL_TS[pid] = ts_epoch
            _MM30_ATTACHED_EXIT_PRIMED = True
            return
        for key, pid, reason, oid, ts_text, ts_epoch in found:
            if key in _MM30_ATTACHED_EXIT_SEEN_KEYS:
                continue
            _MM30_ATTACHED_EXIT_SEEN_KEYS.add(key)
            if reason == "SL" and ts_epoch > 0:
                prev = float(_MM30_ATTACHED_EXIT_LAST_SL_TS.get(pid, 0.0) or 0.0)
                if ts_epoch > prev:
                    _MM30_ATTACHED_EXIT_LAST_SL_TS[pid] = ts_epoch
            _MM30_ATTACHED_EXIT_PENDING.append({"pid": pid, "reason": reason, "oid": oid, "ts": ts_text, "ts_epoch": ts_epoch})
        if len(_MM30_ATTACHED_EXIT_PENDING) > 200:
            _MM30_ATTACHED_EXIT_PENDING = _MM30_ATTACHED_EXIT_PENDING[-200:]
    except Exception:
        pass


def _mm30_attached_exit_drain(cfg: Dict[str, Any]):
    global _MM30_ATTACHED_EXIT_PENDING
    tp_n = 0
    sl_n = 0
    exit_n = 0
    _mm30_attached_exit_refresh(cfg)
    try:
        pending = list(_MM30_ATTACHED_EXIT_PENDING)
        _MM30_ATTACHED_EXIT_PENDING = []
        for ev in pending:
            pid = str(ev.get("pid") or "")
            reason = str(ev.get("reason") or "")
            oid = str(ev.get("oid") or "")
            ts_text = str(ev.get("ts") or "")
            if reason == "TP":
                tp_n += 1
                _activity(cfg, f"[TP] pid={pid} src=attached_exit oid={oid} ts={ts_text}")
            elif reason == "SL":
                sl_n += 1
                _activity(cfg, f"[SL] pid={pid} src=attached_exit oid={oid} ts={ts_text}")
            else:
                exit_n += 1
                _activity(cfg, f"[EXIT] pid={pid} src=attached_exit oid={oid} ts={ts_text}")
    except Exception:
        pass
    return tp_n, sl_n, exit_n

def _cancel_orders_safe(client, order_ids):
    if not order_ids:
        return
    try:
        client.cancel_orders(order_ids=order_ids)
        return
    except TypeError:
        pass
    except Exception:
        pass
    try:
        client.cancel_orders(order_ids)
    except Exception:
        pass

def _cancel_stale_buy_orders(client, cfg: Dict[str, Any]) -> None:
    global _BUY_OPEN_SWEEP_LAST
    try:
        stale_sec = float(cfg.get("BUY_STALE_CANCEL_SEC", 15) or 15)
        max_open = int(cfg.get("BUY_MAX_OPEN", 1) or 1)
    except Exception:
        stale_sec = 15.0
        max_open = 1

    if stale_sec <= 0 and max_open <= 0:
        return

    now = time.time()
    # avoid running more than once per second even if tick loop is tight
    if now - float(_BUY_OPEN_SWEEP_LAST or 0.0) < 1.0:
        return
    _BUY_OPEN_SWEEP_LAST = now

    try:
        resp = client.list_orders(order_status=["OPEN"], limit=200)
    except TypeError:
        try:
            resp = client.list_orders(limit=200)
        except Exception:
            return
    except Exception:
        return

    orders = resp.get("orders") if isinstance(resp, dict) else getattr(resp, "orders", resp)
    if not orders or not isinstance(orders, list):
        return

    buys = []
    for o in orders:
        try:
            side = str((o.get("side") if isinstance(o, dict) else getattr(o, "side", "")) or "").upper()
            if side != "BUY":
                continue
            pid = str((o.get("product_id") if isinstance(o, dict) else getattr(o, "product_id", "")) or (o.get("productId") if isinstance(o, dict) else getattr(o, "productId", "")) or "")
            oid = str((o.get("order_id") if isinstance(o, dict) else getattr(o, "order_id", "")) or (o.get("orderId") if isinstance(o, dict) else getattr(o, "orderId", "")) or "")
            cts = str((o.get("created_time") if isinstance(o, dict) else getattr(o, "created_time", "")) or (o.get("created_at") if isinstance(o, dict) else getattr(o, "created_at", "")) or "")
            ts0 = _parse_iso_ts(cts)
            age = (now - ts0) if ts0 > 0 else 0.0
            buys.append((age, ts0, pid, oid))
        except Exception:
            continue

    if not buys:
        return

    # cancel stale
    stale_ids = []
    for age, ts0, pid, oid in buys:
        if stale_sec > 0 and age >= stale_sec and oid:
            stale_ids.append(oid)
            print(f"[buy_cancel_stale] pid={pid} age={age:.1f}")
    if stale_ids:
        _cancel_orders_safe(client, stale_ids)

    # enforce max open after stale cancels (best-effort; we don't re-fetch)
    if max_open >= 0:
        remain = [(age, ts0, pid, oid) for (age, ts0, pid, oid) in buys if oid and oid not in set(stale_ids)]
        # sort oldest first
        remain.sort(key=lambda x: (x[1] if x[1] > 0 else 0.0))
        if max_open == 0:
            extra = remain
        else:
            extra = remain[:-max_open] if len(remain) > max_open else []
        extra_ids = [oid for _,_,_,oid in extra if oid]
        for age, ts0, pid, oid in extra:
            if oid:
                print(f"[buy_cancel_stale] pid={pid} age={age:.1f}")
        if extra_ids:
            _cancel_orders_safe(client, extra_ids)


def _cancel_orphan_sell_brackets(client, cfg: Dict[str, Any], held_bases_all: set) -> int:
    """Cancel orphan SELL trigger-bracket orders when PFID has zero base balance."""
    global _ORPHAN_BRACKET_SWEEP_LAST
    try:
        sweep_sec = float(cfg.get("ORPHAN_BRACKET_SWEEP_SEC", 30) or 30)
    except Exception:
        sweep_sec = 30.0

    now = time.time()
    if sweep_sec > 0 and (now - float(_ORPHAN_BRACKET_SWEEP_LAST or 0.0)) < sweep_sec:
        return 0
    _ORPHAN_BRACKET_SWEEP_LAST = now

    try:
        resp = client.list_orders(order_status=["OPEN"], limit=200)
    except TypeError:
        try:
            resp = client.list_orders(limit=200)
        except Exception:
            return 0
    except Exception:
        return 0

    orders = resp.get("orders") if isinstance(resp, dict) else getattr(resp, "orders", resp)
    if not orders or not isinstance(orders, list):
        return 0

    pfid = os.environ.get("PFID", "").strip() or str(cfg.get("PFID") or "").strip()
    cancel_ids = []
    cancelled_pids = []

    for o in orders:
        try:
            side = str((o.get("side") if isinstance(o, dict) else getattr(o, "side", "")) or "").upper()
            if side != "SELL":
                continue
            pid = str((o.get("product_id") if isinstance(o, dict) else getattr(o, "product_id", "")) or (o.get("productId") if isinstance(o, dict) else getattr(o, "productId", "")) or "")
            if not pid or not pid.endswith("-USD"):
                continue
            base = str(pid).split("-")[0].upper()
            if base and base in held_bases_all:
                continue

            o_pfid = str((o.get("retail_portfolio_id") if isinstance(o, dict) else getattr(o, "retail_portfolio_id", "")) or (o.get("portfolio_uuid") if isinstance(o, dict) else getattr(o, "portfolio_uuid", "")) or "")
            if pfid and o_pfid and o_pfid != pfid:
                continue

            oc = o.get("order_configuration") if isinstance(o, dict) else getattr(o, "order_configuration", None)
            type_keys = list(oc.keys()) if isinstance(oc, dict) else []
            order_type = str((o.get("order_type") if isinstance(o, dict) else getattr(o, "order_type", "")) or "").upper()
            client_oid = str((o.get("client_order_id") if isinstance(o, dict) else getattr(o, "client_order_id", "")) or "")
            if ("trigger_bracket_gtc" not in type_keys) and (order_type != "TAKE_PROFIT_STOP_LOSS") and ("_attached" not in client_oid):
                continue

            oid = str((o.get("order_id") if isinstance(o, dict) else getattr(o, "order_id", "")) or (o.get("orderId") if isinstance(o, dict) else getattr(o, "orderId", "")) or "")
            if not oid:
                continue
            trigger_status = str((o.get("trigger_status") if isinstance(o, dict) else getattr(o, "trigger_status", "")) or "")
            cancel_ids.append(oid)
            cancelled_pids.append(pid)
            _activity(cfg, f"[orphan_bracket] pid={pid} action=cancel base_held=0 oid={oid} type={','.join(type_keys) if type_keys else order_type} trigger_status={trigger_status}")
        except Exception:
            continue

    if cancel_ids:
        _cancel_orders_safe(client, cancel_ids)
        try:
            with _ATTACHED_OPEN_LOCK:
                for pid in cancelled_pids:
                    _ATTACHED_OPEN.pop(pid, None)
        except Exception:
            pass
    return len(cancel_ids)

# ---------- MM16_BUY_STALE_CANCEL ----------# ---------- main loop ----------

def run_loop(console: bool = True, ticks: int = 0) -> None:
    """
    Core ticker loop. If ticks>0, exits after that many ticks.
    """
    cfg = load_settings()
    pfid = os.environ.get("PFID", "").strip() or str(cfg.get("PFID") or "").strip()
    # MM19_STARTUP_HANG_GUARD: prevent indefinite hangs on network calls
    try:
        socket.setdefaulttimeout(float(cfg.get("HTTP_TIMEOUT_SEC", 15.0)))
    except Exception:
        pass
    _print_header(cfg)
    _write_run_active(cfg.get("RUN_ACTIVE_PATH", "logs/run_active.json"))
    _spawn_activity_ticker(cfg)
    try:
        _activity(cfg, f"[run_start] pfid={os.environ.get('PFID','') or cfg.get('PFID','')} tick_sec={cfg.get('TICK_SEC')} top_n={cfg.get('TOP_N')} soldier_usd={cfg.get('SOLDIER_USD')}")
    except Exception:
        pass
    _hang_guard_start(cfg)

    c = get_client()

    max_spr_bps = _D(cfg.get("MAX_SPREAD_PCT", 40)) * D("100")  # percent → bps
    min_tob_usd = _D(cfg.get("MIN_TOPBOOK_USD", 1))
    min_dmid_bps = _D(cfg.get("MIN_DMID_BPS", 3))
    min_press = _D(cfg.get("BOOK_PRESSURE_MIN", 0.55))
    cooldown = int(cfg.get("COOLDOWN_TICKS", 0))
    topn = int(cfg.get("TOP_N", 40))

    last_buy_tick: Dict[str, int] = {}
    last_mid: Dict[str, D] = {}
    t = 0
    held: Dict[str, int] = {}  # MM18_HELD_STATE (pyramid cap state)

    while True:
        try:
            live_cfg = load_settings()
            if isinstance(live_cfg, dict):
                # Keep safety / identity paths pinned until an intentional restart,
                # but let runtime thresholds and pacing settings hot-apply on save.
                for locked_key in ("DRY", "PFID", "RUN_ACTIVE_PATH", "ACTIVITY_LOG_PATH"):
                    if locked_key in cfg:
                        live_cfg[locked_key] = cfg.get(locked_key)
                changed_keys = [
                    k for k in sorted(set(cfg.keys()) | set(live_cfg.keys()))
                    if cfg.get(k) != live_cfg.get(k)
                ]
                if changed_keys:
                    cfg = live_cfg
                    try:
                        changed_preview = ",".join(changed_keys[:8])
                        if len(changed_keys) > 8:
                            changed_preview += ",..."
                        _activity(cfg, f"[settings_reload] changed={changed_preview}")
                    except Exception:
                        pass
        except Exception:
            pass
        t += 1
        print(f"{_utc_hms()} tick {t} start")
        try:
            if t == 1:
                try:
                    _activity(cfg, "[startup] before_scores")
                except Exception:
                    pass
            rows = _scores(c, cfg)
            if t == 1:
                try:
                    _activity(cfg, f"[startup] after_scores rows={len(rows)}")
                except Exception:
                    pass
            if not rows:
                print("No pairs pass filters")

            # prewarm higher-timeframe context for the current visible board before the pane renders
            try:
                if _cycle_ctx_autofill_enabled(cfg):
                    for pre_pid, _pre_score in rows[: min(12, topn)]:
                        _cycle_ctx_autofill_request(cfg, pre_pid)
            except Exception:
                pass

            # print pane and collect live metrics
            metrics: Dict[str, Dict[str, D]] = {}
            for rk, (pid, score) in enumerate(rows[: min(6, topn)], start=1):
                if t == 1 and rk == 1:
                    try:
                        _activity(cfg, f"[startup] before_book_metrics pid={pid}")
                    except Exception:
                        pass
                if t == 1:
                    try:
                        n = int(cfg.get("STARTUP_TRACE_BOOK_N", 25))
                        if rk <= n:
                            _activity(cfg, f"[startup] before_book_metrics pid={pid} rk={rk}")
                    except Exception:
                        pass
                mid, spr_bps, tob, press = _book_metrics(c, pid)
                if t == 1:
                    try:
                        n = int(cfg.get("STARTUP_TRACE_BOOK_N", 25))
                        if rk <= n:
                            _activity(cfg, f"[startup] after_book_metrics pid={pid} rk={rk}")
                    except Exception:
                        pass
                prev = last_mid.get(pid, D("0"))
                dmid_bps = ((mid - prev) / prev * D("10000")) if prev > 0 else D("0")
                metrics[pid] = {
                    "mid": mid,
                    "spr_bps": spr_bps,
                    "tob": tob,
                    "press": press,
                    "dmid_bps": dmid_bps,
                }                # dmid% is dmid_bps / 100
                vol_usd = 0.0
                try:
                    if u_dyn and hasattr(u_dyn, 'LAST_VOL24H_USD'):
                        vol_usd = float(u_dyn.LAST_VOL24H_USD.get(pid, 0.0) or 0.0)
                except Exception:
                    vol_usd = 0.0
                vol_m = _D(vol_usd) / D('1000000')
                tdi_preview = None
                try:
                    try:
                        _trough_update(cfg, pid, t, float(mid))
                    except Exception:
                        pass
                    trough_info = None
                    try:
                        _tpct, _tlo, _thi, _tn = _trough_compute(cfg, pid, t, float(mid))
                    except Exception:
                        _tpct, _tlo, _thi, _tn = (None, None, None, 0)
                    if (_tpct is not None) or (int(_tn) > 0):
                        trough_info = {
                            "trough_n": int(_tn),
                        }
                        if _tpct is not None:
                            trough_info["trough_pct"] = float(round(float(_tpct), 6))
                    cycle_preview = _cycle_ctx_for_pid_dynamic(cfg, pid)
                    tdi_cycle_preview = cycle_preview if _cycle_ctx_enabled(cfg) else None
                    tdi_preview = _tdi_compute(cfg, pid, score, metrics[pid], tick=t, pct24=float(_gainer_24h_pct(pid, cfg)), trough_info=trough_info, cycle_info=tdi_cycle_preview)
                except Exception:
                    tdi_preview = None
                print(
                    f"{_fmt_pid_ticker(pid):<23}{_D(score):>9.3f}{rk:>5}{vol_m:>9.2f}{(dmid_bps / D('100')):>7.2f}{_fmt_bp(spr_bps):>7}{_tdi_preview_text(tdi_preview)}{_cycle_ctx_brief(cfg, pid):>28}"
                )

            # per-tick filter diagnostics (counts + reject reasons)
            diag_on = _diag_enabled(cfg) and (t % _diag_every_ticks(cfg) == 0)
            diag_rej: Dict[str, int] = {}
            diag_soft: Dict[str, int] = {}
            diag_considered = 0
            diag_checked = 0
            diag_passed = 0
            diag_buy_ok = 0
            diag_buy_fail = 0

            # Free one held name early when its short-horizon continuation has clearly rolled over.
            try:
                _maybe_rollover_exit_held_positions(c, cfg, t, metrics)
            except Exception as e:
                _activity(cfg, f"[ROLLOVER_EXIT_ERR] tick={t} err={e}")

            # maker-only autobuy with continuation gates
            # Spread gate: prefer MAX_SPR_BPS, fallback to MAX_SPREAD_PCT (percent)
            try:
                max_spr_bps = float(cfg.get("MAX_SPR_BPS", 0) or 0)
            except Exception:
                max_spr_bps = 0.0
            if max_spr_bps <= 0.0:
                try:
                    max_spr_bps = float(cfg.get("MAX_SPREAD_PCT", 0.6)) * 100.0
                except Exception:
                    max_spr_bps = 25.0
            min_tob_usd = float(cfg.get("MIN_TOPBOOK_USD", 250))
            min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 2))
            top_n = int(cfg.get("TOP_N", 50))
            cooldown = int(cfg.get("COOLDOWN_TICKS", 10))
            max_sold = int(cfg.get("MAX_SOLDIERS_PER_PID", cfg.get("MAX_SOLDIERS_PER_PRODUCT", 2)) or 2)

            if cfg.get("AUTO_TRADE", True) and rows:
                # cancel stale buy orders (keep book clean)
                try:
                    _cancel_stale_buy_orders(c, cfg)
                except Exception:
                    pass

                # Expand the candidate pool, then re-rank by reliability eligibility before
                # the heavier TDI and preentry path so dirty names do not dominate top slots.
                if cfg.get("RANK_BY_24H_PCT", True):
                    try:
                        rows_ranked = sorted(
                            rows,
                            key=lambda it: float(_gainer_24h_pct(it[0], cfg)),
                            reverse=True,
                        )
                    except Exception:
                        rows_ranked = list(rows)
                else:
                    rows_ranked = list(rows)

                candidate_pool_limit = _candidate_pool_limit(cfg, top_n)
                rows_pool = rows_ranked[:candidate_pool_limit]
                candidate_prefetch: Dict[str, Dict[str, Any]] = {}
                ranked_rows: list[tuple[tuple, tuple[str, Any]]] = []
                for source_index, (pid, score) in enumerate(rows_pool):
                    m_prefetch = metrics.get(pid)
                    if m_prefetch is None:
                        try:
                            m_prefetch = _book_metrics(c, pid)
                        except Exception:
                            m_prefetch = None
                        if m_prefetch is not None:
                            metrics[pid] = m_prefetch
                    if isinstance(m_prefetch, tuple):
                        try:
                            _mid, _spr, _tob, _press = m_prefetch
                            _prev = last_mid.get(pid, D("0"))
                            _dmid = ((_mid - _prev) / _prev * D("10000")) if _prev > 0 else D("0")
                            m_prefetch = {
                                "mid": _mid,
                                "spr_bps": _spr,
                                "tob": _tob,
                                "press": _press,
                                "dmid_bps": _dmid,
                            }
                            metrics[pid] = m_prefetch
                        except Exception:
                            m_prefetch = None
                    try:
                        tape_prefetch = _record_tape_quality(pid, m_prefetch, cfg, t)
                    except Exception:
                        tape_prefetch = None
                    try:
                        elig_ok, elig_reason, tape_prefetch = _symbol_reliability_eligibility_allows(
                            cfg,
                            pid,
                            m_prefetch,
                            t,
                            tape_info=tape_prefetch,
                        )
                    except Exception:
                        elig_ok, elig_reason = True, ""
                    candidate_prefetch[pid] = {
                        "metric": m_prefetch,
                        "tape_quality": tape_prefetch,
                        "elig_ok": bool(elig_ok),
                        "elig_reason": str(elig_reason or ""),
                    }
                    ranked_rows.append(
                        (
                            _symbol_reliability_rank_tuple(
                                tape_prefetch,
                                bool(elig_ok),
                                source_index,
                            ),
                            (pid, score),
                        )
                    )
                rows_iter = [row for _rank, row in sorted(ranked_rows, key=lambda it: it[0])[:top_n]]

                max_tries = max(1, int(top_n))
                tries = 0
                now_ts = time.time()

                # Buy pacing (selectivity governor)
                buy_attempted_this_tick = 0
                buy_ok_this_tick = 0
                max_buy_attempts_this_tick = int(cfg.get('BUY_MAX_TRIES_PER_TICK', cfg.get('MAX_BUY_ATTEMPTS_PER_TICK', 1)))
                max_buys_per_tick = int(cfg.get('MAX_BUYS_PER_TICK', 1))

                # Diversification cap: block NEW pid buys when INV_MAX_PIDS reached
                try:
                    inv_cap = int(cfg.get('INV_MAX_PIDS', 0) or 0)
                except Exception:
                    inv_cap = 0
                held_bases = set()
                if inv_cap > 0:
                    # held_bases should reflect *current* holdings; do not let the in-run "held" dict
                    # permanently inflate diversification cap after positions are sold.
                    try:
                        pos_bases = set(_accounts_positions(c, cfg).keys())
                    except Exception:
                        pos_bases = set()
                    held_bases = set(pos_bases)

                    # Include very recent buys to cover accounts cache lag, and prune stale held entries.
                    try:
                        lag_ticks = int(cfg.get('HELD_BASES_LAG_TICKS', 0) or 0)
                    except Exception:
                        lag_ticks = 0
                    if lag_ticks <= 0:
                        try:
                            lag_ticks = int(max(10, float(cfg.get('POS_CACHE_SEC', 20)) / max(1.0, float(cfg.get('TICK_SEC', 3.0))) + 5))
                        except Exception:
                            lag_ticks = 25

                    # prune held entries no longer present in accounts beyond lag window
                    try:
                        for k in list(held.keys()):
                            try:
                                base_k = str(k).split('-')[0].upper()
                                lb = int(last_buy_tick.get(k, -999999))
                                if (base_k not in pos_bases) and ((t - lb) > lag_ticks):
                                    held.pop(k, None)
                            except Exception:
                                continue
                    except Exception:
                        pass

                    # overlay recent held bases for cache lag only
                    try:
                        overlay = {
                            str(k).split('-')[0].upper()
                            for k, v in held.items()
                            if int(v) > 0 and (t - int(last_buy_tick.get(k, -999999))) <= lag_ticks
                        }
                        held_bases.update(overlay)
                    except Exception:
                        pass

                rotated_this_tick = False
                for pid, score in rows_iter:
                    diag_considered += 1

                    # Precompute base and inv-cap condition (evaluated later after signal gates)
                    try:
                        base = str(pid).split('-')[0].upper()
                    except Exception:
                        base = ''
                    try:
                        is_held = (base in held_bases) or (int(held.get(pid, 0)) > 0)
                    except Exception:
                        is_held = False
                    inv_cap_block = bool(inv_cap > 0 and base and (not is_held) and (len(held_bases) >= inv_cap))
                    max_sold_block = False


                    # buy-fail cooldown (temporary pause after API/order errors)
                    if _buy_fail_cooldown_active(pid, now_ts):
                        _diag_inc(diag_rej, 'bf_cd')
                        continue

                    # Collect 24h gainer context early, but do not kill the name yet.
                    # Strong bullish lift-off setups can still be valid before the 24h tape fully catches up.
                    pct24 = None
                    try:
                        pct24 = float(_gainer_24h_pct(pid, cfg))
                    except Exception:
                        pass

                    if tries > max_tries:
                        _diag_inc(diag_rej, 'max_tries')
                        break

                    prefetched = candidate_prefetch.get(pid, {})
                    m = prefetched.get("metric")
                    if m is None:
                        m = metrics.get(pid)
                    if m is None:
                        m = _book_metrics(c, pid)
                        if m is None:
                            _diag_inc(diag_rej, 'no_book')
                            continue
                        metrics[pid] = m

                    diag_checked += 1

                    # hard gates
                    # MM18_FILTERDIAG_TUPLEFIX: normalize tuple metrics into dict for gate indexing
                    if isinstance(m, tuple):
                        try:
                            _mid, _spr, _tob, _press = m
                            _prev = last_mid.get(pid, D("0"))
                            _dmid = ((_mid - _prev) / _prev * D("10000")) if _prev > 0 else D("0")
                            m = {"mid": _mid, "spr_bps": _spr, "tob": _tob, "press": _press, "dmid_bps": _dmid}
                            metrics[pid] = m
                        except Exception:
                            continue

                    tape_quality = prefetched.get("tape_quality")
                    elig_ok = bool(prefetched.get("elig_ok", True))
                    elig_reason = str(prefetched.get("elig_reason", "") or "")
                    if tape_quality is None:
                        try:
                            tape_quality = _record_tape_quality(pid, m, cfg, t)
                        except Exception:
                            tape_quality = None
                    if not elig_ok:
                        elig_reason_str = elig_reason.strip().lower()
                        elig_family = _reliability_reason_family(elig_reason_str)
                        if elig_family == 'u0':
                            _diag_inc(diag_rej, 'u0')
                        elif elig_family == 'tobq':
                            _diag_inc(diag_rej, 'tob')
                        elif elig_family == 'spread':
                            _diag_inc(diag_rej, 'spr')
                        elif elig_family == 'press':
                            _diag_inc(diag_rej, 'sb')
                        elif elig_family == 'hist':
                            _diag_inc(diag_rej, 'u0')
                        _diag_inc(diag_rej, str(elig_reason_str or 'elig_q'))
                        tries += 1
                        continue

                    tdi_payload = None
                    tdi_cycle_payload = None
                    try:
                        _trough_update(cfg, pid, t, float(m.get("mid", 0) or 0))
                    except Exception:
                        pass
                    try:
                        _tpct, _tlo, _thi, _tn = _trough_compute(cfg, pid, t, float(m.get("mid", 0) or 0))
                    except Exception:
                        _tpct, _tlo, _thi, _tn = (None, None, None, 0)
                    try:
                        _trough_info = None
                        if (_tpct is not None) or (int(_tn) > 0):
                            _trough_info = {
                                "trough_n": int(_tn),
                            }
                            if _tpct is not None:
                                _trough_info["trough_pct"] = float(round(float(_tpct), 6))
                        cycle_payload = _cycle_ctx_for_pid_dynamic(cfg, pid)
                        tdi_cycle_payload = cycle_payload if _cycle_ctx_enabled(cfg) else None
                        tdi_payload = _tdi_compute(
                            cfg,
                            pid,
                            score,
                            m,
                            tick=t,
                            pct24=(pct24 if 'pct24' in locals() else None),
                            trough_info=_trough_info,
                            cycle_info=tdi_cycle_payload,
                            tape_info=tape_quality,
                        )
                        _tdi_log_snapshot(cfg, tdi_payload)
                    except Exception:
                        tdi_payload = None

                    preentry_ok, preentry_reason, tape_quality = _preentry_tape_gate_allows(
                        cfg,
                        pid,
                        m,
                        t,
                        tape_info=tape_quality,
                        tdi_payload=tdi_payload,
                        cycle_payload=tdi_cycle_payload,
                    )
                    if not preentry_ok:
                        preentry_reason_str = str(preentry_reason or "").strip().lower()
                        preentry_family = _reliability_reason_family(preentry_reason_str)
                        if preentry_family == 'u0':
                            _diag_inc(diag_rej, 'u0')
                        elif preentry_family == 'tobq':
                            _diag_inc(diag_rej, 'tob')
                        elif preentry_family == 'spread':
                            _diag_inc(diag_rej, 'spr')
                        elif preentry_family == 'press':
                            _diag_inc(diag_rej, 'sb')
                        elif preentry_family == 'hist':
                            _diag_inc(diag_rej, 'u0')
                        if preentry_reason_str == 'preq_fresh':
                            _diag_inc(diag_rej, 'u0')
                        _diag_inc(diag_rej, str(preentry_reason_str or 'preq'))
                        tries += 1
                        continue

                    if not _g24h_gate_allows(cfg, pct24, tdi_payload=tdi_payload, cycle_payload=tdi_cycle_payload):
                        _diag_inc(diag_soft, 'g24h')
                        continue

                    if m["spr_bps"] > max_spr_bps:
                        _diag_inc(diag_rej, 'spr')
                        tries += 1
                        continue
                    if not _tob_gate_allows(cfg, m, tdi_payload=tdi_payload, cycle_payload=tdi_cycle_payload):
                        _diag_inc(diag_rej, 'tob')
                        tries += 1
                        continue
                    if not _dmid_gate_allows(cfg, m, tdi_payload=tdi_payload, cycle_payload=tdi_cycle_payload):
                        _diag_inc(diag_rej, 'dmid')
                        tries += 1
                        continue
                    if t - last_buy_tick.get(pid, -cooldown) < cooldown:
                        _diag_inc(diag_rej, 'cd')
                        tries += 1
                        continue

                    # Soldier cap must be based on actual position, not just in-run BUY_OK count.
                    # We still keep the in-run counter as a backstop for cache lag.
                    pos_sold = 0
                    try:
                        pos_sold = int(_soldiers_held(c, pid, m.get("mid", 0), cfg))
                    except Exception:
                        pos_sold = 0

                    held_sold = max(int(held.get(pid, 0)), int(pos_sold))
                    if held_sold >= max_sold:
                        max_sold_block = True

                    # pyramid rules (when already holding)
                    # Require "green" before adding to an existing position (prevents averaging down).
                    if pos_sold > 0 and bool(cfg.get('PYRAMID_REQUIRE_GREEN', True)):
                        try:
                            ent_px = float(_entry_px_cached(c, pid, cfg) or 0.0)
                            mid_now = float(m.get("mid", 0) or 0.0)
                            if ent_px > 0.0 and mid_now > 0.0 and mid_now < ent_px:
                                _diag_inc(diag_rej, 'pyr_red')
                                tries += 1
                                continue
                        except Exception:
                            pass

                    gap = int(cfg.get('PYRAMID_MIN_TICKS_BETWEEN_BUYS', cfg.get('PYRAMID_TICK_GAP', 6)) or 6)
                    if held_sold > 0 and (t - last_buy_tick.get(pid, -9999) < gap):
                        _diag_inc(diag_rej, 'pyr_gap')
                        tries += 1
                        continue

                    # stop-loss reentry guard (avoid immediate re-buys after SL)
                    if _stop_loss_reentry_block(pid, cfg, t):
                        # Allow re-entry early only if score is exceptionally strong
                        try:
                            smin = float(cfg.get('SL_REENTRY_SCORE_MIN', 0.95) or 0.95)
                        except Exception:
                            smin = 0.95
                        if float(score) < smin:
                            _diag_inc(diag_rej, "sl_re")
                            tries += 1
                            continue

                    # Continuation gate: require the name to still be pressing higher before BUY.
                    try:
                        _mid = _D(m.get('mid', 0)) if isinstance(m, dict) else D('0')
                        _dmid = float(m.get('dmid_bps', m.get('dmid', 0)) or 0) if isinstance(m, dict) else 0.0
                        try:
                            _trough_update(cfg, pid, t, float(_mid))
                        except Exception:
                            pass
                        _press = float(m.get('press', 0.5) or 0.5) if isinstance(m, dict) else 0.5
                        if not _sb_update(pid, _mid, _dmid, _press, cfg, t):
                            _diag_inc(diag_rej, 'sb')
                            tries += 1
                            continue
                    except Exception:
                        pass

                    # refresh idea state (diagnostic only in continuation mode)
                    idea_state = _idea_update(pid, _mid, t, cfg)

                    # offline-safe: skip buys while offline if configured
                    if _offline_block_trading(cfg) and _offline_is_offline(cfg):
                        _diag_inc(diag_rej, 'off')
                        _offline_note(cfg, f'[offline_skip_buy] tick={t} pid={pid}')
                        tries += 1
                        continue

                    # MM25_INTERVAL_AWARE_TROUGH_CONTEXT: keep as diagnostic/support context only.
                    cycle_ctx = None
                    if _cycle_ctx_enabled(cfg):
                        try:
                            cycle_ctx = _cycle_ctx_phase_gate(cfg, pid)
                        except Exception:
                            cycle_ctx = None

                    tp_fast_ctx = None
                    if _cycle_tp_fast_gate_enabled(cfg):
                        try:
                            tp_fast_ctx = _cycle_tp_fast_support_gate(cfg, pid)
                        except Exception:
                            tp_fast_ctx = None

                    # MM24_TROUGH_GATE: require entries to stay close to the rolling trough.
                    trough_extra: Optional[Dict[str, Any]] = None
                    trough_block = False
                    trough_block_reason = 'trough'
                    try:
                        _tmax = float(cfg.get('TROUGH_PCT_MAX', 0.0) or 0.0)
                    except Exception:
                        _tmax = 0.0
                    if 0.0 < _tmax < 1.0:
                        try:
                            _tpct, _tlo, _thi, _tn = _trough_compute(cfg, pid, t, float(_mid))
                        except Exception:
                            _tpct, _tlo, _thi, _tn = (None, None, None, 0)
                        if _tpct is not None:
                            trough_extra = {
                                'trough_pct': float(round(float(_tpct), 6)),
                                'trough_n': int(_tn),
                                'trough_lo': float(_tlo) if _tlo is not None else None,
                                'trough_hi': float(_thi) if _thi is not None else None,
                                'trough_max': float(_tmax),
                            }
                            if 0.0 < _tmax < 1.0:
                                trough_block = bool(float(_tpct) > float(_tmax))
                                trough_extra['trough_would_block'] = trough_block
                            if isinstance(cycle_ctx, dict) and cycle_ctx:
                                trough_extra.update({
                                    'cycle_interval': cycle_ctx.get('interval'),
                                    'cycle_phase': cycle_ctx.get('phase'),
                                    'cycle_source': cycle_ctx.get('source'),
                                    'cycle_tp_hit_rate_pct': cycle_ctx.get('tp_hit_rate_pct'),
                                })
                            trough_extra = {k: v for k, v in trough_extra.items() if v is not None}
                        else:
                            try:
                                _min_trough_n = int(_trough_params(cfg)[3])
                            except Exception:
                                _min_trough_n = 1
                            trough_extra = {
                                'trough_n': int(_tn or 0),
                                'trough_min_samples': int(_min_trough_n),
                                'trough_max': float(_tmax),
                                'trough_would_block': True,
                            }
                            trough_block = True
                            trough_block_reason = 'trough_wait'
                    if trough_block:
                        _diag_inc(diag_rej, trough_block_reason)
                        tries += 1
                        extra = dict(trough_extra or {})
                        _paper_buy_signal(cfg, t, pid, score, m, idea_state, trough_block_reason, extra=(extra or None))
                        continue

                    # signal passed (paper-buy candidate)
                    diag_passed += 1

                    try:
                        tdi_gate_score = float((tdi_payload or {}).get('tdi_score', 0.0) or 0.0)
                    except Exception:
                        tdi_gate_score = 0.0
                    try:
                        tdi_gate_top_reasons = list((tdi_payload or {}).get('top_reasons') or [])[:3] if isinstance(tdi_payload, dict) else []
                    except Exception:
                        tdi_gate_top_reasons = []
                    try:
                        tdi_gate_cycle_phase = str((tdi_payload or {}).get('cycle_phase') or (tdi_payload or {}).get('ctx_phase') or '') if isinstance(tdi_payload, dict) else ''
                    except Exception:
                        tdi_gate_cycle_phase = ''

                    # TDI is shadow-only until it proves predictive quality against
                    # otherwise-valid trade decisions. Keep logging it, but do not veto.
                    tdi_shadow_low = False
                    tdi_shadow_extra: Dict[str, Any] = {}
                    try:
                        min_live_tdi_score = _tdi_min_buy_score(
                            cfg,
                            m,
                            tdi_payload=tdi_payload,
                            cycle_payload=tdi_cycle_payload,
                        )
                        tdi_shadow_extra = {
                            'tdi_score': round(float(tdi_gate_score), 2),
                            'tdi_score_min': min_live_tdi_score,
                            'tdi_shadow_low': False,
                        }
                        if tdi_gate_top_reasons:
                            tdi_shadow_extra['tdi_top_reasons'] = '|'.join(
                                str(x) for x in tdi_gate_top_reasons if str(x).strip()
                            )
                        if str(tdi_gate_cycle_phase or '').strip():
                            tdi_shadow_extra['tdi_cycle_phase'] = str(tdi_gate_cycle_phase).strip()
                        if float(tdi_gate_score) < min_live_tdi_score:
                            tdi_shadow_low = True
                            tdi_shadow_extra['tdi_shadow_low'] = True
                    except Exception:
                        tdi_shadow_low = False
                        tdi_shadow_extra = {}

                    # INV_MAX_PIDS: block NEW bases when at cap (log as paper signal)
                    if inv_cap_block:
                        _diag_inc(diag_rej, 'inv_cap')
                        tries += 1
                        extra = {'inv_max_pids': inv_cap, 'held_bases_count': len(held_bases)}
                        if trough_extra:
                            extra.update(trough_extra)
                        _paper_buy_signal(
                            cfg, t, pid, score, m, idea_state, 'inv_cap',
                            extra=extra
                        )
                        # Optional rotation: sell one loser to free a slot for a strong new candidate.
                        if (not rotated_this_tick) and bool(cfg.get('ROTATE_AT_INV_CAP', False)):
                            if _rotate_cooldown_active(now_ts):
                                _diag_inc(diag_rej, 'rot_cd')
                            else:
                                did = _rotate_free_slot_at_cap(c, cfg, held_bases, pid, float(score), now_ts)
                                if did:
                                    _diag_inc(diag_rej, 'rot')
                                    rotated_this_tick = True
                                    break
                        continue

                    # Soldier/pyramid cap: log paper signal, do not buy
                    if max_sold_block:
                        _diag_inc(diag_rej, 'max_sold')
                        tries += 1
                        extra = {'max_soldiers_per_pid': max_sold, 'held_soldiers': held_sold, 'pos_soldiers': pos_sold}
                        if trough_extra:
                            extra.update(trough_extra)
                        _paper_buy_signal(
                            cfg, t, pid, score, m, idea_state, 'max_sold',
                            extra=extra
                        )
                        continue

                    # In DRY mode, let the paper lane evaluate entries without
                    # requiring real account USD. Keep the live USD guardrail intact.
                    try:
                        usd_avail = _usd_available(c, pfid)
                        need_usd = float(cfg.get('USD_RESERVE', 0.0)) + float(cfg.get('SOLDIER_USD', 10.0))
                        if (not bool(cfg.get('DRY', False))) and usd_avail < need_usd:
                            _diag_inc(diag_rej, 'usd')
                            tries += 1
                            extra = {'usd_available': usd_avail, 'usd_need': need_usd}
                            if trough_extra:
                                extra.update(trough_extra)
                            _paper_buy_signal(
                                cfg, t, pid, score, m, idea_state, 'usd',
                                extra=extra
                            )
                            continue
                    except Exception:
                        pass

                    # DRY guard: never place real orders in DRY mode
                    try:
                        if bool(cfg.get('DRY', False)):
                            _diag_inc(diag_rej, 'dry')
                            tries += 1
                            dry_extra = dict(trough_extra or {})
                            if tdi_shadow_extra:
                                dry_extra.update(tdi_shadow_extra)
                            _paper_buy_signal(cfg, t, pid, score, m, idea_state, 'dry', extra=(dry_extra or None))
                            break
                    except Exception:
                        pass


                    # place buy (maker limit), then hand off TP
                    # Buy pacing: limit burst buys and enforce a global cooldown
                    if buy_ok_this_tick >= max_buys_per_tick:
                        _diag_inc(diag_rej, 'buy_lim')
                        break
                    if buy_attempted_this_tick >= max_buy_attempts_this_tick:
                        _diag_inc(diag_rej, 'buy_lim')
                        break
                    # BUY_GLOBAL_COOLDOWN_SEC governs cross-tick pacing.
                    # Same-tick throughput is governed by MAX_BUYS_PER_TICK.
                    if buy_ok_this_tick == 0 and time.time() < float(_GLOBAL_BUY_STATE.get('until', 0.0)):
                        _diag_inc(diag_rej, 'gb_cd')
                        tries += 1
                        continue
                    buy_attempted_this_tick += 1

                    try:
                        try:
                            _mm30_attached_exit_refresh(cfg)
                            _sl_cd = float(cfg.get("SL_REENTRY_COOLDOWN_SEC", 0) or 0)
                            _sl_score_min = float(cfg.get("SL_REENTRY_SCORE_MIN", 1.0) or 1.0)
                            if _sl_cd > 0:
                                _last_sl = float(_MM30_ATTACHED_EXIT_LAST_SL_TS.get(pid, 0.0) or 0.0)
                                if _last_sl > 0:
                                    _age = _now_ts() - _last_sl
                                    if _age < _sl_cd and float(score or 0.0) < _sl_score_min:
                                        _activity(cfg, f"[PAPER_BUY_SIGNAL] pid={pid} blocked_by=sl_re src=attached_exit age_sec={_age:.1f} cooldown_sec={_sl_cd:.1f} score={float(score or 0.0):.4f} score_min={_sl_score_min:.4f}")
                                        continue
                        except Exception:
                            pass
                        _activity(cfg, f"[BUY] tick={t} pid={pid} score={score:.4f}")
                        size_q = float(cfg.get('SOLDIER_USD', 10.0))
                        size_str = f"{size_q:.2f}"
                        resp = _place_order_adaptive(product_id=pid, side='BUY', size=size_str, size_type='QUOTE', cfg=cfg, client=c)
                        ok2 = bool(resp.get('ok'))
                        oid = str(resp.get('order_id') or resp.get('id') or resp.get('client_order_id') or '')
                        msg = str(resp.get('error') or resp.get('message') or resp.get('status') or '')

                        if not ok2:
                            _diag_inc(diag_rej, 'buy_fail')
                            diag_buy_fail += 1
                            _activity(cfg, f"[BUY_FAIL] pid={pid} err={msg}")
                            _buy_fail_cooldown_set(pid, now_ts, cfg)
                            tries += 1
                            continue

                        diag_buy_ok += 1
                        last_buy_tick[pid] = t
                        _LAST_BUY_TICK[pid] = t  # MM21: enable SL_GRACE_TICKS

                        held[pid] = held.get(pid, 0) + 1

                        buy_ok_parts = [f"pid={pid}", f"oid={oid}"]
                        try:
                            buy_ok_parts.append(f"tdi_score={round(float(tdi_gate_score), 2)}")
                        except Exception:
                            pass
                        try:
                            if tdi_gate_top_reasons:
                                buy_ok_parts.append(f"tdi_top_reasons={'|'.join(str(x) for x in tdi_gate_top_reasons if str(x).strip())}")
                        except Exception:
                            pass
                        try:
                            if str(tdi_gate_cycle_phase or '').strip():
                                buy_ok_parts.append(f"cycle_phase={str(tdi_gate_cycle_phase).strip()}")
                        except Exception:
                            pass
                        try:
                            buy_ok_parts.append(f"tdi_shadow_low={1 if tdi_shadow_low else 0}")
                        except Exception:
                            pass
                        _activity(cfg, f"[BUY_OK] {' '.join(buy_ok_parts)}")

                        # MM23_ATTACHED_TPSL: if entry used exchange-side attached TP/SL, log the bracket prices.
                        try:
                            if isinstance(resp, dict) and resp.get("attached_tpsl"):
                                tp = resp.get("attached_tp") or ""
                                slp = resp.get("attached_sl") or ""
                                ref = resp.get("attached_entry_ref") or ""
                                _activity(cfg, f"[ATTACHED_TPSL] pid={pid} entry_ref={ref} tp={tp} sl={slp} oid={oid}")

                                # Track open attached entry so we can emit SELL_OK when it exits on-exchange.
                                try:
                                    rec = {
                                        "tick": int(t),
                                        "entry_ref": float(ref) if str(ref).strip() else 0.0,
                                        "tp": float(tp) if str(tp).strip() else 0.0,
                                        "sl": float(slp) if str(slp).strip() else 0.0,
                                        "oid": str(oid or ""),
                                    }
                                    with _ATTACHED_OPEN_LOCK:
                                        _ATTACHED_OPEN[pid] = rec
                                except Exception:
                                    pass
                        except Exception:
                            pass

                        # Global buy cooldown applies to the next tick's first buy.
                        buy_ok_this_tick += 1
                        try:
                            gb_cd = float(cfg.get('BUY_GLOBAL_COOLDOWN_SEC', 30.0))
                        except Exception:
                            gb_cd = 30.0
                        _GLOBAL_BUY_STATE['until'] = time.time() + gb_cd

                        if buy_ok_this_tick >= max_buys_per_tick:
                            break

                        # TP handoff (best-effort)
                        try:
                            exit_engine.ensure_tp_for_product(c, pid, cfg, pfid)
                        except Exception as e:
                            _diag_inc(diag_rej, 'tp_fail')
                            _activity(cfg, f"[tp_error] pid={pid} err={e}")

                        continue

                    except Exception as e:
                        _diag_inc(diag_rej, 'buy_ex')
                        diag_buy_fail += 1
                        _activity(cfg, f"[BUY_FAIL] pid={pid} err={e}")
                        _buy_fail_cooldown_set(pid, now_ts, cfg)
                        tries += 1
                        continue

            _dry_pnl_mark_from_rows(cfg, t, metrics if isinstance(metrics, dict) else {})

            # per-tick diagnostics summary (activity_ticker.log)
            if diag_on:
                try:
                    u = _diag_universe_last()
                    u_out = u.get('uni_out', u.get('passed', u.get('out', None)))
                    u_disc = u.get('discovered', u.get('discover', 0))
                    u_rej = u.get('rejects', {}) if isinstance(u.get('rejects', {}), dict) else {}
                    u_str = str(u_out) if u_out is not None else ''
                    if u_disc:
                        u_str = f"{u_str}/{u_disc}"

                    s = len(rows) if isinstance(rows, list) else 0
                    top = len(rows_iter) if 'rows_iter' in locals() and isinstance(rows_iter, list) else 0

                    rej_str = _diag_fmt_counts(diag_rej, max_items=10)
                    u_rej_str = _diag_fmt_counts({str(k): int(v) for k, v in u_rej.items()}, max_items=6) if u_rej else ''
                    soft_str = _diag_fmt_counts(diag_soft, max_items=6)
                    rel_keys = (
                        "u0",
                        "u0_now",
                        "u0_cd",
                        "preq_hist",
                        "preq_fresh",
                        "preq_tobq",
                        "preq_spread",
                        "preq_press",
                        "preq_q_u0",
                        "preq_q_hist",
                        "preq_q_tobq",
                        "preq_q_spread",
                        "preq_q_press",
                        "preq_q_infra",
                    )
                    rel_local = {k: int(diag_rej.get(k, 0) or 0) for k in rel_keys if int(diag_rej.get(k, 0) or 0) > 0}
                    rel_uni = {k: int(u_rej.get(k, 0) or 0) for k in rel_keys if int(u_rej.get(k, 0) or 0) > 0}
                    rel_local_str = _diag_fmt_counts(rel_local, max_items=len(rel_keys)) if rel_local else ''
                    rel_uni_str = _diag_fmt_counts(rel_uni, max_items=len(rel_keys)) if rel_uni else ''

                    parts = [
                        f"tick={t}",
                        f"U={u_str}" if u_str else None,
                        f"S={s}",
                        f"top={top}",
                        f"chk={diag_checked}",
                        f"pass={diag_passed}",
                        f"bok={diag_buy_ok}",
                        f"bf={diag_buy_fail}",
                        (f"rej={rej_str}" if rej_str else None),
                        (f"rel={rel_local_str}" if rel_local_str else None),
                        (f"u_rej={u_rej_str}" if u_rej_str else None),
                        (f"u_rel={rel_uni_str}" if rel_uni_str else None),
                        (f"soft={soft_str}" if soft_str else None),
                    ]
                    line = ' '.join([p for p in parts if p])
                    held_count = 0  # MM18_FILTERDIAG_FIX (do not overwrite held dict)
                    _activity(cfg, f"[tick_diag] {line}")
                except Exception:
                    pass

            if t == 1:
                _hang_guard_cancel(cfg)

            # maintenance / TP / SL checks (can be async to keep ticker timing stable)
            maint_async = bool(cfg.get("MAINT_ASYNC", True))
            if maint_async:
                _schedule_maintenance(cfg, t, metrics)
            else:
                # periodic TP check for held assets (every 2 ticks)
                if t % 2 == 0:
                    uni = _universe(c, cfg)
                    for pid in uni:
                        try:
                            if not _has_position(c, pid, cfg):
                                continue
                            mid = metrics.get(pid, {}).get("mid", D("0"))
                            if mid <= 0:
                                mid, _, _, _ = _book_metrics(c, pid)

                            # optional stop-loss check
                            grace = int(cfg.get("SL_GRACE_TICKS", 10))
                            if (t - int(_LAST_BUY_TICK.get(pid, -999999))) < grace:
                                slr = {"action": "skip_grace"}
                            else:
                                slr = stop_loss.check_and_exit(c, pid, cfg, None)
                            if isinstance(slr, dict) and slr.get("action") == "stop_loss":
                                _SL_REENTRY_LAST_STOP[pid] = time.time()
                                continue

                            r = exit_engine.ensure_tp_for_product(c, pid, cfg, mid)
                            if isinstance(r, dict) and not _ok(r) and r.get("error"):
                                print(f"tp placement for {pid} err={r.get('error')}")
                        except Exception as e:
                            print(f"tp check failed {pid}: {e}")

                # optional inventory holdings scan (gated by TP_INVENTORY_* settings)
                _mm16_inventory_holdings(c, cfg, t)

            _maybe_print_pnl(c, cfg, metrics, t)
            _maybe_print_pnl_block(c, cfg, t)

            # remember mids
            for pid, d in metrics.items():
                last_mid[pid] = d["mid"]

        except Exception as e:
            print(f"[tick_error] {type(e).__name__}: {e}")

        if ticks and t >= int(ticks):
            break

        time.sleep(float(cfg.get("TICK_SEC", 3.0)))


def main() -> None:
    import argparse

    ap = argparse.ArgumentParser()
    ap.add_argument("--console", action="store_true", default=False)
    ap.add_argument("--ticks", type=int, default=0)
    args = ap.parse_args()
    run_loop(console=args.console, ticks=args.ticks)


def _offline_is_offline(cfg: Dict[str, Any]) -> bool:
    # True when we should consider the environment "offline"
    try:
        return bool(_offline_active(cfg))  # if the codebase already defines this
    except Exception:
        # fallback: allow explicit config-driven offline mode
        try:
            return bool(cfg.get("OFFLINE_MODE", False))
        except Exception:
            return False


def _offline_block_trading(cfg: Dict[str, Any]) -> bool:
    # When offline, default is to block trading (safety-first).
    try:
        if not _offline_is_offline(cfg):
            return False
        return bool(cfg.get("OFFLINE_BLOCK_TRADING", True))
    except Exception:
        return True


# --- MM19 runtime fixes: pfid + buy-fail cooldown helpers ---
if "pfid" not in globals():
    pfid = os.environ.get("PFID")
if "_BUY_FAIL_COOLDOWN_UNTIL" not in globals():
    _BUY_FAIL_COOLDOWN_UNTIL = {}
if "_buy_fail_cooldown_active" not in globals():
    def _buy_fail_cooldown_active(pid, now_ts):
        return float(_BUY_FAIL_COOLDOWN_UNTIL.get(str(pid), 0.0)) > float(now_ts)
if "_buy_fail_cooldown_set" not in globals():
    def _buy_fail_cooldown_set(pid, now_ts, cfg):
        cd = float(cfg.get("BUY_FAIL_COOLDOWN_SEC", 180))
        _BUY_FAIL_COOLDOWN_UNTIL[str(pid)] = float(now_ts) + cd

if __name__ == "__main__":
    main()




# MM16_TICKER_PNL_STARTUP


# MM16_TICKER_PNL_FIX1




# MM16_INV_HOLDINGS



# MM16_SMART_BUY


# MM16_STEP5_VIRTUAL_PROBE
