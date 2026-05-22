from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def _project_root() -> Path:
    # <ROOT>/managers/menu_manager/menu_shortcut_guard.py -> <ROOT>
    return Path(__file__).resolve().parents[2]


def _desktop_dir() -> Path:
    # Prefer Windows Desktop via USERPROFILE, but fall back safely.
    up = os.environ.get("USERPROFILE")
    if up:
        d = Path(up) / "Desktop"
        if d.exists():
            return d
    d = Path.home() / "Desktop"
    return d if d.exists() else Path.home()


def _ps_sq(s: str) -> str:
    """
    PowerShell single-quote escape:
    In PS: ' becomes '' inside single-quoted strings.
    """
    return s.replace("'", "''")


def _create_windows_shortcut(lnk_path: Path, target_path: Path, args: str, workdir: Path, desc: str) -> None:
    """
    Uses WScript.Shell COM via PowerShell to create/update a .lnk shortcut.
    """
    lnk = _ps_sq(str(lnk_path))
    target = _ps_sq(str(target_path))
    arguments = _ps_sq(args)
    wd = _ps_sq(str(workdir))
    description = _ps_sq(desc)

    # Use the python executable as the icon (index 0)
    icon = _ps_sq(f"{target_path},0")

    ps = f"""
$WshShell = New-Object -ComObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut('{lnk}')
$Shortcut.TargetPath = '{target}'
$Shortcut.Arguments = '{arguments}'
$Shortcut.WorkingDirectory = '{wd}'
$Shortcut.WindowStyle = 1
$Shortcut.Description = '{description}'
$Shortcut.IconLocation = '{icon}'
$Shortcut.Save()
"""

    subprocess.run(
        ["powershell.exe", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", ps],
        check=True,
        capture_output=True,
        text=True,
    )


def _write_cmd_fallback(cmd_path: Path, target_path: Path, workdir: Path) -> None:
    """
    Fallback launcher if .lnk creation fails.
    """
    content = "\r\n".join(
        [
            "@echo off",
            f'cd /d "{workdir}"',
            f'"{target_path}" -X utf8 -u -m managers',
            "pause",
            "",
        ]
    )
    cmd_path.write_text(content, encoding="utf-8")


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Create/update a Desktop shortcut for `python -m managers`.")
    ap.add_argument("--name", default="KOKO Menu", help="Shortcut base name (without extension).")
    ap.add_argument("--where", default="desktop", choices=["desktop", "root"], help="Where to place the shortcut.")
    args = ap.parse_args(argv)

    root = _project_root()
    py = Path(sys.executable)

    # The *module* entrypoint (no root launcher .py files)
    module_args = "-X utf8 -u -m managers"

    if os.name != "nt":
        # Non-Windows: just emit a small shell script in root as best-effort.
        sh_path = root / f"{args.name}.sh"
        sh = "\n".join(
            [
                "#!/usr/bin/env bash",
                f'cd "{root}"',
                f'"{py}" {module_args}',
                "",
            ]
        )
        sh_path.write_text(sh, encoding="utf-8")
        print(f"Wrote (non-Windows fallback): {sh_path}")
        return 0

    if args.where == "desktop":
        out_dir = _desktop_dir()
    else:
        out_dir = root

    lnk_path = out_dir / f"{args.name}.lnk"
    cmd_path = out_dir / f"{args.name}.cmd"

    try:
        _create_windows_shortcut(
            lnk_path=lnk_path,
            target_path=py,
            args=module_args,
            workdir=root,
            desc="Launch KOKO Menu Manager (module entrypoint)",
        )
        print(f"Shortcut updated: {lnk_path}")
        return 0
    except Exception as e:
        # Fallback: create a .cmd launcher
        try:
            _write_cmd_fallback(cmd_path=cmd_path, target_path=py, workdir=root)
            print(f"[WARN] .lnk creation failed, wrote fallback launcher: {cmd_path}")
            print(f"[WARN] Reason: {e}")
            return 0
        except Exception as e2:
            print(f"[ERROR] Could not create shortcut or fallback launcher.\n  Shortcut error: {e}\n  Fallback error: {e2}")
            return 2


if __name__ == "__main__":
    raise SystemExit(main())
