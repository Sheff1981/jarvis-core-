"""Console-free JARVIS voice entry point with a per-user log and single-instance guard.

Run with: pythonw.exe -m jarvis.background <voice_chat.py options>
This module imports voice_chat only after redirecting stdout/stderr to a file.
"""
import contextlib
import datetime as dt
import os
from pathlib import Path
import sys
import traceback


@contextlib.contextmanager
def single_instance():
    """Prevent two background voice agents in the same Windows logon session."""
    if sys.platform != "win32":
        yield True
        return

    import ctypes
    kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel32.CreateMutexW.argtypes = (ctypes.c_void_p, ctypes.c_int, ctypes.c_wchar_p)
    kernel32.CreateMutexW.restype = ctypes.c_void_p
    kernel32.CloseHandle.argtypes = (ctypes.c_void_p,)
    kernel32.CloseHandle.restype = ctypes.c_int

    handle = kernel32.CreateMutexW(None, False, "Local\\JARVIS-Core-Voice")
    error_code = ctypes.get_last_error()
    if not handle:
        raise ctypes.WinError(error_code)
    try:
        yield error_code != 183  # ERROR_ALREADY_EXISTS
    finally:
        kernel32.CloseHandle(handle)


def default_log_path():
    base = os.environ.get("LOCALAPPDATA")
    return Path(base) / "JARVIS" / "logs" / "voice.log" if base else Path.home() / ".jarvis" / "logs" / "voice.log"


def run(argv=None, *, log_file=None):
    """Start voice_chat with redirected output; return the process exit code."""
    path = Path(log_file) if log_file is not None else default_log_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    args = list(sys.argv[1:] if argv is None else argv)

    # Preserve the last log from a crash; never log raw microphone recordings.
    if path.exists() and path.stat().st_size > 2 * 1024 * 1024:
        archive = path.with_name(path.name + ".1")
        path.replace(archive)

    with path.open("a", encoding="utf-8", buffering=1) as log:
        with contextlib.redirect_stdout(log), contextlib.redirect_stderr(log):
            print("JARVIS background started:", dt.datetime.now(dt.timezone.utc).isoformat(), flush=True)
            try:
                with single_instance() as acquired:
                    if not acquired:
                        print("JARVIS background is already running; second instance refused.", flush=True)
                        return 0
                    import voice_chat

                    previous_argv = sys.argv
                    try:
                        sys.argv = [str(Path(voice_chat.__file__)), *args]
                        voice_chat.main()
                    finally:
                        sys.argv = previous_argv
                    return 0
            except SystemExit as exc:
                return exc.code if isinstance(exc.code, int) else (1 if exc.code else 0)
            except Exception:
                traceback.print_exc()
                return 1


if __name__ == "__main__":
    raise SystemExit(run())
