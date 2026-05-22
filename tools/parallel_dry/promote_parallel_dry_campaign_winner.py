from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, Dict, Optional


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Promote a clear parallel dry campaign winner into the main lane.")
    p.add_argument("--base-root", default=r"C:\ai_trading_bot_koko")
    p.add_argument("--status-json", default=r"C:\ai_trading_bot_koko\logs\parallel_dry_campaign_status.json")
    p.add_argument("--write", action="store_true", help="Apply the promotion to run_settings.json.")
    return p.parse_args()


def load_json(path: Path) -> Dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, data: Dict[str, Any]) -> None:
    path.write_text(json.dumps(data, indent=2), encoding="utf-8")


def find_winner_entry(summary: Dict[str, Any], winner_name: str) -> Optional[Dict[str, Any]]:
    for row in summary.get("clones", []):
        if str(row.get("name")) == winner_name:
            return row
    return None


def main() -> None:
    args = parse_args()
    base_root = Path(args.base_root)
    status_path = Path(args.status_json)
    settings_path = base_root / "run_settings.json"

    if not status_path.exists():
        raise SystemExit(f"Campaign status artifact missing: {status_path}")
    if not settings_path.exists():
        raise SystemExit(f"Main run settings missing: {settings_path}")

    summary = load_json(status_path)
    settings = load_json(settings_path)
    campaign = settings.get("PARALLEL_DRY_CAMPAIGN") or {}
    if not isinstance(campaign, dict):
        raise SystemExit("PARALLEL_DRY_CAMPAIGN is missing or invalid in run_settings.json")

    decision = summary.get("decision") or {}
    if str(decision.get("status")) != "clear_winner":
        print("No promotion applied: campaign has no clear winner yet.")
        print(str(decision.get("reason") or "Comparable blocks are not yet decisive."))
        return

    winner_name = str(decision.get("winner") or "").strip()
    winner = find_winner_entry(summary, winner_name)
    if not winner:
        raise SystemExit(f"Winner '{winner_name}' not found in campaign summary.")

    axis_key = str(summary.get("axis_key") or campaign.get("AXIS_KEY") or campaign.get("AXIS_NAME") or "").strip()
    axis_mode = str(campaign.get("AXIS_MODE") or "setting").strip()
    if axis_mode != "setting":
        raise SystemExit(f"Promotion helper only supports AXIS_MODE=setting, got: {axis_mode}")
    if not axis_key:
        raise SystemExit("No axis key found for promotion.")

    axis_value = winner.get("axis_value")
    current_value = settings.get(axis_key)
    freeze = bool(campaign.get("FREEZE_MAIN_UNLESS_CLEAR_WINNER", True))

    print(f"Campaign winner: {winner_name}")
    print(f"Axis: {axis_key}")
    print(f"Current main value: {current_value}")
    print(f"Winner value: {axis_value}")
    print(f"Freeze main unless clear winner: {freeze}")
    print(str(decision.get("reason") or ""))

    if not args.write:
        print("Dry run only. Re-run with --write to apply this promotion to run_settings.json.")
        return

    settings[axis_key] = axis_value
    save_json(settings_path, settings)
    print(f"Applied promotion: {axis_key} -> {axis_value}")


if __name__ == "__main__":
    main()
