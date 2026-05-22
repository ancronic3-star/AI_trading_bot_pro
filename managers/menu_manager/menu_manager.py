#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
KOKO main menu / launcher.

- A: start run loop (child console)
- B: stop run loop
- C: balances viewer (child console)
- D: quick test (placeholder)
- E: settings editor
- H: PnL / history snapshot (child console)
- S: WM4 localhost website sandbox (child console)
- Majors / universe utilities
"""

from __future__ import annotations

import json
import os
import sys
import time
import traceback
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


# Allow running as a script: ensure repo root is on sys.path
# (so `python managers/menu_manager/menu_manager.py` works from repo root)
try:
    from pathlib import Path
    _ROOT = Path(__file__).resolve().parents[2]
    if str(_ROOT) not in sys.path:
        sys.path.insert(0, str(_ROOT))
except Exception:
    pass

# ---------------------------------------------------------------------------
# Imports from project
# ---------------------------------------------------------------------------

try:
    from managers.config_manager import settings as cfg  # shared settings store
except Exception:  # pragma: no cover
    cfg = None  # fallback to local JSON store

try:
    from managers.process_manager import spawn  # child-process utilities
except Exception as e:  # pragma: no cover
    print(f"FATAL: cannot import managers.process_manager.spawn: {e}")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants / defaults
# ---------------------------------------------------------------------------

VERSION = "0.3.1-mm15.43"
# PID + log tracking for run loop
_PID_NOW = os.path.join("logs", "run_console_current.pid")
_PID_SIDE = os.path.join("logs", "run_console_pidfile.txt")
_PID_WRAPPER = os.path.join("logs", "run_console_wrapper.pid")
_RUN_CONSOLE_CMD = os.path.join("logs", "run_console_launch.cmd")

_SPAWN_LOG = os.path.join("logs", "spawn_%Y%m%d_%H%M%S.log")

# Logs for the viewers (templates, spawn formats with strftime)
_BALANCE_LOG = os.path.join("logs", "balance_viewer_%Y%m%d_%H%M%S.log")
_PNL_LOG = os.path.join("logs", "pnl_snapshot_%Y%m%d_%H%M%S.log")
_DIAG_LOG = os.path.join("logs", "run_diagnostics_%Y%m%d_%H%M%S.log")
_WM4_LOCALHOST_LOG = os.path.join("logs", "wm4_localhost_%Y%m%d_%H%M%S.log")
_WM4_LOCALHOST_PID = os.path.join("logs", "wm4_localhost_current.pid")
_WM4_LOCALHOST_URL = "http://localhost:3000/"
_WM4_LOCALHOST_REPO = os.path.join(os.path.expanduser("~"), "Downloads", "tdi-factor-live-current")
_WM4_LOCALHOST_CMD = os.path.join("logs", "wm4_localhost_launch.cmd")

# Paper-signal trough scoring (wait tool)
_TROUGH_WAIT_SCORE_LOG = os.path.join("logs", "trough_wait_score_%Y%m%d_%H%M%S.log")

# Live snapshot / website bridge
_LIVE_SNAPSHOT_WRITER_LOG = os.path.join("logs", "live_snapshot_writer_%Y%m%d_%H%M%S.log")
_LIVE_SNAPSHOT_HTTP_LOG = os.path.join("logs", "live_snapshot_http_%Y%m%d_%H%M%S.log")
_LIVE_SNAPSHOT_TUNNEL_LOG = os.path.join("logs", "live_snapshot_tunnel_%Y%m%d_%H%M%S.log")
_LIVE_SNAPSHOT_WRITER_PID = os.path.join("logs", "live_snapshot_writer_current.pid")
_LIVE_SNAPSHOT_HTTP_PID = os.path.join("logs", "live_snapshot_http_current.pid")
_LIVE_SNAPSHOT_TUNNEL_PID = os.path.join("logs", "live_snapshot_tunnel_current.pid")
_LIVE_SNAPSHOT_ENV = os.path.join("logs", "handoffs", "live_snapshot_bridge_current.env")
_LIVE_SNAPSHOT_PORT = 8765
_LIVE_SNAPSHOT_INTERVAL_SEC = 5



# Defaults used only when config manager is unavailable / empty
DEFAULTS: Dict[str, Any] = {
    "DRY": False,
    "AUTO_TRADE": True,
    "SMART_BUY": True,
    "BUY_CONFIRM_TICKS": 3,
    "TREND_TICKS": 5,
    "TREND_BPS_MIN": 5.0,
    "IDEA_STREAK_MIN": 3,
    "IDEA_PNL_BPS_MIN": 10.0,
    "IDEA_EXPIRE_TICKS": 20,
    "TOP_N": 8,
    "MIN_TOPBOOK_USD": 100.0,
    "MAX_SPREAD_PCT": 0.01,
    "TICK_SEC": 0.05,
    "SOLDIER_USD": 4.0,
    "COOLDOWN_TICKS": 1,
    "TP_PCT": 2.5,
    "SL_PCT": 0.8,
    "TDI_MIN_BUY_SCORE": 80.0,
    "Z_BUY": 0.03,
    "Z_EXIT": 0.035,
    "DEFAULT_PRODUCT_ID": "XRP",
    "QUICK_HOLD_SEC": 2,
    "PFID": "",
    "PROFILE": "KOKO",
    "UNIVERSE_MODE": "TOP",   # "TOP" or "LIST"
    "UNIVERSE_TOP": 60,
    "UNIVERSE_LIST": [],
    "MAJORS_INCLUDE": False,
    "MAJORS_LIST": [],
    "LIMIT_ONLY": True,
    "MIN_1M_VOL": 5.0,
    "GAINERS_ONLY": True,
    "MIN_24H_PCT": 2.0,
    "RANK_BY_24H_PCT": True,
    "STATS_TTL_SEC": 60,
    "USD_ONLY_QUOTES": True,
    "USD_RESERVE": 10.0,
    "MIN_DMID_BPS": 3.0,
    "BOOK_PRESSURE_MIN": 0.6,
    "HEADER_EVERY": 10,
    "RUN_ACTIVE_PATH": "logs/run_active.json",
"SELL_AT_LOSS": False,
"SL_CONFIRM_TICKS": 3,
"SL_COOLDOWN_SEC": 120,
    "SL_GRACE_TICKS": 10,
    "SL_REENTRY_COOLDOWN_SEC": 1800,
    "SL_REENTRY_SCORE_MIN": 0.90,
"SL_LOG_EVERY_SEC": 60,
"INV_MAX_PIDS": 12,
"PNL_TICKER_EVERY": 20,
"ENTRY_CACHE_SEC": 300,
"POS_CACHE_SEC": 20,
"MID_CACHE_SEC": 10,
"MAX_SOLDIERS_PER_PID": 5,
"PYRAMID_MIN_TICKS_BETWEEN_BUYS": 0,
"BUY_MAX_TRIES_PER_TICK": 1,
"MAX_BUYS_PER_TICK": 1,
"BUY_GLOBAL_COOLDOWN_SEC": 30.0,
"BUY_STALE_CANCEL_SEC": 15.0,
"BUY_MAX_OPEN": 1,
"BUY_FAIL_COOLDOWN_SEC": 180.0,
"BUY_CHASE_BPS": 8.0,
"BUY_CHASE_MAX_SPREAD_BPS": 25.0,
    "ACTIVITY_TICKER": True,
    "MAINT_ASYNC": True,
    "MAINT_EVERY_TICKS": 2,
    "MARKET_TICKER_MINIMAL": True,
    "PNL_TO_ACTIVITY": True,
    # Offline / travel-safe behavior
    "OFFLINE_PAUSE_MAINT": True,
    "OFFLINE_BLOCK_TRADING": True,
    "OFFLINE_BACKOFF_MIN_SEC": 15.0,
    "OFFLINE_BACKOFF_MAX_SEC": 300.0,
    "OFFLINE_BACKOFF_MULT": 1.7,
    "OFFLINE_LOG_EVERY_SEC": 30.0,
    "ACTIVITY_LOG_PATH": "logs/activity_ticker.log",
    "ACTIVITY_TICKER_TITLE": "MM18 Activity",

}

# Editable keys and their types for the settings editor
EDITABLE_KEYS: List[Tuple[str, str]] = [
    ("DRY", "bool"),
    ("AUTO_TRADE", "bool"),
    ("SMART_BUY", "bool"),
    ("GAINERS_ONLY", "bool"),
    ("RANK_BY_24H_PCT", "bool"),
    ("TOP_N", "int"),
    ("BUY_CONFIRM_TICKS", "int"),
    ("TREND_TICKS", "int"),
    ("MIN_TOPBOOK_USD", "float"),
    ("MAX_SPREAD_PCT", "float"),
    ("TICK_SEC", "float"),
    ("SOLDIER_USD", "float"),
    ("COOLDOWN_TICKS", "int"),
    ("TP_PCT", "float"),
    ("SL_PCT", "float"),
    ("TDI_MIN_BUY_SCORE", "float"),
    ("Z_BUY", "float"),
    ("Z_EXIT", "float"),
    ("DEFAULT_PRODUCT_ID", "str"),
    ("QUICK_HOLD_SEC", "int"),
    ("PFID", "str"),
    ("PROFILE", "str"),
    ("UNIVERSE_MODE", "choice"),   # TOP/LIST
    ("UNIVERSE_TOP", "int"),
    ("UNIVERSE_LIST", "list"),
    ("MAJORS_INCLUDE", "bool"),
    ("MAJORS_LIST", "list"),
    ("LIMIT_ONLY", "bool"),
    ("MIN_1M_VOL", "float"),
    ("USD_ONLY_QUOTES", "bool"),
    ("USD_RESERVE", "float"),
    ("MIN_DMID_BPS", "float"),
    ("BOOK_PRESSURE_MIN", "float"),
    ("TREND_BPS_MIN", "float"),
    ("MIN_24H_PCT", "float"),
    ("IDEA_STREAK_MIN", "int"),
    ("IDEA_PNL_BPS_MIN", "float"),
    ("IDEA_EXPIRE_TICKS", "int"),
    ("HEADER_EVERY", "int"),
    ("RUN_ACTIVE_PATH", "str"),
("SELL_AT_LOSS", "bool"),
("SL_CONFIRM_TICKS", "int"),
("SL_COOLDOWN_SEC", "float"),
    ("SL_GRACE_TICKS", "int"),
    ("SL_REENTRY_COOLDOWN_SEC", "float"),
    ("SL_REENTRY_SCORE_MIN", "float"),
("SL_LOG_EVERY_SEC", "float"),
("INV_MAX_PIDS", "int"),
("PNL_TICKER_EVERY", "int"),
("ENTRY_CACHE_SEC", "float"),
("POS_CACHE_SEC", "float"),
("MID_CACHE_SEC", "float"),
("BUY_MAX_TRIES_PER_TICK", "int"),
("MAX_BUYS_PER_TICK", "int"),
("BUY_GLOBAL_COOLDOWN_SEC", "float"),
("BUY_STALE_CANCEL_SEC", "float"),
("BUY_MAX_OPEN", "int"),
("BUY_FAIL_COOLDOWN_SEC", "float"),
    ("STATS_TTL_SEC", "int"),
("MAX_SOLDIERS_PER_PID", "int"),
("PYRAMID_MIN_TICKS_BETWEEN_BUYS", "int"),
("BUY_CHASE_BPS", "float"),
("BUY_CHASE_MAX_SPREAD_BPS", "float"),
    ("ACTIVITY_TICKER", "bool"),
    ("MAINT_ASYNC", "bool"),
    ("MAINT_EVERY_TICKS", "int"),
    ("MARKET_TICKER_MINIMAL", "bool"),
    ("PNL_TO_ACTIVITY", "bool"),

]
# ---------------------------------------------------------------------------
# Local settings store (fallback if config_manager.settings not available)
# ---------------------------------------------------------------------------


def _fallback_settings_path() -> str:
    # Local-only backup, not used if cfg.load_settings/save_settings are present
    return os.path.join("logs", "menu_settings.json")

def _repo_root() -> str:
    """Return repository root folder (two levels above this file)."""
    here = os.path.abspath(os.path.dirname(__file__))
    return os.path.abspath(os.path.join(here, os.pardir, os.pardir))



def _ensure_parent_dir(path: str) -> None:
    p = os.path.dirname(path) or "."
    try:
        os.makedirs(p, exist_ok=True)
    except Exception:
        pass


def _load_settings_local() -> Dict[str, Any]:
    path = _fallback_settings_path()
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as fh:
                data = json.load(fh) or {}
                if not isinstance(data, dict):
                    data = {}
        else:
            data = {}
    except Exception:
        data = {}
    merged = dict(DEFAULTS)
    merged.update(data)
    return merged


def _save_settings_local(d: Dict[str, Any]) -> Dict[str, Any]:
    merged = dict(DEFAULTS)
    merged.update(d or {})
    path = _fallback_settings_path()
    try:
        _ensure_parent_dir(path)
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(merged, fh, indent=2)
        print("Settings saved successfully.")
    except Exception as e:
        print(f"Warning: failed to save local settings: {e}")
    return merged


def load_settings() -> Dict[str, Any]:
    # Prefer central config manager if available (keeps menu + bot in sync)
    s: Any = None
    if cfg and hasattr(cfg, "load_settings"):
        try:
            s = cfg.load_settings()
        except Exception:
            s = None

    if not isinstance(s, dict):
        s = _load_settings_local()

    # Always backfill defaults for predictable behavior (do not overwrite).
    try:
        for k, v in DEFAULTS.items():
            if k not in s:
                s[k] = v
    except Exception:
        pass

    return s


def save_settings(d: Dict[str, Any]) -> Dict[str, Any]:
    # IMPORTANT: some config managers persist successfully but return None.
    # Always return a dict so the menu never crashes.
    d = d or {}

    # Prefer the central config manager if present.
    if cfg and hasattr(cfg, "save_settings"):
        try:
            out = cfg.save_settings(d)
        except Exception:
            out = None

        if isinstance(out, dict):
            print("Settings saved successfully.")
            return out

        # If the save returned nothing, try to reload (common case).
        if hasattr(cfg, "load_settings"):
            try:
                reloaded = cfg.load_settings()
            except Exception:
                reloaded = None
            if isinstance(reloaded, dict):
                print("Settings saved successfully.")
                return reloaded

        # Last resort: write locally and return the input dict.
        try:
            _save_settings_local(d)
        except Exception:
            pass

        print("Settings saved successfully.")
        return d

    # Local mode
    try:
        out = _save_settings_local(d)
    except Exception:
        out = None

    print("Settings saved successfully.")
    return out if isinstance(out, dict) else d


# ---------------------------------------------------------------------------
# UI helpers
# ---------------------------------------------------------------------------


def _header(settings: Dict[str, Any]) -> str:
    mode = "DRY" if bool(settings.get("DRY")) else "LIVE"
    default_pid = settings.get("DEFAULT_PRODUCT_ID") or "NONE"
    pfid = os.environ.get("PFID", "").strip() or (settings.get("PFID") or "NONE")
    quick_hold = settings.get("QUICK_HOLD_SEC", 0)
    profile = settings.get("PROFILE") or "NONE"
    return (
        f"[{time.strftime('%Y-%m-%d %H:%M:%S')}] "
        f"Menu Manager {VERSION} - MODE={mode} DEFAULT_PRODUCT_ID={default_pid} "
        f"PFID={pfid} PROFILE={profile} QUICK_HOLD_SEC={quick_hold}"
    )


def _print_settings(settings: Dict[str, Any]) -> None:
    print("Current settings:")
    for k in [
        "DRY", "AUTO_TRADE", "TOP_N", "MIN_TOPBOOK_USD", "MAX_SPREAD_PCT",
        "TICK_SEC", "SOLDIER_USD", "COOLDOWN_TICKS", "TP_PCT", "SL_PCT", "TDI_MIN_BUY_SCORE",
        "Z_BUY", "Z_EXIT",
        "DEFAULT_PRODUCT_ID", "QUICK_HOLD_SEC", "PFID", "PROFILE",
        "UNIVERSE_MODE", "UNIVERSE_TOP", "UNIVERSE_LIST",
        "MAJORS_INCLUDE", "MAJORS_LIST",
        "LIMIT_ONLY", "MIN_1M_VOL", "USD_ONLY_QUOTES",
        "MIN_DMID_BPS", "BOOK_PRESSURE_MIN",
        "HEADER_EVERY", "RUN_ACTIVE_PATH",
"MAX_SOLDIERS_PER_PID", "PYRAMID_MIN_TICKS_BETWEEN_BUYS",
"BUY_CHASE_BPS", "BUY_CHASE_MAX_SPREAD_BPS",

    ]:
        print(f"  {k} = {settings.get(k)}")


def _print_universe(settings: Dict[str, Any]) -> None:
    print("Universe Settings:")
    for k in ["UNIVERSE_MODE", "UNIVERSE_TOP", "UNIVERSE_LIST",
              "MAJORS_INCLUDE", "MAJORS_LIST"]:
        print(f"  {k} = {settings.get(k)}")

# ---------------------------------------------------------------------------
# Parse helpers for editor
# ---------------------------------------------------------------------------


def _parse_value(kind: str, raw: str) -> Any:
    s = (raw or "").strip()
    if kind == "bool":
        return s.lower() in ("1", "true", "t", "yes", "y", "on")
    if kind == "int":
        return int(float(s))  # tolerate "10.0"
    if kind == "float":
        return float(s)
    if kind == "list":
        if not s:
            return []
        ss = s.strip()
        if ss in ("[]", "[ ]"):
            return []
        if ss.startswith("[") and ss.endswith("]"):
            try:
                v = json.loads(ss)
                if isinstance(v, list):
                    out = []
                    for x in v:
                        xs = str(x).strip()
                        if xs:
                            out.append(xs.upper().replace("/", "-"))
                    return out
            except Exception:
                pass
        return [x.strip().upper().replace("/", "-") for x in ss.split(",") if x.strip()]
    if kind == "choice":
        s = s.upper()
        return "LIST" if s.startswith("L") else "TOP"
    # default str
    return s

# ---------------------------------------------------------------------------
# Settings editor + universe / majors helpers
# ---------------------------------------------------------------------------


def edit_settings(settings: Dict[str, Any]) -> Dict[str, Any]:
    while True:
        print("\nSettings editor:")
        for idx, item in enumerate(EDITABLE_KEYS, start=1):
            k, kind = item[0], item[1]
            print(f"{idx:>2}. {k:<18} [{kind}]  current={settings.get(k)!r}")
        print("99. Back to main menu")
        sel = input("> ").strip()
        if sel in ("99", "b", "B", "q", "Q"):
            return settings
        try:
            idx = int(sel)
        except Exception:
            print("Invalid selection.")
            continue
        if not (1 <= idx <= len(EDITABLE_KEYS)):
            print("Out of range.")
            continue
        key, kind = EDITABLE_KEYS[idx - 1]
        cur = settings.get(key)
        new_raw = input(f"Enter new value for {key} ({kind}) [current={cur!r}]: ")
        try:
            settings[key] = _parse_value(kind, new_raw)
            settings = save_settings(settings)
        except Exception as e:
            print(f"Failed to set {key}: {e}")
    # unreachable


def toggle_majors(settings: Dict[str, Any]) -> Dict[str, Any]:
    settings["MAJORS_INCLUDE"] = not bool(settings.get("MAJORS_INCLUDE", False))
    print(f"Majors inclusion → {settings['MAJORS_INCLUDE']}")
    return save_settings(settings)


def edit_majors_list(settings: Dict[str, Any]) -> Dict[str, Any]:
    raw = input(
        "Enter MAJORS_LIST (comma-separated, e.g., BTC-USD,ETH-USD,SOL-USD,XRP-USD): "
    ).strip()
    settings["MAJORS_LIST"] = _parse_value("list", raw)
    print(f"MAJORS_LIST → {settings['MAJORS_LIST']}")
    return save_settings(settings)


def toggle_universe_mode(settings: Dict[str, Any]) -> Dict[str, Any]:
    mode = str(settings.get("UNIVERSE_MODE", "TOP")).upper()
    settings["UNIVERSE_MODE"] = "LIST" if mode == "TOP" else "TOP"
    print(f"UNIVERSE_MODE → {settings['UNIVERSE_MODE']}")
    return save_settings(settings)


def set_universe_top(settings: Dict[str, Any]) -> Dict[str, Any]:
    raw = input("UNIVERSE_TOP (int): ").strip()
    try:
        settings["UNIVERSE_TOP"] = int(float(raw))
    except Exception:
        print("Invalid number.")
        return settings
    return save_settings(settings)


def set_universe_list(settings: Dict[str, Any]) -> Dict[str, Any]:
    raw = input("UNIVERSE_LIST (comma-separated product_ids): ").strip()
    settings["UNIVERSE_LIST"] = _parse_value("list", raw)
    return save_settings(settings)

# ---------------------------------------------------------------------------
# Run control (child console)
# ---------------------------------------------------------------------------




def quick_test(settings: dict) -> None:
    """Quick non-trading checks: filesystem, env vars, and imports.

    This is intentionally safe (no API calls / no orders).
    """
    print()
    print("======================================================================")
    print("QUICK TEST (NON-TRADING)")
    print("======================================================================")
    repo_root = _repo_root()
    print(f"RepoRoot: {repo_root}")
    print(f"Python:   {sys.executable}")

    key_file = os.environ.get("COINBASE_KEY_FILE", "")
    pfid = os.environ.get("PFID", "")
    print(f"COINBASE_KEY_FILE: {key_file or '(not set)'}")
    if key_file and os.path.isfile(key_file):
        try:
            sz = os.path.getsize(key_file)
            print(f"  Key file exists ({sz} bytes)")
        except Exception:
            print("  Key file exists")
    else:
        print("  Key file missing/invalid")

    print(f"PFID: {pfid or '(not set)'}")

    logs_dir = os.path.join(repo_root, "logs")
    try:
        os.makedirs(logs_dir, exist_ok=True)
        test_path = os.path.join(logs_dir, "_write_test.tmp")
        with open(test_path, "w", encoding="utf-8") as f:
            f.write("ok")
        os.remove(test_path)
        print(f"Logs: writable ({logs_dir})")
    except Exception as e:
        print(f"Logs: NOT writable ({logs_dir})  err={type(e).__name__}: {e}")

    import importlib

    mods = [
        "managers.run_manager.run_manager",
        "managers.universe_manager.universe_dynamic",
        "managers.strategy_manager.strategy_core",
        "managers.strategy_manager.mechanic",
    ]
    for m in mods:
        try:
            importlib.import_module(m)
            print(f"Import OK: {m}")
        except Exception as e:
            print(f"Import FAIL: {m}  err={type(e).__name__}: {e}")


    # Optional API sanity check (still NON-TRADING): fetch product list + show USD 24h volumes
    print()
    print("API sanity check (NON-TRADING)...")
    try:
        from managers.auth_manager.auth_jwt import get_client
        from managers.universe_manager import universe_dynamic as u_dyn
        c = get_client()
        # pull a batch of products; volume comes from List Products (approximate_quote_24h_volume when available)
        resp = c.get_products(limit=250)
        prods = getattr(resp, 'products', None) or (resp.get('products') if isinstance(resp, dict) else None) or []
        vols = {}  # pid -> vol_usd_24h
        for p in prods:
            pid = u_dyn._norm_id(u_dyn._get(p, 'product_id') or u_dyn._get(p, 'productId') or '')
            if not pid:
                continue
            q = (u_dyn._get(p, 'quote_currency_id') or u_dyn._get(p, 'quoteCurrencyId') or
                 u_dyn._get(p, 'quote_currency') or u_dyn._get(p, 'quoteCurrency') or '')
            if str(q).upper() != 'USD':
                continue
            vol = float(u_dyn._usd_quote_vol_24h(p) or 0.0)
            if vol > 0:
                vols[pid] = vol
        if not vols:
            print('  WARNING: USD 24h quote volume map is empty (check API fields / connectivity).')
        else:
            top = sorted(vols.items(), key=lambda kv: kv[1], reverse=True)[:10]
            print('  Top USD 24h volumes (M USD):')
            for pid, vol in top:
                print(f'    {pid:<12} {vol/1_000_000.0:>12.2f}')
            min_m = float(settings.get('MIN_1M_VOL', 0.0) or 0.0)
            meets = sum(1 for v in vols.values() if v >= (min_m * 1_000_000.0))
            print(f'  Meets MIN_1M_VOL >= {min_m:.2f}M : {meets}/{len(vols)}')
    except Exception as e:
        print(f'  API check failed: {type(e).__name__}: {e}')

    input("Press Enter to return to menu...")


def _write_text(path: str, text: str) -> None:
    try:
        _ensure_parent_dir(path)
        with open(path, "w", encoding="utf-8") as fh:
            fh.write(text)
    except Exception:
        pass


def _read_text(path: str) -> str:
    try:
        with open(path, "r", encoding="utf-8") as fh:
            return fh.read()
    except Exception:
        return ""


def _store_pid(pid: int, pidfile_from_spawn: str) -> None:
    _write_text(_PID_NOW, str(int(pid)))
    _write_text(_PID_SIDE, pidfile_from_spawn)


def _load_pid() -> int:
    try:
        return int(_read_text(_PID_NOW).strip())
    except Exception:
        return 0


def _run_active_path() -> str:
    return os.path.join(_repo_root(), "logs", "run_active.json")


def _read_run_active_pid() -> int:
    try:
        raw = _read_text(_run_active_path()).strip()
        if not raw:
            return 0
        data = json.loads(raw)
        return int(data.get("pid") or 0)
    except Exception:
        return 0


def _write_run_active_state(pid: int, state: str) -> None:
    payload = {
        "pid": int(pid or 0),
        "ts": time.strftime("%H:%M:%S"),
        "state": str(state or "").strip() or "unknown",
    }
    _write_text(_run_active_path(), json.dumps(payload))


def _clear_run_tracking() -> None:
    _write_text(_PID_NOW, "0")
    _write_text(_PID_SIDE, "")
    _write_text(_PID_WRAPPER, "0")
    _write_run_active_state(0, "stopped")


def _load_wrapper_pid() -> int:
    try:
        return int(_read_text(_PID_WRAPPER).strip())
    except Exception:
        return 0


def _list_live_bot_loop_processes() -> List[Dict[str, Any]]:
    host = _find_powershell_host() or "powershell.exe"
    script = r"""
