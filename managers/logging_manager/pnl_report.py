import json
import os
import collections
from pathlib import Path

# PROJECT ROOT:  .../ai_trading_bot_koko
ROOT_DIR = Path(__file__).resolve().parents[2]

# Try multiple reasonable locations for fills JSON
CANDIDATES = [
    ROOT_DIR / "fills_all.json",
    ROOT_DIR / "fills_dump.json",
    ROOT_DIR / "logs" / "fills_all.json",
    ROOT_DIR / "logs" / "fills_dump.json",
]

path: Path | None = None
for p in CANDIDATES:
    if p.exists():
        path = p
        break

if path is None:
    print("No fills JSON found.")
    print("Looked for:")
    for p in CANDIDATES:
        print("  -", p)
    raise SystemExit(1)

with path.open("r", encoding="utf-8") as fh:
    f = json.load(fh)

# sort by time if present
f.sort(key=lambda x: x.get("time", ""))

by = collections.defaultdict(list)
for r in f:
    by[r.get("product_id", "UNK")].append(r)


def compute(rows):
    pos = 0.0
    cost = 0.0
    pnl = 0.0
    fees = 0.0
    for r in rows:
        price = float(r.get("price", 0) or 0)
        size = float(r.get("size", 0) or 0)
        fee = float(r.get("fee", 0) or 0)
        side = (r.get("side", "") or "").upper()
        if side == "BUY":
            fees += fee
            pos += size
            cost += price * size
        elif side == "SELL":
            fees += fee
            if pos > 1e-12:
                qty = min(size, pos)
                avg = cost / pos
                pnl += (price - avg) * qty - fee
                pos -= qty
                cost -= avg * qty
                if size - qty > 1e-12:
                    # Any extra "over‑sold" size, treat as flat pnl at sell px
                    pnl += price * (size - qty)
    avg = cost / pos if pos > 1e-12 else 0.0
    return pnl, fees, pos, avg


tot_pnl = 0.0
tot_fees = 0.0

print(f"PNL REPORT from fills JSON: {path}")
print()
print(f"{'product':10s} {'pnl':>10s} {'fees':>10s} {'pos':>14s} {'avg_entry':>14s}")
print("-" * 60)

for pid, rows in sorted(by.items()):
    pnl, fees, pos, avg = compute(rows)
    tot_pnl += pnl
    tot_fees += fees
    print(
        f"{pid:10s} "
        f"{pnl:10.2f} "
        f"{fees:10.2f} "
        f"{pos:14.6f} "
        f"{avg:14.6f}"
    )

print("-" * 60)
print(f"{'TOTAL':10s} {tot_pnl:10.2f} {tot_fees:10.2f}")
