from __future__ import annotations

from typing import Any, Dict, List, Optional

__all__ = ["TDI_VERSION", "TDI_WEIGHTS", "compute_tdi"]

TDI_VERSION = "v6"
TDI_WEIGHTS: Dict[str, float] = {
    "trough": 0.45,
    "cycle": 0.25,
    "momentum": 0.08,
    "liquidity": 0.05,
    "spread": 0.05,
    "pressure": 0.05,
    "quality": 0.07,
}

_BULL_PHASES = {"lifting_from_trough", "bottoming"}
_BEAR_PHASES = {"descending_from_crest", "rolling_over"}


def _f(x: Any, default: float = 0.0) -> float:
    try:
        if x is None:
            return float(default)
        return float(x)
    except Exception:
        return float(default)


def _clip(x: float, lo: float = 0.0, hi: float = 100.0) -> float:
    if x < lo:
        return float(lo)
    if x > hi:
        return float(hi)
    return float(x)


def _band(score: float) -> str:
    s = _f(score)
    if s >= 80.0:
        return "strong"
    if s >= 65.0:
        return "forming"
    if s >= 50.0:
        return "neutral"
    return "weak"


def _trough_score(trough_pct: Optional[float]) -> float:
    if trough_pct is None:
        return 50.0
    tp = _f(trough_pct, 0.5)
    if tp < 0.0:
        tp = 0.0
    if tp > 1.0:
        tp = 1.0
    # Keep "closer to trough = higher value" true, but soften the decay so
    # lifting names do not instantly collapse to unusable scores once they
    # leave the exact bottom.
    return _clip((1.0 - (tp ** 3.0)) * 100.0)


def _momentum_score(dmid_bps: float) -> float:
    # 0 bps = neutral, rising ticks lift the score, falling ticks reduce it.
    return _clip(50.0 + (_f(dmid_bps) * 5.0))


def _liquidity_score(tob_usd: float, min_topbook_usd: float) -> float:
    base = max(1.0, _f(min_topbook_usd, 50.0))
    ratio = _f(tob_usd) / base
    return _clip(ratio * 50.0)


def _spread_score(spr_bps: float, max_spr_bps: float) -> float:
    cap = max(1.0, _f(max_spr_bps, 90.0))
    return _clip(100.0 * (1.0 - (_f(spr_bps) / (cap * 2.0))))


def _pressure_score(press: float) -> float:
    # book pressure is already in [0,1] in current bot plumbing.
    return _clip(_f(press, 0.5) * 100.0)


def _quality_score(context: Dict[str, Any]) -> float:
    fresh_ratio = _clip(_f(context.get("tape_fresh_ratio"), 0.0) * 100.0)
    spread_ok_ratio = _clip(_f(context.get("tape_spread_ok_ratio"), 0.0) * 100.0)
    press_ok_ratio = _clip(_f(context.get("tape_press_ok_ratio"), 0.0) * 100.0)
    top_ratio = max(0.0, _f(context.get("tape_top_ratio"), 0.0))
    top_score = _clip(min(1.5, top_ratio) / 1.5 * 100.0)
    symbol_quality = _clip(_f(context.get("symbol_quality_score"), 0.0))
    score = (
        (fresh_ratio * 0.35)
        + (spread_ok_ratio * 0.20)
        + (press_ok_ratio * 0.15)
        + (top_score * 0.20)
        + (symbol_quality * 0.10)
    )
    if _f(context.get("tape_u0_streak"), 0.0) >= 3.0:
        score -= min(18.0, (_f(context.get("tape_u0_streak"), 0.0) - 2.0) * 4.0)
    if _b(context.get("tape_u0_cooldown")):
        score -= 20.0
    return _clip(score)


def _s(value: Any) -> str:
    return str(value or "").strip().lower()


