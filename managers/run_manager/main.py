# Forwarder so `from run_manager import main` resolves to managers/main.py:main
import importlib, pathlib, sys
PARENT = pathlib.Path(__file__).resolve().parent.parent  # ...\managers
if str(PARENT) not in sys.path:
    sys.path.append(str(PARENT))  # append to avoid shadowing stdlib

def main(*args, **kwargs):
    m = importlib.import_module("main")  # loads ...\managers\main.py
    if not hasattr(m, "main"):
        raise ImportError("managers/main.py does not define main()")
    return m.main(*args, **kwargs)
