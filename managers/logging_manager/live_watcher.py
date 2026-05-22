# managers/logging_manager/live_watcher.py
# KOKO Live Watcher (robust autosource)
# - Tails the most relevant *active* log file under <repo>/logs
# - Prints activity lines in real-time (order/cancel/reject/ticks)
# - Designed to be launched from the Menu "A Start run loop" every time.

from __future__ import annotations

import argparse
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable, Optional


# Default: broad enough to prove "it's alive" even if order lines aren't present.
DEFAULT_FILTER_REGEX = (
    r"(\[BUY\]|\[SELL\]|\[TP\]|\[SL\]|\[TP_INV\]|\[CANCEL\]|\[REJECT\]|\[REPLACE\]|\[AMEND\]|"
    r"autobuy|placing|placed|cancel|cancell|canceled|cancelled|reject|replac|amend|resubmit|retry|"
    r"failed|error|err=|exception|traceback|order_id|client_order|client_oid|fill|FILL|stop|"
    r"\btick\s+\d+\s+start\b|No pairs pass filters|MODE=)"
)


@dataclass(frozen=True)
class SourcePick:
    path: Path
    reason: str
    probe_sec: float


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _safe_print(s: str) -> None:
    try:
        sys.stdout.write(s + "\n")
        sys.stdout.flush()
    except Exception:
        # Never crash the watcher because stdout is broken.
        pass


def _repo_root() -> Path:
    # <ROOT>/managers/logging_manager/live_watcher.py -> parents: logging_manager, managers, <ROOT>
    return Path(__file__).resolve().parents[2]


def _logs_dir(root: Path) -> Path:
    return root / "logs"


