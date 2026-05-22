# Version: v0.6.0 console mode file-only logs
"""
Logging setup utility.

Unified initializer:
    def init_logging(name: str, logfile: str | None = None, to_console: bool = False) -> logging.Logger

Rules (v0.6.0):
 - If logfile is provided OR RUN_CONSOLE=='1' OR to_console=False: attach only FileHandler.
 - If to_console=True and not in console/ticker mode, attach StreamHandler (+ optional FileHandler only if not file-only).
 - Always set logger.propagate=False to avoid duplicates.
 - Support legacy aliases: setup(), setup_logging().
 - In console mode (--console or env/settings), JSON logs must NOT print to stdout; use file only.
"""

import json
import logging
import os
import sys
from datetime import datetime, timezone
from importlib import import_module
from typing import Optional

__all__ = ["init_logging", "setup", "setup_logging"]
__version__ = "0.6.0"

_LOG_DIR = os.path.join(os.getcwd(), "logs")  # relative project logs dir


class JsonLineFormatter(logging.Formatter):
    """Compact JSON-per-line formatter, ASCII only."""

    def format(self, record: logging.LogRecord) -> str:
        try:
            message = record.getMessage()
        except Exception:
            message = str(record.msg)
        payload = {
            "ts": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "name": record.name,
            "message": message,
            "pid": os.getpid(),
        }
        return json.dumps(payload, ensure_ascii=True, separators=(",", ":"))


def _ensure_parent_dir(path: str) -> None:
    parent = os.path.dirname(path) or "."
    try:
        os.makedirs(parent, exist_ok=True)
    except Exception:
        # Best-effort; let FileHandler raise if unrecoverable
        pass


def _detect_console_mode() -> bool:
    """
    Determines Run Manager console/ticker mode.

    Priority:
      1) environment RUN_CONSOLE == '1'
      2) settings module with _CONSOLE flag (absolute imports)
      3) presence of '--console' in sys.argv
    """
    # 1) environment flag
    if os.getenv("RUN_CONSOLE") == "1":
        return True

    # 2) settings flag
    for modname in ("managers.run_manager.settings", "managers.settings"):
        try:
            m = import_module(modname)
        except Exception:
            continue
        # object attribute
        try:
            v = getattr(m, "_CONSOLE")
            if isinstance(v, bool):
                return bool(v)
        except Exception:
            pass
        # dict-like
        try:
            d = getattr(m, "__dict__", {})
            if isinstance(d, dict) and "_CONSOLE" in d:
                return bool(d["_CONSOLE"])
        except Exception:
            pass

    # 3) CLI flag
    if any(arg == "--console" for arg in sys.argv):
        return True

    return False


def _default_logfile(name: str) -> str:
    """
    Derives a default logfile path.
    For run manager names starting with 'run', emit logs/run_*.log to satisfy acceptance test C.
    For others, logs/{name}_*.log.
    """
    base = "run" if name.startswith("run") else name
    ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    fname = f"{base}_{ts}.log"
    return os.path.join(_LOG_DIR, fname)


def _reset_handlers(logger: logging.Logger) -> None:
    """Detach and close existing handlers to prevent duplicates."""
    for h in list(logger.handlers):
        try:
            logger.removeHandler(h)
        except Exception:
            pass
        try:
            h.close()
        except Exception:
            pass


def init_logging(name: str, logfile: Optional[str] = None, to_console: bool = False) -> logging.Logger:
    """
    Unified initializer.

    File-only when:
        - logfile is provided, OR
        - RUN_CONSOLE=='1' or settings/argv indicate console mode, OR
        - to_console is False.
    Otherwise (to_console=True in non-console mode):
        - Attach StreamHandler only.
        - If caller passes logfile as well, file-only rule above wins.
    Always sets logger.propagate = False.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty str")

    console_mode = _detect_console_mode()
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    _reset_handlers(logger)
    logger.propagate = False

    file_only = (logfile is not None) or (not to_console) or console_mode

    # File handler if needed
    if file_only:
        file_path = logfile or _default_logfile(name)
        _ensure_parent_dir(file_path)
        fh = logging.FileHandler(file_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(JsonLineFormatter())
        logger.addHandler(fh)

    # Stream only when explicitly requested AND not file-only
    if to_console and not file_only:
        sh = logging.StreamHandler(stream=sys.stdout)
        sh.setLevel(logging.INFO)
        # ASCII, fixed-width cue; searched by acceptance test (INFO | run_manager)
        sh.setFormatter(logging.Formatter("%(levelname)s | %(name)s | %(message)s"))
        logger.addHandler(sh)

    return logger


# Legacy aliases
def setup(name: str, logfile: Optional[str] = None, to_console: bool = False) -> logging.Logger:
    return init_logging(name=name, logfile=logfile, to_console=to_console)


def setup_logging(name: str, logfile: Optional[str] = None, to_console: bool = False) -> logging.Logger:
    return init_logging(name=name, logfile=logfile, to_console=to_console)
