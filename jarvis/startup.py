"""Opt-in per-user Windows Startup shortcut script for JARVIS.

No startup registration occurs when this module is imported.
"""
import os
from pathlib import Path
import sys


STARTUP_NAME = "JARVIS-Local.cmd"


def startup_folder(appdata=None):
    root = appdata if appdata is not None else os.environ.get("APPDATA")
    if not root:
        raise RuntimeError("Windows APPDATA is unavailable")
    return Path(root) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def startup_script(python_exe, entry_script, model_dir, db_path, llm_model="qwen2.5:3b"):
    """Create a quoted, absolute-path command without shell metacharacter injection."""
    paths = [Path(p).resolve() for p in (python_exe, entry_script, model_dir, db_path)]
    if not paths[0].is_file() or not paths[1].is_file() or not paths[2].is_dir():
        raise ValueError("Python, voice_chat.py and the Vosk model must exist")
    values = [str(p) for p in paths]
    if any(any(ch in value for ch in ('"', '%', '!', '\r', '\n', '^', '&', '|', '<', '>')) for value in values):
        raise ValueError("Unsupported character in startup path")
    if not llm_model or any(ch in llm_model for ch in ('"', '%', '!', '\r', '\n', '^', '&', '|', '<', '>')):
        raise ValueError("Unsafe model name")
    python, entry, model, db = values
    return (
        "@echo off\r\n"
        f'cd /d "{Path(entry).parent}"\r\n'
        f'"{python}" "{entry}" --model "{model}" --db "{db}" '
        f'--llm-model "{llm_model}" --require-wake-word --speak\r\n'
    )


def install(script, appdata=None):
    """Explicit opt-in only. Never overwrite a foreign or modified startup entry."""
    if sys.platform != "win32":
        raise RuntimeError("Windows only")
    folder = startup_folder(appdata)
    target = folder / STARTUP_NAME
    if target.exists():
        raise FileExistsError(f"Startup entry already exists: {target}")
    folder.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="") as stream:
        stream.write(script)
    return target


def uninstall(appdata=None):
    """Remove only JARVIS's own startup entry; never touch other entries."""
    if sys.platform != "win32":
        raise RuntimeError("Windows only")
    target = startup_folder(appdata) / STARTUP_NAME
    if target.is_symlink():
        raise RuntimeError("Refusing to remove a symlink")
    if not target.exists():
        return False
    if not target.is_file():
        raise RuntimeError("Unexpected startup entry type")
    text = target.read_text(encoding="utf-8")
    if "--require-wake-word --speak" not in text or "voice_chat.py" not in text:
        raise RuntimeError("Startup entry was modified; refusing automatic removal")
    target.unlink()
    return True
