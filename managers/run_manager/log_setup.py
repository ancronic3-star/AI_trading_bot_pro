# Version: v0.6.0 console mode file-only logs
"""
Logging setup utility.

Implements a unified initializer:
    def init_logging(name: str, logfile: str | None = None, to_console: bool = False) -> logging.Logger

Rules:
 - If to_console=True and not in Run Manager console mode, attach StreamHandler + optional FileHandler.
 - If to_console=False OR if settings['_CONSOLE']=True, then attach only FileHandler. No StreamHandler.
 - Always set logger.propagate=False to avoid duplicates.
 - Support legacy aliases: setup(), setup_logging().
 - In console mode (--console), JSON logs must NOT print to stdout; they must go only to logfile.
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
    Determines Run Manager console mode.

    Priority:
      1) settings module with _CONSOLE flag (absolute imports)
      2) presence of '--console' in sys.argv
    """
    for modname in ("managers.run_manager.settings", "managers.settings"):
        try:
            m = import_module(modname)
        except Exception:
            continue
        try:
            # object attribute
            if isinstance(getattr(m, "_CONSOLE"), bool):
                return bool(getattr(m, "_CONSOLE"))
        except Exception:
            pass
        try:
            # dict-like
            d = getattr(m, "__dict__", {})
            if isinstance(d, dict) and "_CONSOLE" in d:
                return bool(d["_CONSOLE"])
        except Exception:
            pass

    # Fallback to CLI flag
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

    If to_console is True and not in console mode:
        - Attach StreamHandler to stdout.
        - If logfile is provided, also attach FileHandler.
    If to_console is False OR if console mode is active:
        - Attach only FileHandler (to logfile if provided, else a default path).
        - Do NOT attach StreamHandler.
    Always sets logger.propagate = False.
    """
    if not isinstance(name, str) or not name:
        raise ValueError("name must be a non-empty str")

    console_mode = _detect_console_mode()

    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)
    _reset_handlers(logger)
    logger.propagate = False

    # Determine if a file handler is required
    need_file = (not to_console) or console_mode or (logfile is not None)
    if need_file:
        file_path = logfile or _default_logfile(name)
        _ensure_parent_dir(file_path)
        fh = logging.FileHandler(file_path, encoding="utf-8")
        fh.setLevel(logging.INFO)
        fh.setFormatter(JsonLineFormatter())
        logger.addHandler(fh)

    # Stream only when explicitly requested AND not in console mode
    if to_console and not console_mode:
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
