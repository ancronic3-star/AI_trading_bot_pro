import argparse
import json
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


UTC = timezone.utc
TP_PCT_DEFAULT = 5.0
SL_PCT_DEFAULT = 8.0
HORIZONS_MINUTES = (30, 240)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Replay KOKO dry variants against historical TDI snapshots.")
    p.add_argument("--base-root", default=r"C:\ai_trading_bot_koko")
    p.add_argument("--clone-root", default=r"C:\ai_trading_bot_koko_parallel")
    p.add_argument("--snapshots", default=r"C:\ai_trading_bot_koko\logs\tdi_snapshots.jsonl")
    p.add_argument("--since-days", type=int, default=30)
    p.add_argument("--output", default=None, help="Optional JSON output path.")
    return p.parse_args()


def iso_to_dt(value: str) -> datetime:
    return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(UTC)


def cfg_max_spr_bps(cfg: Dict[str, Any]) -> float:
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


@dataclass
class ContinuationParams:
    last_step_subtract: float = 9.0
    last_step_floor: float = -9.0
    prior_step_floor: float = -39.0
    step_slack: int = 10
    relief_last_subtract: float = 4.5
    relief_last_floor: float = -4.5
    relief_prior_base: float = 24.0
    relief_prior_mult: float = 2.5


@dataclass
class TdiGateParams:
    strong_tob_mult: float = 1.0
    strong_tob_floor: float = 60.0
    strong_dmid_add: float = 1.5
    strong_dmid_floor: float = 4.0
    strong_spr_mult: float = 0.50
    strong_press_floor: float = 0.05
    market_tob_mult: float = 2.0
    market_tob_floor: float = 120.0
    market_dmid_add: float = 4.0
    market_dmid_floor: float = 8.0
    adaptive_floor: float = 56.0
    adaptive_subtract: float = 14.0


@dataclass
class DmidGateParams:
    mild_abs_floor: float = 4.5
    mild_mult: float = 0.65
    strong_press_floor: float = 0.15
    strong_spr_mult: float = 0.5
    truth_floor: float = 68.0


@dataclass
class HorizonResult:
    end_ts: datetime
    status: str = "open"
    last_ret: float = 0.0
    max_ret: float = 0.0
    min_ret: float = 0.0


@dataclass
class ActiveSignal:
    variant: str
    product_id: str
    entry_ts: datetime
    entry_price: float
    horizons: Dict[int, HorizonResult]


@dataclass
class VariantSpec:
    name: str
    root: Path
    cfg: Dict[str, Any]
    cont: ContinuationParams
    tdi: TdiGateParams
    dmid: DmidGateParams
    counts: Counter = field(default_factory=Counter)
    sb_state: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    active: Dict[str, List[ActiveSignal]] = field(default_factory=lambda: defaultdict(list))
    outcome_counts: Dict[int, Counter] = field(default_factory=lambda: defaultdict(Counter))
    outcome_returns: Dict[int, Dict[str, float]] = field(default_factory=lambda: defaultdict(lambda: {"sum_last": 0.0, "sum_max": 0.0, "sum_min": 0.0}))
    admitted_examples: List[Dict[str, Any]] = field(default_factory=list)
    reject_examples: Dict[str, List[Dict[str, Any]]] = field(default_factory=lambda: defaultdict(list))


def _extract_float(pattern: str, text: str, default: float) -> float:
    m = re.search(pattern, text)
    if not m:
        return default
    try:
        return float(m.group(1))
    except Exception:
        return default


def _extract_int(pattern: str, text: str, default: int) -> int:
    m = re.search(pattern, text)
    if not m:
        return default
    try:
        return int(m.group(1))
    except Exception:
        return default


