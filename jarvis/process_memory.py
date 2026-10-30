"""Lightweight process memory metrics using the standard library.

Windows uses GetProcessMemoryInfo when available; Unix uses /proc/self/status
on Linux. Missing metrics are reported as None, not estimated.
"""
from dataclasses import dataclass
import os
import sys


@dataclass(frozen=True)
class ProcessMemory:
    rss_bytes: int | None
    platform: str


def current_process_memory():
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes

        class MemoryCounters(ctypes.Structure):
            _fields_ = [
                ("cb", wintypes.DWORD),
                ("PageFaultCount", wintypes.DWORD),
                ("PeakWorkingSetSize", ctypes.c_size_t),
                ("WorkingSetSize", ctypes.c_size_t),
                ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPagedPoolUsage", ctypes.c_size_t),
                ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
                ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
                ("PagefileUsage", ctypes.c_size_t),
                ("PeakPagefileUsage", ctypes.c_size_t),
            ]
        counters = MemoryCounters()
        counters.cb = ctypes.sizeof(counters)
        process = ctypes.windll.kernel32.GetCurrentProcess()
        ok = ctypes.windll.psapi.GetProcessMemoryInfo(
            process, ctypes.byref(counters), counters.cb)
        return ProcessMemory(int(counters.WorkingSetSize) if ok else None, "win32")

    if sys.platform.startswith("linux"):
        try:
            with open("/proc/self/status", encoding="ascii") as handle:
                for line in handle:
                    if line.startswith("VmRSS:"):
                        return ProcessMemory(int(line.split()[1]) * 1024, "linux")
        except (OSError, ValueError, IndexError):
            pass
        return ProcessMemory(None, "linux")
    return ProcessMemory(None, sys.platform)
