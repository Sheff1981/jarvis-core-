"""Approved, narrowly scoped local filesystem operations.

No shell commands, file writes, deletes or process launches are exposed.
"""
from pathlib import Path
import threading
import time

from jarvis.permissions import PermissionGate


class WindowsActions:
    def __init__(self, gate=None):
        self.gate = gate if gate is not None else PermissionGate()
        self._lock = threading.Lock()
        self.audit = []

    def propose(self, operation, target):
        if operation not in ("list_directory", "file_info"):
            raise ValueError("Operation is not supported")
        path = str(Path(target).expanduser().resolve(strict=False))
        return self.gate.propose(operation, path, f"{operation}: {path}")

    def execute(self, token, operation, target):
        path = str(Path(target).expanduser().resolve(strict=False))
        if not self.gate.consume(token, operation, path):
            raise PermissionError("Explicit approval is required")
        try:
            if operation == "list_directory":
                directory = Path(path)
                if not directory.is_dir():
                    raise NotADirectoryError(path)
                result = sorted(item.name for item in directory.iterdir())[:200]
            elif operation == "file_info":
                entry = Path(path)
                info = entry.stat()
                result = {"name": entry.name, "size": info.st_size,
                          "is_file": entry.is_file(), "is_dir": entry.is_dir()}
            else:
                raise ValueError("Unsupported operation")
        except Exception as exc:
            self._record(operation, path, "error", type(exc).__name__)
            raise
        self._record(operation, path, "success", "")
        return result

    def _record(self, operation, target, status, detail):
        with self._lock:
            self.audit.append({
                "timestamp": time.time(), "operation": operation,
                "target": target, "status": status, "detail": detail
            })