def load_continuation_params(run_manager_path: Path) -> ContinuationParams:
    text = run_manager_path.read_text(encoding="utf-8", errors="ignore")
    return ContinuationParams(
        last_step_subtract=_extract_float(r"last_step_bps >= max\(min_dmid_bps - ([0-9.]+),", text, 9.0),
        last_step_floor=_extract_float(r"last_step_bps >= max\(min_dmid_bps - [0-9.]+, (-?[0-9.]+)\)", text, -9.0),
        prior_step_floor=_extract_float(r"prior_step_bps >= (-?[0-9.]+)", text, -39.0),
        step_slack=_extract_int(r"step_ok = positive_steps >= max\(1, len\(deltas_bps\) - ([0-9]+)\)", text, 10),
        relief_last_subtract=_extract_float(r"relief_last_bps = max\(min_dmid_bps - ([0-9.]+),", text, 4.5),
        relief_last_floor=_extract_float(r"relief_last_bps = max\(min_dmid_bps - [0-9.]+, (-?[0-9.]+)\)", text, -4.5),
        relief_prior_base=_extract_float(r"relief_prior_floor = -max\(([0-9.]+), trend_bps_min \*", text, 24.0),
        relief_prior_mult=_extract_float(r"relief_prior_floor = -max\([0-9.]+, trend_bps_min \* ([0-9.]+)\)", text, 2.5),
    )


def load_tdi_gate_params(text: str) -> TdiGateParams:
    return TdiGateParams(
        strong_tob_mult=_extract_float(r"tob_usd >= max\(min_tob_usd \* ([0-9.]+),", text, 1.0),
        strong_tob_floor=_extract_float(r"tob_usd >= max\(min_tob_usd \* [0-9.]+, ([0-9.]+)\)", text, 60.0),
        strong_dmid_add=_extract_float(r"dmid_bps >= max\(min_dmid_bps \+ ([0-9.]+),", text, 1.5),
        strong_dmid_floor=_extract_float(r"dmid_bps >= max\(min_dmid_bps \+ [0-9.]+, ([0-9.]+)\)", text, 4.0),
        strong_spr_mult=_extract_float(r"spr_bps <= max_spr_bps \* ([0-9.]+)", text, 0.50),
        strong_press_floor=_extract_float(r"and pressure >= ([0-9.]+)\s*\n\s*\)", text, 0.05),
        market_tob_mult=_extract_float(r"tob_usd >= max\(min_tob_usd \* ([0-9.]+), 120\.0\)", text, 2.0),
        market_tob_floor=_extract_float(r"tob_usd >= max\(min_tob_usd \* [0-9.]+, ([0-9.]+)\)\s*\n\s*and dmid_bps >= max\(min_dmid_bps \+ 4\.0, 8\.0\)", text, 120.0),
        market_dmid_add=_extract_float(r"and dmid_bps >= max\(min_dmid_bps \+ ([0-9.]+), 8\.0\)", text, 4.0),
        market_dmid_floor=_extract_float(r"and dmid_bps >= max\(min_dmid_bps \+ [0-9.]+, ([0-9.]+)\)", text, 8.0),
        adaptive_floor=_extract_float(r"return max\(([0-9.]+), base_min_score - 14\.0\)", text, 56.0),
        adaptive_subtract=_extract_float(r"return max\([0-9.]+, base_min_score - ([0-9.]+)\)", text, 14.0),
    )


def load_dmid_gate_params(text: str) -> DmidGateParams:
    return DmidGateParams(
        mild_abs_floor=_extract_float(r"mild_pullback_floor = min_dmid_bps - max\(([0-9.]+), trend_bps_min \*", text, 4.5),
        mild_mult=_extract_float(r"mild_pullback_floor = min_dmid_bps - max\([0-9.]+, trend_bps_min \* ([0-9.]+)\)", text, 0.65),
        strong_press_floor=_extract_float(r"and pressure >= ([0-9.]+)\s*\n\s*and spr_bps <= max_spr_bps \* 0\.[0-9]+\s*\n\s*\)", text, 0.15),
        strong_spr_mult=_extract_float(r"and spr_bps <= max_spr_bps \* ([0-9.]+)\s*\n\s*\)", text, 0.5),
        truth_floor=_extract_float(r"truth_ok = max\(tdi_score, truth_score, continuation_floor\) >= ([0-9.]+)", text, 68.0),
    )


def load_variant(name: str, root: Path) -> VariantSpec:
    cfg = json.loads((root / "run_settings.json").read_text(encoding="utf-8"))
    run_manager_path = root / "managers" / "run_manager" / "run_manager.py"
    text = run_manager_path.read_text(encoding="utf-8", errors="ignore")
    cont = load_continuation_params(run_manager_path)
    tdi = load_tdi_gate_params(text)
    dmid = load_dmid_gate_params(text)
    return VariantSpec(name=name, root=root, cfg=cfg, cont=cont, tdi=tdi, dmid=dmid)


