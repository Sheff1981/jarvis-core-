"""Approved, narrowly scoped local filesystem operations.

No shell commands, file writes, deletes or process launches are exposed.
"""
import os
import subprocess
from pathlib import Path
import threading
import time

from jarvis.permissions import PermissionGate
from jarvis.windows_perception import list_visible_windows


class WindowsActions:
    def __init__(self, gate=None, audit_store=None):
        self.gate = gate if gate is not None else PermissionGate()
        self._lock = threading.Lock()
        self.audit = []
        self.audit_store = audit_store

    def propose(self, operation, target):
        if operation not in ("list_directory", "file_info", "open_explorer", "open_app", "list_windows"):
            raise ValueError("Operation is not supported")
        path = (target.strip().casefold() if operation in ("open_app", "list_windows") else
                str(Path(target).expanduser().resolve(strict=False)))
        if operation == "open_app" and path not in ("notepad", "calculator", "explorer"):
            raise ValueError("Application is not in the approved catalog")
        return self.gate.propose(operation, path, f"{operation}: {path}")

    def execute(self, token, operation, target):
        path = (target.strip().casefold() if operation in ("open_app", "list_windows") else
                str(Path(target).expanduser().resolve(strict=False)))
        if not self.gate.consume(token, operation, path):
            raise PermissionError("Explicit approval is required")
        try:
            if operation == "list_windows":
                if path != "desktop":
                    raise ValueError("Invalid desktop target")
                result = list_visible_windows()
            elif operation == "list_directory":
                directory = Path(path)
                if not directory.is_dir():
                    raise NotADirectoryError(path)
                result = sorted(item.name for item in directory.iterdir())[:200]
            elif operation == "file_info":
                entry = Path(path)
                info = entry.stat()
                result = {"name": entry.name, "size": info.st_size,
                          "is_file": entry.is_file(), "is_dir": entry.is_dir()}
            elif operation == "open_app":
                if os.name != "nt":
                    raise OSError("Запуск приложений доступен только в Windows")
                catalog = {"notepad": "notepad.exe", "calculator": "calc.exe",
                           "explorer": "explorer.exe"}
                if path not in catalog:
                    raise ValueError("Application is not in the approved catalog")
                subprocess.Popen([catalog[path]], shell=False)
                result = {"launched": path}
            elif operation == "open_explorer":
                if os.name != "nt":
                    raise OSError("Открытие Проводника доступно только в Windows")
                if not Path(path).is_dir():
                    raise NotADirectoryError(path)
                os.startfile(path)
                result = {"opened": path}
            else:
                raise ValueError("Unsupported operation")
        except Exception as exc:
            self._record(operation, path, "error", type(exc).__name__)
            raise
        self._record(operation, path, "success", "")
        return result

    def _record(self, operation, target, status, detail):
        if self.audit_store is not None:
            self.audit_store.record(operation, target, status, detail)
        with self._lock:
            self.audit.append({
                "timestamp": time.time(), "operation": operation,
                "target": target, "status": status, "detail": detail
            })