$items = Get-CimInstance Win32_Process |
    Where-Object {
        $_.Name -eq 'python.exe' -and
        ($_.CommandLine -match 'managers\\run_manager\\run_manager\.py')
    } |
    Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine
$items | ConvertTo-Json -Depth 3 -Compress
"""
    try:
        proc = subprocess.run(
            [host, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        raw = (proc.stdout or "").strip()
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        out: List[Dict[str, Any]] = []
        for item in data or []:
            try:
                pid = int(item.get("ProcessId") or 0)
            except Exception:
                pid = 0
            if pid > 0 and spawn.is_alive(pid):
                out.append({
                    "pid": pid,
                    "ppid": int(item.get("ParentProcessId") or 0),
                    "created": str(item.get("CreationDate") or ""),
                    "cmd": str(item.get("CommandLine") or ""),
                })
        out.sort(key=lambda x: (x.get("created") or "", x.get("pid") or 0))
        return out
    except Exception:
        return []


def _kill_live_bot_loop_pid(pid: int) -> bool:
    try:
        if pid > 0 and spawn.is_alive(pid):
            return bool(spawn.kill(pid))
    except Exception:
        pass
    return not spawn.is_alive(pid)


def _list_activity_ticker_processes() -> List[Dict[str, Any]]:
    host = _find_powershell_host() or "powershell.exe"
    repo_root = _repo_root().replace("\\", "\\\\")
    script = rf"""
