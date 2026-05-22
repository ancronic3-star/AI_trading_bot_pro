from __future__ import annotations

import argparse
import json
import math
import re
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional


TICK_RE = re.compile(
    r"^\[(?P<ts>[^\]]+)\] \[tick_diag\] tick=(?P<tick>\d+) "
    r"U=(?P<u>\d+) S=(?P<s>\d+) top=(?P<top>\d+) chk=(?P<chk>\d+) pass=(?P<pass>\d+)"
)


@dataclass
class TickEvent:
    ts: datetime
    tick: int
    u: int
    chk: int
    passed: int
    rejects: Dict[str, int]


@dataclass
class BlockSummary:
    observed: int = 0
    strategy_observed: int = 0
    pass_ticks: int = 0
    u0_ticks: int = 0
    rejects: Counter = None  # type: ignore[assignment]

    def __post_init__(self) -> None:
        if self.rejects is None:
            self.rejects = Counter()

    @property
    def reach_rate(self) -> Optional[float]:
        if self.strategy_observed <= 0:
            return None
        return float(self.pass_ticks) / float(self.strategy_observed)

    @property
    def stability_rate(self) -> Optional[float]:
        if self.observed <= 0:
            return None
        return float(self.strategy_observed) / float(self.observed)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Evaluate KOKO parallel dry lanes in comparable time blocks.")
    p.add_argument("--base-root", default=r"C:\ai_trading_bot_koko")
    p.add_argument("--clone-root", default=r"C:\ai_trading_bot_koko_parallel")
    p.add_argument("--format", choices=("text", "json"), default="text")
    p.add_argument("--output", default=None, help="Optional JSON output artifact path.")
    return p.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def tail_text(path: Path, max_bytes: int = 4_000_000) -> str:
    with path.open("rb") as f:
        f.seek(0, 2)
        size = f.tell()
        start = max(0, size - max_bytes)
        f.seek(start)
        data = f.read()
    return data.decode("utf-8", errors="ignore")


def parse_rejects(line: str) -> Dict[str, int]:
    out: Dict[str, int] = {}
    if "rej=" in line:
        tail = line.split("rej=", 1)[1]
        tail = tail.split(" soft=", 1)[0].strip()
        for part in tail.split(","):
            part = part.strip()
            if not part or ":" not in part:
                continue
            key, raw = part.split(":", 1)
            try:
                out[key.strip()] = int(raw.strip())
            except Exception:
                continue
    if "soft=" in line:
        soft_tail = line.split("soft=", 1)[1].strip()
        for part in soft_tail.split(","):
            part = part.strip()
            if not part or ":" not in part:
                continue
            key, raw = part.split(":", 1)
            try:
                out[f"soft_{key.strip()}"] = int(raw.strip())
            except Exception:
                continue
    return out


def parse_tick_events(path: Path) -> List[TickEvent]:
    if not path.exists():
        return []
    events: List[TickEvent] = []
    for line in tail_text(path).splitlines():
        m = TICK_RE.match(line.strip())
        if not m:
            continue
        try:
            ts = datetime.strptime(m.group("ts"), "%Y-%m-%d %H:%M:%S")
        except Exception:
            continue
        events.append(
            TickEvent(
                ts=ts,
                tick=int(m.group("tick")),
                u=int(m.group("u")),
                chk=int(m.group("chk")),
                passed=int(m.group("pass")),
                rejects=parse_rejects(line),
            )
        )
    return events


def mean(values: Iterable[Optional[float]]) -> Optional[float]:
    clean = [float(v) for v in values if v is not None]
    if not clean:
        return None
    return sum(clean) / float(len(clean))


