"""
universe_dynamic.py - dynamic USD universe builder for run_manager.

Drop-in replacement, full-file overwrite.
"""

from __future__ import annotations

from typing import List, Dict, Any, Tuple
from dataclasses import dataclass
import logging
import json
from datetime import datetime, timezone

_LOG = logging.getLogger("managers.universe_manager.universe_dynamic")


# Last-seen computed 24h USD quote volumes (debug/UI only).
# Populated by _fetch_usd_products(). Keys are product_id, values are USD volume.
LAST_VOL24H_USD: dict[str, float] = {}
LAST_DIAG: dict[str, Any] = {}
LAST_COHORT_BY_PID: dict[str, str] = {}
LAST_TAPE_QUALITY_BY_PID: dict[str, float] = {}

# Hard default majors used only when we explicitly want to force-include them.
MAJORS: Tuple[str, ...] = ("BTC-USD", "ETH-USD", "SOL-USD", "XRP-USD")

# Quote currencies we consider (run_manager already enforces USD-only quotes,
# but we keep this explicit here).
USD_QUOTES: Tuple[str, ...] = ("USD",)

# Some assets we generally do NOT want to trade as "alpha" even if they
# have large books (stablecoins / pseudo‑dollars).
STABLE_BASES: Tuple[str, ...] = (
    "USD", "USDT", "USDC", "USD1", "DAI", "PYUSD", "FDUSD", "TUSD", "USDS"
)


# ---------- small helpers ----------

def _as_bool(value: Any, default: bool = False) -> bool:
    """
    Best-effort conversion to bool.

    Accepts bools, ints/floats, and strings like 'true'/'false',
    'yes'/'no', 'on'/'off', '1'/'0'. Anything unknown falls back to default.
    """
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    if isinstance(value, (int, float)):
        return bool(value)
    if isinstance(value, str):
        v = value.strip().lower()
        if v in ("1", "true", "t", "yes", "y", "on"):
            return True
        if v in ("0", "false", "f", "no", "n", "off"):
            return False
    return default


def _norm_id(x: Any) -> str:
    if x is None:
        return ""
    p = str(x).strip().upper()
    p = p.replace("/", "-")
    if p.endswith(".USD"):
        p = p[:-4] + "-USD"
    return p

def _valid_pid(pid: str) -> bool:
    # basic sanity: product ids look like BASE-QUOTE (e.g. BTC-USD)
    if not pid or '-' not in pid:
        return False
    if '[' in pid or ']' in pid:
        return False
    return True



@dataclass(frozen=True)
class BookRow:
    """Normalized best-bid/ask row with convenient derived metrics."""
    pid: str
    bid: float
    bid_sz: float
    ask: float
    ask_sz: float

    @property
    def tob_usd(self) -> float:
        """Top-of-book USD liquidity estimate (min(bid*bid_sz, ask*ask_sz))."""
        try:
            if self.bid <= 0 or self.ask <= 0:
                return 0.0
            bid_usd = self.bid * (self.bid_sz if self.bid_sz > 0 else 0.0)
            ask_usd = self.ask * (self.ask_sz if self.ask_sz > 0 else 0.0)
            v = bid_usd if bid_usd < ask_usd else ask_usd
            return float(v) if v > 0 else 0.0
        except Exception:
            return 0.0

def _safe_float(x: Any) -> float:
    """Best-effort numeric coercion.
    Handles numeric strings (with commas), Decimals, and simple dict wrappers like {'value': '...'}.
    Returns 0.0 on failure.
    """
    if x is None:
        return 0.0

    # Fast path for real numbers
    if isinstance(x, (int, float)):
        v = float(x)
        return 0.0 if v != v else v  # NaN guard

    # Common dict wrapper shapes
    if isinstance(x, dict):
        for k in ("value", "amount", "volume", "usd", "quote", "base"):
            if k in x:
                return _safe_float(x.get(k))
        return 0.0

    # Common attribute wrapper shapes
    for attr in ("value", "amount"):
        if hasattr(x, attr):
            try:
                return _safe_float(getattr(x, attr))
            except Exception:
                pass

    try:
        s = str(x).strip()
        if not s:
            return 0.0
        # Strip common thousands separators
        s = s.replace(",", "").replace("_", "")
        v = float(s)
        return 0.0 if v != v else v
    except Exception:
        return 0.0



