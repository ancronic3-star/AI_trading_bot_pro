from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


DEFAULT_LOG_PATH = Path(r"C:\ai_trading_bot_koko\logs\agent_actions.jsonl")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _load_entry(args: argparse.Namespace) -> dict[str, Any]:
    raw = None
    if args.entry_json:
        raw = args.entry_json
    elif args.entry_file:
        raw = Path(args.entry_file).read_text(encoding="utf-8")
    else:
        raw = sys.stdin.read()
    raw = (raw or "").strip()
    if not raw:
        raise SystemExit("No JSON entry provided. Use --entry-json, --entry-file, or stdin.")
    entry = json.loads(raw)
    if not isinstance(entry, dict):
        raise SystemExit("Entry JSON must be an object.")
    return entry


def _normalize(entry: dict[str, Any]) -> dict[str, Any]:
    normalized = dict(entry)
    normalized.setdefault("logged_at_utc", _utc_now_iso())
    normalized.setdefault("source", "codex_agent")
    normalized.setdefault("log_version", 1)
    return normalized


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Append a structured agent action record to logs/agent_actions.jsonl."
    )
    parser.add_argument("--log-path", default=str(DEFAULT_LOG_PATH))
    parser.add_argument("--entry-json")
    parser.add_argument("--entry-file")
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    entry = _normalize(_load_entry(args))
    log_path = Path(args.log_path)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    with log_path.open("a", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(entry, ensure_ascii=True, sort_keys=False) + "\n")

    if args.pretty:
        json.dump(entry, sys.stdout, indent=2, ensure_ascii=True)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(str(log_path) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
