# C:\ai_trading_bot_koko\managers\diagnostics_manager\activity_ticker.py
# Simple tail viewer for logs/activity_ticker.log (spawned as a separate console).

from __future__ import annotations

import argparse
import os
import time
import re
from pathlib import Path

_SETTINGS_RELOAD_RE = re.compile(r"\[settings_reload\]\s+changed=(.+)")


def _set_title(title: str) -> None:
    try:
        if os.name != "nt":
            return
        import ctypes  # type: ignore
        ctypes.windll.kernel32.SetConsoleTitleW(str(title))
    except Exception:
        return


def _extract_settings_indicator(line: str) -> str | None:
    try:
        m = _SETTINGS_RELOAD_RE.search(str(line or ""))
        if not m:
            return None
        changed = str(m.group(1) or "").strip()
        return changed or None
    except Exception:
        return None


def _render_title(base_title: str, indicator: str | None) -> str:
    title = str(base_title or "MM18 Activity")
    if indicator:
        title = f"{title} | settings: {indicator}"
    # Keep console titles readable on Windows.
    return title[:240]


def _read_last_lines(path: Path, n: int = 200) -> list[str]:
    try:
        if not path.exists():
            return []
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 8192
            data = b""
            while size > 0 and data.count(b"\n") <= n:
                step = min(block, size)
                size -= step
                f.seek(size)
                data = f.read(step) + data
            lines = data.splitlines()[-n:]
        return [ln.decode("utf-8", errors="replace") for ln in lines]
    except Exception:
        return []


def tail(path: Path, title: str, poll_sec: float = 0.20) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    current_indicator: str | None = None
    _set_title(_render_title(title, current_indicator))

    # Print the tail so the window isn't empty.
    for ln in _read_last_lines(path, n=120):
        maybe_indicator = _extract_settings_indicator(ln)
        if maybe_indicator:
            current_indicator = maybe_indicator
        print(ln)
    _set_title(_render_title(title, current_indicator))
    if current_indicator:
        print(f"[settings_indicator] active={current_indicator}")

    # Open in a+ to create if missing.
    with open(path, "a+", encoding="utf-8") as f:
        f.seek(0, os.SEEK_END)
        while True:
            line = f.readline()
            if line:
                clean = line.rstrip("\n")
                maybe_indicator = _extract_settings_indicator(clean)
                if maybe_indicator and maybe_indicator != current_indicator:
                    current_indicator = maybe_indicator
                    _set_title(_render_title(title, current_indicator))
                    print(f"[settings_indicator] active={current_indicator}")
                print(clean)
            else:
                time.sleep(poll_sec)


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--path", default=os.environ.get("MM_ACTIVITY_LOG_PATH", "logs/activity_ticker.log"))
    ap.add_argument("--title", default=os.environ.get("MM_ACTIVITY_TITLE", "MM18 Activity"))
    args = ap.parse_args()

    p = Path(str(args.path))
    if not p.is_absolute():
        p = Path.cwd() / p

    tail(p, str(args.title))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