# MIN_1M_VOL guardrail:
# - Coinbase exposes both base volume (coins) and quote volume (USD) over 24h on product listings.
# - We want the USD/quote-side volume so it is comparable across products.
# - Setting MIN_1M_VOL is interpreted as 'minimum 24h quote volume in MILLIONS of USD'.

_QUOTE_VOL_KEYS_24H = (
    'approximate_quote_24h_volume',
    'approximate_quote_volume_24h',
    'approximate_quote_24_h_volume',
    'approximate_quote_24H_volume',
    'approximateQuote24hVolume',
    'approximateQuoteVolume24h',
    'approx_quote_volume_24h',
    'approxQuoteVolume24h',
    'quote_volume_24h',
    'quote_volume_24_h',
    'quoteVolume24h',
    'quote_volume',
    'quoteVolume',
)

_BASE_VOL_KEYS_24H = (
    'base_volume_24h',
    'base_volume_24_h',
    'baseVolume24h',
    'base_volume',
    'baseVolume',
    'volume',
    'volume_24h',
    'volume_24_h',
    'volume24h',
)

_PRICE_KEYS = (
    'price',
    'last',
    'last_price',
    'lastPrice',
    'mid_price',
    'midPrice',
    'mid',
    'mark',
)

def _usd_quote_vol_24h(p: Any) -> float:
    """Best-effort 24h *USD/quote* volume for a product.

    Preferred: explicit quote-volume fields (e.g. approximate_quote_24h_volume).
    Fallback: base-volume * price (only if a price-like field exists).
    """
    for k in _QUOTE_VOL_KEYS_24H:
        v = _safe_float(_get(p, k))
        if v > 0:
            return v

    base = 0.0
    for k in _BASE_VOL_KEYS_24H:
        base = _safe_float(_get(p, k))
        if base > 0:
            break
    if base <= 0:
        return 0.0

    px = 0.0
    for k in _PRICE_KEYS:
        px = _safe_float(_get(p, k))
        if px > 0:
            break
    if px <= 0:
        return 0.0

    return base * px
def _now_hms_utc() -> str:
    try:
        return datetime.now(timezone.utc).strftime("%H:%M:%S")
    except Exception:
        return "00:00:00"


def _json_info(stage: str, payload: Dict[str, Any]) -> None:
    try:
        msg = {"stage": stage, "ts": _now_hms_utc(), **payload}
        _LOG.info(json.dumps(msg, separators=(",", ":")))
    except Exception:
        # Never let logging break the strategy.
        pass


def _get(obj: Any, name: str, default: Any = None) -> Any:
    """
    Generic getter that works for both dicts and SDK objects.
    """
    if isinstance(obj, dict):
        return obj.get(name, default)
    return getattr(obj, name, default)


# ---------- product discovery ----------

def _iter_products(resp: Any):
    """
    Normalises the shape returned by client.get_products().
    Handles dicts with 'products', objects with .products, or a bare list.
    """
    if resp is None:
        return []
    if isinstance(resp, list):
        return resp
    if isinstance(resp, dict):
        prods = resp.get("products") or resp.get("data") or []
        return prods if isinstance(prods, list) else []
    prods = getattr(resp, "products", None)
    if isinstance(prods, list):
        return prods
    return []