def discover_variants(base_root: Path, clone_root: Path) -> List[VariantSpec]:
    variants = [load_variant("baseline", base_root)]
    if clone_root.exists():
        for child in sorted(clone_root.iterdir()):
            if child.is_dir() and (child / "run_settings.json").exists():
                variants.append(load_variant(child.name, child))
    return variants


def g24h_gate_allows(cfg: Dict[str, Any], pct24: Optional[float], payload: Dict[str, Any]) -> bool:
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
    try:
        top_reasons = [str(x).strip().lower() for x in (payload.get("top_reasons") or []) if str(x).strip()]
    except Exception:
        top_reasons = []

    bullish = "momentum" in top_reasons or "pressure" in top_reasons
    tape_bullish = dmid_bps > 0.0 and pressure >= 60.0
    if not (bullish or tape_bullish):
        return False

    try:
        relief_score_min = float(cfg.get("G24H_RELIEF_TDI_SCORE_MIN", 60.0) or 60.0)
    except Exception:
        relief_score_min = 60.0
    return max(tdi_score, truth_score, continuation_floor) >= relief_score_min


def tob_gate_allows(cfg: Dict[str, Any], m: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    try:
        tob_usd = float(m.get("tob_usd", 0.0) or 0.0)
    except Exception:
        tob_usd = 0.0
    try:
        min_tob_usd = float(cfg.get("MIN_TOPBOOK_USD", 50.0) or 50.0)
    except Exception:
        min_tob_usd = 50.0
    if tob_usd >= min_tob_usd:
        return True

    try:
        dmid_bps = float(m.get("dmid_bps", 0.0) or 0.0)
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
    max_spr_bps = cfg_max_spr_bps(cfg)
    try:
        min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 0.0) or 0.0)
    except Exception:
        min_dmid_bps = 0.0
    try:
        tdi_score = float(payload.get("tdi_score", 0.0) or 0.0)
    except Exception:
        tdi_score = 0.0
    cycle_phase = str(payload.get("cycle_phase") or "").strip().lower()

    hard_floor = max(20.0, min_tob_usd * 0.4)
    strong_dmid = dmid_bps >= max(min_dmid_bps + 1.0, 4.0)
    strong_press = pressure >= 0.18
    tight_enough = spr_bps <= max_spr_bps * 0.6
    truth_ok = tdi_score >= 66.0 or cycle_phase == "lifting_from_trough"
    return tob_usd >= hard_floor and strong_dmid and strong_press and tight_enough and truth_ok


def tdi_min_buy_score(spec: VariantSpec, m: Dict[str, Any], payload: Dict[str, Any]) -> float:
    cfg = spec.cfg
    tdi = spec.tdi
    try:
        base_min_score = min(float(cfg.get("TDI_MIN_BUY_SCORE", 70.0) or 70.0), 70.0)
    except Exception:
        base_min_score = 70.0

    tob_usd = float(m.get("tob_usd", 0.0) or 0.0)
    dmid_bps = float(m.get("dmid_bps", 0.0) or 0.0)
    pressure = float(m.get("press", 0.5) or 0.5)
    spr_bps = float(m.get("spr_bps", 0.0) or 0.0)
    max_spr_bps = cfg_max_spr_bps(cfg)
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
        top_reasons = [str(x).strip().lower() for x in (payload.get("top_reasons") or []) if str(x).strip()]
    except Exception:
        top_reasons = []
    cycle_phase = str(payload.get("cycle_phase") or "").strip().lower()

    strong_tape = (
        tob_usd >= max(min_tob_usd * tdi.strong_tob_mult, tdi.strong_tob_floor)
        and dmid_bps >= max(min_dmid_bps + tdi.strong_dmid_add, tdi.strong_dmid_floor)
        and spr_bps <= max_spr_bps * tdi.strong_spr_mult
        and pressure >= tdi.strong_press_floor
    )
    market_truth_ok = (
        "momentum" in top_reasons
        and ("liquidity" in top_reasons or "pressure" in top_reasons)
        and tob_usd >= max(min_tob_usd * tdi.market_tob_mult, tdi.market_tob_floor)
        and dmid_bps >= max(min_dmid_bps + tdi.market_dmid_add, tdi.market_dmid_floor)
    )
    truth_ok = (
        ("momentum" in top_reasons or "pressure" in top_reasons)
        and (truth_score >= 60.0 or cycle_phase == "lifting_from_trough" or market_truth_ok)
    )
    if strong_tape and truth_ok:
        return max(tdi.adaptive_floor, base_min_score - tdi.adaptive_subtract)
    return base_min_score


