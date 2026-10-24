"""Opt-in per-user Windows voice startup, with no console or elevated rights.

The generated .vbs launcher uses pythonw.exe and jarvis.background. Importing
this module never registers startup. Legacy JARVIS-Local.cmd entries are not
silently overwritten.
"""
import argparse
import math
import os
from pathlib import Path
import sys


STARTUP_NAME = "JARVIS-Local.vbs"
LEGACY_STARTUP_NAME = "JARVIS-Local.cmd"
MARKER = "' JARVIS-CORE Voice Startup v2"


def startup_folder(appdata=None):
    root = appdata if appdata is not None else os.environ.get("APPDATA")
    if not root:
        raise RuntimeError("Windows APPDATA is unavailable")
    return Path(root) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"


def _safe(value):
    text = str(value)
    if not text or any(ch in text for ch in ('"', '%', '!', '\r', '\n', '^', '&', '|', '<', '>')):
        raise ValueError("Unsafe character in startup parameter")
    return text


def _quote_vbs(value):
    return '"' + value.replace('"', '""') + '"'


def startup_script(python_exe, entry_script, model_dir, db_path,
                   llm_model="qwen2.5:3b-instruct-q6_K", *,
                   piper_bin=None, piper_voice=None, piper_length_scale=1.15,
                   cpu_only=True, tray=True, diagnostics=True,
                   ollama_keep_alive=0, llm_history_turns=8, llm_no_think=False):
    """Build a hidden, quoted user startup script for the current voice entry point."""
    paths = [Path(value).resolve() for value in
             (python_exe, entry_script, model_dir, db_path)]
    python, entry, vosk, db = paths
    if not python.is_file() or not entry.is_file() or not vosk.is_dir():
        raise ValueError("Python, voice_chat.py and Vosk directory must exist")
    if entry.name.lower() != "voice_chat.py":
        raise ValueError("Expected the checked-out voice_chat.py entry point")
    pythonw = python if python.name.lower() == "pythonw.exe" else python.with_name("pythonw.exe")
    if not pythonw.is_file():
        raise ValueError("pythonw.exe is required for hidden startup")
    if (piper_bin is None) != (piper_voice is None):
        raise ValueError("Specify both Piper executable and voice model")
    if not math.isfinite(piper_length_scale) or not 0.5 <= piper_length_scale <= 3:
        raise ValueError("Invalid Piper length scale")
    if (type(ollama_keep_alive) is not int or not 0 <= ollama_keep_alive <= 300):
        raise ValueError("Invalid Ollama keep-alive seconds")
    if (type(llm_history_turns) is not int or not 1 <= llm_history_turns <= 8):
        raise ValueError("Invalid LLM history turns")
    if not isinstance(llm_no_think, bool):
        raise ValueError("Invalid LLM thinking setting")
    if llm_no_think and not cpu_only:
        raise ValueError("Disabling thinking requires CPU mode")

    args = [
        "--model", _safe(vosk), "--db", _safe(db),
        "--llm-model", _safe(llm_model), "--speak",
    ]
    if cpu_only:
        args.append("--cpu-only")
    if tray:
        args.append("--tray")
    if diagnostics:
        args.append("--diagnostics")
    if ollama_keep_alive:
        args.extend(("--ollama-keep-alive", str(ollama_keep_alive)))
    if llm_history_turns != 8:
        args.extend(("--llm-history-turns", str(llm_history_turns)))
    if llm_no_think:
        args.append("--llm-no-think")
    if piper_bin is not None:
        piper = Path(piper_bin).resolve()
        voice = Path(piper_voice).resolve()
        if not piper.is_file() or not voice.is_file() or voice.suffix.lower() != ".onnx":
            raise ValueError("Piper executable and .onnx model must exist")
        args.extend(("--tts", "piper", "--piper-bin", _safe(piper),
                     "--piper-voice", _safe(voice),
                     "--piper-length-scale", str(piper_length_scale)))
    # Use pythonw, not python, to avoid a persistent console window.
    command = '"' + _safe(pythonw) + '" -m jarvis.background ' + " ".join(
        '"' + _safe(a) + '"' for a in args
    )
    return (
        MARKER + "\r\n"
        + 'Set shell = CreateObject("WScript.Shell")\r\n'
        + 'shell.CurrentDirectory = ' + _quote_vbs(_safe(entry.parent)) + "\r\n"
        + 'shell.Run ' + _quote_vbs(command) + ', 0, False\r\n'
    )