def _fetch_usd_products(client, usd_quotes: Tuple[str, ...]) -> Tuple[List[str], Dict[str, float]]:
    """Return (product_ids, vol24h_usd_map) for ONLINE spot products quoted in USD-like quote currencies.

    vol24h_usd_map is *quote* volume (USD) over 24h (best-effort).
    """
    def _call_list_products(method_name, attempts):
        method = getattr(client, method_name, None)
        if not callable(method):
            return None
        for kwargs in attempts:
            try:
                return method(**kwargs) if kwargs else method()
            except TypeError:
                # SDK signature mismatch; try next
                continue
            except Exception:
                continue
        return None

    public_attempts = (
        {'product_type': 'SPOT', 'limit': 1000},
        {'product_type': 'SPOT', 'limit': 500},
        {'product_type': 'SPOT'},
        {'limit': 1000},
        {'limit': 500},
        {},
    )
    private_attempts = (
        {'limit': 250},
        {'product_type': 'SPOT'},
        {'product_type': 'SPOT', 'limit': 250},
        {},
    )

    resp = _call_list_products('get_public_products', public_attempts)
    if resp is None:
        resp = _call_list_products('get_products', private_attempts)
    if resp is None:
        return [], {}

    products = getattr(resp, 'products', None)
    if products is None:
        products = _get(resp, 'products')
    rows = products if isinstance(products, list) else list(_iter_products(resp))

    out: List[str] = []
    vol24h_usd: Dict[str, float] = {}
    for p in rows:
        pid = _norm_id(_get(p, 'product_id', _get(p, 'productId')))
        if not pid:
            continue
        quote = _get(p, 'quote_currency_id') or _get(p, 'quoteCurrencyId') or _get(p, 'quote_currency')
        base = _get(p, 'base_currency_id') or _get(p, 'baseCurrencyId') or _get(p, 'base_currency')
        status = _get(p, 'status')
        product_type = str(_get(p, 'product_type', _get(p, 'productType', ''))).strip().upper()
        if product_type and product_type != 'SPOT':
            continue
        if quote in usd_quotes and str(status).strip().lower() == 'online' and base not in STABLE_BASES:
            out.append(pid)
            vol24h_usd[pid] = _usd_quote_vol_24h(p)
    global LAST_VOL24H_USD
    LAST_VOL24H_USD = dict(vol24h_usd)
    return out, vol24h_usd

def _parse_pricebook_row(row: Any) -> BookRow | None:
    """
    `row` comes from client.get_best_bid_ask(product_ids=...).pricebooks[*]
    or similar. We only care about the first bid/ask level.
    """
    pid = _norm_id(_get(row, "product_id", _get(row, "productId")))
    if not pid:
        return None

    bids = _get(row, "bids", []) or []
    asks = _get(row, "asks", []) or []

    def _first_px_sz(side_rows) -> Tuple[float, float]:
        if not side_rows:
            return 0.0, 0.0
        r0 = side_rows[0]
        px = _safe_float(_get(r0, "price"))
        sz = _safe_float(_get(r0, "size"))
        return px, sz

    bid, bid_sz = _first_px_sz(bids)
    ask, ask_sz = _first_px_sz(asks)
    return BookRow(pid=pid, bid=bid, bid_sz=bid_sz, ask=ask, ask_sz=ask_sz)


def _batch_best_bid_ask(client, product_ids: List[str], chunk_size: int = 100) -> Tuple[Dict[str, BookRow], Dict[str, int]]:
    """
    Batch fetch of best bid/ask for all product_ids.

    Coinbase may truncate very large product_id lists. We therefore chunk requests
    and merge results.

    Returns (books, stats) where stats includes:
      - calls: number of API calls made
      - requested: total product_ids requested across chunks
      - rows: total rows returned across chunks
      - returned: unique BookRows parsed (unique product_ids)
      - errors: number of chunk call failures
    """
    out: Dict[str, BookRow] = {}
    stats: Dict[str, int] = {"calls": 0, "requested": 0, "rows": 0, "returned": 0, "errors": 0}
    if client is None or not product_ids:
        return out, stats

    # De-dupe while preserving order; also normalise ids.
    seen: set[str] = set()
    pids: List[str] = []
    for pid in product_ids:
        pid = _norm_id(pid)
        if not pid or pid in seen:
            continue
        if not _valid_pid(pid):
            continue
        seen.add(pid)
        pids.append(pid)

    if not pids:
        return out, stats

    if chunk_size <= 0:
        chunk_size = len(pids)

    for i in range(0, len(pids), chunk_size):
        chunk = pids[i : i + chunk_size]
        stats["calls"] += 1
        stats["requested"] += len(chunk)
        try:
            resp = client.get_best_bid_ask(product_ids=chunk)
        except Exception as e:
            stats["errors"] += 1
            _LOG.error(f"universe_dynamic.get_best_bid_ask error (chunk {i // chunk_size + 1}): {e}")
            continue

        rows = _get(resp, "pricebooks", None) or _get(resp, "data", None) or []
        if not isinstance(rows, list):
            rows = []
        stats["rows"] += len(rows)

        for row in rows:
            br = _parse_pricebook_row(row)
            if br and br.pid:
                out[br.pid] = br

    stats["returned"] = len(out)
    return out, stats



def _inc_count(target: Dict[str, int], key: str, n: int = 1) -> None:
    try:
        target[str(key)] = int(target.get(str(key), 0) or 0) + int(n)
    except Exception:
        pass


