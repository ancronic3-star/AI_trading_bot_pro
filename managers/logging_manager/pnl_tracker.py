# pnl_tracker.py — lightweight orders/fills counters + uptime STAT60
# Optional: parses 'trades.log' to count orders/fills and estimates simple PnL
# without changing the engine. If fill price/qty present, PnL sums (sell - buy).

import os
import time
import re
import sys
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path

# PROJECT ROOT:  .../ai_trading_bot_koko
ROOT_DIR = Path(__file__).resolve().parents[2]
# trades.log is kept at the project root
LOG_PATH = str(ROOT_DIR / "trades.log")
SLEEP = float(os.environ.get("PNL_TAIL_SECONDS", "0.5"))

# Example fragments we try to parse:
# "BUY FILLED BTC-USD qty~0.0012 px~65000.12"
# "SELL FILLED DOGE-USD qty~20.8681 px~0.24"
SIDE_PAT = re.compile(r"\b(BUY|SELL)\b", re.IGNORECASE)
QTY_PAT = re.compile(r"qty[~=:\s]*([0-9.]+)")
PX_PAT = re.compile(r"(px|price)[~=:\s]*([0-9.]+)", re.IGNORECASE)


def ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")


def d(x):
    try:
        return Decimal(x)
    except (InvalidOperation, TypeError):
        return None


def parse_line(line: str):
    side_m = SIDE_PAT.search(line)
    if not side_m:
        return None
    side = side_m.group(1).upper()
    qm = QTY_PAT.search(line)
    pm = PX_PAT.search(line)
    qty = d(qm.group(1)) if qm else None
    px = d(pm.group(2)) if pm else None
    if qty is None or px is None:
        return {"side": side, "qty": None, "px": None}
    return {"side": side, "qty": qty, "px": px}


def main() -> None:
    # Counters
    orders = 0
    fills = 0
    buys = 0
    sells = 0
    realized = Decimal("0")
    start = time.time()
    last_stat = start

    # Wait for file if missing
    while not os.path.exists(LOG_PATH):
        print(f"[{ts()}] ALERT trades.log not found at {LOG_PATH}; waiting…")
        time.sleep(2.0)

    with open(LOG_PATH, "r", encoding="utf-8", errors="replace") as f:
        f.seek(0, os.SEEK_END)
        print(f"[{ts()}] PNL_TRACKER START at end of {LOG_PATH}")
        while True:
            line = f.readline()
            if not line:
                time.sleep(SLEEP)
                # periodic STAT60 even if no new lines
                now = time.time()
                if now - last_stat >= 60:
                    up = int(now - start)
                    print(
                        f"[{ts()}] STAT60 orders={orders} fills={fills} "
                        f"buys={buys} sells={sells} pnl={realized} uptime={up}s"
                    )
                    last_stat = now
                continue

            low = line.lower()
            if "enter" in low or "exit" in low or "order" in low:
                orders += 1

            if "fill" in low or "filled" in low:
                fills += 1
                info = parse_line(line)
                if info:
                    if info["side"] == "BUY":
                        buys += 1
                        if info["qty"] is not None and info["px"] is not None:
                            realized -= (info["qty"] * info["px"])
                    elif info["side"] == "SELL":
                        sells += 1
                        if info["qty"] is not None and info["px"] is not None:
                            realized += (info["qty"] * info["px"])

            # Lightweight echo for visibility on key events
            if "fill" in low or "filled" in low or "exit" in low:
                sys.stdout.write(line.rstrip("\n") + "\n")
                sys.stdout.flush()

            # periodic STAT60 tick
            now = time.time()
            if now - last_stat >= 60:
                up = int(now - start)
                print(
                    f"[{ts()}] STAT60 orders={orders} fills={fills} "
                    f"buys={buys} sells={sells} pnl={realized} uptime={up}s"
                )
                last_stat = now


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print(f"[{ts()}] PNL_TRACKER STOP")