def dmid_gate_allows(spec: VariantSpec, m: Dict[str, Any], payload: Dict[str, Any]) -> bool:
    cfg = spec.cfg
    dcfg = spec.dmid
    try:
        dmid_bps = float(m.get("dmid_bps", 0.0) or 0.0)
    except Exception:
        dmid_bps = 0.0
    try:
        min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 0.0) or 0.0)
    except Exception:
        min_dmid_bps = 0.0
    if dmid_bps >= min_dmid_bps:
        return True

    tob_usd = float(m.get("tob_usd", 0.0) or 0.0)
    pressure = float(m.get("press", 0.5) or 0.5)
    spr_bps = float(m.get("spr_bps", 0.0) or 0.0)
    max_spr_bps = cfg_max_spr_bps(cfg)
    try:
        min_tob_usd = float(cfg.get("MIN_TOPBOOK_USD", 50.0) or 50.0)
    except Exception:
        min_tob_usd = 50.0
    try:
        trend_bps_min = float(cfg.get("TREND_BPS_MIN", 12.0) or 12.0)
    except Exception:
        trend_bps_min = 12.0

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
    cycle_phase = str(payload.get("cycle_phase") or "").strip().lower()

    mild_pullback_floor = min_dmid_bps - max(dcfg.mild_abs_floor, trend_bps_min * dcfg.mild_mult)
    strong_tape = (
        tob_usd >= max(min_tob_usd * 1.0, 60.0)
        and pressure >= dcfg.strong_press_floor
        and spr_bps <= max_spr_bps * dcfg.strong_spr_mult
    )
    truth_ok = max(tdi_score, truth_score, continuation_floor) >= dcfg.truth_floor or cycle_phase == "lifting_from_trough"
    return dmid_bps >= mild_pullback_floor and strong_tape and truth_ok


def sb_update(spec: VariantSpec, product_id: str, mid: float, dmid_bps: float, tick: int) -> bool:
    cfg = spec.cfg
    cont = spec.cont
    confirm_n = int(cfg.get("BUY_CONFIRM_TICKS", 3) or 3)
    trend_n = int(cfg.get("TREND_TICKS", 5) or 5)
    trend_bps_min = float(cfg.get("TREND_BPS_MIN", 5.0) or 5.0)
    min_dmid_bps = float(cfg.get("MIN_DMID_BPS", 0.0) or 0.0)
    confirm_n = max(confirm_n, 1)
    trend_n = max(trend_n, 2)

    st = spec.sb_state.setdefault(product_id, {"mids": [], "confirm": 0})
    mids = st.get("mids", [])
    if mid > 0:
        mids.append(float(mid))
    if len(mids) > trend_n:
        mids = mids[-trend_n:]
    st["mids"] = mids

    deltas_bps: List[float] = []
    for idx in range(1, len(mids)):
        base = float(mids[idx - 1] or 0.0)
        last = float(mids[idx] or 0.0)
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
    trend_ok = len(mids) >= trend_n and trend_bps >= trend_bps_min
    dmid_ok = float(dmid_bps or 0.0) >= min_dmid_bps
    pressing_now = (
        last_step_bps >= max(min_dmid_bps - cont.last_step_subtract, cont.last_step_floor)
        and prior_step_bps >= cont.prior_step_floor
    )
    step_ok = positive_steps >= max(1, len(deltas_bps) - cont.step_slack)
    relief_trend_bps = max(trend_bps_min * 0.05, 0.5)
    relief_last_bps = max(min_dmid_bps - cont.relief_last_subtract, cont.relief_last_floor)
    relief_prior_floor = -max(cont.relief_prior_base, trend_bps_min * cont.relief_prior_mult)
    relief_ok = bool(
        len(deltas_bps) >= 2
        and trend_bps >= relief_trend_bps
        and last_step_bps >= relief_last_bps
        and positive_steps >= max(1, len(deltas_bps) - cont.step_slack)
        and prior_step_bps >= relief_prior_floor
        and not (last_step_bps <= -3.0 and prior_step_bps <= -2.0)
    )
    sig_ok = (trend_ok and dmid_ok and pressing_now and step_ok and (not cooling)) or relief_ok
    st["confirm"] = int(st.get("confirm", 0)) + 1 if sig_ok else 0
    st["last_tick"] = tick
    return int(st["confirm"]) >= confirm_n


