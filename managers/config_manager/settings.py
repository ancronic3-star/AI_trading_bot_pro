import json
import os
from typing import Any, Dict, List, Optional

# Project root = parent of "managers"
_ROOT_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
SETTINGS_PATH = os.path.join(_ROOT_DIR, "run_settings.json")
SEED_SETTINGS_PATH = os.path.join(_ROOT_DIR, "run_settings.seed.json")

LEGACY_DEFAULT_SETTINGS: Dict[str, Any] = {
    "DRY": False,
    "AUTO_TRADE": True,

    # sizing
    "SOLDIER_USD": 2.0,

    # gates
    "MIN_TOPBOOK_USD": 250.0,
    "MAX_SPREAD_PCT": 1.0,          # percent, e.g. 1.0 = 1.00%
    "MIN_DMID_BPS": 1.0,            # basis points, e.g. 1.0 = 1 bp
    "BOOK_PRESSURE_MIN": 0.62,      # 0..1

    "COOLDOWN_TICKS": 62,
    "TOP_N": 8,
    "TICK_SEC": 3.0,
    "BUY_MAX_TRIES_PER_TICK": 1,
    "MAX_BUYS_PER_TICK": 1,
    "BUY_GLOBAL_COOLDOWN_SEC": 30.0,
    "BUY_STALE_CANCEL_SEC": 15.0,
    "BUY_MAX_OPEN": 1,
    "BUY_FAIL_COOLDOWN_SEC": 180.0,

    # exits
    "TP_PCT": 4.4,
    "SL_PCT": 2,
    # MM23: use Coinbase exchange-managed attached TP/SL on BUY (trigger_bracket_gtc)
    "EXIT_ATTACHED_TPSL": False,


    # ids
    "DEFAULT_PRODUCT_ID": "XRP-USD",
    "PFID": "",
    "PROFILE": "KOKO",
    "PORTFOLIO": "KOKO",

    # universe
    "UNIVERSE_MODE": "TOP",         # TOP or LIST
    "UNIVERSE_TOP": 30,
    "UNIVERSE_LIST": [],

    # majors
    "MAJORS_INCLUDE": False,
    "MAJORS_LIST": [],
}

_LIST_KEYS = {"UNIVERSE_LIST", "MAJORS_LIST"}
_FLOAT_KEYS = {
    "SOLDIER_USD", "MIN_TOPBOOK_USD", "MAX_SPREAD_PCT", "MIN_DMID_BPS",
    "BOOK_PRESSURE_MIN", "TICK_SEC", "TP_PCT", "SL_PCT",
    "BUY_GLOBAL_COOLDOWN_SEC", "BUY_STALE_CANCEL_SEC", "BUY_FAIL_COOLDOWN_SEC",
}
_INT_KEYS = {
    "COOLDOWN_TICKS", "TOP_N", "UNIVERSE_TOP",
    "BUY_MAX_TRIES_PER_TICK", "MAX_BUYS_PER_TICK", "BUY_MAX_OPEN",
}
_BOOL_KEYS = {"DRY", "AUTO_TRADE", "MAJORS_INCLUDE"}


def _coerce_types(d: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(d)

    for k in _BOOL_KEYS:
        if k in out:
            out[k] = bool(out[k])

    for k in _INT_KEYS:
        if k in out:
            try:
                out[k] = int(out[k])
            except Exception:
                pass

    for k in _FLOAT_KEYS:
        if k in out:
            try:
                out[k] = float(out[k])
            except Exception:
                pass

    for k in _LIST_KEYS:
        if k in out:
            v = out[k]
            if v is None:
                out[k] = []
            elif isinstance(v, list):
                out[k] = v
            else:
                # allow comma-separated strings
                if isinstance(v, str):
                    out[k] = [x.strip() for x in v.split(",") if x.strip()]
                else:
                    out[k] = []

    # normalize product id
    pid = (out.get("DEFAULT_PRODUCT_ID") or "").strip().upper()
    if pid and "-" not in pid:
        pid = pid + "-USD"
    if pid:
        out["DEFAULT_PRODUCT_ID"] = pid

    # normalize UNIVERSE_MODE
    um = (out.get("UNIVERSE_MODE") or "TOP").strip().upper()
    out["UNIVERSE_MODE"] = "LIST" if um == "LIST" else "TOP"

    return out


def _load_seed_defaults() -> Dict[str, Any]:
    if not os.path.exists(SEED_SETTINGS_PATH):
        return {}
    try:
        with open(SEED_SETTINGS_PATH, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if isinstance(raw, dict):
            return _coerce_types(raw)
    except Exception:
        pass
    return {}


DEFAULT_SETTINGS: Dict[str, Any] = _load_seed_defaults() or dict(LEGACY_DEFAULT_SETTINGS)


def save_settings(data: Dict[str, Any], path: str = SETTINGS_PATH) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)
    merged = {}
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
            if isinstance(existing, dict):
                merged.update(existing)
        except Exception:
            pass
    if isinstance(data, dict):
        merged.update(data)
    tmp_path = f"{path}.tmp"
    with open(tmp_path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, sort_keys=True)
    os.replace(tmp_path, path)


def load_settings(path: str = SETTINGS_PATH) -> Dict[str, Any]:
    if not os.path.exists(path):
        d = _coerce_types(dict(DEFAULT_SETTINGS))
        save_settings(d, path)
        return d

    try:
        with open(path, "r", encoding="utf-8") as f:
            raw = json.load(f)
        if not isinstance(raw, dict):
            raise ValueError("run_settings.json is not a JSON object")
    except Exception:
        # fallback to defaults if file is corrupted
        d = _coerce_types(dict(DEFAULT_SETTINGS))
        save_settings(d, path)
        return d

    merged = dict(DEFAULT_SETTINGS)
    merged.update(raw)
    merged = _coerce_types(merged)
    return merged
