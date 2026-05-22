# managers/process_manager/spawn.py
# Public API:
#   launch_detached(python_exe, args, logfile_path) -> dict
#   launch_console(python_exe, args, logfile_path) -> dict
#   spawn_console_tail(logfile_path, title='') -> dict
#   write_sentinel(logfile_path, label) -> None
#   await_pid_alive(pid, timeout_s=5.0) -> bool
#   await_log_activity(logfile_path, min_bytes=1, timeout_s=5.0) -> bool
#   is_alive(pid) -> bool
#   kill(pid) -> bool
#
# Windows-only. ASCII only. Env pass-through. No nested menus.
# Headless: DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP with stdout/stderr -> logfile.
# Console:  CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP with visible child console.
# Tail:     CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP PowerShell Get-Content -Wait viewer.

from __future__ import annotations

import os
import sys
import time
import signal
import ctypes
from ctypes import wintypes
from pathlib import Path
import subprocess

__all__ = [
    "launch_detached",
    "launch_console",
    "spawn_console_tail",
    "write_sentinel",
    "await_pid_alive",
    "await_log_activity",
    "is_alive",
    "kill",
    "ProcessManagerError",
    "ProcessLaunchError",
]

# ---- Errors ----

class ProcessManagerError(Exception):
    pass

class ProcessLaunchError(ProcessManagerError):
    pass

# ---- Windows guard and constants ----

if os.name != "nt":
    raise ProcessManagerError("process_manager is Windows-only.")

DETACHED_PROCESS = 0x00000008
CREATE_NEW_PROCESS_GROUP = 0x00000200
CREATE_NEW_CONSOLE = 0x00000010
STILL_ACTIVE = 259

# ---- Utils ----

def _project_root() -> Path:
    # managers/process_manager/spawn.py -> parents[2] == project root
    return Path(__file__).resolve().parents[2]

def _strftime_path(p: str | Path) -> Path:
    s = str(p)
    try:
        s = time.strftime(s)
    except Exception:
        pass
    pt = Path(s)
    if not pt.parent.exists():
        pt.parent.mkdir(parents=True, exist_ok=True)
    return pt

def _guard_no_nested_menu(args: list[str]) -> None:
    joined = " ".join(str(a).lower() for a in (args or []))
    if "menu_manager" in joined:
        raise ProcessLaunchError("Refusing to launch menu_manager (no nested menus).")

def _sanitize_exe(python_exe: str) -> str:
    exe = str(python_exe).strip()
    if (exe.startswith('"') and exe.endswith('"')) or (exe.startswith("'") and exe.endswith("'")):
        exe = exe[1:-1]
    if not os.path.isfile(exe) or not exe.lower().endswith(".exe"):
        raise OSError("invalid python_exe")
    return exe

def _open_log(logfile: Path):
    # Append in binary to avoid encoding issues; parent ensured in _strftime_path
    return open(logfile, "ab", buffering=0)

def _write_pid_file(logfile: Path, pid: int) -> str:
    pidfile = str(logfile) + ".pid"
    try:
        Path(pidfile).write_text(str(pid), encoding="utf-8")
    except Exception:
        pass
    return pidfile

def _safe_args(args: list[str]) -> list[str]:
    out = []
    for a in args or []:
        s = str(a).replace("\r", " ").replace("\n", " ")
        out.append(s)
    return out

def _try_log_line(log_path: Path, line: str) -> None:
    try:
        with _open_log(log_path) as lf:
            lf.write((line + "\n").encode("utf-8", "replace"))
    except Exception:
        pass

# ---- Sentinels and waits ----

def write_sentinel(logfile_path: str | Path, label: str) -> None:
    """Pre-create logfile and write a single sentinel line."""
    logp = _strftime_path(logfile_path)
    ts = time.strftime("%Y-%m-%d %H:%M:%S")
    _try_log_line(logp, f"[{ts}] [SPAWN_START] {label}")

def await_pid_alive(pid: int, timeout_s: float = 5.0) -> bool:
    """Poll liveness until timeout."""
    t0 = time.time()
    while time.time() - t0 < float(timeout_s):
        if is_alive(pid):
            return True
        time.sleep(0.05)
    return is_alive(pid)

def await_log_activity(logfile_path: str | Path, min_bytes: int = 1, timeout_s: float = 5.0) -> bool:
    """Wait until logfile size >= min_bytes or timeout. Returns True on activity."""
    logp = _strftime_path(logfile_path)
    t0 = time.time()
    last = logp.stat().st_size if logp.exists() else 0
    target = max(int(min_bytes), 0)
    while time.time() - t0 < float(timeout_s):
        if logp.exists():
            sz = logp.stat().st_size
            if sz >= target and sz > last:
                return True
            last = sz
        time.sleep(0.05)
    if logp.exists():
        return logp.stat().st_size >= target
    return False

# ---- Public API ----