$items = Get-CimInstance Win32_Process |
    Where-Object {{
        $_.Name -eq 'python.exe' -and
        ($_.CommandLine -match 'activity_ticker\.py') -and
        ($_.CommandLine -match '{repo_root}')
    }} |
    Select-Object ProcessId,ParentProcessId,CreationDate,CommandLine
$items | ConvertTo-Json -Depth 3 -Compress
"""
    try:
        proc = subprocess.run(
            [host, "-NoLogo", "-NoProfile", "-NonInteractive", "-Command", script],
            cwd=_repo_root(),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=15,
            check=False,
        )
        raw = (proc.stdout or "").strip()
        if not raw:
            return []
        data = json.loads(raw)
        if isinstance(data, dict):
            data = [data]
        out: List[Dict[str, Any]] = []
        for item in data or []:
            try:
                pid = int(item.get("ProcessId") or 0)
            except Exception:
                pid = 0
            if pid > 0 and spawn.is_alive(pid):
                out.append({
                    "pid": pid,
                    "ppid": int(item.get("ParentProcessId") or 0),
                    "created": str(item.get("CreationDate") or ""),
                    "cmd": str(item.get("CommandLine") or ""),
                })
        out.sort(key=lambda x: (x.get("created") or "", x.get("pid") or 0))
        return out
    except Exception:
        return []


def _kill_activity_ticker_pid(pid: int) -> bool:
    try:
        if pid > 0 and spawn.is_alive(pid):
            return bool(spawn.kill(pid))
    except Exception:
        pass
    return not spawn.is_alive(pid)


def _stop_all_activity_tickers() -> Tuple[List[int], List[int]]:
    seen: List[int] = []
    for item in _list_activity_ticker_processes():
        pid = int(item.get("pid") or 0)
        if pid > 0 and pid not in seen:
            seen.append(pid)

    stopped: List[int] = []
    for pid in seen:
        if _kill_activity_ticker_pid(pid):
            stopped.append(pid)

    t0 = time.time()
    remaining: List[int] = []
    while time.time() - t0 < 6.0:
        remaining = [int(item.get("pid") or 0) for item in _list_activity_ticker_processes()]
        if not remaining:
            break
        for pid in list(remaining):
            _kill_activity_ticker_pid(pid)
        time.sleep(0.25)

    remaining = [int(item.get("pid") or 0) for item in _list_activity_ticker_processes()]
    return stopped, remaining


def _stop_all_live_bot_loops() -> Tuple[List[int], List[int]]:
    seen: List[int] = []
    for item in _list_live_bot_loop_processes():
        pid = int(item.get("pid") or 0)
        if pid > 0 and pid not in seen:
            seen.append(pid)
    tracked = _load_pid()
    active = _read_run_active_pid()
    wrapper = _load_wrapper_pid()
    for pid in (tracked, active):
        if pid > 0 and pid not in seen:
            seen.append(pid)

    stopped: List[int] = []
    for pid in seen:
        if _kill_live_bot_loop_pid(pid):
            stopped.append(pid)

    t0 = time.time()
    remaining: List[int] = []
    while time.time() - t0 < 6.0:
        remaining = [int(item.get("pid") or 0) for item in _list_live_bot_loop_processes()]
        if not remaining:
            break
        for pid in list(remaining):
            _kill_live_bot_loop_pid(pid)
        time.sleep(0.25)

    remaining = [int(item.get("pid") or 0) for item in _list_live_bot_loop_processes()]
    if wrapper > 0:
        try:
            if spawn.is_alive(wrapper):
                spawn.kill(wrapper)
        except Exception:
            pass
    if not remaining:
        _clear_run_tracking()
    return stopped, remaining


def _resolve_authoritative_run_pid(wrapper_pid: int = 0, timeout_s: float = 8.0) -> int:
    t0 = time.time()
    last_candidates: List[int] = []
    while time.time() - t0 < float(timeout_s):
        items = _list_live_bot_loop_processes()
        candidates = [item for item in items if int(item.get("pid") or 0) > 0]
        last_candidates = [int(item.get("pid") or 0) for item in candidates]
        run_active_pid = _read_run_active_pid()
        if run_active_pid > 0 and run_active_pid in last_candidates and spawn.is_alive(run_active_pid):
            return run_active_pid
        if wrapper_pid > 0:
            direct_children = [
                int(item.get("pid") or 0)
                for item in candidates
                if int(item.get("ppid") or 0) == int(wrapper_pid)
            ]
            if len(direct_children) == 1 and spawn.is_alive(direct_children[0]):
                return direct_children[0]
        if len(last_candidates) == 1 and last_candidates[0] != int(wrapper_pid or 0):
            return last_candidates[0]
        time.sleep(0.25)
    if wrapper_pid > 0:
        items = _list_live_bot_loop_processes()
        direct_children = [
            int(item.get("pid") or 0)
            for item in items
            if int(item.get("pid") or 0) > 0 and int(item.get("ppid") or 0) == int(wrapper_pid)
        ]
        if len(direct_children) == 1 and spawn.is_alive(direct_children[0]):
            return direct_children[0]
    if len(last_candidates) == 1 and last_candidates[0] != int(wrapper_pid or 0):
        return last_candidates[0]
    return 0


def _find_powershell_host() -> str:
    try:
        import shutil
        for name in ("pwsh.exe", "pwsh", "powershell.exe", "powershell"):
            found = shutil.which(name)
            if found and os.path.isfile(found):
                return found
    except Exception:
        pass
    cands = [
        os.path.join(os.environ.get("ProgramFiles", ""), "PowerShell", "7", "pwsh.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "PowerShell", "7", "pwsh.exe"),
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", "WindowsPowerShell", "v1.0", "powershell.exe"),
    ]
    for p in cands:
        if p and os.path.isfile(p):
            return p
    return ""


def _find_cmd_host() -> str:
    try:
        import shutil
        for name in ("cmd.exe", "cmd"):
            found = shutil.which(name)
            if found and os.path.isfile(found):
                return found
    except Exception:
        pass
    p = os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", "cmd.exe")
    return p if os.path.isfile(p) else ""


def start_wm4_localhost_sandbox() -> None:
    repo = _WM4_LOCALHOST_REPO
    if not os.path.isdir(repo):
        print(f"WM4 localhost repo not found: {repo}")
        return
    pkg = os.path.join(repo, "package.json")
    if not os.path.isfile(pkg):
        print(f"WM4 localhost package.json not found: {pkg}")
        return

    host = _find_cmd_host()
    if not host:
        print("cmd.exe host not found; cannot start WM4 localhost sandbox.")
        return

    try:
        _kill_named_pid(_WM4_LOCALHOST_PID)
    except Exception:
        pass

    try:
        spawn.write_sentinel(_WM4_LOCALHOST_LOG, "wm4_localhost")
    except Exception:
        pass

    launcher = "\r\n".join([
        "@echo off",
        f'cd /d "{repo}"',
        "taskkill /F /IM node.exe >nul 2>&1",
        "npm run dev -- --host --port 3000",
        "",
    ])
    _write_text(_WM4_LOCALHOST_CMD, launcher)
    args = ["/K", _WM4_LOCALHOST_CMD]
    info = spawn.launch_console(host, args, _WM4_LOCALHOST_LOG)
    pid = int(info.get("pid") or 0)
    _store_named_pid(_WM4_LOCALHOST_PID, pid)
    print(f"Started WM4 localhost website sandbox. PID={pid}")
    print(f"URL: {_WM4_LOCALHOST_URL}")


def start_run_console() -> None:
    """
    Launch the run loop in a NEW console window, UTF-8 & unbuffered, non-blocking.
    """
    existing = _list_live_bot_loop_processes()
    existing_tickers = _list_activity_ticker_processes()
    if existing or existing_tickers:
        pids = [int(item.get("pid") or 0) for item in existing if int(item.get("pid") or 0) > 0]
        ticker_pids = [int(item.get("pid") or 0) for item in existing_tickers if int(item.get("pid") or 0) > 0]
        if pids:
            print(f"Existing live bot loop(s) detected: {pids}")
        if ticker_pids:
            print(f"Existing activity ticker window(s) detected: {ticker_pids}")
        print("Stopping existing live bot loop(s) and activity ticker window(s) before visible restart...")
        stopped, remaining = _stop_all_live_bot_loops()
        ticker_stopped, ticker_remaining = _stop_all_activity_tickers()
        print(f"Stopped existing loop PID(s): {stopped if stopped else 'none'}")
        print(f"Stopped existing activity ticker PID(s): {ticker_stopped if ticker_stopped else 'none'}")
        if remaining or ticker_remaining:
            print(f"Refusing to start: duplicate live bot loop PID(s) still alive: {remaining}")
            if ticker_remaining:
                print(f"Refusing to start: duplicate activity ticker PID(s) still alive: {ticker_remaining}")
            return

    py_exe = sys.executable
    args = [
        "-X", "utf8",
        "-u",
        "managers\\run_manager\\run_manager.py",
        "--console",
    ]
    try:
        spawn.write_sentinel(_SPAWN_LOG, "run_loop_console")
    except Exception:
        pass

    info = spawn.launch_console(py_exe, args, _SPAWN_LOG)
    wrapper_pid = 0
    pidfile = str(info.get("pidfile") or "")
    launch_pid = int(info.get("pid") or 0)
    _write_text(_PID_WRAPPER, "0")

    auth_pid = _resolve_authoritative_run_pid(launch_pid, timeout_s=12.0)
    if auth_pid <= 0:
        if launch_pid > 0:
            try:
                spawn.kill(launch_pid)
            except Exception:
                pass
        _clear_run_tracking()
        print(f"Live start failed: launch PID={launch_pid} never produced a surviving authoritative run_manager.py process.")
        return

    _store_pid(auth_pid, pidfile)
    print(f"Started run loop in visible child console. Launch PID={launch_pid} authoritative loop PID={auth_pid}")


def stop_run_console() -> None:
    """
    Exhaustively stops every live bot-loop process so no orphan/duplicate run_manager
    instance survives a menu stop.
    """
    stopped, remaining = _stop_all_live_bot_loops()
    ticker_stopped, ticker_remaining = _stop_all_activity_tickers()
    if not stopped and not remaining and not ticker_stopped and not ticker_remaining:
        print("No live bot-loop or activity ticker PID found.")
        return
    print(f"Stopped live bot-loop PID(s): {stopped if stopped else 'none'}")
    print(f"Stopped activity ticker PID(s): {ticker_stopped if ticker_stopped else 'none'}")
    if remaining:
        print(f"STOP FAILED: live bot-loop PID(s) still alive: {remaining}")
    if ticker_remaining:
        print(f"STOP FAILED: activity ticker PID(s) still alive: {ticker_remaining}")
    if ticker_remaining or remaining:
        return
    else:
        print("Stop complete. Zero live bot-loop and activity ticker PID(s) remain.")

# ---------------------------------------------------------------------------
# Viewer helpers (balance + PnL)
# ---------------------------------------------------------------------------


def open_balance_viewer_console() -> None:
    """
    Launch the balances viewer in a detached process and tail its output
    in a dedicated console window so it stays open instead of flashing and closing.
    """
    py_exe = sys.executable
    args = [
        "-X", "utf8",
        "-u",
        "managers\\balance_manager\\balance_viewer.py",
    ]
    label = "balance_viewer"
    try:
        spawn.write_sentinel(_BALANCE_LOG, label)
    except Exception:
        pass
    info = spawn.launch_detached(py_exe, args, _BALANCE_LOG)
    logfile = str(info.get("logfile") or _BALANCE_LOG)
    try:
        spawn.await_log_activity(logfile, min_bytes=64, timeout_s=5.0)
    except Exception:
        pass
    spawn.spawn_console_tail(logfile, title="Balances viewer")


def open_pnl_snapshot_console() -> None:
    """
    Launch the PnL / history snapshot in a detached process and tail its
    output in a dedicated console window so it stays open.
    """
    py_exe = sys.executable
    args = [
        "-X", "utf8",
        "-u",
        "managers\\logging_manager\\diag_pnl_snapshot.py",
    ]
    label = "pnl_snapshot"
    try:
        spawn.write_sentinel(_PNL_LOG, label)
    except Exception:
        pass
    info = spawn.launch_detached(py_exe, args, _PNL_LOG)
    logfile = str(info.get("logfile") or _PNL_LOG)
    try:
        spawn.await_log_activity(logfile, min_bytes=64, timeout_s=5.0)
    except Exception:
        pass
    spawn.spawn_console_tail(logfile, title="PnL / history snapshot")



def open_run_diagnostics_console(extra_args: list[str] | None = None) -> None:
    """Launch run analytics diagnostics in a NEW console window.

    Uses spawn.launch_console() with the current Python executable.
    We execute the diagnostics *file path* (not -m) so it works regardless of working directory.
    The diagnostics script is invoked with --pause so the window stays open until you press ENTER.
    """
    py_exe = sys.executable  # must be .exe on Windows; spawn verifies

    # Resolve repo root and diagnostics script path
    try:
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[2]
        diag_script = repo_root / "managers" / "logging_manager" / "diag_run_analytics.py"
        diag_path = str(diag_script)
    except Exception:
        diag_path = os.path.join("managers", "logging_manager", "diag_run_analytics.py")

    args: list[str] = [
        "-X", "utf8",
        "-u",
        diag_path,
    ]
    if extra_args:
        args.extend([str(x) for x in extra_args])
    if "--pause" not in args:
        args.append("--pause")

    info = spawn.launch_console(py_exe, args, _DIAG_LOG)
    pid = int(info.get("pid") or 0)
    print(f"Started run diagnostics (pid={pid}).")
def run_diagnostics_menu() -> None:
    """Submenu under G for diagnostics options."""
    while True:
        print("\nRun diagnostics (G):")
        print(" 1) Since last [run_start] (default)")
        print(" 2) Last N ticks")
        print(" 3) Last N hours")
        print(" 4) Advanced")
        print(" 9) Back")
        sel = input("> ").strip()
        if sel == "9":
            return
        if sel == "1" or sel == "":
            open_run_diagnostics_console([])
            return
        if sel == "2":
            s = input("Ticks (int, e.g., 5000): ").strip()
            try:
                n = int(s)
            except Exception:
                print("Invalid ticks.")
                continue
            open_run_diagnostics_console(["--since-ticks", str(n)])
            return
        if sel == "3":
            s = input("Hours (int, e.g., 6): ").strip()
            try:
                h = int(s)
            except Exception:
                print("Invalid hours.")
                continue
            open_run_diagnostics_console(["--since-hours", str(h)])
            return
        if sel == "4":
            # advanced: choose mode + optional overrides
            mode = input("Mode (runstart/ticks/hours) [runstart]: ").strip().lower() or "runstart"
            extra: list[str] = []
            if mode == "ticks":
                s = input("Ticks (int) [5000]: ").strip() or "5000"
                try:
                    n = int(s)
                    extra += ["--since-ticks", str(n)]
                except Exception:
                    print("Invalid ticks.")
                    continue
            elif mode == "hours":
                s = input("Hours (int) [6]: ").strip() or "6"
                try:
                    h = int(s)
                    extra += ["--since-hours", str(h)]
                except Exception:
                    print("Invalid hours.")
                    continue
            # optional knobs
            s = input("Run tail lines (int) [200000]: ").strip() or "200000"
            try:
                tl = int(s)
                extra += ["--run-tail-lines", str(tl)]
            except Exception:
                print("Invalid run tail lines.")
                continue

            s = input("Max trades to analyze (int) [30]: ").strip() or "30"
            try:
                mt = int(s)
                extra += ["--max-trades", str(mt)]
            except Exception:
                print("Invalid max trades.")
                continue

            s = input("Lookback minutes (int) [60]: ").strip() or "60"
            try:
                lb = int(s)
                extra += ["--lookback-min", str(lb)]
            except Exception:
                print("Invalid lookback minutes.")
                continue

            s = input("Forward minutes (int) [30]: ").strip() or "30"
            try:
                fw = int(s)
                extra += ["--forward-min", str(fw)]
            except Exception:
                print("Invalid forward minutes.")
                continue

            open_run_diagnostics_console(extra)
            return

        print("Unknown selection.")



# ---------------------------------------------------------------------------
# Paper-signal trough scoring (wait tool)
# ---------------------------------------------------------------------------


def open_trough_wait_score_console(extra_args: list[str] | None = None) -> None:
    """Launch the paper-signal trough wait+score tool in a NEW console window.

    The tool will wait until a target number of [PAPER_BUY_SIGNAL] lines have
    been observed since the last [run_start], then score those signals against
    Coinbase 1-minute candles and produce a zip report under logs\analysis_trough.
    """
    py_exe = sys.executable

    # Resolve repo root and tool script path
    try:
        from pathlib import Path
        repo_root = Path(__file__).resolve().parents[2]
        tool_script = repo_root / "managers" / "logging_manager" / "diag_trough_wait_score.py"
        tool_path = str(tool_script)
    except Exception:
        tool_path = os.path.join("managers", "logging_manager", "diag_trough_wait_score.py")

    args: list[str] = [
        "-X", "utf8",
        "-u",
        tool_path,
    ]
    if extra_args:
        args.extend([str(x) for x in extra_args])
    if "--pause" not in args:
        args.append("--pause")
    if "--no-prompt" not in args:
        args.append("--no-prompt")

    info = spawn.launch_console(py_exe, args, _TROUGH_WAIT_SCORE_LOG)
    pid = int(info.get("pid") or 0)
    print(f"Started trough wait+score tool (pid={pid}).")



def trough_wait_score_menu() -> None:
    """
    Hotkey W: launch diagnostics in a new console.

    Modes:
      1) SCORE (paper): wait for [PAPER_BUY_SIGNAL] lines then score trough/forward stats.
      2) EVENT WATCH: capture next real [BUY_OK]/[SELL_OK] events into zip packs.
      3) TDI ENTRY ATTRIBUTION: join PAPER_BUY_SIGNAL / BUY_OK to nearest prior TDI snapshot.
      4) TP-RELATIVE CYCLE MAP: compare crest/trough timing across Coinbase intervals vs target TP.
    """
    print("\nW tool modes:")
    print("  1) Wait+score PAPER_BUY_SIGNAL (paper)")
    print("  2) Event watch BUY_OK / SELL_OK (no babysitting)")
    print("  3) TDI entry attribution (zipped report)")
    print("  4) TP-relative cycle map (zipped report)")
    s = input("Select mode [1]: ").strip() or "1"
    if s not in ("1", "2", "3", "4"):
        print("Invalid mode.")
        return

    if s == "1":
        print("\nPaper-signal trough scoring (wait tool):")
        s2 = input("Target PAPER_BUY_SIGNAL count [50]: ").strip() or "50"
        try:
            target = int(s2)
        except Exception:
            print("Invalid target.")
            return
        if target < 1:
            target = 1

        s2 = input("Max wait minutes [120]: ").strip() or "120"
        try:
            max_min = int(s2)
        except Exception:
            print("Invalid max minutes.")
            return
        if max_min < 1:
            max_min = 1

        s2 = input("Score limit (signals to score) [target]: ").strip()
        if not s2:
            limit = target
        else:
            try:
                limit = int(s2)
            except Exception:
                print("Invalid score limit.")
                return
        if limit < 1:
            limit = 1

        s2 = input("Forward window minutes [180] (180=3h, 720=12h, 1440=24h): ").strip() or "180"
        try:
            fwd = int(s2)
        except Exception:
            print("Invalid forward minutes.")
            return
        if fwd < 30:
            fwd = 30

        open_trough_wait_score_console([
            "--mode", "score",
            "--target", str(target),
            "--max-minutes", str(max_min),
            "--limit", str(limit),
            "--forward-min", str(fwd),
        ])
        return

    if s == "2":
        print("\nEvent watch mode:")
        print("  1) Capture next BUY_OK")
        print("  2) Capture next SELL_OK")
        print("  3) Capture BOTH (BUY_OK then SELL_OK)")
        s3 = input("Capture selection [3]: ").strip() or "3"
        if s3 == "1":
            ev = "buy"
        elif s3 == "2":
            ev = "sell"
        elif s3 == "3":
            ev = "both"
        else:
            print("Invalid selection.")
            return

        s4 = input("Max wait minutes [720]: ").strip() or "720"
        try:
            max_min = int(s4)
        except Exception:
            print("Invalid max minutes.")
            return
        if max_min < 1:
            max_min = 1

        s5 = input("Activity log tail lines to include [250000]: ").strip() or "250000"
        try:
            tail_lines = int(s5)
        except Exception:
            print("Invalid tail lines.")
            return
        if tail_lines < 1000:
            tail_lines = 1000

        s6 = input("Retro capture from existing log tail first? [Y]: ").strip().lower()
        retro = (s6 == "" or s6.startswith("y"))

        args = [
            "--mode", "event",
            "--event", ev,
            "--max-minutes", str(max_min),
            "--tail-lines", str(tail_lines),
        ]
        if retro:
            args.append("--retro")

        open_trough_wait_score_console(args)
        return

    if s == "4":
        settings = load_settings()
        tp_cfg = str(settings.get("TP_PCT") or "0").strip() or "0"
        sl_cfg = str(settings.get("SL_PCT") or "0").strip() or "0"
        print("\nTP-relative cycle map:")
        print("  1) Quick current bot target (auto products, TP from settings)")
        print("  2) Quick scalp map (TP 2.0)")
        print("  3) Quick stretch map (TP 10.0)")
        print("  4) Advanced custom")
        s3 = input("Run type [1]: ").strip() or "1"
        if s3 in ("1", "2", "3"):
            if s3 == "1":
                tp_pct = tp_cfg
                label = f"current bot target TP={tp_cfg}%"
            elif s3 == "2":
                tp_pct = "2.0"
                label = "scalp preset TP=2.0%"
            else:
                tp_pct = "10.0"
                label = "stretch preset TP=10.0%"
            args = [
                "--mode", "cycle",
                "--recent-products", "12",
                "--tp-pct", str(tp_pct),
                "--adverse-pct", str(sl_cfg),
                "--bars-per-interval", "240",
                "--min-swing-pct", "0",
                "--min-bars", "2",
            ]
            print(
                f"Launching quick cycle map: {label}; products=auto(recent paper -> recent TDI -> default watchlist); "
                f"adverse={sl_cfg}%; bars=240; min_swing=auto; min_bars=2"
            )
            open_trough_wait_score_console(args)
            return
        if s3 != "4":
            print("Invalid selection.")
            return

        print("\nAdvanced custom cycle map:")
        print("Leave Product IDs blank to auto-use recent PAPER_BUY_SIGNAL symbols, then recent TDI symbols, then a default watchlist.")
        s4 = input("Product IDs csv [recent paper symbols]: ").strip()
        s5 = input("Recent unique PAPER_BUY_SIGNAL symbols [8]: ").strip() or "8"
        try:
            recent_products = int(s5)
        except Exception:
            print("Invalid recent product count.")
            return
        if recent_products < 1:
            recent_products = 1

        s6 = input("Target TP percent [settings]: ").strip()
        tp_pct = s6 if s6 else "0"

        s7 = input("Adverse move percent [settings SL]: ").strip()
        adverse_pct = s7 if s7 else "0"

        s8 = input("Candles per interval [240] (max 300): ").strip() or "240"
        try:
            bars_per_interval = int(s8)
        except Exception:
            print("Invalid candles per interval.")
            return
        if bars_per_interval < 30:
            bars_per_interval = 30
        if bars_per_interval > 300:
            bars_per_interval = 300

        s9 = input("Min swing percent [auto=TP/2 or 0.5]: ").strip()
        min_swing_pct = s9 if s9 else "0"

        s10 = input("Min bars between swings [2]: ").strip() or "2"
        try:
            min_bars = int(s10)
        except Exception:
            print("Invalid min bars.")
            return
        if min_bars < 1:
            min_bars = 1

        args = [
            "--mode", "cycle",
            "--recent-products", str(recent_products),
            "--tp-pct", str(tp_pct),
            "--adverse-pct", str(adverse_pct),
            "--bars-per-interval", str(bars_per_interval),
            "--min-swing-pct", str(min_swing_pct),
            "--min-bars", str(min_bars),
        ]
        if s4:
            args.extend(["--products", s4])

        open_trough_wait_score_console(args)
        return

        s8 = input("Candles per interval [240] (max 300): ").strip() or "240"
        try:
            bars_per_interval = int(s8)
        except Exception:
            print("Invalid candles per interval.")
            return
        if bars_per_interval < 30:
            bars_per_interval = 30
        if bars_per_interval > 300:
            bars_per_interval = 300

        s9 = input("Min swing percent [auto=TP/2 or 0.5]: ").strip()
        min_swing_pct = s9 if s9 else "0"

        s10 = input("Min bars between swings [2]: ").strip() or "2"
        try:
            min_bars = int(s10)
        except Exception:
            print("Invalid min bars.")
            return
        if min_bars < 1:
            min_bars = 1

        args = [
            "--mode", "cycle",
            "--recent-products", str(recent_products),
            "--tp-pct", str(tp_pct),
            "--adverse-pct", str(adverse_pct),
            "--bars-per-interval", str(bars_per_interval),
            "--min-swing-pct", str(min_swing_pct),
            "--min-bars", str(min_bars),
        ]
        if s4:
            args.extend(["--products", s4])

        open_trough_wait_score_console(args)
        return

    print("\nTDI entry attribution:")
    print("  1) PAPER_BUY_SIGNAL entries")
    print("  2) BUY_OK entries")
    print("  3) BOTH")
    s3 = input("Entry source [1]: ").strip() or "1"
    if s3 == "1":
        entry_source = "paper"
    elif s3 == "2":
        entry_source = "buy"
    elif s3 == "3":
        entry_source = "both"
    else:
        print("Invalid selection.")
        return

    s4 = input("Latest joined rows in report [40]: ").strip() or "40"
    try:
        latest_rows = int(s4)
    except Exception:
        print("Invalid latest rows.")
        return
    if latest_rows < 1:
        latest_rows = 1

    s5 = input("Activity/TDI tail lines to include in zip [5000]: ").strip() or "5000"
    try:
        tail_lines = int(s5)
    except Exception:
        print("Invalid tail lines.")
        return
    if tail_lines < 500:
        tail_lines = 500

    open_trough_wait_score_console([
        "--mode", "tdi",
        "--entry-source", entry_source,
        "--latest-rows", str(latest_rows),
        "--tail-lines", str(tail_lines),
    ])


# ---------------------------------------------------------------------------
# Live snapshot writer / website bridge
# ---------------------------------------------------------------------------


def _latest_env_file() -> str:
    try:
        handoffs = Path("logs") / "handoffs"
        cand = sorted(handoffs.glob("live_snapshot_bridge_*.env"), key=lambda p: p.stat().st_mtime)
        if cand:
            return str(cand[-1])
    except Exception:
        pass
    return _LIVE_SNAPSHOT_ENV


def _parse_env_file(path: str) -> Dict[str, str]:
    out: Dict[str, str] = {}
    try:
        if os.path.exists(path):
            for line in _read_text(path).splitlines():
                s = line.strip()
                if not s or s.startswith("#") or "=" not in s:
                    continue
                k, v = s.split("=", 1)
                out[k.strip()] = v.strip()
    except Exception:
        pass
    return out


def _write_env_file(path: str, data: Dict[str, Any]) -> None:
    try:
        _ensure_parent_dir(path)
        lines = [f"{k}={v}" for k, v in data.items()]
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n".join(lines) + "\n")
    except Exception:
        pass


def _find_cloudflared_exe() -> str:
    # PATH first
    try:
        import shutil
        found = shutil.which("cloudflared")
        if found and os.path.isfile(found):
            return found
    except Exception:
        pass
    cands = [
        os.path.join(os.environ.get("ProgramFiles", ""), "cloudflared", "cloudflared.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "cloudflared", "cloudflared.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Microsoft", "WinGet", "Links", "cloudflared.exe"),
        os.path.join(os.environ.get("LOCALAPPDATA", ""), "Programs", "cloudflared", "cloudflared.exe"),
    ]
    for p in cands:
        if p and os.path.isfile(p):
            return p
    # Recursive fallback (can be a little slow, so only after the direct checks)
    for root in filter(None, [os.environ.get("ProgramFiles"), os.environ.get("ProgramFiles(x86)"), os.environ.get("LOCALAPPDATA")]):
        try:
            for base, _dirs, files in os.walk(root):
                for name in files:
                    if name.lower() == "cloudflared.exe":
                        return os.path.join(base, name)
        except Exception:
            continue
    return ""


def _find_ssh_exe() -> str:
    try:
        import shutil
        found = shutil.which("ssh")
        if found and os.path.isfile(found):
            return found
    except Exception:
        pass
    cands = [
        os.path.join(os.environ.get("WINDIR", "C:\\Windows"), "System32", "OpenSSH", "ssh.exe"),
        os.path.join(os.environ.get("ProgramFiles", ""), "OpenSSH", "ssh.exe"),
        os.path.join(os.environ.get("ProgramFiles(x86)", ""), "OpenSSH", "ssh.exe"),
    ]
    for p in cands:
        if p and os.path.isfile(p):
            return p
    return ""


def _random_token(n: int = 40) -> str:
    import random
    import string
    alphabet = string.ascii_letters + string.digits
    return "".join(random.choice(alphabet) for _ in range(int(n)))


def _store_named_pid(path: str, pid: int) -> None:
    _write_text(path, str(int(pid)))


def _load_named_pid(path: str) -> int:
    try:
        return int(_read_text(path).strip())
    except Exception:
        return 0


def _kill_named_pid(path: str) -> bool:
    pid = _load_named_pid(path)
    if pid <= 0:
        return False
    try:
        alive = spawn.is_alive(pid)
    except Exception:
        alive = False
    if alive:
        try:
            spawn.kill(pid)
        except Exception:
            pass
    try:
        _write_text(path, "")
    except Exception:
        pass
    return alive


def _sanitize_public_tunnel_url(url: str) -> str:
    u = str(url or "").strip().rstrip("/")
    if not u:
        return ""
    bad_bits = [
        "admin.localhost.run",
        "localhost.run/docs",
        "twitter.com/localhost_run",
        "http://localhost:3000",
    ]
    if any(bit in u for bit in bad_bits):
        return ""
    if not (u.startswith("https://") or u.startswith("http://")):
        return ""
    return u


def _wait_for_public_tunnel_result(logfile: str, timeout_s: float = 20.0) -> Dict[str, str]:
    import re
    out: Dict[str, str] = {"url": "", "provider": "", "error": "", "detail": ""}
    trycloudflare_pat = re.compile(r"https://[a-zA-Z0-9.-]+\.trycloudflare\.com")
    localhostrun_pat = re.compile(r"https://[a-zA-Z0-9.-]+\.(?:lhr\.life|localhost\.run)")
    tunneled_pat = re.compile(r"tunneled with tls termination,\s*(https://[^\s]+)", re.IGNORECASE)
    fatal_markers = [
        "failed to unmarshal quick Tunnel",
        "Error unmarshaling QuickTunnel response",
        "Worker threw exception",
        "status_code=\"500 Internal Server Error\"",
        "invalid character '<' looking for beginning of value",
        "invalid character 'e' looking for beginning of value",
        "Permission denied (publickey)",
        "administratively prohibited",
        "Connection closed by remote host",
    ]
    t0 = time.time()
    while time.time() - t0 < float(timeout_s):
        try:
            raw = _read_text(logfile)
        except Exception:
            raw = ""
        txt = raw or ""
        if txt:
            m = tunneled_pat.findall(txt)
            if m:
                for candidate in reversed(m):
                    clean = _sanitize_public_tunnel_url(candidate)
                    if clean:
                        out["url"] = clean
                        out["provider"] = "localhost.run"
                        return out
            m = trycloudflare_pat.findall(txt)
            if m:
                for candidate in reversed(m):
                    clean = _sanitize_public_tunnel_url(candidate)
                    if clean:
                        out["url"] = clean
                        out["provider"] = "cloudflare_quick_tunnel"
                        return out
            m = localhostrun_pat.findall(txt)
            if m:
                for candidate in reversed(m):
                    clean = _sanitize_public_tunnel_url(candidate)
                    if clean:
                        out["url"] = clean
                        out["provider"] = "localhost.run"
                        return out
            lines = [ln.strip() for ln in txt.splitlines() if ln.strip()]
            for line in reversed(lines):
                if any(mark in line for mark in fatal_markers):
                    out["error"] = "tunnel_failed"
                    out["detail"] = line[:500]
                    break
        time.sleep(0.75)
    return out


def _writer_args() -> List[str]:
    return [
        "-X", "utf8",
        "-u",
        "-m", "managers.logging_manager.live_snapshot_writer",
        "--interval", str(_LIVE_SNAPSHOT_INTERVAL_SEC),
    ]


def _http_args(token: str) -> List[str]:
    return [
        "-X", "utf8",
        "-u",
        "-m", "managers.logging_manager.live_snapshot_http",
        "--host", "127.0.0.1",
        "--port", str(_LIVE_SNAPSHOT_PORT),
        "--snapshot", "live_snapshot.json",
        "--token", str(token),
    ]


def _tunnel_args() -> List[str]:
    return ["tunnel", "--url", f"http://127.0.0.1:{_LIVE_SNAPSHOT_PORT}"]


def _localhostrun_tunnel_args() -> List[str]:
    return [
        "-o", "StrictHostKeyChecking=no",
        "-o", "ServerAliveInterval=30",
        "-o", "ExitOnForwardFailure=yes",
        "-R", f"80:127.0.0.1:{_LIVE_SNAPSHOT_PORT}",
        "nokey@localhost.run",
    ]


def start_live_snapshot_writer() -> None:
    py_exe = sys.executable
    try:
        old = _load_named_pid(_LIVE_SNAPSHOT_WRITER_PID)
        if old > 0 and spawn.is_alive(old):
            print(f"Live snapshot writer already running (pid={old}).")
            return
    except Exception:
        pass
    try:
        spawn.write_sentinel(_LIVE_SNAPSHOT_WRITER_LOG, "live_snapshot_writer")
    except Exception:
        pass
    info = spawn.launch_detached(py_exe, _writer_args(), _LIVE_SNAPSHOT_WRITER_LOG)
    pid = int(info.get("pid") or 0)
    _store_named_pid(_LIVE_SNAPSHOT_WRITER_PID, pid)
    print(f"Started live snapshot writer (pid={pid}).")


def start_live_snapshot_bridge() -> None:
    py_exe = sys.executable
    env_path = _latest_env_file()
    env_data = _parse_env_file(env_path)
    token = str(env_data.get("LIVE_SNAPSHOT_TOKEN") or "").strip() or _random_token(40)

    existing_http_pid = _load_named_pid(_LIVE_SNAPSHOT_HTTP_PID)
    existing_tunnel_pid = _load_named_pid(_LIVE_SNAPSHOT_TUNNEL_PID)
    existing_url = _sanitize_public_tunnel_url(str(env_data.get("LIVE_SNAPSHOT_URL") or "").strip())
    http_alive = existing_http_pid > 0 and spawn.is_alive(existing_http_pid)
    tunnel_alive = existing_tunnel_pid > 0 and spawn.is_alive(existing_tunnel_pid)

    if http_alive and tunnel_alive and existing_url:
        print(f"Live snapshot bridge already running (bridge pid={existing_http_pid}, tunnel pid={existing_tunnel_pid}).")
        print(f"LIVE_SNAPSHOT_URL={existing_url}")
        print(f"LIVE_SNAPSHOT_TOKEN={token}")
        return

    if not http_alive:
        try:
            _kill_named_pid(_LIVE_SNAPSHOT_HTTP_PID)
        except Exception:
            pass
        try:
            spawn.write_sentinel(_LIVE_SNAPSHOT_HTTP_LOG, "live_snapshot_http")
        except Exception:
            pass
        http_info = spawn.launch_detached(py_exe, _http_args(token), _LIVE_SNAPSHOT_HTTP_LOG)
        http_pid = int(http_info.get("pid") or 0)
        _store_named_pid(_LIVE_SNAPSHOT_HTTP_PID, http_pid)
        bridge_log = str(http_info.get("logfile") or time.strftime(_LIVE_SNAPSHOT_HTTP_LOG))
    else:
        http_pid = existing_http_pid
        bridge_log = str(env_data.get("BRIDGE_LOG") or time.strftime(_LIVE_SNAPSHOT_HTTP_LOG))

    time.sleep(2.0)

    def _write_bridge_env(url: str, tunnel_pid: int, tunnel_log: str, provider: str, tunnel_error: str = "") -> None:
        data = {
            "LIVE_SNAPSHOT_URL": (str(url).rstrip("/") + "/live_snapshot.json") if url else "",
            "LIVE_SNAPSHOT_TOKEN": token,
            "BRIDGE_PID": str(http_pid),
            "TUNNEL_PID": str(int(tunnel_pid or 0)),
            "BRIDGE_LOG": bridge_log,
            "TUNNEL_LOG": tunnel_log,
            "TUNNEL_PROVIDER": provider,
        }
        if provider == "cloudflare_quick_tunnel":
            cf_exe = _find_cloudflared_exe()
            if cf_exe:
                data["CLOUDFLARED"] = cf_exe
        if tunnel_error:
            data["TUNNEL_ERROR"] = tunnel_error
        _write_env_file(_LIVE_SNAPSHOT_ENV, data)

    if http_alive and tunnel_alive and not existing_url:
        existing_tunnel_log = str(env_data.get("TUNNEL_LOG") or "").strip()
        if existing_tunnel_log:
            result = _wait_for_public_tunnel_result(existing_tunnel_log, timeout_s=8.0)
            recovered_url = _sanitize_public_tunnel_url(str(result.get("url") or "").strip())
            recovered_provider = str(result.get("provider") or env_data.get("TUNNEL_PROVIDER") or "").strip() or "localhost.run"
            recovered_error = str(result.get("detail") or result.get("error") or env_data.get("TUNNEL_ERROR") or "").strip()
            if recovered_url:
                _write_bridge_env(recovered_url, existing_tunnel_pid, existing_tunnel_log, recovered_provider, recovered_error)
                print(f"Live snapshot bridge already running (bridge pid={existing_http_pid}, tunnel pid={existing_tunnel_pid}).")
                print(f"LIVE_SNAPSHOT_URL={recovered_url.rstrip('/')}/live_snapshot.json")
                print(f"LIVE_SNAPSHOT_TOKEN={token}")
                if recovered_provider:
                    print(f"Tunnel provider={recovered_provider}")
                return

    # Try Cloudflare Quick Tunnel first.
    cf_exe = _find_cloudflared_exe()
    if cf_exe:
        try:
            _kill_named_pid(_LIVE_SNAPSHOT_TUNNEL_PID)
        except Exception:
            pass
        try:
            spawn.write_sentinel(_LIVE_SNAPSHOT_TUNNEL_LOG, "live_snapshot_tunnel")
        except Exception:
            pass
        tunnel_info = spawn.launch_detached(cf_exe, _tunnel_args(), _LIVE_SNAPSHOT_TUNNEL_LOG)
        tunnel_pid = int(tunnel_info.get("pid") or 0)
        _store_named_pid(_LIVE_SNAPSHOT_TUNNEL_PID, tunnel_pid)
        tunnel_log = str(tunnel_info.get("logfile") or time.strftime(_LIVE_SNAPSHOT_TUNNEL_LOG))
        result = _wait_for_public_tunnel_result(tunnel_log, timeout_s=12.0)
        url = str(result.get("url") or "").strip()
        provider = str(result.get("provider") or "cloudflare_quick_tunnel").strip() or "cloudflare_quick_tunnel"
        tunnel_error = str(result.get("detail") or result.get("error") or "").strip()
        if url:
            _write_bridge_env(url, tunnel_pid, tunnel_log, provider)
            print(f"LIVE_SNAPSHOT_URL={str(url).rstrip('/')}/live_snapshot.json")
            print(f"LIVE_SNAPSHOT_TOKEN={token}")
            return
        try:
            if tunnel_pid > 0 and spawn.is_alive(tunnel_pid):
                spawn.kill(tunnel_pid)
        except Exception:
            pass
        _store_named_pid(_LIVE_SNAPSHOT_TUNNEL_PID, 0)
        if tunnel_error:
            print("Cloudflare Quick Tunnel failed; trying localhost.run fallback...")
            print(f"Tunnel detail: {tunnel_error}")

    # Fallback to localhost.run via ssh.
    ssh_exe = _find_ssh_exe()
    if not ssh_exe:
        tunnel_log = str(env_data.get("TUNNEL_LOG") or time.strftime(_LIVE_SNAPSHOT_TUNNEL_LOG))
        _write_bridge_env("", 0, tunnel_log, "none", "ssh_not_found_for_localhostrun_fallback")
        print("Local bridge is up, but no public tunnel could be started.")
        print("ssh.exe not found for localhost.run fallback.")
        print(f"Env file: {_latest_env_file()}")
        return

    try:
        spawn.write_sentinel(_LIVE_SNAPSHOT_TUNNEL_LOG, "live_snapshot_tunnel")
    except Exception:
        pass
    tunnel_info = spawn.launch_detached(ssh_exe, _localhostrun_tunnel_args(), _LIVE_SNAPSHOT_TUNNEL_LOG)
    tunnel_pid = int(tunnel_info.get("pid") or 0)
    _store_named_pid(_LIVE_SNAPSHOT_TUNNEL_PID, tunnel_pid)
    tunnel_log = str(tunnel_info.get("logfile") or time.strftime(_LIVE_SNAPSHOT_TUNNEL_LOG))
    result = _wait_for_public_tunnel_result(tunnel_log, timeout_s=30.0)
    url = str(result.get("url") or "").strip()
    tunnel_error = str(result.get("detail") or result.get("error") or "").strip()
    if url:
        _write_bridge_env(url, tunnel_pid, tunnel_log, "localhost.run")
        print(f"LIVE_SNAPSHOT_URL={str(url).rstrip('/')}/live_snapshot.json")
        print(f"LIVE_SNAPSHOT_TOKEN={token}")
        print("Tunnel provider=localhost.run")
        return

    _write_bridge_env("", tunnel_pid, tunnel_log, "localhost.run", tunnel_error or "public_url_not_detected")
    print("Local bridge is up, but public tunnel URL was not detected.")
    if tunnel_error:
        print(f"Tunnel detail: {tunnel_error}")
    print(f"Env file: {_latest_env_file()}")


def show_live_snapshot_bridge() -> None:

    env_path = _latest_env_file()
    data = _parse_env_file(env_path)
    writer_pid = _load_named_pid(_LIVE_SNAPSHOT_WRITER_PID)
    http_pid = _load_named_pid(_LIVE_SNAPSHOT_HTTP_PID)
    tunnel_pid = _load_named_pid(_LIVE_SNAPSHOT_TUNNEL_PID)
    current_url = _sanitize_public_tunnel_url(str(data.get("LIVE_SNAPSHOT_URL") or "").strip())
    tunnel_log = str(data.get("TUNNEL_LOG") or "").strip()
    if tunnel_pid > 0 and spawn.is_alive(tunnel_pid) and (not current_url) and tunnel_log:
        recovered = _wait_for_public_tunnel_result(tunnel_log, timeout_s=6.0)
        recovered_url = _sanitize_public_tunnel_url(str(recovered.get("url") or "").strip())
        if recovered_url:
            data["LIVE_SNAPSHOT_URL"] = recovered_url.rstrip("/") + "/live_snapshot.json"
            data["TUNNEL_PROVIDER"] = str(recovered.get("provider") or data.get("TUNNEL_PROVIDER") or "").strip() or "localhost.run"
            data.pop("TUNNEL_ERROR", None)
            _write_env_file(env_path, data)
    print("\nLive snapshot bridge status:")
    print(f"  WRITER_PID = {writer_pid}  alive={spawn.is_alive(writer_pid) if writer_pid > 0 else False}")
    print(f"  BRIDGE_PID = {http_pid}  alive={spawn.is_alive(http_pid) if http_pid > 0 else False}")
    print(f"  TUNNEL_PID = {tunnel_pid}  alive={spawn.is_alive(tunnel_pid) if tunnel_pid > 0 else False}")
    print(f"  ENV_FILE = {env_path}")
    for k in ["LIVE_SNAPSHOT_URL", "LIVE_SNAPSHOT_TOKEN", "TUNNEL_PROVIDER", "CLOUDFLARED", "BRIDGE_LOG", "TUNNEL_LOG", "TUNNEL_ERROR"]:
        if k in data:
            print(f"  {k} = {data.get(k)}")


def stop_live_snapshot_bridge() -> None:
    a = _kill_named_pid(_LIVE_SNAPSHOT_TUNNEL_PID)
    b = _kill_named_pid(_LIVE_SNAPSHOT_HTTP_PID)
    print(f"Stopped tunnel? {a} | stopped bridge? {b}")


def stop_live_snapshot_writer() -> None:
    a = _kill_named_pid(_LIVE_SNAPSHOT_WRITER_PID)
    print(f"Stopped live snapshot writer? {a}")


def live_snapshot_menu() -> None:
    while True:
        print("\nLive snapshot / website bridge:")
        print("  1) Start live snapshot writer")
        print("  2) Start public live snapshot bridge")
        print("  3) Start BOTH")
        print("  4) Show current URL/token/status")
        print("  5) Stop bridge")
        print("  6) Stop writer")
        print("  7) Stop BOTH")
        print("  9) Back")
        sel = input("> ").strip() or "9"
        if sel == "9":
            return
        if sel == "1":
            start_live_snapshot_writer()
            continue
        if sel == "2":
            start_live_snapshot_bridge()
            continue
        if sel == "3":
            start_live_snapshot_writer()
            start_live_snapshot_bridge()
            continue
        if sel == "4":
            show_live_snapshot_bridge()
            continue
        if sel == "5":
            stop_live_snapshot_bridge()
            continue
        if sel == "6":
            stop_live_snapshot_writer()
            continue
        if sel == "7":
            stop_live_snapshot_bridge()
            stop_live_snapshot_writer()
            continue
        print("Unknown selection.")


# ---------------------------------------------------------------------------
# Main menu
# ---------------------------------------------------------------------------


def sell_all_menu(settings: Dict[str, Any]) -> None:
    """
    Menu hotkey: SELL ALL / complete liquidation.

    Does nothing unless operator confirms by typing SELLALL.
    DRY preview available by typing DRY.
    """
    def _audit_paths(stamp: str) -> Dict[str, str]:
        base = os.path.join("logs", "updates", f"sell_all_audit_{stamp}")
        return {
            "base": base,
            "pre_pnl": os.path.join(base, "pre_pnl_snapshot.txt"),
            "post_pnl": os.path.join(base, "post_pnl_snapshot.txt"),
            "sell_all_result": os.path.join(base, "sell_all_result.json"),
            "summary": os.path.join(base, "summary.txt"),
            "settings_snapshot": os.path.join(base, "run_settings.json"),
            "live_snapshot": os.path.join(base, "live_snapshot.json"),
            "tracked_account": os.path.join(base, "tracked_account_snapshot.json"),
            "decision_replay": os.path.join(base, "decision_replay_snapshot.json"),
            "wm3_support": os.path.join(base, "wm3_support_snapshot.json"),
            "update_jsonl": os.path.join("logs", "updates", "UPDATE_LOG.jsonl"),
            "update_md": os.path.join("logs", "updates", "UPDATE_LOG.md"),
        }

    def _copy_if_exists(src: str, dst: str) -> None:
        try:
            if os.path.exists(src):
                _ensure_parent_dir(dst)
                with open(src, "rb") as rf, open(dst, "wb") as wf:
                    wf.write(rf.read())
        except Exception:
            pass

    def _write_text(path: str, value: str) -> None:
        try:
            _ensure_parent_dir(path)
            with open(path, "w", encoding="utf-8") as fh:
                fh.write(value)
        except Exception:
            pass

    def _capture_context(paths: Dict[str, str], cfg: Dict[str, Any]) -> None:
        repo_root = _repo_root()
        settings_candidates = [
            os.path.join(repo_root, "run_settings.json"),
            os.path.join(repo_root, "managers", "config_manager", "run_settings.json"),
        ]
        copied = False
        for candidate in settings_candidates:
            if os.path.exists(candidate):
                _copy_if_exists(candidate, paths["settings_snapshot"])
                copied = True
                break
        if not copied:
            try:
                _write_text(paths["settings_snapshot"], json.dumps(cfg or {}, indent=2))
            except Exception:
                pass
        _copy_if_exists(os.path.join(repo_root, "live_snapshot.json"), paths["live_snapshot"])
        _copy_if_exists(os.path.join(repo_root, "tracked_account_snapshot.json"), paths["tracked_account"])
        _copy_if_exists(os.path.join(repo_root, "decision_replay_snapshot.json"), paths["decision_replay"])
        _copy_if_exists(os.path.join(repo_root, "wm3_support_snapshot.json"), paths["wm3_support"])

    def _capture_pnl_snapshot_to_file(out_path: str) -> str:
        import subprocess
        repo_root = _repo_root()
        args = [sys.executable, "-X", "utf8", "-u", "managers\\logging_manager\\diag_pnl_snapshot.py"]
        try:
            proc = subprocess.run(
                args,
                cwd=repo_root,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=180,
                check=False,
            )
            snapshot_text = proc.stdout or ""
            if proc.stderr:
                snapshot_text += "\n[stderr]\n" + proc.stderr
            if not snapshot_text.strip():
                snapshot_text = f"[sell_all audit] pnl snapshot produced no output; exit_code={proc.returncode}\n"
            _write_text(out_path, snapshot_text)
            return f"ok exit_code={proc.returncode}"
        except Exception as e:
            msg = f"[sell_all audit] pnl snapshot failed: {e}\n"
            _write_text(out_path, msg)
            return f"error {e}"

    def _append_audit_log(stamp: str, paths: Dict[str, str], preview: bool) -> None:
        try:
            row = {
                "ts": stamp,
                "type": "sell_all_audit",
                "preview": bool(preview),
                "pre_pnl": paths["pre_pnl"],
                "post_pnl": paths["post_pnl"],
                "sell_all_result": paths["sell_all_result"],
                "settings_snapshot": paths["settings_snapshot"],
                "live_snapshot": paths["live_snapshot"],
                "tracked_account_snapshot": paths["tracked_account"],
                "decision_replay_snapshot": paths["decision_replay"],
                "wm3_support_snapshot": paths["wm3_support"],
                "mechanic": "MM28",
            }
            _ensure_parent_dir(paths["update_jsonl"])
            with open(paths["update_jsonl"], "a", encoding="utf-8") as fh:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
            with open(paths["update_md"], "a", encoding="utf-8") as fh:
                fh.write("\n## " + stamp + "\n")
                fh.write("- type: sell_all_audit\n")
                fh.write(f"- preview: {bool(preview)}\n")
                fh.write("- pre_pnl: " + paths["pre_pnl"] + "\n")
                fh.write("- post_pnl: " + paths["post_pnl"] + "\n")
                fh.write("- sell_all_result: " + paths["sell_all_result"] + "\n")
        except Exception:
            pass

    print("\n" + "=" * 72)
    print("DANGER: SELL ALL / COMPLETE LIQUIDATION")
    print("- This will MARKET-SELL all non-USD assets in the active PFID.")
    print("- Stop the run loop first (hotkey B).")
    print("- Type DRY for a preview (no orders).")
    print("=" * 72 + "\n")

    resp = input("Type SELLALL to confirm, DRY for preview, or ENTER to cancel: ").strip().upper()
    if not resp:
        print("Canceled.")
        return

    try:
        stop_run_console()
    except Exception:
        pass

    try:
        from managers.orders_manager.limit_maker import sell_all_positions
    except Exception as e:
        print(f"[SELL_ALL ERROR] Could not import sell_all_positions: {e}")
        return

    cfg = dict(settings or {})
    cfg["AUTO_TRADE"] = False

    stamp = time.strftime("%Y%m%d_%H%M%S")
    paths = _audit_paths(stamp)
    _capture_context(paths, cfg)
    pre_status = _capture_pnl_snapshot_to_file(paths["pre_pnl"])

    if resp == "DRY":
        cfg["DRY"] = True
        print("\n[SELL_ALL PREVIEW] DRY=True (no orders will be placed)\n")
        out = sell_all_positions(settings=cfg, cancel_orders_first=False, verbose=True, min_notional_usd=0.0)
        print("\n[SELL_ALL PREVIEW RESULT]")
        try:
            print(json.dumps(out, indent=2))
            _write_text(paths["sell_all_result"], json.dumps(out, indent=2))
        except Exception:
            print(out)
            _write_text(paths["sell_all_result"], str(out))
        post_status = _capture_pnl_snapshot_to_file(paths["post_pnl"])
        _write_text(paths["summary"], "\n".join([
            f"stamp={stamp}",
            "mode=DRY",
            f"pre_pnl_status={pre_status}",
            f"post_pnl_status={post_status}",
            f"sell_all_result={paths['sell_all_result']}",
        ]) + "\n")
        _append_audit_log(stamp, paths, preview=True)
        print(f"\n[SELL_ALL AUDIT] {paths['base']}")
        return

    if resp != "SELLALL":
        print("Canceled (confirmation not received).")
        return

    cfg["DRY"] = False
    print("\n[SELL_ALL EXECUTE] Proceeding with liquidation...\n")
    out = sell_all_positions(settings=cfg, cancel_orders_first=True, verbose=True, min_notional_usd=0.0)

    print("\n[SELL_ALL RESULT]")
    try:
        print(json.dumps(out, indent=2))
        _write_text(paths["sell_all_result"], json.dumps(out, indent=2))
    except Exception:
        print(out)
        _write_text(paths["sell_all_result"], str(out))

    post_status = _capture_pnl_snapshot_to_file(paths["post_pnl"])
    _write_text(paths["summary"], "\n".join([
        f"stamp={stamp}",
        "mode=EXECUTE",
        f"pre_pnl_status={pre_status}",
        f"post_pnl_status={post_status}",
        f"sell_all_result={paths['sell_all_result']}",
    ]) + "\n")
    _append_audit_log(stamp, paths, preview=False)
    print(f"\n[SELL_ALL AUDIT] {paths['base']}")

def menu() -> None:
    settings = load_settings()
    print(_header(settings))
    _print_settings(settings)
    _print_universe(settings)

    while True:
        print("A Start run loop")
        print("B Stop run loop")
        print("C Balances viewer")
        print("D Quick test menu")
        print("E Settings editor")
        print("H PnL / history snapshot")
        print("G Run diagnostics")
        print("W Wait tool (paper + event watch)")
        print("V Live snapshot / website bridge")
        print("S WM4 localhost website sandbox")
        print("M Toggle Majors (ON/OFF)")
        print("J Edit Majors List")
        print("T Toggle Universe Mode (TOP/LIST)")
        print("U Set Universe Top")
        print("L Set Universe List")
        print("X SELL ALL (LIQUIDATE) - DANGER")
        print("Q Quit")
        sel = input("Select or hotkey: ").strip().upper()

        try:
            if sel == "A":
                start_run_console()
            elif sel == "B":
                stop_run_console()
            elif sel == "C":
                open_balance_viewer_console()
            elif sel == "D":
                quick_test(settings)
            elif sel == "E":
                settings = edit_settings(settings)
            elif sel == "H":
                open_pnl_snapshot_console()
            elif sel == "G":
                run_diagnostics_menu()
            elif sel == "W":
                trough_wait_score_menu()
            elif sel == "V":
                live_snapshot_menu()
            elif sel == "S":
                start_wm4_localhost_sandbox()
            elif sel == "M":
                settings = toggle_majors(settings)
            elif sel == "J":
                settings = edit_majors_list(settings)
            elif sel == "T":
                settings = toggle_universe_mode(settings)
            elif sel == "U":
                settings = set_universe_top(settings)
            elif sel == "L":
                settings = set_universe_list(settings)
            elif sel == "X":
                sell_all_menu(settings)
            elif sel == "Q":
                print("Bye.")
                break
            else:
                print("Unknown selection.")
        except Exception:
            print("\n[MENU ERROR] Action failed; returning to menu.\n")
            traceback.print_exc()
        # keep header fresh each loop
        print("\n" + _header(settings))


if __name__ == "__main__":
    try:
        menu()
    except KeyboardInterrupt:
        print("\nInterrupted.")



# MM16_MENU_SL_INV









