import json
import os
import faulthandler
import sys
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

LOG_PATH = ROOT / "logs" / "dry_supervised_loop.log"
SCORE_PATH = ROOT / "logs" / "dry_pnl_score.json"


def _log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def _score_summary() -> str:
    try:
        data = json.loads(SCORE_PATH.read_text(encoding="utf-8"))
    except Exception as exc:
        return f"score_unavailable={type(exc).__name__}"

    realized = float(data.get("realized_pnl_usd") or 0.0)
    unrealized = float(data.get("unrealized_pnl_usd") or 0.0)
    net = realized + unrealized
    return (
        f"pnl realized={realized:.6f} unrealized={unrealized:.6f} net={net:.6f} "
        f"open={data.get('open_count')} closed={data.get('closed')} "
        f"wins={data.get('wins')} losses={data.get('losses')} "
        f"blocked_open={data.get('blocked_open')}"
    )


def main() -> None:
    sleep_sec = float(os.environ.get("KOKO_SUPERVISOR_SLEEP_SEC", "20"))
    max_cycles = int(os.environ.get("KOKO_SUPERVISOR_MAX_CYCLES", "0") or "0")
    _log(
        "supervisor_start "
        f"pid={os.getpid()} dry_expected=true live_expected=false "
        f"pfid_present={bool(os.environ.get('PFID'))} "
        f"key_file_present={bool(os.environ.get('COINBASE_KEY_FILE'))}"
    )
    _log("import_run_loop_start")
    dump_path = ROOT / "logs" / f"dry_supervised_import_dump_{os.getpid()}.log"
    dump_file = dump_path.open("w", encoding="utf-8")
    faulthandler.dump_traceback_later(30, repeat=True, file=dump_file)
    from managers.run_manager.run_manager import run_loop
    faulthandler.cancel_dump_traceback_later()
    dump_file.close()
    _log("import_run_loop_done")

    cycles = 0
    while True:
        cycles += 1
        started = time.time()
        _log(f"cycle_start {_score_summary()}")
        try:
            run_loop(console=False, ticks=1)
            elapsed = time.time() - started
            _log(f"cycle_done elapsed_sec={elapsed:.1f} {_score_summary()}")
        except Exception as exc:
            elapsed = time.time() - started
            _log(f"cycle_error elapsed_sec={elapsed:.1f} {type(exc).__name__}: {exc}")
        if max_cycles > 0 and cycles >= max_cycles:
            _log(f"supervisor_stop max_cycles={max_cycles}")
            return
        time.sleep(sleep_sec)


if __name__ == "__main__":
    main()
