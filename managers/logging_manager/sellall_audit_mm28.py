from __future__ import annotations

import contextlib
import io
import json
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

_LAST_AUDIT_DIR: Path | None = None


def _root_from_here() -> Path:
    return Path(__file__).resolve().parents[2]


def _ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def _ts() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def _utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _write_text(path: Path, text: str) -> None:
    path.write_text(text, encoding="utf-8")


def _copy_if_exists(src: Path, dst: Path) -> None:
    if src.exists():
        dst.write_bytes(src.read_bytes())


def _capture_pnl_snapshot() -> str:
    import importlib

    mod = importlib.import_module("managers.logging_manager.diag_pnl_snapshot")
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        if hasattr(mod, "print_pnl_snapshot"):
            mod.print_pnl_snapshot()
        elif hasattr(mod, "main"):
            try:
                mod.main()
            except SystemExit:
                pass
        else:
            raise RuntimeError("diag_pnl_snapshot has neither print_pnl_snapshot() nor main()")
    return buf.getvalue()


def _append_update_logs(root: Path, payload: dict[str, Any], md_lines: list[str]) -> None:
    updates = root / "logs" / "updates"
    _ensure_dir(updates)
    jsonl = updates / "UPDATE_LOG.jsonl"
    md = updates / "UPDATE_LOG.md"
    with jsonl.open("a", encoding="utf-8") as f:
        f.write(json.dumps(payload, separators=(",", ":")) + "\n")
    with md.open("a", encoding="utf-8") as f:
        for line in md_lines:
            f.write(line + "\n")


def _sidecar_paths(root: Path) -> list[Path]:
    return [
        root / "live_snapshot.json",
        root / "tracked_account_snapshot.json",
        root / "decision_replay_snapshot.json",
        root / "wm3_support_snapshot.json",
    ]


def begin_sellall_audit() -> str:
    global _LAST_AUDIT_DIR

    root = _root_from_here()
    updates = root / "logs" / "updates"
    audit_dir = updates / f"sellall_audit_{_ts()}"
    _ensure_dir(audit_dir)
    _LAST_AUDIT_DIR = audit_dir

    _copy_if_exists(root / "run_settings.json", audit_dir / "run_settings_pre.json")
    for p in _sidecar_paths(root):
        _copy_if_exists(p, audit_dir / f"pre_{p.name}")

    pre_err = ""
    try:
        pre_txt = _capture_pnl_snapshot()
    except Exception as exc:
        pre_err = f"PRE_PNL_CAPTURE_ERROR: {type(exc).__name__}: {exc}\n"
        pre_txt = pre_err
    _write_text(audit_dir / "pnl_pre.txt", pre_txt)
    _write_text(audit_dir / "begin_summary.txt", f"started_at_utc={_utc_now_iso()}\npre_capture_error={bool(pre_err)}\n")
    return str(audit_dir)


def end_sellall_audit(audit_dir: str | None = None) -> str:
    global _LAST_AUDIT_DIR

    root = _root_from_here()
    if audit_dir:
        path = Path(audit_dir)
    elif _LAST_AUDIT_DIR is not None:
        path = _LAST_AUDIT_DIR
    else:
        path = root / "logs" / "updates" / f"sellall_audit_{_ts()}"
        _ensure_dir(path)

    time.sleep(2.0)

    _copy_if_exists(root / "run_settings.json", path / "run_settings_post.json")
    for p in _sidecar_paths(root):
        _copy_if_exists(p, path / f"post_{p.name}")

    post_err = ""
    try:
        post_txt = _capture_pnl_snapshot()
    except Exception as exc:
        post_err = f"POST_PNL_CAPTURE_ERROR: {type(exc).__name__}: {exc}\n"
        post_txt = post_err
    _write_text(path / "pnl_post.txt", post_txt)

    summary_lines = [
        f"sellall_audit_dir={path}",
        f"completed_at_utc={_utc_now_iso()}",
        f"post_capture_error={bool(post_err)}",
    ]
    _write_text(path / "summary.txt", "\n".join(summary_lines) + "\n")

    payload = {
        "ts": datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "type": "sell_all_audit",
        "path": str(path),
        "pre_pnl": str(path / "pnl_pre.txt"),
        "post_pnl": str(path / "pnl_post.txt"),
        "mechanic": "MM28",
    }
    md_lines = [
        "",
        f"## {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "- type: sell_all_audit",
        f"- path: {path}",
        f"- pre_pnl: {path / 'pnl_pre.txt'}",
        f"- post_pnl: {path / 'pnl_post.txt'}",
        "- mechanic: MM28",
    ]
    _append_update_logs(root, payload, md_lines)
    return str(path)