def install(script, appdata=None):
    """Register only after a successful manual run; never replace an entry."""
    if sys.platform != "win32":
        raise RuntimeError("Windows only")
    folder = startup_folder(appdata)
    target = folder / STARTUP_NAME
    legacy = folder / LEGACY_STARTUP_NAME
    if target.exists() or legacy.exists() or target.is_symlink() or legacy.is_symlink():
        raise FileExistsError("A JARVIS startup entry already exists; inspect it first")
    if not script.startswith(MARKER + "\r\n") or "jarvis.background" not in script:
        raise ValueError("Refusing an unrecognized startup script")
    folder.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="") as stream:
        stream.write(script)
    return target


def uninstall(appdata=None):
    """Remove only recognizable JARVIS startup entries; keep code and databases."""
    if sys.platform != "win32":
        raise RuntimeError("Windows only")
    folder = startup_folder(appdata)
    removed = False
    for name in (STARTUP_NAME, LEGACY_STARTUP_NAME):
        target = folder / name
        if target.is_symlink():
            raise RuntimeError("Refusing to remove a symlink")
        if not target.exists():
            continue
        if not target.is_file():
            raise RuntimeError("Unexpected startup entry type")
        body = target.read_text(encoding="utf-8")
        recognized = ((name == STARTUP_NAME and body.startswith(MARKER) and
                       "jarvis.background" in body) or
                      (name == LEGACY_STARTUP_NAME and
                       "--require-wake-word --speak" in body and "voice_chat.py" in body))
        if not recognized:
            raise RuntimeError("Startup entry was modified; refusing automatic removal")
        target.unlink()
        removed = True
    return removed


def main(argv=None):
    parser = argparse.ArgumentParser(description="JARVIS voice startup for the current Windows user")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--install", action="store_true", help="Install after manual voice validation")
    group.add_argument("--remove", action="store_true", help="Disable startup without deleting JARVIS")
    parser.add_argument("--python", default=sys.executable)
    parser.add_argument("--entry", default=str(Path(__file__).resolve().parent.parent / "voice_chat.py"))
    parser.add_argument("--model")
    parser.add_argument("--db")
    parser.add_argument("--llm-model", default="qwen2.5:3b-instruct-q6_K")
    parser.add_argument("--piper-bin")
    parser.add_argument("--piper-voice")
    parser.add_argument("--piper-length-scale", type=float, default=1.15)
    parser.add_argument("--ollama-keep-alive", type=int, default=0)
    parser.add_argument("--llm-history-turns", type=int, default=8)
    parser.add_argument("--llm-no-think", action="store_true")
    args = parser.parse_args(argv)
    if args.remove:
        print("JARVIS autostart removed:", uninstall())
        return
    if not args.model or not args.db or not args.piper_bin or not args.piper_voice:
        parser.error("--install requires --model, --db, --piper-bin and --piper-voice")
    script = startup_script(
        args.python, args.entry, args.model, args.db, args.llm_model,
        piper_bin=args.piper_bin, piper_voice=args.piper_voice,
        piper_length_scale=args.piper_length_scale,
        ollama_keep_alive=args.ollama_keep_alive,
        llm_history_turns=args.llm_history_turns,
        llm_no_think=args.llm_no_think,
    )
    print("JARVIS autostart installed:", install(script))


if __name__ == "__main__":
    main()