def launch_detached(python_exe: str, args: list[str], logfile_path: str | Path) -> dict:
    """
    Headless mode: no visible console. Stdout/stderr -> logfile.
    Returns dict: {"pid": int, "logfile": str, "pidfile": str}.
    """
    exe = _sanitize_exe(python_exe)
    logfile = _strftime_path(logfile_path)
    _guard_no_nested_menu(args)
    safe_args = _safe_args(args)

    cmd = [exe, *safe_args]
    env = os.environ.copy()
    cwd = _project_root()
    creationflags = DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP

    try:
        with _open_log(logfile) as lf:
            proc = subprocess.Popen(
                cmd,
                cwd=str(cwd),
                env=env,
                stdout=lf,
                stderr=subprocess.STDOUT,
                stdin=subprocess.DEVNULL,
                creationflags=creationflags,
                close_fds=True,
                shell=False,
            )
        pid = int(proc.pid)
        pidfile = _write_pid_file(logfile, pid)
        return {"pid": pid, "logfile": str(logfile), "pidfile": pidfile}
    except OSError as e:
        _try_log_line(
            logfile,
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [LAUNCH_FAILED] {e.__class__.__name__}: exe={exe}; args={safe_args}",
        )
        raise

def launch_console(python_exe: str, args: list[str], logfile_path: str | Path) -> dict:
    """
    Visible console mode: new console window; child's stdout/stderr render there.
    Returns dict: {"pid": int, "logfile": str, "pidfile": str}.
    """
    exe = _sanitize_exe(python_exe)
    logfile = _strftime_path(logfile_path)  # ensure parent exists and for pid sidecar
    _guard_no_nested_menu(args)
    safe_args = _safe_args(args)

    cmd = [exe, *safe_args]
    env = os.environ.copy()
    cwd = _project_root()
    creationflags = CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP

    try:
        # Do not redirect stdio. The child console owns output.
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
            shell=False,
        )
        pid = int(proc.pid)
        pidfile = _write_pid_file(logfile, pid)
        return {"pid": pid, "logfile": str(logfile), "pidfile": str(pidfile)}
    except OSError as e:
        _try_log_line(
            logfile,
            f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] [LAUNCH_FAILED] {e.__class__.__name__}: exe={exe}; args={safe_args}",
        )
        raise

def spawn_console_tail(logfile_path: str, title: str = "") -> dict:
    """
    Open a new console window that tails a logfile live via PowerShell.
    Returns dict: {"pid": int}
    """
    p = Path(logfile_path)
    if not p.exists():
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text("", encoding="utf-8")

    # Sanitize title for single-quoted PowerShell string.
    ttl = (title or "").replace("'", "''").strip()
    p_escaped = str(p).replace("'", "''")
    ps_cmd = (
        "$Host.UI.RawUI.WindowTitle='{ttl}'; "
        "Get-Content -Path '{path}' -Wait -Encoding UTF8"
    ).format(ttl=ttl, path=p_escaped)

    cmd = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps_cmd]
    env = os.environ.copy()
    cwd = _project_root()
    creationflags = CREATE_NEW_CONSOLE | CREATE_NEW_PROCESS_GROUP

    try:
        proc = subprocess.Popen(
            cmd,
            cwd=str(cwd),
            env=env,
            stdin=subprocess.DEVNULL,
            creationflags=creationflags,
            close_fds=True,
            shell=False,
        )
        return {"pid": int(proc.pid)}
    except OSError as e:
        raise ProcessLaunchError(f"spawn_console_tail failed: {e}") from e

# ---- Liveness and kill ----

def is_alive(pid: int) -> bool:
    """
    True if process exists and exit code is STILL_ACTIVE.
    """
    if not isinstance(pid, int) or pid <= 0:
        return False

    PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    OpenProcess = kernel32.OpenProcess
    OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
    OpenProcess.restype = wintypes.HANDLE

    GetExitCodeProcess = kernel32.GetExitCodeProcess
    GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
    GetExitCodeProcess.restype = wintypes.BOOL

    CloseHandle = kernel32.CloseHandle
    CloseHandle.argtypes = [wintypes.HANDLE]
    CloseHandle.restype = wintypes.BOOL

    hProc = OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, wintypes.DWORD(pid))
    if not hProc:
        return False
    try:
        code = wintypes.DWORD(0)
        ok = GetExitCodeProcess(hProc, ctypes.byref(code))
        if not ok:
            return False
        return int(code.value) == STILL_ACTIVE
    finally:
        try:
            CloseHandle(hProc)
        except Exception:
            pass

def kill(pid: int) -> bool:
    """
    Attempts graceful termination, then force kill if needed.
    Returns True if the process is no longer alive.
    """
    if not isinstance(pid, int) or pid <= 0:
        return False
    try:
        os.kill(pid, signal.SIGTERM)
    except Exception:
        try:
            kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
            OpenProcess = kernel32.OpenProcess
            TerminateProcess = kernel32.TerminateProcess
            CloseHandle = kernel32.CloseHandle
            PROCESS_TERMINATE = 0x0001
            h = OpenProcess(PROCESS_TERMINATE, False, wintypes.DWORD(pid))
            if h:
                try:
                    TerminateProcess(h, 1)
                finally:
                    CloseHandle(h)
        except Exception:
            pass

    t0 = time.time()
    while time.time() - t0 < 3.0:
        if not is_alive(pid):
            return True
        time.sleep(0.1)
    return not is_alive(pid)