def make_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "tdi_score": row.get("tdi_score", 0.0),
        "tdi_truth_score": row.get("tdi_truth_score", 0.0),
        "tdi_continuation_floor": row.get("tdi_continuation_floor", 0.0),
        "top_reasons": row.get("top_reasons") or [],
        "cycle_phase": row.get("cycle_phase") or row.get("ctx_phase") or "",
        "dmid_bps": row.get("dmid_bps", 0.0),
        "press": row.get("press", 0.0),
    }


def maybe_store_example(bucket: List[Dict[str, Any]], row: Dict[str, Any], reason: str) -> None:
    if len(bucket) >= 5:
        return
    bucket.append(
        {
            "ts": row.get("ts"),
            "tick": row.get("tick"),
            "product_id": row.get("product_id"),
            "price": row.get("price"),
            "tdi_score": row.get("tdi_score"),
            "bot_score": row.get("bot_score"),
            "g24h_pct": row.get("g24h_pct"),
            "dmid_bps": row.get("dmid_bps"),
            "spr_bps": row.get("spr_bps"),
            "tob_usd": row.get("tob_usd"),
            "press": row.get("press"),
            "reason": reason,
        }
    )


def update_active_signals(spec: VariantSpec, product_id: str, ts: datetime, price: float) -> None:
    signals = spec.active.get(product_id)
    if not signals:
        return
    keep: List[ActiveSignal] = []
    tp_pct = float(spec.cfg.get("TP_PCT", TP_PCT_DEFAULT) or TP_PCT_DEFAULT) / 100.0
    sl_pct = float(spec.cfg.get("SL_PCT", SL_PCT_DEFAULT) or SL_PCT_DEFAULT) / 100.0
    for signal in signals:
        all_closed = True
        for horizon_min, result in signal.horizons.items():
            if result.status != "open":
                continue
            ret = (price / signal.entry_price) - 1.0 if signal.entry_price > 0 else 0.0
            result.last_ret = ret
            result.max_ret = max(result.max_ret, ret)
            result.min_ret = min(result.min_ret, ret)
            if ret >= tp_pct:
                result.status = "tp_first"
            elif ret <= -sl_pct:
                result.status = "sl_first"
            elif ts >= result.end_ts:
                result.status = "timeout"
            if result.status == "open":
                all_closed = False
        if all_closed:
            finalize_signal(spec, signal)
        else:
            keep.append(signal)
    if keep:
        spec.active[product_id] = keep
    else:
        spec.active.pop(product_id, None)


def finalize_signal(spec: VariantSpec, signal: ActiveSignal) -> None:
    for horizon_min, result in signal.horizons.items():
        if result.status == "open":
            result.status = "censored"
        spec.outcome_counts[horizon_min][result.status] += 1
        spec.outcome_returns[horizon_min]["sum_last"] += result.last_ret
        spec.outcome_returns[horizon_min]["sum_max"] += result.max_ret
        spec.outcome_returns[horizon_min]["sum_min"] += result.min_ret


def record_admission(spec: VariantSpec, row: Dict[str, Any], ts: datetime) -> None:
    spec.counts["dry"] += 1
    maybe_store_example(spec.admitted_examples, row, "dry")
    horizons = {
        minutes: HorizonResult(end_ts=ts + timedelta(minutes=minutes))
        for minutes in HORIZONS_MINUTES
    }
    signal = ActiveSignal(
        variant=spec.name,
        product_id=str(row["product_id"]),
        entry_ts=ts,
        entry_price=float(row.get("price", 0.0) or 0.0),
        horizons=horizons,
    )
    spec.active[signal.product_id].append(signal)