def floor_block(ts: datetime, start: datetime, seconds: int) -> int:
    return int((ts - start).total_seconds() // seconds)


def format_pct(value: Optional[float]) -> str:
    if value is None:
        return "n/a"
    return f"{value * 100.0:.1f}%"


def dominant_choke_axis(choke: Optional[str], current_axis: Optional[str] = None) -> Optional[str]:
    choke_key = str(choke or "").strip()
    axis_key = str(current_axis or "").strip().upper()
    if choke_key == "tob":
        if axis_key == "MIN_TOPBOOK_USD":
            return "MAX_SPR_BPS"
        if axis_key == "MAX_SPR_BPS":
            return "BOOK_PRESSURE_MIN"
        return "MIN_TOPBOOK_USD"
    if choke_key == "sb":
        if axis_key == "TREND_BPS_MIN":
            return "MIN_TOPBOOK_USD"
        return "TREND_BPS_MIN"
    mapping = {
        "dmid": "MIN_DMID_BPS",
        "soft_g24h": "MIN_24H_PCT",
    }
    return mapping.get(choke_key)


def parent_reject_key(key: str) -> str:
    raw = str(key or "").strip()
    if not raw:
        return raw
    mapping = {
        "u0": "u0",
        "u0_now": "u0",
        "u0_cd": "u0",
        "preq_hist": "u0",
        "preq_fresh": "u0",
        "preq_tobq": "tob",
        "preq_spread": "spr",
        "preq_press": "sb",
    }
    return mapping.get(raw, raw)


def pick_campaign(cfg: Dict[str, Any]) -> Dict[str, Any]:
    campaign = cfg.get("PARALLEL_DRY_CAMPAIGN") or {}
    if not isinstance(campaign, dict):
        return {}
    return campaign


def discover_clones(clone_root: Path, campaign: Dict[str, Any], axis_key: str) -> List[Dict[str, Any]]:
    prefix = str(campaign.get("CLONE_PREFIX") or "").strip()
    clones: List[Dict[str, Any]] = []
    if not clone_root.exists():
        return clones
    for child in sorted(clone_root.iterdir()):
        if not child.is_dir():
            continue
        if prefix and not child.name.startswith(prefix):
            continue
        settings_path = child / "run_settings.json"
        activity_path = child / "logs" / "activity_ticker.log"
        if not settings_path.exists() or not activity_path.exists():
            continue
        settings = load_json(settings_path)
        clones.append(
            {
                "name": child.name,
                "root": child,
                "activity_path": activity_path,
                "axis_value": settings.get(axis_key),
            }
        )
    return clones


def summarize(base_root: Path, clone_root: Path) -> Dict[str, Any]:

    cfg = load_json(base_root / "run_settings.json")
    campaign = pick_campaign(cfg)
    axis_key = str(campaign.get("AXIS_KEY") or campaign.get("AXIS_NAME") or "MIN_TOPBOOK_USD")
    dwell_minutes = int(campaign.get("DWELL_MINUTES") or 90)
    block_minutes = int(campaign.get("BLOCK_MINUTES") or 30)
    min_blocks = int(campaign.get("MIN_BLOCKS_FOR_PROMOTION") or 3)
    min_ticks_per_block = int(campaign.get("MIN_TICKS_PER_BLOCK") or 8)
    required_block_win_rate = float(campaign.get("REQUIRED_BLOCK_WIN_RATE") or 0.67)
    required_reach_edge = float(campaign.get("REQUIRED_REACH_EDGE") or 0.08)
    required_stability_floor = float(campaign.get("REQUIRED_STABILITY_FLOOR") or 0.85)
    required_stability_edge = float(campaign.get("REQUIRED_STABILITY_EDGE") or 0.03)
    treat_u0_as_reliability = bool(campaign.get("TREAT_U0_AS_RELIABILITY", True))
    reliability_alert_u0_share = float(campaign.get("RELIABILITY_ALERT_U0_SHARE") or 0.25)

    clones = discover_clones(clone_root, campaign, axis_key)
    clone_events: Dict[str, List[TickEvent]] = {}
    latest_times: List[datetime] = []
    for clone in clones:
        events = parse_tick_events(clone["activity_path"])
        clone_events[clone["name"]] = events
        if events:
            latest_times.append(events[-1].ts)

    if not clones or not latest_times:
        return {
            "campaign_active": bool(campaign.get("ACTIVE", False)),
            "axis_key": axis_key,
            "status": "no_data",
            "message": "No clone data available.",
        }

    window_end = min(latest_times)
    window_start = window_end - timedelta(minutes=dwell_minutes)
    block_seconds = block_minutes * 60
    block_count = max(1, int(math.floor(dwell_minutes / block_minutes)))

    block_data: Dict[str, List[BlockSummary]] = {clone["name"]: [BlockSummary() for _ in range(block_count)] for clone in clones}
    reliability_flags: Dict[str, bool] = {}

    for clone in clones:
        name = clone["name"]
        for event in clone_events[name]:
            if event.ts < window_start or event.ts > window_end:
                continue
            idx = floor_block(event.ts, window_start, block_seconds)
            if idx < 0 or idx >= block_count:
                continue
            block = block_data[name][idx]
            block.observed += 1
            is_u0 = event.u <= 0
            if is_u0:
                block.u0_ticks += 1
            if (not treat_u0_as_reliability) or (not is_u0):
                block.strategy_observed += 1
                if event.passed > 0:
                    block.pass_ticks += 1
                block.rejects.update(event.rejects)

        total_observed = sum(b.observed for b in block_data[name])
        total_u0 = sum(b.u0_ticks for b in block_data[name])
        reliability_flags[name] = total_observed > 0 and (float(total_u0) / float(total_observed)) >= reliability_alert_u0_share

    comparable_blocks: List[int] = []
    for idx in range(block_count):
        if all(block_data[clone["name"]][idx].observed >= min_ticks_per_block for clone in clones):
            comparable_blocks.append(idx)

    per_clone: List[Dict[str, Any]] = []
    block_wins = Counter()
    overall_rejects = Counter()
    overall_reject_details = Counter()
    for idx in comparable_blocks:
        candidates = []
        for clone in clones:
            summary = block_data[clone["name"]][idx]
            candidates.append((summary.reach_rate or -1.0, summary.stability_rate or -1.0, clone["name"]))
        winner = sorted(candidates, reverse=True)[0][2]
        block_wins[winner] += 1

    for clone in clones:
        name = clone["name"]
        blocks = [block_data[name][idx] for idx in comparable_blocks]
        reach = mean(block.reach_rate for block in blocks)
        stability = mean(block.stability_rate for block in blocks)
        rejects = Counter()
        for block in blocks:
            rejects.update(block.rejects)
        overall_reject_details.update(rejects)
        folded_rejects = Counter()
        for key, value in rejects.items():
            folded_rejects.update({parent_reject_key(key): value})
        overall_rejects.update(folded_rejects)
        per_clone.append(
            {
                "name": name,
                "axis_value": clone["axis_value"],
                "reach_rate": reach,
                "stability_rate": stability,
                "block_wins": block_wins.get(name, 0),
                "comparable_blocks": len(comparable_blocks),
                "u0_share": (
                    float(sum(b.u0_ticks for b in block_data[name])) / float(sum(b.observed for b in block_data[name]))
                    if sum(b.observed for b in block_data[name]) > 0
                    else None
                ),
                "dominant_rejects": dict(folded_rejects.most_common(3)),
                "dominant_reject_details": dict(rejects.most_common(5)),
                "reliability_alert": reliability_flags[name],
            }
        )

    ranked = sorted(
        per_clone,
        key=lambda row: (
            row["reach_rate"] if row["reach_rate"] is not None else -1.0,
            row["stability_rate"] if row["stability_rate"] is not None else -1.0,
        ),
        reverse=True,
    )

    choke_counter = Counter({k: v for k, v in overall_rejects.items() if k != "dry"})
    dominant_choke = None
    dominant_choke_count = 0
    dominant_axis = None
    if choke_counter:
        dominant_choke, dominant_choke_count = choke_counter.most_common(1)[0]
    dominant_axis = dominant_choke_axis(dominant_choke, axis_key)

    next_action = {
        "status": "gather_more_data" if len(comparable_blocks) < min_blocks else "hold",
        "reason": "Comparable blocks are still below the promotion threshold.",
        "recommended_choke": dominant_choke,
        "recommended_axis": dominant_axis,
    }
    if any(row["reliability_alert"] for row in ranked):
        next_action = {
            "status": "fix_reliability",
            "reason": "U=0/data-starved behavior is still materially affecting one or more lanes.",
            "recommended_choke": dominant_choke,
            "recommended_axis": dominant_axis,
        }

    decision = {
        "status": "no_clear_winner",
        "winner": None,
        "reason": "Comparable blocks are not yet decisive.",
    }
    if ranked and len(comparable_blocks) >= min_blocks:
        best = ranked[0]
        runner = ranked[1] if len(ranked) > 1 else None
        block_win_rate = (
            float(best["block_wins"]) / float(len(comparable_blocks))
            if comparable_blocks
            else 0.0
        )
        reach_edge = (
            (best["reach_rate"] or 0.0) - ((runner["reach_rate"] or 0.0) if runner else 0.0)
        )
        stability_edge = (
            (best["stability_rate"] or 0.0) - ((runner["stability_rate"] or 0.0) if runner else 0.0)
        )
        if (
            block_win_rate >= required_block_win_rate
            and (best["reach_rate"] or 0.0) >= required_reach_edge
            and reach_edge >= required_reach_edge
            and (best["stability_rate"] or 0.0) >= required_stability_floor
            and stability_edge >= required_stability_edge
            and not best["reliability_alert"]
        ):
            decision = {
                "status": "clear_winner",
                "winner": best["name"],
                "reason": (
                    f"{best['name']} leads with reach {format_pct(best['reach_rate'])}, "
                    f"stability {format_pct(best['stability_rate'])}, "
                    f"and block wins {best['block_wins']}/{len(comparable_blocks)}."
                ),
            }
            next_action = {
                "status": "promotion_ready",
                "reason": str(decision.get("reason") or ""),
                "recommended_choke": dominant_choke,
                "recommended_axis": dominant_axis,
            }
    if (
        len(comparable_blocks) >= min_blocks
        and decision.get("status") != "clear_winner"
        and dominant_axis
    ):
        next_action = {
            "status": "shift_axis",
            "reason": f"No clear winner on the current axis; dominant remaining choke is {dominant_choke}.",
            "recommended_choke": dominant_choke,
            "recommended_axis": dominant_axis,
        }

    return {
        "generated_at": datetime.now().isoformat(sep=" "),
        "campaign_active": bool(campaign.get("ACTIVE", False)),
        "axis_key": axis_key,
        "freeze_main_unless_clear_winner": bool(campaign.get("FREEZE_MAIN_UNLESS_CLEAR_WINNER", True)),
        "promote_main_automatically": bool(campaign.get("PROMOTE_MAIN_AUTOMATICALLY", False)),
        "window_start": window_start.isoformat(sep=" "),
        "window_end": window_end.isoformat(sep=" "),
        "dwell_minutes": dwell_minutes,
        "block_minutes": block_minutes,
        "comparable_blocks": len(comparable_blocks),
        "required_blocks": min_blocks,
        "decision": decision,
        "overall_rejects": dict(overall_rejects.most_common()),
        "overall_reject_details": dict(overall_reject_details.most_common()),
        "dominant_choke": dominant_choke,
        "dominant_choke_count": dominant_choke_count,
        "dominant_next_axis": dominant_axis,
        "next_action": next_action,
        "clones": ranked,
    }


def render_text(summary: Dict[str, Any]) -> str:
    if summary.get("status") == "no_data":
        return summary["message"]

    lines = [
        (
            "Campaign summary: axis={axis} window={dwell}m blocks={blocks}/{required} "
            "decision={decision}"
        ).format(
            axis=summary.get("axis_key"),
            dwell=summary.get("dwell_minutes"),
            blocks=summary.get("comparable_blocks"),
            required=summary.get("required_blocks"),
            decision=summary.get("decision", {}).get("status"),
        ),
        "  " + str(summary.get("decision", {}).get("reason", "")),
        "  next_action={status} choke={choke} next_axis={axis} reason={reason}".format(
            status=((summary.get("next_action") or {}).get("status")),
            choke=summary.get("dominant_choke"),
            axis=summary.get("dominant_next_axis"),
            reason=((summary.get("next_action") or {}).get("reason")),
        ),
    ]
    for row in summary.get("clones", []):
        reject_text = ",".join(f"{k}:{v}" for k, v in row.get("dominant_rejects", {}).items()) or "none"
        lines.append(
            "  {name} value={value} reach={reach} stability={stability} wins={wins}/{blocks} u0={u0} reject={rejects}{alert}".format(
                name=row.get("name"),
                value=row.get("axis_value"),
                reach=format_pct(row.get("reach_rate")),
                stability=format_pct(row.get("stability_rate")),
                wins=row.get("block_wins"),
                blocks=row.get("comparable_blocks"),
                u0=format_pct(row.get("u0_share")),
                rejects=reject_text,
                alert=" ALERT_U0" if row.get("reliability_alert") else "",
            )
        )
    return "\n".join(lines)


def main() -> None:
    args = parse_args()
    summary = summarize(Path(args.base_root), Path(args.clone_root))
    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    if args.format == "json":
        print(json.dumps(summary, indent=2))
        return
    print(render_text(summary))


if __name__ == "__main__":
    main()