def _spread_pct(bid: float, ask: float) -> float:
    try:
        if bid <= 0.0 or ask <= 0.0:
            return 999.0
        mid = 0.5 * (bid + ask)
        if mid <= 0.0:
            return 999.0
        return float(((ask - bid) / mid) * 100.0)
    except Exception:
        return 999.0


def _cohort_order(settings: Dict[str, Any]) -> List[str]:
    raw = settings.get("UNIVERSE_COHORT_ORDER", ["prime", "standard", "speculative"])
    if isinstance(raw, list):
        out = [str(x).strip().lower() for x in raw if str(x).strip()]
    else:
        out = ["prime", "standard", "speculative"]
    return out or ["prime", "standard", "speculative"]


def _cohort_split(settings: Dict[str, Any]) -> Dict[str, float]:
    raw = settings.get(
        "UNIVERSE_COHORT_TOP_SPLIT",
        {"prime": 0.55, "standard": 0.30, "speculative": 0.15},
    )
    out: Dict[str, float] = {}
    if isinstance(raw, dict):
        for key, value in raw.items():
            try:
                out[str(key).strip().lower()] = max(0.0, float(value))
            except Exception:
                continue
    if not out:
        out = {"prime": 0.55, "standard": 0.30, "speculative": 0.15}
    return out


def _cohort_profile(
    pid: str,
    bid: float,
    ask: float,
    topusd: float,
    vol24h_usd: float,
    settings: Dict[str, Any],
) -> Dict[str, Any]:
    min_topbook_usd = max(1.0, float(settings.get("MIN_TOPBOOK_USD", 50.0) or 50.0))
    max_spread_pct = max(0.01, float(settings.get("MAX_SPREAD_PCT", 0.50) or 0.50))
    base_vol_m = max(0.5, float(settings.get("UNIVERSE_COHORT_BASE_VOL_M", 2.0) or 2.0))
    base_vol_usd = max(1.0, base_vol_m * 1_000_000.0)
    spread_pct = _spread_pct(bid, ask)
    tob_ratio = float(topusd) / float(min_topbook_usd) if min_topbook_usd > 0.0 else 0.0
    vol_ratio = float(vol24h_usd) / float(base_vol_usd) if base_vol_usd > 0.0 else 0.0
    spread_ratio = spread_pct / max_spread_pct if max_spread_pct > 0.0 else 999.0

    if tob_ratio >= 2.5 and vol_ratio >= 2.0 and spread_ratio <= 0.45:
        cohort = "prime"
    elif tob_ratio >= 1.1 and vol_ratio >= 0.8 and spread_ratio <= 0.80:
        cohort = "standard"
    else:
        cohort = "speculative"

    quality = 0.0
    quality += min(40.0, tob_ratio * 16.0)
    quality += min(30.0, vol_ratio * 10.0)
    quality += max(0.0, 30.0 * (1.0 - min(spread_ratio, 1.5) / 1.5))
    if pid in MAJORS:
        quality += 2.0

    return {
        "cohort": cohort,
        "quality": round(float(max(0.0, min(100.0, quality))), 2),
        "tob_ratio": round(float(tob_ratio), 3),
        "vol_ratio": round(float(vol_ratio), 3),
        "spread_pct": round(float(spread_pct), 4),
    }