def summarize_variant(spec: VariantSpec) -> Dict[str, Any]:
    summary = {
        "variant": spec.name,
        "root": str(spec.root),
        "settings": {
            "TDI_MIN_BUY_SCORE": spec.cfg.get("TDI_MIN_BUY_SCORE"),
            "MIN_24H_PCT": spec.cfg.get("MIN_24H_PCT"),
            "TREND_BPS_MIN": spec.cfg.get("TREND_BPS_MIN"),
            "TOP_N": spec.cfg.get("TOP_N"),
            "BUY_MAX_OPEN": spec.cfg.get("BUY_MAX_OPEN"),
            "MAX_BUYS_PER_TICK": spec.cfg.get("MAX_BUYS_PER_TICK"),
        },
        "continuation": {
            "prior_step_floor": spec.cont.prior_step_floor,
            "last_step_subtract": spec.cont.last_step_subtract,
            "step_slack": spec.cont.step_slack,
        },
        "tdi_gate": {
            "strong_tob_mult": spec.tdi.strong_tob_mult,
            "strong_tob_floor": spec.tdi.strong_tob_floor,
            "strong_dmid_add": spec.tdi.strong_dmid_add,
            "strong_dmid_floor": spec.tdi.strong_dmid_floor,
            "strong_spr_mult": spec.tdi.strong_spr_mult,
            "adaptive_floor": spec.tdi.adaptive_floor,
            "adaptive_subtract": spec.tdi.adaptive_subtract,
        },
        "dmid_gate": {
            "mild_abs_floor": spec.dmid.mild_abs_floor,
            "mild_mult": spec.dmid.mild_mult,
            "strong_press_floor": spec.dmid.strong_press_floor,
            "strong_spr_mult": spec.dmid.strong_spr_mult,
            "truth_floor": spec.dmid.truth_floor,
        },
        "counts": dict(spec.counts),
        "admitted_examples": spec.admitted_examples,
        "reject_examples": {k: v for k, v in spec.reject_examples.items()},
        "outcomes": {},
    }
    for horizon_min in sorted(spec.outcome_counts):
        counts = spec.outcome_counts[horizon_min]
        totals = sum(counts.values()) or 1
        returns = spec.outcome_returns[horizon_min]
        summary["outcomes"][f"{horizon_min}m"] = {
            "counts": dict(counts),
            "avg_last_ret_pct": round((returns["sum_last"] / totals) * 100.0, 4),
            "avg_best_ret_pct": round((returns["sum_max"] / totals) * 100.0, 4),
            "avg_worst_ret_pct": round((returns["sum_min"] / totals) * 100.0, 4),
        }
    return summary


def replay(variants: List[VariantSpec], snapshots_path: Path, since_dt: datetime) -> Dict[str, Any]:
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None
    rows_scanned = 0
    rows_used = 0

    with snapshots_path.open("r", encoding="utf-8") as fh:
        for line in fh:
            rows_scanned += 1
            line = line.strip()
            if not line:
                continue
            try:
                row = json.loads(line)
            except json.JSONDecodeError:
                continue
            ts_raw = row.get("ts")
            pid = row.get("product_id")
            price = row.get("price")
            if not ts_raw or not pid or not price:
                continue
            ts = iso_to_dt(str(ts_raw))
            if ts < since_dt:
                continue
            rows_used += 1
            if first_ts is None:
                first_ts = ts
            last_ts = ts

            payload = make_payload(row)
            m = {
                "mid": float(row.get("price", 0.0) or 0.0),
                "spr_bps": float(row.get("spr_bps", 0.0) or 0.0),
                "tob_usd": float(row.get("tob_usd", 0.0) or 0.0),
                "tob": float(row.get("tob_usd", 0.0) or 0.0),
                "press": float(row.get("press", 0.0) or 0.0),
                "dmid_bps": float(row.get("dmid_bps", 0.0) or 0.0),
                "dmid": float(row.get("dmid_bps", 0.0) or 0.0),
            }
            tick = int(row.get("tick", 0) or 0)
            pct24 = row.get("g24h_pct")
            tdi_score = float(row.get("tdi_score", 0.0) or 0.0)

            for spec in variants:
                update_active_signals(spec, str(pid), ts, float(price))
                spec.counts["snapshots"] += 1

                if not g24h_gate_allows(spec.cfg, pct24, payload):
                    spec.counts["g24h"] += 1
                    maybe_store_example(spec.reject_examples["g24h"], row, "g24h")
                    continue

                if float(m["spr_bps"]) > cfg_max_spr_bps(spec.cfg):
                    spec.counts["spr"] += 1
                    maybe_store_example(spec.reject_examples["spr"], row, "spr")
                    continue

                if not tob_gate_allows(spec.cfg, m, payload):
                    spec.counts["tob"] += 1
                    maybe_store_example(spec.reject_examples["tob"], row, "tob")
                    continue

                if not dmid_gate_allows(spec, m, payload):
                    spec.counts["dmid"] += 1
                    maybe_store_example(spec.reject_examples["dmid"], row, "dmid")
                    continue

                if not sb_update(spec, str(pid), float(price), float(m["dmid_bps"]), tick):
                    spec.counts["sb"] += 1
                    maybe_store_example(spec.reject_examples["sb"], row, "sb")
                    continue

                min_live_tdi_score = tdi_min_buy_score(spec, m, payload)
                if tdi_score < min_live_tdi_score:
                    spec.counts["tdi_low"] += 1
                    maybe_store_example(spec.reject_examples["tdi_low"], row, "tdi_low")
                    continue

                record_admission(spec, row, ts)

    for spec in variants:
        for product_id in list(spec.active.keys()):
            for signal in spec.active[product_id]:
                finalize_signal(spec, signal)
            spec.active.pop(product_id, None)

    return {
        "snapshots_path": str(snapshots_path),
        "since": since_dt.isoformat(),
        "first_ts": first_ts.isoformat() if first_ts else None,
        "last_ts": last_ts.isoformat() if last_ts else None,
        "rows_scanned": rows_scanned,
        "rows_used": rows_used,
        "variants": [summarize_variant(spec) for spec in variants],
    }