def _b(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    text = _s(value)
    return text in {"1", "true", "yes", "on"}


def _cycle_support_score(context: Dict[str, Any]) -> float:
    explicit = _f(context.get("cycle_support_score"), -1.0)
    if explicit >= 0.0:
        return _clip(explicit)
    conf = _clip(_f(context.get("cycle_confidence"), 0.0))
    tp_hit = _clip(_f(context.get("cycle_tp_hit_rate_pct"), 0.0))
    qtr = max(0.0, min(5.0, _f(context.get("cycle_qualified_troughs"), 0.0)))
    phase = _s(context.get("cycle_phase"))
    stance = _s(context.get("cycle_stance"))
    allow = _b(context.get("cycle_allow"))
    block = _b(context.get("cycle_block"))

    phase_bonus = 0.0
    if phase in _BULL_PHASES or stance == "bull":
        phase_bonus = 12.0
    elif phase in _BEAR_PHASES or stance == "bear":
        phase_bonus = -18.0

    gate_bonus = 6.0 if allow else (-12.0 if block else 0.0)
    return _clip((conf * 0.60) + (tp_hit * 0.25) + (qtr * 3.0) + phase_bonus + gate_bonus)


def _trough_maturity(context: Dict[str, Any]) -> float:
    n = _f(context.get("trough_n"), 0.0)
    return _clip((n / 12.0) * 100.0) / 100.0


def _continuation_floor(
    context: Dict[str, Any],
    components: Dict[str, float],
    cycle_support: float,
) -> tuple[float, List[str]]:
    phase = _s(context.get("cycle_phase"))
    stance = _s(context.get("cycle_stance"))
    bullish = phase in _BULL_PHASES or stance == "bull" or _b(context.get("cycle_allow"))
    bearish = phase in _BEAR_PHASES or stance == "bear" or _b(context.get("cycle_block"))
    if not bullish and not bearish:
        return 0.0, []

    momentum = _f(components.get("momentum"), 50.0)
    spread = _f(components.get("spread"), 50.0)
    liquidity = _f(components.get("liquidity"), 50.0)
    pressure = _f(components.get("pressure"), 50.0)

    cont = (
        (cycle_support * 0.78)
        + (max(0.0, momentum - 50.0) * 0.18)
        + (max(0.0, spread - 70.0) * 0.10)
        + (max(0.0, liquidity - 50.0) * 0.08)
        + (max(0.0, pressure - 50.0) * 0.08)
    )
    maturity = _trough_maturity(context)
    if context.get("trough_pct") is None:
        cont = min(cont, 58.0 + (12.0 * maturity))
        tags = ["bull_cycle_floor", "immature_trough_cap"] if bullish else ["bear_cycle_cap", "immature_trough_cap"]
    else:
        cont = min(cont, 60.0 + (40.0 * maturity))
        tags = ["bull_cycle_floor"] if bullish else ["bear_cycle_cap"]
    if bullish:
        return _clip(cont), tags
    return _clip(cont * 0.45), tags


def _flow_floor(
    context: Dict[str, Any],
    components: Dict[str, float],
    cycle_support: float,
) -> tuple[float, List[str]]:
    regime = _s(context.get("flow_regime"))
    flow_score = _clip(_f(context.get("flow_score"), 0.0))
    if regime not in {"ride", "pullback", "breakout", "float"} or flow_score < 55.0:
        return 0.0, []

    momentum = _f(components.get("momentum"), 50.0)
    liquidity = _f(components.get("liquidity"), 50.0)
    spread = _f(components.get("spread"), 50.0)
    pressure = _f(components.get("pressure"), 50.0)
    quality = _f(components.get("quality"), 50.0)
    trough_known = context.get("trough_pct") is not None

    base = (
        (flow_score * 0.46)
        + (max(0.0, momentum - 50.0) * 0.18)
        + (max(0.0, liquidity - 50.0) * 0.10)
        + (max(0.0, spread - 60.0) * 0.09)
        + (max(0.0, pressure - 50.0) * 0.10)
        + (max(0.0, quality - 55.0) * 0.07)
        + (cycle_support * 0.18)
    )

    tags = [f"flow_{regime}_floor"]
    if regime == "ride":
        floor = base + 10.0
    elif regime == "pullback":
        floor = base + 5.0
    elif regime == "breakout":
        floor = base + 3.0
    else:
        floor = base - 3.0

    if not trough_known and regime != "ride":
        floor = min(floor, 72.0)
        tags.append("flow_no_trough_cap")
    elif not trough_known:
        floor = min(floor, 84.0)
    return _clip(floor), tags


def _support_delta(components: Dict[str, float]) -> float:
    # Secondary tape inputs still matter as tie-breakers after the main truth
    # anchor is set.
    return float(
        (_f(components.get("momentum"), 50.0) - 50.0) * 0.05
        + (_f(components.get("liquidity"), 50.0) - 50.0) * 0.03
        + (_f(components.get("spread"), 50.0) - 50.0) * 0.04
        + (_f(components.get("pressure"), 50.0) - 50.0) * 0.03
        + (_f(components.get("quality"), 50.0) - 50.0) * 0.05
    )


def _shape_adjustment(
    reasons: List[str],
    trough_pct: Optional[float] = None,
) -> tuple[float, List[str]]:
    top = [str(x).strip() for x in (reasons or []) if str(x).strip()]
    top2 = top[:2]
    top3 = top[:3]
    adj = 0.0
    tags: List[str] = []

    # Shape tags fine-tune the score around the truth anchor.
    if top3 and top3[0] == "liquidity":
        adj -= 4.0
        tags.append("liq_top1_penalty")
    if {"liquidity", "spread"} <= set(top2) and "pressure" not in top3:
        adj -= 3.0
        tags.append("liq_spread_penalty")
    if {"momentum", "pressure"} <= set(top3):
        adj += 5.0
        tags.append("mom_press_bonus")
    if {"quality", "momentum"} <= set(top3):
        adj += 3.0
        tags.append("quality_momentum_bonus")
    return float(adj), tags


def _reliability_adjustment(context: Dict[str, Any], components: Dict[str, float]) -> tuple[float, List[str]]:
    tags: List[str] = []
    delta = 0.0
    fresh_ratio = _f(context.get("tape_fresh_ratio"), 0.0)
    u0_streak = _f(context.get("tape_u0_streak"), 0.0)
    quality = _f(components.get("quality"), 50.0)
    cohort = _s(context.get("symbol_cohort"))
    infra_share = _f(context.get("symbol_infra_share"), 0.0)
    quarantine_reason = _s(context.get("symbol_quarantine_reason") or context.get("symbol_reliability_dominant_reason"))
    regime = _s(context.get("flow_regime"))
    flow_score = _f(context.get("flow_score"), 0.0)

    if _b(context.get("tape_u0_cooldown")):
        delta -= 10.0
        tags.append("u0_cooldown_penalty")
    elif u0_streak >= 3.0:
        delta -= min(8.0, (u0_streak - 2.0) * 2.0)
        tags.append("u0_streak_penalty")

    if _b(context.get("symbol_quarantined")):
        delta -= 12.0
        tags.append(f"symbol_quarantine_{quarantine_reason or 'infra'}")
    elif infra_share >= 0.45:
        delta -= min(8.0, (infra_share - 0.45) * 20.0)
        tags.append("infra_share_penalty")
    elif infra_share <= 0.20 and fresh_ratio >= 0.75 and quality >= 72.0:
        delta += 1.5
        tags.append("infra_clean_bonus")

    if fresh_ratio < 0.55:
        delta -= (0.55 - fresh_ratio) * 12.0
        tags.append("fresh_ratio_penalty")
    elif fresh_ratio >= 0.80 and quality >= 72.0:
        delta += 2.5
        tags.append("clean_tape_bonus")

    if cohort == "speculative":
        delta -= 1.5
        tags.append("speculative_penalty")
    elif cohort == "prime" and quality >= 70.0:
        delta += 1.5
        tags.append("prime_quality_bonus")

    if regime == "ride" and flow_score >= 72.0 and quality >= 70.0 and fresh_ratio >= 0.70:
        delta += 2.0
        tags.append("ride_flow_bonus")
    elif regime == "pullback" and flow_score >= 66.0 and quality >= 68.0:
        delta += 1.0
        tags.append("pullback_flow_bonus")

    return float(delta), tags


def compute_tdi(context: Dict[str, Any]) -> Dict[str, Any]:
    """Compute an observational TDI payload from existing evaluation inputs only."""
    ctx = dict(context or {})
    trough_pct = ctx.get("trough_pct")
    dmid_bps = _f(ctx.get("dmid_bps"), 0.0)
    tob_usd = _f(ctx.get("tob_usd", ctx.get("tob")), 0.0)
    spr_bps = _f(ctx.get("spr_bps"), 0.0)
    press = _f(ctx.get("press"), 0.5)
    max_spr_bps = _f(ctx.get("max_spr_bps"), 90.0)
    min_topbook_usd = _f(ctx.get("min_topbook_usd"), 50.0)

    components = {
        "trough": round(_trough_score(trough_pct), 2),
        "momentum": round(_momentum_score(dmid_bps), 2),
        "liquidity": round(_liquidity_score(tob_usd, min_topbook_usd), 2),
        "spread": round(_spread_score(spr_bps, max_spr_bps), 2),
        "pressure": round(_pressure_score(press), 2),
        "quality": round(_quality_score(ctx), 2),
    }

    trough_truth = round(_f(components.get("trough"), 50.0), 2)
    cycle_support = round(_cycle_support_score(ctx), 2)
    continuation_floor, continuation_tags = _continuation_floor(ctx, components, cycle_support)
    flow_floor, flow_tags = _flow_floor(ctx, components, cycle_support)
    truth_score = round(max(trough_truth, continuation_floor, flow_floor), 2)
    support_delta = _support_delta(components)

    reasons: List[str] = [
        name for name, _ in sorted(
            components.items(),
            key=lambda kv: (_f(kv[1]), kv[0]),
            reverse=True,
        )[:3]
    ]
    score_adjustment, score_adjustment_tags = _shape_adjustment(reasons, trough_pct)
    reliability_adjustment, reliability_tags = _reliability_adjustment(ctx, components)
    net_support = max(-12.0, min(10.0, support_delta + score_adjustment + reliability_adjustment))
    tdi_score = round(_clip(truth_score + net_support), 2)

    return {
        "tdi_version": TDI_VERSION,
        "tdi_raw_score": truth_score,
        "tdi_score": tdi_score,
        "tdi_band": _band(tdi_score),
        "tdi_truth_score": truth_score,
        "tdi_trough_truth": trough_truth,
        "tdi_cycle_support": cycle_support,
        "tdi_continuation_floor": round(continuation_floor, 2),
        "tdi_flow_floor": round(flow_floor, 2),
        "tdi_support_delta": round(net_support, 2),
        "tdi_score_adjustment": round(score_adjustment, 2),
        "tdi_reliability_adjustment": round(reliability_adjustment, 2),
        "tdi_score_adjustment_tags": continuation_tags + flow_tags + score_adjustment_tags + reliability_tags,
        "components": components,
        "top_reasons": reasons,
    }
