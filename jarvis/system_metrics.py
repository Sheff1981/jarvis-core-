"""Best-effort real system metrics; unavailable values are null, never fabricated."""
import os
import platform
import urllib.error
import urllib.request


def snapshot():
    data = {"platform": platform.system(), "cpu_count": os.cpu_count(),
            "ram_total_bytes": None, "ram_available_bytes": None,
            "ollama": "offline"}
    if os.name == "nt":
        try:
            import ctypes
            from ctypes import wintypes
            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [("dwLength", wintypes.DWORD), ("dwMemoryLoad", wintypes.DWORD),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            memory = MEMORYSTATUSEX()
            memory.dwLength = ctypes.sizeof(memory)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(memory)):
                data["ram_total_bytes"] = memory.ullTotalPhys
                data["ram_available_bytes"] = memory.ullAvailPhys
        except (AttributeError, OSError, ValueError):
            pass
    else:
        try:
            page = os.sysconf("SC_PAGE_SIZE")
            data["ram_total_bytes"] = page * os.sysconf("SC_PHYS_PAGES")
            data["ram_available_bytes"] = page * os.sysconf("SC_AVPHYS_PAGES")
        except (ValueError, OSError, AttributeError):
            pass
    try:
        with urllib.request.urlopen("http://127.0.0.1:11434/api/version", timeout=0.35) as response:
            if response.status == 200:
                data["ollama"] = "online"
    except (OSError, ValueError):
        pass
    return data