def _rank_candidates_by_tob(
    books: Dict[str, BookRow],
    vol24h_usd_map: Dict[str, float],
    settings: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """
    Returns list of (pid, score, bid, ask, topusd), sorted by score desc.
    Score is tob_usd with a slight preference for majors so they are not
    *completely* starved when conditions are similar.
    """
    ranked: List[Dict[str, Any]] = []
    for pid, br in books.items():
        tob = br.tob_usd
        if tob <= 0:
            continue
        profile = _cohort_profile(pid, br.bid, br.ask, br.tob_usd, float(vol24h_usd_map.get(pid, 0.0) or 0.0), settings)
        cohort = str(profile.get("cohort") or "speculative")
        quality = float(profile.get("quality", 0.0) or 0.0)
        bonus = 1.05 if pid in MAJORS else 1.0
        cohort_bonus = {"prime": 1.18, "standard": 1.08, "speculative": 0.96}.get(cohort, 1.0)
        clean_bias = 1.0
        if _as_bool(settings.get("UNIVERSE_CLEAN_TAPE_BIAS", True), True):
            clean_bias += max(0.0, min(0.20, quality / 500.0))
        score = tob * bonus * cohort_bonus * clean_bias
        ranked.append(
            {
                "pid": pid,
                "score": float(score),
                "bid": float(br.bid),
                "ask": float(br.ask),
                "topusd": float(br.tob_usd),
                "cohort": cohort,
                "quality": quality,
                "spread_pct": float(profile.get("spread_pct", 999.0) or 999.0),
                "vol24h_usd": float(vol24h_usd_map.get(pid, 0.0) or 0.0),
            }
        )

    ranked.sort(key=lambda x: (float(x.get("score", 0.0) or 0.0), float(x.get("quality", 0.0) or 0.0)), reverse=True)
    return ranked


# ---------- filters + public API ----------

def _passes_filters(
    bid: float,
    ask: float,
    min_topbook_usd: float,
    max_spread_pct: float,
    topusd_hint: float = 0.0,
) -> bool:
    if bid <= 0.0 or ask <= 0.0:
        return False
    mid = 0.5 * (bid + ask)
    if mid <= 0.0:
        return False

    spread = ask - bid
    spct = (spread / mid) if mid > 0.0 else 0.0
    # max_spread_pct is interpreted as *percent*, e.g. 0.50 == 0.5%
    if spct > float(max_spread_pct) / 100.0:
        return False

    topusd = float(topusd_hint) if topusd_hint > 0.0 else mid
    if topusd < float(min_topbook_usd):
        return False

    return True


def _filter_reason(
    bid: float,
    ask: float,
    min_topbook_usd: float,
    max_spread_pct: float,
    topusd_hint: float = 0.0,
) -> str:
    if bid <= 0.0 or ask <= 0.0:
        return "bad_book"
    mid = 0.5 * (bid + ask)
    if mid <= 0.0:
        return "bad_mid"
    spread = ask - bid
    spct = (spread / mid) if mid > 0.0 else 0.0
    if spct > float(max_spread_pct) / 100.0:
        return "wide_spread"
    topusd = float(topusd_hint) if topusd_hint > 0.0 else mid
    if topusd < float(min_topbook_usd):
        return "thin_topbook"
    return ""


def _select_by_cohort(
    rows: List[Dict[str, Any]],
    top_n: int,
    settings: Dict[str, Any],
) -> Tuple[List[Dict[str, Any]], Dict[str, int]]:
    if top_n <= 0:
        return [], {}
    if not _as_bool(settings.get("UNIVERSE_COHORTS_ENABLED", True), True):
        return rows[:top_n], {}

    order = _cohort_order(settings)
    split = _cohort_split(settings)
    grouped: Dict[str, List[Dict[str, Any]]] = {name: [] for name in order}
    extra: List[Dict[str, Any]] = []
    for row in rows:
        cohort = str(row.get("cohort") or "speculative").strip().lower()
        if cohort in grouped:
            grouped[cohort].append(row)
        else:
            extra.append(row)

    selected: List[Dict[str, Any]] = []
    counts: Dict[str, int] = {}
    remaining = int(top_n)
    quotas: Dict[str, int] = {}
    for idx, cohort in enumerate(order):
        available = len(grouped.get(cohort, []))
        if available <= 0 or remaining <= 0:
            quotas[cohort] = 0
            continue
        if idx == len(order) - 1:
            quota = remaining
        else:
            quota = int(round(float(top_n) * float(split.get(cohort, 0.0) or 0.0)))
            quota = max(1, quota)
            quota = min(quota, remaining)
        quotas[cohort] = max(0, min(quota, available))
        remaining -= quotas[cohort]

    for cohort in order:
        take = quotas.get(cohort, 0)
        if take <= 0:
            continue
        picked = grouped.get(cohort, [])[:take]
        selected.extend(picked)
        counts[cohort] = len(picked)
        grouped[cohort] = grouped.get(cohort, [])[take:]

    if len(selected) < top_n and _as_bool(settings.get("UNIVERSE_COHORT_ALLOW_SPILLOVER", True), True):
        leftovers: List[Dict[str, Any]] = []
        for cohort in order:
            leftovers.extend(grouped.get(cohort, []))
        leftovers.extend(extra)
        leftovers.sort(key=lambda x: (float(x.get("score", 0.0) or 0.0), float(x.get("quality", 0.0) or 0.0)), reverse=True)
        for row in leftovers:
            if len(selected) >= top_n:
                break
            selected.append(row)
            cohort = str(row.get("cohort") or "speculative").strip().lower()
            counts[cohort] = int(counts.get(cohort, 0) or 0) + 1

    return selected[:top_n], counts


def build_universe(client, settings: Dict[str, Any], diag: Dict[str, Any] | None = None) -> List[str]:
    """
    Returns a list of product_ids to consider this run.

    Modes:
      - LIST: honour UNIVERSE_LIST exactly (sanity‑checked)
      - TOP:  discover all USD‑quoted products on venue and rank by top-of-book
              liquidity; honour UNIVERSE_TOP / TOP_N, MAJORS_INCLUDE.
    """
    s = settings or {}

    mode = str(s.get("UNIVERSE_MODE", "TOP")).upper()
    top = int(s.get("UNIVERSE_TOP", 80))
    top_n = int(s.get("TOP_N", min(top, 12)))
    min_topbook_usd = float(s.get("MIN_TOPBOOK_USD", 50.0))
    max_spread_pct = float(s.get("MAX_SPREAD_PCT", 0.50))  # percent
    # MIN_1M_VOL is interpreted as 24h quote-volume in MILLIONS of USD (see _usd_quote_vol_24h).
    min_1m_vol_m = float(s.get('MIN_1M_VOL', 0.0) or 0.0)
    min_1m_vol_usd = min_1m_vol_m * 1_000_000.0

    majors_include = _as_bool(s.get("MAJORS_INCLUDE", s.get("MAJORS", True)), True)
    majors_list = [_norm_id(p) for p in s.get("MAJORS_LIST", MAJORS)]
    majors_list = [p for p in majors_list if _valid_pid(p)]
    if not majors_list:
        majors_list = MAJORS[:]

    global LAST_DIAG, LAST_COHORT_BY_PID, LAST_TAPE_QUALITY_BY_PID

    # Explicit LIST mode: honour UNIVERSE_LIST exactly, but still normalise IDs.
    if mode == "LIST":
        out: List[str] = []
        seen = set()
        for raw in list(s.get("UNIVERSE_LIST", [])):
            pid = _norm_id(raw)
            if not pid or pid in seen:
                continue
            out.append(pid)
            seen.add(pid)
        _json_info(
            "universe",
            {
                "mode": mode,
                "top": top,
                "top_n": top_n,
                "majors_include": majors_include,
                "n_candidates": len(out),
                "n_pass": len(out),
                "items": out[:top_n],
            },
        )
        LAST_DIAG = {
            "mode": mode,
            "top": top,
            "top_n": top_n,
            "source": "list",
            "discovered": len(out),
            "uni_out": min(len(out), top_n),
            "rejects": {},
            "cohorts": {},
        }
        if isinstance(diag, dict):
            diag.update(LAST_DIAG)
        return out[:top_n]

    # Dynamic TOP mode.
    discovered, vol24h_usd = _fetch_usd_products(client, USD_QUOTES) if client is not None else ([], {})
    if not discovered:
        _json_info(
            "universe",
            {
                "mode": mode,
                "top": top,
                "top_n": top_n,
                "majors_include": majors_include,
                "n_candidates": 0,
                "n_pass": 0,
                "items": [],
            },
        )
        LAST_DIAG = {
            "mode": mode,
            "top": top,
            "top_n": top_n,
            "source": "dynamic",
            "discovered": 0,
            "uni_out": 0,
            "rejects": {"discover": 1},
            "cohorts": {},
        }
        if isinstance(diag, dict):
            diag.update(LAST_DIAG)
        return []

    # Optionally *force include* majors, even if they would otherwise
    # be skipped, as long as they are USD products.
    if majors_include:
        for m in majors_list:
            if m and m not in discovered:
                discovered.append(m)
    else:
        # If majors_include=False, explicitly drop BTC/ETH if present.
        discovered = [p for p in discovered if p not in ("BTC-USD", "ETH-USD")]

    # Prefilter by 24h quote volume before pricebook fetch to reduce request size.
    # (MIN_1M_VOL is interpreted as "million USD quote volume over 24h".)
    pricebook_ids = discovered
    rej_vol = 0
    if min_1m_vol_usd > 0.0:
        filtered: List[str] = []
        for pid in discovered:
            vol_usd = float(vol24h_usd.get(pid, 0.0) or 0.0)
            if vol_usd >= min_1m_vol_usd:
                filtered.append(pid)
            else:
                rej_vol += 1
        pricebook_ids = filtered

    books_all, bb = _batch_best_bid_ask(client, pricebook_ids)
    ranked = _rank_candidates_by_tob(books_all, vol24h_usd, s)

    pass_rows: List[Dict[str, Any]] = []
    reject_counts: Dict[str, int] = {}
    reject_by_cohort: Dict[str, int] = {}
    cohort_seen: Dict[str, int] = {}
    scanned = 0
    for row in ranked:
        pid = str(row.get("pid") or "")
        cohort = str(row.get("cohort") or "speculative")
        scanned += 1
        _inc_count(cohort_seen, cohort)
        reason = _filter_reason(
            float(row.get("bid", 0.0) or 0.0),
            float(row.get("ask", 0.0) or 0.0),
            min_topbook_usd,
            max_spread_pct,
            topusd_hint=float(row.get("topusd", 0.0) or 0.0),
        )
        if reason:
            _inc_count(reject_counts, reason)
            _inc_count(reject_by_cohort, cohort)
            continue
        pass_rows.append(row)

    initial = pass_rows[: max(0, int(top))]
    selected_rows, selected_by_cohort = _select_by_cohort(initial, top_n, s)
    if len(selected_rows) < top_n and len(initial) < len(pass_rows):
        spill_rows, spill_counts = _select_by_cohort(pass_rows[len(initial):], top_n - len(selected_rows), s)
        selected_rows.extend(spill_rows)
        for key, value in spill_counts.items():
            _inc_count(selected_by_cohort, key, value)

    results: List[str] = []
    LAST_COHORT_BY_PID = {}
    LAST_TAPE_QUALITY_BY_PID = {}
    for row in selected_rows[:top_n]:
        pid = str(row.get("pid") or "")
        if not pid:
            continue
        results.append(pid)
        LAST_COHORT_BY_PID[pid] = str(row.get("cohort") or "speculative")
        LAST_TAPE_QUALITY_BY_PID[pid] = float(row.get("quality", 0.0) or 0.0)

    LAST_DIAG = {
        "mode": mode,
        "top": top,
        "top_n": top_n,
        "source": "dynamic",
        "majors_include": majors_include,
        "min_1m_vol_m": min_1m_vol_m,
        "discovered": len(discovered),
        "pricebook_ids": len(pricebook_ids),
        "scanned": scanned,
        "passed_prefilter": len(pass_rows),
        "uni_out": len(results),
        "rejects": dict(reject_counts),
        "rejects_by_cohort": dict(reject_by_cohort),
        "cohorts": dict(cohort_seen),
        "selected_by_cohort": dict(selected_by_cohort),
        "bb_calls": int(bb.get("calls", 0)) if isinstance(bb, dict) else 0,
        "bb_requested": int(bb.get("requested", 0)) if isinstance(bb, dict) else 0,
        "bb_rows": int(bb.get("rows", 0)) if isinstance(bb, dict) else 0,
        "bb_returned": int(bb.get("returned", 0)) if isinstance(bb, dict) else 0,
        "bb_errors": int(bb.get("errors", 0)) if isinstance(bb, dict) else 0,
    }

    _json_info(
        "universe",
        {
            "mode": mode,
            "top": top,
            "top_n": top_n,
            "majors_include": majors_include,
            "min_1m_vol_m": min_1m_vol_m,
            "n_pricebook_ids": len(pricebook_ids),
            "bb_calls": int(bb.get("calls", 0)) if isinstance(bb, dict) else 0,
            "bb_requested": int(bb.get("requested", 0)) if isinstance(bb, dict) else 0,
            "bb_rows": int(bb.get("rows", 0)) if isinstance(bb, dict) else 0,
            "bb_returned": int(bb.get("returned", 0)) if isinstance(bb, dict) else 0,
            "bb_errors": int(bb.get("errors", 0)) if isinstance(bb, dict) else 0,
            "rej_vol": rej_vol,
            "rej": dict(reject_counts),
            "selected_by_cohort": dict(selected_by_cohort),
            "cohorts": dict(cohort_seen),
            "scanned": scanned,
            "n_candidates": len(discovered),
            "n_pass": len(results),
            "items": results,
        },
    )

    if isinstance(diag, dict):
        diag.update(LAST_DIAG)

    return results