def rank_variants(summary: Dict[str, Any]) -> List[Dict[str, Any]]:
    ranked: List[Dict[str, Any]] = []
    for item in summary["variants"]:
        counts = item["counts"]
        dry = int(counts.get("dry", 0))
        tdi_low = int(counts.get("tdi_low", 0))
        sb = int(counts.get("sb", 0))
        out_240 = item["outcomes"].get("240m", {})
        out_counts = out_240.get("counts", {})
        tp = int(out_counts.get("tp_first", 0))
        sl = int(out_counts.get("sl_first", 0))
        timeout = int(out_counts.get("timeout", 0))
        censored = int(out_counts.get("censored", 0))
        avg_last = float(out_240.get("avg_last_ret_pct", 0.0) or 0.0)
        score = (dry * 3.0) + (tp * 4.0) - (sl * 5.0) + avg_last - (tdi_low * 0.2) - (sb * 0.1) - ((timeout + censored) * 0.05)
        ranked.append(
            {
                "variant": item["variant"],
                "score": round(score, 3),
                "dry": dry,
                "tp_240m": tp,
                "sl_240m": sl,
                "avg_last_ret_240m_pct": avg_last,
                "sb_rejects": sb,
                "tdi_low_rejects": tdi_low,
            }
        )
    ranked.sort(key=lambda x: x["score"], reverse=True)
    return ranked


def main() -> None:
    args = parse_args()
    base_root = Path(args.base_root)
    clone_root = Path(args.clone_root)
    snapshots_path = Path(args.snapshots)

    variants = discover_variants(base_root, clone_root)
    now = datetime.now(UTC)
    since_dt = now - timedelta(days=int(args.since_days))
    summary = replay(variants, snapshots_path, since_dt)
    summary["ranking"] = rank_variants(summary)

    if args.output:
        output_path = Path(args.output)
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = base_root / "tools" / "parallel_dry" / f"replay_summary_{stamp}.json"
    output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")

    print(f"Replay written to: {output_path}")
    print(f"Rows used: {summary['rows_used']}  Window: {summary['first_ts']} -> {summary['last_ts']}")
    print("Ranking:")
    for row in summary["ranking"]:
        print(
            f"  {row['variant']:<16} score={row['score']:>8} "
            f"dry={row['dry']:>6} tp240={row['tp_240m']:>6} sl240={row['sl_240m']:>6} "
            f"avg240={row['avg_last_ret_240m_pct']:>8.3f}%"
        )


if __name__ == "__main__":
    main()