def _read_json_maybe(p: Path) -> dict:
    try:
        import json

        return json.loads(p.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return {}


def _resolve_path(root: Path, p: str) -> Path:
    pp = Path(p)
    if not pp.is_absolute():
        pp = (root / pp).resolve()
    return pp


def _normalize_pattern(pat: str) -> tuple[str, bool]:
    """
    Guard against accidental double-escaping (common when a pattern is passed through shells).
    Example bad:  \\[BUY\\]   (won't match [BUY])
    We collapse \\ -> \ when we see strong indicators.
    """
    if ("\\\\[" in pat) or ("\\\\]" in pat) or ("\\\\b" in pat) or ("\\\\s" in pat):
        return pat.replace("\\\\", "\\"), True
    return pat, False


def _candidate_logs(logs: Path) -> list[Path]:
    if not logs.exists():
        return []
    out: list[Path] = []
    seen: set[str] = set()

    # Priority patterns first, then all *.log as a net.
    patterns = [
        "run_session_*.log",
        "spawn_*.log",
        "run_loop.log",
        "*.log",
    ]

    for pat in patterns:
        for p in logs.glob(pat):
            try:
                if not p.is_file():
                    continue
                name = p.name.lower()
                # Avoid watching watcher output / debug logs.
                if name.startswith("watcher_") or name.startswith("watcher_debug_"):
                    continue
                rp = str(p.resolve())
                if rp in seen:
                    continue
                seen.add(rp)
                out.append(p)
            except Exception:
                continue

    return out


def _stat_mtime_size(p: Path) -> tuple[float, int]:
    st = p.stat()
    return float(st.st_mtime), int(st.st_size)


def _probe_candidates(cands: list[Path], probe_sec: float) -> list[tuple[Path, float, int, int, float]]:
    """
    Returns rows:
      (path, mtime2, size2, delta_size, delta_mtime)
    where delta_* are compared to a snapshot at t0.
    """
    snap1: dict[Path, tuple[float, int]] = {}
    for p in cands:
        try:
            snap1[p] = _stat_mtime_size(p)
        except Exception:
            continue

    # Probe window (allows us to detect the file that is actually growing)
    time.sleep(max(0.0, probe_sec))

    rows: list[tuple[Path, float, int, int, float]] = []
    for p, (m1, s1) in snap1.items():
        try:
            m2, s2 = _stat_mtime_size(p)
            ds = int(max(0, s2 - s1))
            dm = float(m2 - m1)
            rows.append((p, m2, s2, ds, dm))
        except Exception:
            continue

    return rows


def _best_from_probe(rows: list[tuple[Path, float, int, int, float]], *, recent_sec: float) -> Optional[tuple[Path, float, int, int, float]]:
    if not rows:
        return None

    now = time.time()

    # Prefer files that are actively growing in the probe window.
    growing = [r for r in rows if r[3] > 0]
    if growing:
        growing_recent = [r for r in growing if (now - r[1]) <= recent_sec]
        pool = growing_recent if growing_recent else growing
        return max(pool, key=lambda r: (r[3], r[1], r[2]))

    # Else pick most recently modified (prefer "recent")
    recent = [r for r in rows if (now - r[1]) <= recent_sec]
    pool = recent if recent else rows
    return max(pool, key=lambda r: (r[1], r[2]))


def _pick_preferred(args_source: Optional[str]) -> Optional[SourcePick]:
    root = _repo_root()
    logs = _logs_dir(root)

    # 1) CLI arg
    if args_source:
        return SourcePick(_resolve_path(root, args_source), "arg", 0.0)

    # 2) Env var
    env_src = os.environ.get("KOKO_WATCH_SOURCE_LOG", "").strip()
    if env_src:
        return SourcePick(_resolve_path(root, env_src), "env", 0.0)

    # 3) run_active.json hint (if present)
    run_active = logs / "run_active.json"
    if run_active.exists():
        j = _read_json_maybe(run_active)
        for k in ("source_log", "run_log", "log", "log_path", "path"):
            v = j.get(k)
            if isinstance(v, str) and v.strip():
                p = _resolve_path(root, v.strip())
                return SourcePick(p, "run_active.json", 0.0)

    return None


def _choose_source(args_source: Optional[str], *, probe_sec: float, recent_sec: float) -> SourcePick:
    root = _repo_root()
    logs = _logs_dir(root)

    preferred = _pick_preferred(args_source)
    cands = _candidate_logs(logs)

    # Ensure preferred is part of candidates for probing.
    if preferred and preferred.path.exists():
        if preferred.path not in cands:
            cands.insert(0, preferred.path)

    # If no candidates exist, fall back.
    if not cands:
        return SourcePick(logs / "run_loop.log", "fallback(run_loop.log)", probe_sec)

    # Probe for growth; this lets us "lock onto" the actively written file.
    rows = _probe_candidates(cands, probe_sec)
    best = _best_from_probe(rows, recent_sec=recent_sec)

    # Map for deltas.
    delta_size: dict[Path, int] = {p: ds for (p, _m2, _s2, ds, _dm) in rows}

    if preferred:
        # If preferred exists AND is growing, keep it.
        if preferred.path.exists() and delta_size.get(preferred.path, 0) > 0:
            return SourcePick(preferred.path, preferred.reason, probe_sec)

        # If preferred is not growing but something else is, switch.
        if best and best[0] != preferred.path and delta_size.get(best[0], 0) > 0:
            ds = delta_size.get(best[0], 0)
            return SourcePick(best[0], f"{preferred.reason}->auto(growing:{ds}B/{probe_sec:.1f}s)", probe_sec)

        # Otherwise (no clear winner), stick to preferred even if stale.
        return SourcePick(preferred.path, preferred.reason, probe_sec)

    if best:
        ds = int(best[3])
        reason = "auto(recent)"
        if ds > 0:
            reason = f"auto(growing:{ds}B/{probe_sec:.1f}s)"
        return SourcePick(best[0], reason, probe_sec)

    return SourcePick(logs / "run_loop.log", "fallback(run_loop.log)", probe_sec)


def _file_meta(p: Path) -> tuple[str, int, int]:
    try:
        st = p.stat()
        mtime_iso = datetime.fromtimestamp(st.st_mtime, tz=timezone.utc).isoformat(timespec="seconds")
        age = int(_utc_now().timestamp() - st.st_mtime)
        size = int(st.st_size)
        return mtime_iso, age, size
    except Exception:
        return "missing", 0, 0


def _read_tail(path: Path, max_lines: int) -> list[str]:
    # Read last max_lines lines without loading the whole file.
    if max_lines <= 0:
        return []
    try:
        with path.open("rb") as f:
            f.seek(0, os.SEEK_END)
            end = f.tell()
            block = 4096
            data = b""
            pos = end
            lines_found = 0
            while pos > 0 and lines_found <= max_lines:
                read_sz = block if pos >= block else pos
                pos -= read_sz
                f.seek(pos, os.SEEK_SET)
                chunk = f.read(read_sz)
                data = chunk + data
                lines_found = data.count(b"\n")
            text = data.decode("utf-8", errors="replace")
            return text.splitlines()[-max_lines:]
    except Exception:
        return []


def _compile_pattern(no_filter: bool, pattern: str) -> Optional[re.Pattern[str]]:
    if no_filter:
        return None
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        # If pattern is invalid, fall back to no filter (better noisy than silent).
        return None


def _match_lines(lines: Iterable[str], rx: Optional[re.Pattern[str]]) -> list[str]:
    if rx is None:
        return list(lines)
    return [ln for ln in lines if rx.search(ln)]


def main(argv: Optional[list[str]] = None) -> int:
    ap = argparse.ArgumentParser(description="Tail a KOKO log and print activity lines in real time.")
    ap.add_argument(
        "--source-log",
        dest="source_log",
        default=None,
        help="Log file path to tail (absolute or relative to repo root). If omitted, auto-selects an active log under ./logs.",
    )
    ap.add_argument("--lines", type=int, default=200, help="How many lines to show on startup.")
    ap.add_argument("--sleep", type=float, default=0.25, help="Polling interval in seconds.")
    ap.add_argument("--no-filter", action="store_true", help="Show all lines (no pattern filtering).")
    ap.add_argument("--pattern", default=DEFAULT_FILTER_REGEX, help="Regex used to filter lines (ignored with --no-filter).")
    ap.add_argument(
        "--probe-sec",
        type=float,
        default=3.5,
        help="Seconds to probe candidate logs for growth when auto-selecting. (Higher = more reliable, slower startup.)",
    )
    ap.add_argument(
        "--recent-sec",
        type=float,
        default=900.0,
        help="Consider logs modified within this many seconds as 'recent' during auto-selection.",
    )
    ap.add_argument(
        "--auto-rescan-sec",
        type=float,
        default=30.0,
        help="If selected log stops updating for this many seconds, rescan and switch to the currently active log (0 disables).",
    )

    args = ap.parse_args(argv)

    # Normalize pattern if needed.
    norm_pat, changed = _normalize_pattern(str(args.pattern))
    args.pattern = norm_pat

    # Select source.
    if args.source_log:
        pick = SourcePick(_resolve_path(_repo_root(), args.source_log), "arg", 0.0)
    else:
        _safe_print(f"[watcher] probing logs for {args.probe_sec:.1f}s to find the active source...")
        pick = _choose_source(None, probe_sec=float(args.probe_sec), recent_sec=float(args.recent_sec))

    src = pick.path
    mtime_iso, age_sec, size = _file_meta(src)

    _safe_print("=" * 60)
    _safe_print("KOKO LIVE WATCHER")
    _safe_print(f"source_log: {src}")
    _safe_print(f"last_modified_utc: {mtime_iso}  age_sec: {age_sec}")
    _safe_print(f"size_bytes: {size}")
    _safe_print(f"source_reason: {pick.reason}")
    _safe_print(f"probe_sec: {pick.probe_sec:.1f}")
    if args.no_filter:
        _safe_print("filter: OFF (show all lines)")
    else:
        if changed:
            _safe_print("filter: (normalized double-escapes)")
        _safe_print(f"filter: {args.pattern}")
    _safe_print("=" * 60)

    if not src.exists():
        _safe_print(f"ERROR: source_log does not exist: {src}")
        _safe_print("Tip: set KOKO_WATCH_SOURCE_LOG or pass --source-log <path>")
        return 2

    rx = _compile_pattern(bool(args.no_filter), str(args.pattern))

    # Startup tail
    tail = _read_tail(src, int(args.lines))
    for ln in _match_lines(tail, rx):
        _safe_print(ln)

    # Follow
    try:
        with src.open("r", encoding="utf-8", errors="replace") as f:
            f.seek(0, os.SEEK_END)
            last_size = f.tell()

            last_mtime = 0.0
            try:
                last_mtime = src.stat().st_mtime
            except Exception:
                last_mtime = time.time()

            last_change_ts = time.time()

            while True:
                time.sleep(max(float(args.sleep), 0.05))

                # Detect truncate/rotate.
                try:
                    st = src.stat()
                    if st.st_size < last_size:
                        f.seek(0, os.SEEK_SET)
                        last_size = 0
                    if st.st_mtime != last_mtime:
                        last_mtime = float(st.st_mtime)
                        last_change_ts = time.time()
                except Exception:
                    pass

                chunk = f.read()
                if chunk:
                    last_size = f.tell()
                    lines = chunk.splitlines()
                    for ln in _match_lines(lines, rx):
                        _safe_print(ln)

                # Auto-rescan if the chosen file is no longer changing.
                if float(args.auto_rescan_sec) > 0:
                    idle = time.time() - last_change_ts
                    if idle >= float(args.auto_rescan_sec):
                        # Rescan quickly (short probe).
                        new_pick = _choose_source(None, probe_sec=1.5, recent_sec=float(args.recent_sec))
                        if new_pick.path != src and new_pick.path.exists():
                            _safe_print("")
                            _safe_print(f"[watcher] source appears idle ({int(idle)}s). switching -> {new_pick.path} ({new_pick.reason})")
                            try:
                                f.close()
                            except Exception:
                                pass
                            src = new_pick.path
                            mtime_iso, age_sec, size = _file_meta(src)
                            _safe_print("-" * 60)
                            _safe_print(f"source_log: {src}")
                            _safe_print(f"last_modified_utc: {mtime_iso}  age_sec: {age_sec}")
                            _safe_print(f"size_bytes: {size}")
                            _safe_print(f"source_reason: {new_pick.reason}")
                            _safe_print("-" * 60)
                            f = src.open("r", encoding="utf-8", errors="replace")
                            f.seek(0, os.SEEK_END)
                            last_size = f.tell()
                            try:
                                last_mtime = src.stat().st_mtime
                            except Exception:
                                last_mtime = time.time()
                            last_change_ts = time.time()

    except KeyboardInterrupt:
        return 0
    except Exception as e:
        _safe_print(f"WATCHER_FATAL: {type(e).__name__}: {e}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())

