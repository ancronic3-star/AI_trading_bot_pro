import faulthandler
import os
import time
from pathlib import Path


ROOT = Path(__file__).resolve().parent
LOG_PATH = ROOT / "logs" / "dry_main_loop.log"


def _log(message: str) -> None:
    LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    stamp = time.strftime("%Y-%m-%dT%H:%M:%S%z")
    with LOG_PATH.open("a", encoding="utf-8") as handle:
        handle.write(f"[{stamp}] {message}\n")


def main() -> None:
    _log(
        "main_loop_start "
        f"pid={os.getpid()} dry_expected=true live_expected=false "
        f"pfid_present={bool(os.environ.get('PFID'))} "
        f"key_file_present={bool(os.environ.get('COINBASE_KEY_FILE'))}"
    )
    dump_path = ROOT / "logs" / f"dry_main_loop_dump_{os.getpid()}.log"
    dump_file = dump_path.open("w", encoding="utf-8")
    faulthandler.dump_traceback_later(30, repeat=True, file=dump_file)
    _log("import_run_loop_start")
    from managers.run_manager.run_manager import run_loop
    _log("import_run_loop_done")
    faulthandler.cancel_dump_traceback_later()
    dump_file.close()
    run_loop(console=False)


if __name__ == "__main__":
    main()
