#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
PnL / history snapshot viewer (menu option H)

MM26 architecture fix:
- Current open rows are anchored to live balances/accounts, not fills.
- Fills are used for cost basis / realized history only.
- Unsupported, orphan, and negative unmatched rows are quarantined into an exceptions section.
- Entry point remains menu_manager.py::open_pnl_snapshot_console().
"""

from __future__ import annotations

import argparse
import csv
import json
import sys
import os
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


# --- project paths -----------------------------------------------------------


def _find_project_root() -> Path:
    here = Path(__file__).resolve()
    for cand in [here.parent, *here.parents]:
        if (cand / "logs").is_dir():
            return cand
    return here.parent


PROJECT_ROOT = _find_project_root()
LOGS_DIR = PROJECT_ROOT / "logs"
RUN_SETTINGS_PATH = PROJECT_ROOT / "run_settings.json"
LIVE_SNAPSHOT_PATH = PROJECT_ROOT / "live_snapshot.json"

# Ensure absolute imports like `from managers...` work even when this file is
# executed as a script.
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

FILLS_ALL = PROJECT_ROOT / "fills_all.json"
FILLS_DUMP = PROJECT_ROOT / "fills_dump.json"

_STABLE_BASES = {"USD", "USDC", "USDT"}
_EPS = 1e-12


# --- utils ------------------------------------------------------------------


def _load_json_any(path: Path) -> Optional[Any]:
    try:
        with path.open("r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        return None
    except json.JSONDecodeError:
        print(f"[WARN] Could not parse JSON at {path}", file=sys.stderr)
        return None
    except UnicodeDecodeError as exc:
        print(f"[WARN] Unicode error reading {path}: {exc}", file=sys.stderr)
        return None


def _decode_bytes(raw: bytes) -> str:
    for enc in ("utf-8", "latin-1"):
        try:
            return raw.decode(enc)
        except UnicodeDecodeError:
            continue
    return raw.decode("latin-1", errors="ignore")


def _safe_float(x: Any) -> Optional[float]:
    try:
        v = float(x)
        if v != v:
            return None
        return v
    except (TypeError, ValueError):
        return None


def _parse_time_iso(ts: Any) -> str:
    s = str(ts or "").strip()
    if not s:
        return ""
    try:
        s2 = s[:-1] + "+00:00" if s.endswith("Z") else s
        _ = datetime.fromisoformat(s2)
        return s
    except Exception:
        return s


def _approx_equal(a: float, b: float, rel_tol: float = 0.02, abs_tol: float = 1e-8) -> bool:
    if abs(a - b) <= abs_tol:
        return True
    scale = max(abs(a), abs(b), 1.0)
    return abs(a - b) <= (rel_tol * scale)


def _dec(x: Any, default: Optional[float] = 0.0) -> Optional[float]:
    v = _safe_float(x)
    return default if v is None else float(v)


def _to_plain(x: Any) -> Dict[str, Any]:
    if isinstance(x, dict):
        return x
    if x is None:
        return {}
    for meth in ("model_dump", "dict", "to_dict"):
        if hasattr(x, meth):
            try:
                d = getattr(x, meth)()
                if isinstance(d, dict):
                    return d
            except Exception:
                pass
    try:
        d = getattr(x, "__dict__", None)
        if isinstance(d, dict):
            return d
    except Exception:
        pass
    return {}


def _load_settings() -> Dict[str, Any]:
    obj = _load_json_any(RUN_SETTINGS_PATH)
    return obj if isinstance(obj, dict) else {}


def _resolve_pfid(settings: Dict[str, Any]) -> str:
    return str(os.environ.get("PFID") or settings.get("PFID") or "").strip()


def _load_live_snapshot_marks() -> Dict[str, float]:
    obj = _load_json_any(LIVE_SNAPSHOT_PATH)
    out: Dict[str, float] = {}
    if not isinstance(obj, dict):
        return out

    for row in obj.get("positions") or []:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("pair") or row.get("product_id") or "").strip().upper()
        mark = _safe_float(row.get("mark_price"))
        if pid and mark is not None and mark > 0:
            out[pid] = float(mark)

    for row in obj.get("coins") or []:
        if not isinstance(row, dict):
            continue
        pid = str(row.get("product_id") or row.get("pair") or "").strip().upper()
        price = _safe_float(row.get("price"))
        if pid and price is not None and price > 0 and pid not in out:
            out[pid] = float(price)

    return out


# --- fills loading -----------------------------------------------------------


def _load_fills_from_json_text(text: str) -> List[Dict[str, Any]]:
    text = text.strip()
    if not text:
        return []
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        fills: List[Dict[str, Any]] = []
        for line in text.splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
                if isinstance(obj, dict):
                    fills.append(obj)
            except Exception:
                continue
        return fills

    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    if isinstance(data, dict) and isinstance(data.get("fills"), list):
        return [x for x in data["fills"] if isinstance(x, dict)]
    return []


def _load_fills_from_file(path: Path) -> List[Dict[str, Any]]:
    try:
        raw = path.read_bytes()
    except FileNotFoundError:
        return []
    except Exception:
        return []

    text = _decode_bytes(raw)

    if path.suffix.lower() == ".csv":
        fills: List[Dict[str, Any]] = []
        try:
            reader = csv.DictReader(text.splitlines())
            for row in reader:
                if isinstance(row, dict):
                    fills.append(row)
        except Exception:
            return []
        return fills

    return _load_fills_from_json_text(text)


def _load_fills() -> Tuple[List[Dict[str, Any]], str]:
    fills: List[Dict[str, Any]] = []
    fills += _load_fills_from_file(FILLS_ALL)
    fills += _load_fills_from_file(FILLS_DUMP)

    try:
        fills.sort(key=lambda r: _parse_time_iso(r.get("time") or r.get("created_at") or ""))
    except Exception:
        pass

    src = ""
    if FILLS_ALL.exists():
        src = str(FILLS_ALL)
    elif FILLS_DUMP.exists():
        src = str(FILLS_DUMP)
    else:
        src = "fills"
    return fills, src


# --- account / balance fetch ------------------------------------------------


def _iter_accounts(client: Any, pfid: str) -> Iterable[Dict[str, Any]]:
    fn = getattr(client, "get_accounts", None) or getattr(client, "list_accounts", None)
    if not callable(fn):
        return []
    cursor = None
    for _ in range(30):
        kwargs: Dict[str, Any] = {"limit": 250}
        if cursor:
            kwargs["cursor"] = cursor
        if pfid:
            kwargs["portfolio_uuid"] = pfid
        try:
            raw = fn(**kwargs)
        except TypeError:
            try:
                raw = fn(portfolio_uuid=pfid) if pfid else fn()
            except Exception:
                break
        except Exception:
            break

        obj = _to_plain(raw)
        arr = obj.get("accounts") if isinstance(obj, dict) else (obj if isinstance(obj, list) else [])
        arr = arr or []
        for a in arr:
            d = a if isinstance(a, dict) else _to_plain(a)
            a_pfid = str(d.get("portfolio_uuid") or d.get("retail_portfolio_id") or "")
            if pfid and a_pfid and a_pfid != pfid:
                continue
            yield d

        if not (isinstance(obj, dict) and obj.get("has_next")):
            break
        cursor = obj.get("cursor") or None
        if not cursor:
            break


def _account_value_parts(a: Dict[str, Any]) -> Tuple[float, float, float]:
    av = a.get("available_balance") or {}
    hold = a.get("hold") or {}
    bal = a.get("balance") or {}
    available = _dec(av.get("value") if isinstance(av, dict) else av, 0.0) or 0.0
    hold_v = _dec(hold.get("value") if isinstance(hold, dict) else hold, 0.0) or 0.0
    total = _dec(bal.get("value") if isinstance(bal, dict) else bal, available + hold_v)
    if total is None or total <= 0.0:
        total = available + hold_v
    return max(0.0, available), max(0.0, hold_v), max(0.0, total)


def _get_client() -> Any:
    try:
        from managers.auth_manager.auth_jwt import get_client  # type: ignore
    except Exception as exc:
        raise RuntimeError(f"Could not import Coinbase client: {exc}") from exc
    return get_client()


def _live_balances_snapshot() -> Dict[str, Any]:
    settings = _load_settings()
    pfid = _resolve_pfid(settings)
    client = _get_client()
    accounts = list(_iter_accounts(client, pfid))

    open_positions: Dict[str, Dict[str, Any]] = {}
    cash_total = 0.0
    cash_available = 0.0
    for a in accounts:
        cur = str(a.get("currency") or a.get("asset") or "").strip().upper()
        if not cur:
            continue
        avail, hold, total = _account_value_parts(a)
        if total <= 0.0:
            continue
        if cur in _STABLE_BASES:
            cash_total += total
            cash_available += avail
            continue
        pid = f"{cur}-USD"
        open_positions[pid] = {
            "currency": cur,
            "product_id": pid,
            "qty": float(total),
            "available_qty": float(avail),
            "hold_qty": float(hold),
        }

    return {
        "settings": settings,
        "pfid": pfid,
        "accounts_count": len(accounts),
        "cash_total_usd": round(cash_total, 8),
        "cash_available_usd": round(cash_available, 8),
        "open_positions": open_positions,
    }


# --- quote fetch -------------------------------------------------------------


def _chunked(seq: List[str], n: int) -> Iterable[List[str]]:
    if n <= 0:
        n = 50
    for i in range(0, len(seq), n):
        yield seq[i : i + n]


def _parse_pricebook_mid(pb: Dict[str, Any]) -> Optional[float]:
    bid = _safe_float(pb.get("best_bid") or pb.get("bid"))
    ask = _safe_float(pb.get("best_ask") or pb.get("ask"))

    if bid is None:
        bids = pb.get("bids")
        if isinstance(bids, list) and bids:
            b0 = bids[0]
            if isinstance(b0, dict):
                bid = _safe_float(b0.get("price") or b0.get("bid"))
            elif isinstance(b0, (list, tuple)) and len(b0) >= 1:
                bid = _safe_float(b0[0])

    if ask is None:
        asks = pb.get("asks")
        if isinstance(asks, list) and asks:
            a0 = asks[0]
            if isinstance(a0, dict):
                ask = _safe_float(a0.get("price") or a0.get("ask"))
            elif isinstance(a0, (list, tuple)) and len(a0) >= 1:
                ask = _safe_float(a0[0])

    if bid is None or ask is None:
        return None
    if bid <= 0 or ask <= 0:
        return None
    return float((bid + ask) / 2.0)


def _best_bid_ask_mids(product_ids: List[str], batch_size: int = 50) -> Dict[str, float]:
    mids: Dict[str, float] = {}
    if not product_ids:
        return mids

    try:
        client = _get_client()
    except Exception as exc:
        print(f"[WARN] Could not create Coinbase client: {exc}", file=sys.stderr)
        return mids

    def _to_dict_any(x: Any) -> Optional[Dict[str, Any]]:
        if isinstance(x, dict):
            return x
        if x is None:
            return None
        for meth in ("model_dump", "dict", "to_dict"):
            if hasattr(x, meth):
                try:
                    d = getattr(x, meth)()
                    if isinstance(d, dict):
                        return d
                except Exception:
                    pass
        try:
            d = getattr(x, "__dict__", None)
            if isinstance(d, dict) and d:
                return d
        except Exception:
            pass
        return None

    def _extract_pricebooks(resp_any: Any) -> Optional[List[Any]]:
        if resp_any is None:
            return None
        if isinstance(resp_any, list):
            return resp_any
        if isinstance(resp_any, dict):
            pb = resp_any.get("pricebooks") or resp_any.get("pricebook") or resp_any.get("priceBooks")
            if isinstance(pb, dict):
                return [pb]
            if isinstance(pb, list):
                return pb
            return None
        for attr in ("pricebooks", "pricebook", "priceBooks"):
            if hasattr(resp_any, attr):
                try:
                    pb = getattr(resp_any, attr)
                    if isinstance(pb, dict):
                        return [pb]
                    if isinstance(pb, list):
                        return pb
                except Exception:
                    pass
        d = _to_dict_any(resp_any)
        if isinstance(d, dict):
            pb = d.get("pricebooks") or d.get("pricebook") or d.get("priceBooks")
            if isinstance(pb, dict):
                return [pb]
            if isinstance(pb, list):
                return pb
        return None

    def _get_pid(pb: Any) -> str:
        if isinstance(pb, dict):
            pid2 = pb.get("product_id") or pb.get("productId") or pb.get("PRODUCT_ID") or pb.get("id")
            return str(pid2 or "").strip().upper()
        for attr in ("product_id", "productId", "id"):
            if hasattr(pb, attr):
                try:
                    v = getattr(pb, attr)
                    if v:
                        return str(v).strip().upper()
                except Exception:
                    pass
        d = _to_dict_any(pb)
        if isinstance(d, dict):
            pid2 = d.get("product_id") or d.get("productId") or d.get("id")
            return str(pid2 or "").strip().upper()
        return ""

    def _get_mid(pb: Any) -> Optional[float]:
        if isinstance(pb, dict):
            return _parse_pricebook_mid(pb)
        d = _to_dict_any(pb)
        if isinstance(d, dict):
            return _parse_pricebook_mid(d)
        return None

    def _ingest(resp_any: Any) -> None:
        pricebooks = _extract_pricebooks(resp_any)
        if not isinstance(pricebooks, list) or not pricebooks:
            return
        for pb in pricebooks:
            pid2 = _get_pid(pb)
            if not pid2:
                continue
            mid = _get_mid(pb)
            if mid is not None:
                mids[pid2] = mid

    bad: List[str] = []
    for chunk in _chunked(product_ids, batch_size):
        try:
            resp = client.get_best_bid_ask(product_ids=chunk)  # type: ignore[attr-defined]
            _ingest(resp)
            continue
        except Exception as exc:
            print(f"[WARN] get_best_bid_ask failed for batch (fallback to per-pid): {exc}", file=sys.stderr)

        for pid in chunk:
            try:
                resp1 = client.get_best_bid_ask(product_ids=[pid])  # type: ignore[attr-defined]
                _ingest(resp1)
            except Exception:
                bad.append(pid)

    if bad:
        uniq = sorted(set(bad))
        preview = ", ".join(uniq[:10])
        more = "" if len(uniq) <= 10 else f" (+{len(uniq)-10} more)"
        print(f"[WARN] Skipped unsupported product_ids in get_best_bid_ask: {preview}{more}", file=sys.stderr)

    return mids


# --- PnL math ----------------------------------------------------------------


def _avg_cost_pnl_from_fills(fills: List[Dict[str, Any]]) -> Dict[str, Dict[str, Any]]:
    """
    Average-cost accounting on fills.

    - BUY: increases position and cost basis (px*sz + fee)
    - SELL: realizes pnl = (px*qty - fee) - avg_cost*qty, reduces cost basis.
      If oversold beyond position, excess is treated as flat proceeds (best-effort),
      but that excess must not contaminate live open inventory.
    """
    pos = defaultdict(float)
    cost_basis = defaultdict(float)
    realized = defaultdict(float)
    fees = defaultdict(float)
    buy_sz = defaultdict(float)
    buy_cost = defaultdict(float)

    last_buy_dt: Dict[str, datetime] = {}
    last_buy_time: Dict[str, str] = {}
    last_buy_px: Dict[str, float] = {}
    last_buy_sz2: Dict[str, float] = {}

    for f in fills:
        pid = (f.get("product_id") or f.get("pid") or "").strip().upper()
        side = (f.get("side") or "").strip().upper()
        px = _safe_float(f.get("price"))
        sz = _safe_float(f.get("size"))
        fee = _safe_float(f.get("fee")) or 0.0

        t_raw = f.get("time") or f.get("created_at") or f.get("trade_time")
        t_str = str(t_raw or "").strip()
        t_dt: Optional[datetime] = None
        if t_str:
            try:
                t2 = t_str[:-1] + "+00:00" if t_str.endswith("Z") else t_str
                t_dt = datetime.fromisoformat(t2)
            except Exception:
                t_dt = None

        if not pid or not side or px is None or sz is None:
            continue

        fees[pid] += fee

        if side == "BUY":
            pos[pid] += sz
            cost_basis[pid] += (px * sz) + fee
            buy_sz[pid] += sz
            buy_cost[pid] += (px * sz) + fee

            if t_str:
                if t_dt is not None:
                    prev = last_buy_dt.get(pid)
                    if prev is None or t_dt > prev:
                        last_buy_dt[pid] = t_dt
                        last_buy_time[pid] = t_str
                        last_buy_px[pid] = float(px)
                        last_buy_sz2[pid] = float(sz)
                elif pid not in last_buy_time:
                    last_buy_time[pid] = t_str
                    last_buy_px[pid] = float(px)
                    last_buy_sz2[pid] = float(sz)

        elif side == "SELL":
            proceeds = (px * sz) - fee
            if pos[pid] > _EPS and cost_basis[pid] > 0:
                qty = min(sz, pos[pid])
                avg = cost_basis[pid] / pos[pid]
                realized[pid] += (px * qty) - (avg * qty) - fee
                pos[pid] -= qty
                cost_basis[pid] -= avg * qty
                extra = sz - qty
                if extra > _EPS:
                    realized[pid] += px * extra
                    pos[pid] -= extra
            else:
                realized[pid] += proceeds
                pos[pid] -= sz

    out: Dict[str, Dict[str, Any]] = {}
    for pid in sorted(set(list(pos.keys()) + list(realized.keys()) + list(buy_sz.keys()))):
        p = float(pos[pid])
        open_cost = float(cost_basis[pid]) if cost_basis[pid] > 0 else 0.0
        avg_entry = (open_cost / p) if p > _EPS and open_cost > 0 else None
        if avg_entry is None and buy_sz[pid] > _EPS:
            avg_entry = buy_cost[pid] / buy_sz[pid]
        out[pid] = {
            "fills_position_size": p,
            "open_cost_basis_usd": open_cost,
            "avg_entry_px": avg_entry,
            "realized_pnl_usd": float(realized[pid]),
            "fees_usd": float(fees[pid]),
            "last_buy_time": last_buy_time.get(pid, ""),
            "last_buy_px": last_buy_px.get(pid),
            "last_buy_sz": last_buy_sz2.get(pid),
        }
    return out


def _extract_recent_buy_fills(fills: List[Dict[str, Any]], limit: int = 500) -> List[Dict[str, Any]]:
    rec: List[Tuple[datetime, Dict[str, Any]]] = []
    for f in fills:
        pid = (f.get("product_id") or f.get("pid") or "").strip().upper()
        side = (f.get("side") or "").strip().upper()
        if side != "BUY" or not pid:
            continue
        px = _safe_float(f.get("price"))
        sz = _safe_float(f.get("size"))
        if px is None or sz is None:
            continue
        t_raw = f.get("time") or f.get("created_at") or f.get("trade_time")
        t_str = str(t_raw or "").strip()
        if not t_str:
            continue
        try:
            t2 = t_str[:-1] + "+00:00" if t_str.endswith("Z") else t_str
            dt = datetime.fromisoformat(t2)
        except Exception:
            continue
        rec.append((dt, {"pid": pid, "time": t_str, "price": float(px), "size": float(sz)}))
    rec.sort(key=lambda x: x[0], reverse=True)
    return [row for _, row in rec[: max(0, int(limit or 0))]]


def _build_balance_anchored_snapshot() -> Tuple[Dict[str, Any], str]:
    live = _live_balances_snapshot()
    pfid = str(live.get("pfid") or "")
    fills, fills_src = _load_fills()
    fills_map = _avg_cost_pnl_from_fills(fills)
    recent_buys = _extract_recent_buy_fills(fills, limit=500)

    live_positions = live.get("open_positions") or {}
    quote_pids: List[str] = sorted([pid for pid in live_positions.keys() if isinstance(pid, str) and pid.endswith("-USD")])

    # Include the most recent BUY symbols for the recent-buys grading section.
    extra_pids: List[str] = []
    seen = set()
    for r in recent_buys[:50]:
        pid = str(r.get("pid") or "").strip().upper()
        if not pid or not pid.endswith("-USD"):
            continue
        base = pid.split("-", 1)[0].upper()
        if base in _STABLE_BASES or pid in seen:
            continue
        seen.add(pid)
        extra_pids.append(pid)

    mids = _best_bid_ask_mids(quote_pids + extra_pids, batch_size=50)
    fallback_marks = _load_live_snapshot_marks()
    for pid in list(quote_pids) + list(extra_pids):
        if pid not in mids:
            px = _safe_float(fallback_marks.get(pid))
            if px is not None and px > 0:
                mids[pid] = float(px)

    open_rows: Dict[str, Dict[str, Any]] = {}
    exceptions: List[Dict[str, Any]] = []
    realized_closed: Dict[str, Dict[str, Any]] = {}
    total_unrealized = 0.0
    total_realized = 0.0
    equity = float(live.get("cash_total_usd") or 0.0)

    for pid, hist in fills_map.items():
        total_realized += float(_safe_float(hist.get("realized_pnl_usd")) or 0.0)

    for pid, lp in sorted(live_positions.items()):
        qty = float(_safe_float(lp.get("qty")) or 0.0)
        hist = fills_map.get(pid) or {}
        fills_qty = float(_safe_float(hist.get("fills_position_size")) or 0.0)
        avg_entry = _safe_float(hist.get("avg_entry_px"))
        mid = _safe_float(mids.get(pid))
        if mid is None:
            mid = _safe_float(fallback_marks.get(pid))

        market_value = (mid * qty) if (mid is not None and qty > _EPS) else None
        if market_value is not None:
            equity += market_value

        unrealized = None
        unrealized_pct = None
        basis_status = "matched"

        if fills_qty <= _EPS or avg_entry is None or avg_entry <= 0:
            basis_status = "missing"
            exceptions.append({
                "type": "basis_missing_for_live_holding",
                "product_id": pid,
                "live_qty": round(qty, 8),
                "fills_qty": round(fills_qty, 8),
                "detail": "live balance exists but positive remaining fill basis was not found",
            })
        else:
            if not _approx_equal(fills_qty, qty, rel_tol=0.02, abs_tol=max(1e-8, qty * 0.001)):
                basis_status = "qty_mismatch"
                exceptions.append({
                    "type": "live_vs_fills_qty_mismatch",
                    "product_id": pid,
                    "live_qty": round(qty, 8),
                    "fills_qty": round(fills_qty, 8),
                    "detail": "using fills-derived average entry as best-effort basis",
                })
            if mid is not None and qty > _EPS:
                unrealized = float((mid - avg_entry) * qty)
                unrealized_pct = float((mid / avg_entry - 1.0) * 100.0)
                total_unrealized += unrealized

        if mid is None:
            exceptions.append({
                "type": "missing_live_mark",
                "product_id": pid,
                "live_qty": round(qty, 8),
                "detail": "no bid/ask or fallback mark available",
            })

        open_rows[pid] = {
            "product_id": pid,
            "qty": round(qty, 8),
            "available_qty": round(float(_safe_float(lp.get("available_qty")) or 0.0), 8),
            "hold_qty": round(float(_safe_float(lp.get("hold_qty")) or 0.0), 8),
            "avg_entry_px": None if avg_entry is None else float(avg_entry),
            "mid_px": None if mid is None else float(mid),
            "market_value_usd": None if market_value is None else float(market_value),
            "unrealized_pnl_usd": None if unrealized is None else float(unrealized),
            "unrealized_pnl_pct": None if unrealized_pct is None else float(unrealized_pct),
            "realized_pnl_usd": float(_safe_float(hist.get("realized_pnl_usd")) or 0.0),
            "basis_status": basis_status,
            "last_buy_time": str(hist.get("last_buy_time") or ""),
            "last_buy_px": _safe_float(hist.get("last_buy_px")),
            "last_buy_sz": _safe_float(hist.get("last_buy_sz")),
        }

    for pid, hist in sorted(fills_map.items()):
        if pid in open_rows:
            continue
        realized = float(_safe_float(hist.get("realized_pnl_usd")) or 0.0)
        fills_qty = float(_safe_float(hist.get("fills_position_size")) or 0.0)

        if not isinstance(pid, str) or not pid.endswith("-USD"):
            exceptions.append({
                "type": "unsupported_fill_product",
                "product_id": str(pid),
                "fills_qty": round(fills_qty, 8),
                "realized_pnl_usd": realized,
                "detail": "non-USD or malformed product id in fills history",
            })
            continue

        base = pid.split("-", 1)[0].upper()
        if base in _STABLE_BASES:
            continue

        if fills_qty < -_EPS:
            exceptions.append({
                "type": "negative_unmatched_inventory",
                "product_id": pid,
                "fills_qty": round(fills_qty, 8),
                "realized_pnl_usd": realized,
                "detail": "sell history exceeded tracked buy inventory",
            })
            continue

        if fills_qty > _EPS:
            exceptions.append({
                "type": "orphan_positive_fill_inventory",
                "product_id": pid,
                "fills_qty": round(fills_qty, 8),
                "realized_pnl_usd": realized,
                "detail": "fills imply open inventory but no live balance exists now",
            })
            continue

        if abs(realized) >= 0.01:
            realized_closed[pid] = {
                "product_id": pid,
                "realized_pnl_usd": realized,
                "fees_usd": float(_safe_float(hist.get("fees_usd")) or 0.0),
                "last_buy_time": str(hist.get("last_buy_time") or ""),
                "last_buy_px": _safe_float(hist.get("last_buy_px")),
                "last_buy_sz": _safe_float(hist.get("last_buy_sz")),
            }

    snapshot = {
        "meta": {
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "pfid": pfid,
            "source_open_positions": "live_balances",
            "fills_source": fills_src,
            "accounts_count": int(live.get("accounts_count") or 0),
            "cash_total_usd": float(live.get("cash_total_usd") or 0.0),
            "cash_available_usd": float(live.get("cash_available_usd") or 0.0),
            "equity_estimate_usd": round(equity, 8),
            "open_positions_count": len(open_rows),
            "exceptions_count": len(exceptions),
        },
        "open": open_rows,
        "realized": {
            "total_realized_usd": round(total_realized, 8),
            "closed_only": realized_closed,
        },
        "exceptions": exceptions,
        "_recent_buys": recent_buys,
    }
    return snapshot, "live_balances+fills"


# --- formatting --------------------------------------------------------------


def _fmt_pos(x: Any) -> str:
    try:
        v = float(x or 0.0)
        return f"{v:14.8f}"
    except Exception:
        return f"{'':14s}"


def _fmt_float(x: Any, width: int, prec: int, blank_if_none: bool = True) -> str:
    if x is None and blank_if_none:
        return " " * width
    try:
        v = float(x or 0.0)
        return f"{v:{width}.{prec}f}"
    except Exception:
        return " " * width


# --- output -----------------------------------------------------------------


def print_pnl_snapshot(snapshot: Dict[str, Any], source_label: str, show_json: bool = False, show_all: bool = False, recent_n: int = 15, recent_hours: float = 24.0) -> None:
    meta = snapshot.get("meta") if isinstance(snapshot, dict) else {}
    open_map = snapshot.get("open") if isinstance(snapshot, dict) else None
    realized = snapshot.get("realized") if isinstance(snapshot, dict) else {}
    exceptions = snapshot.get("exceptions") if isinstance(snapshot, dict) else []

    if show_json:
        json.dump(snapshot, sys.stdout, indent=2, sort_keys=True)
        return

    print("=== PNL / history snapshot ===\n")
    print(f"As of {datetime.now(timezone.utc).isoformat()}   |   Source: {source_label}")
    print(f"PFID: {meta.get('pfid') or '(not set)'}   |   Fills: {meta.get('fills_source') or 'none'}")
    print(
        f"Open positions: {int(meta.get('open_positions_count') or 0)}   |   "
        f"Cash USD: {_fmt_float(meta.get('cash_total_usd'), 10, 4, blank_if_none=False).strip()}   |   "
        f"Equity est: {_fmt_float(meta.get('equity_estimate_usd'), 10, 4, blank_if_none=False).strip()}\n"
    )

    if not isinstance(open_map, dict):
        print("[INFO] Snapshot JSON has no 'open' section.")
        return

    print("Open positions (balance-anchored):")
    print(f"{'pid':<14} {'qty':>14} {'avg_entry':>12} {'mid':>12} {'uPnL$':>10} {'uPnL%':>7} {'real$':>10}")
    print("-" * 92)

    tot_upnl = 0.0
    rows_out = 0
    for pid, row in sorted(open_map.items()):
        qty = _safe_float(row.get("qty")) or 0.0
        avg_entry = row.get("avg_entry_px")
        mid = row.get("mid_px")
        upnl = row.get("unrealized_pnl_usd")
        upnl_pct = row.get("unrealized_pnl_pct")
        real = _safe_float(row.get("realized_pnl_usd")) or 0.0

        if not show_all and qty <= _EPS:
            continue

        if upnl is not None:
            tot_upnl += float(upnl)
        rows_out += 1
        print(
            f"{pid:<14} "
            f"{_fmt_pos(qty)} "
            f"{_fmt_float(avg_entry, 12, 6)} "
            f"{_fmt_float(mid, 12, 6)} "
            f"{_fmt_float(upnl, 10, 4, blank_if_none=False)} "
            f"{_fmt_float(upnl_pct, 7, 2)} "
            f"{_fmt_float(real, 10, 4, blank_if_none=False)}"
        )

    print()
    print(f"Open totals  ->  unrealized: {tot_upnl:.4f} USD   |   realized history total: {float(_safe_float((realized or {}).get('total_realized_usd')) or 0.0):.4f} USD")

    closed_only = (realized or {}).get("closed_only") if isinstance(realized, dict) else {}
    if isinstance(closed_only, dict) and closed_only:
        print()
        print("Closed / realized-only history (top by |realized|):")
        print(f"{'pid':<14} {'real$':>12} {'fees$':>12} {'last_buy_time':<25}")
        print("-" * 68)
        items = sorted(
            closed_only.values(),
            key=lambda r: abs(_safe_float((r or {}).get("realized_pnl_usd")) or 0.0),
            reverse=True,
        )
        if not show_all:
            items = items[:20]
        for row in items:
            pid = str(row.get("product_id") or "")
            real = _safe_float(row.get("realized_pnl_usd")) or 0.0
            fees = _safe_float(row.get("fees_usd")) or 0.0
            last_buy_time = str(row.get("last_buy_time") or "")
            print(
                f"{pid:<14} "
                f"{_fmt_float(real, 12, 4, blank_if_none=False)} "
                f"{_fmt_float(fees, 12, 4, blank_if_none=False)} "
                f"{last_buy_time:<25}"
            )

    if isinstance(exceptions, list) and exceptions:
        print()
        print("Exceptions / quarantined rows:")
        print(f"{'type':<28} {'pid':<14} {'fills/live':>16} {'detail'}")
        print("-" * 110)
        rows = exceptions if show_all else exceptions[:30]
        for ex in rows:
            if not isinstance(ex, dict):
                continue
            typ = str(ex.get("type") or "")
            pid = str(ex.get("product_id") or "")
            mixed = ""
            if "fills_qty" in ex or "live_qty" in ex:
                mixed = f"{str(ex.get('fills_qty', ''))}/{str(ex.get('live_qty', ''))}"
            detail = str(ex.get("detail") or "")
            print(f"{typ:<28} {pid:<14} {mixed:>16} {detail}")
        if not show_all and len(exceptions) > len(rows):
            print(f"[INFO] {len(exceptions) - len(rows)} more exception rows hidden (use --all).")

    try:
        rn = int(recent_n or 0)
    except Exception:
        rn = 0
    try:
        rh = float(recent_hours or 0.0)
    except Exception:
        rh = 0.0

    if rn > 0:
        rec_any = snapshot.get("_recent_buys")
        rec_list: List[Dict[str, Any]] = rec_any if isinstance(rec_any, list) else []
        cutoff = None
        if rh > 0:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=rh)

        out_rows: List[Dict[str, Any]] = []
        mids_for_recent = {pid: _safe_float((open_map.get(pid) or {}).get("mid_px")) for pid in open_map.keys()}
        fallback_marks = _load_live_snapshot_marks()
        for r in rec_list:
            if not isinstance(r, dict):
                continue
            pid = str(r.get("pid") or "").strip().upper()
            t_str = str(r.get("time") or "").strip()
            px = _safe_float(r.get("price"))
            sz = _safe_float(r.get("size"))
            if not pid or not t_str or px is None or sz is None:
                continue
            try:
                t2 = t_str[:-1] + "+00:00" if t_str.endswith("Z") else t_str
                dt = datetime.fromisoformat(t2)
            except Exception:
                continue
            if cutoff is not None and dt < cutoff:
                continue
            out_rows.append({"dt": dt, "pid": pid, "buy_px": float(px), "size": float(sz)})

        out_rows.sort(key=lambda x: x["dt"], reverse=True)
        out_rows = out_rows[:rn]

        if out_rows:
            print()
            hlabel = f"last {rh:g}h" if rh > 0 else "all"
            print(f"Recent buys ({hlabel}, newest first; n={len(out_rows)}):")
            print(f"{'pid':<14} {'buy_time':<20} {'buy_px':>10} {'mid':>10} {'ret%':>7} {'ret$':>10}")
            print("-" * 80)
            green = 0
            for r in out_rows:
                pid = r["pid"]
                dt = r["dt"]
                buy_px = r["buy_px"]
                size = r["size"]
                mid = mids_for_recent.get(pid)
                if mid is None:
                    mid = _safe_float(fallback_marks.get(pid))
                ret_pct = None
                ret_usd = None
                if mid is not None and buy_px > 0:
                    ret_pct = (mid / buy_px - 1.0) * 100.0
                    ret_usd = (mid - buy_px) * size
                if ret_pct is not None and ret_pct > 0:
                    green += 1
                bt2 = dt.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S")
                print(
                    f"{pid:<14} "
                    f"{bt2:<20} "
                    f"{buy_px:10.6f} "
                    f"{_fmt_float(mid, 10, 6)} "
                    f"{_fmt_float(ret_pct, 7, 2)} "
                    f"{_fmt_float(ret_usd, 10, 4, blank_if_none=False)}"
                )
            print(f"[INFO] recent_buys_green={green}/{len(out_rows)} ({hlabel})")

    if not show_all:
        print(f"[INFO] Showing {rows_out} open rows. Use --all to expand realized/exceptions sections.")


def main(argv: Optional[List[str]] = None) -> None:
    parser = argparse.ArgumentParser(description="PnL / history snapshot viewer")
    parser.add_argument("--hold", action="store_true", help="wait for Enter before exiting")
    parser.add_argument("--json", action="store_true", help="print raw JSON snapshot instead of table")
    parser.add_argument("--all", action="store_true", help="show all rows (including realized/exceptions expansions)")
    parser.add_argument("--recent", type=int, default=15, help="show N recent BUY fills (0 to disable)")
    parser.add_argument("--recent-hours", type=float, default=24.0, help="recent buys window in hours (default 24; 0=all)")
    args = parser.parse_args(argv)

    try:
        snap, src = _build_balance_anchored_snapshot()
    except Exception as exc:
        print("=== PNL / history snapshot ===\n")
        print(f"[ERROR] Could not build balance-anchored PnL snapshot: {exc}")
        if args.hold:
            try:
                input("\nPress Enter to close...")
            except Exception:
                pass
        return

    print_pnl_snapshot(snap, src, show_json=args.json, show_all=args.all, recent_n=args.recent, recent_hours=args.recent_hours)
    if args.hold:
        try:
            input("\nPress Enter to close...")
        except Exception:
            pass


if __name__ == "__main__":
    main()
