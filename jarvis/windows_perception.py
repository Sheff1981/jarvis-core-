"""Read visible desktop window titles on Windows, without capturing screen content."""
import ctypes
import os
from ctypes import wintypes


def list_visible_windows(limit=30):
    if os.name != "nt":
        raise OSError("Window enumeration is supported only on Windows")
    if not 1 <= limit <= 100:
        raise ValueError("Window limit must be 1..100")
    user32 = ctypes.windll.user32
    titles = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def visit(hwnd, unused):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0 or length > 4096:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        if user32.GetWindowTextW(hwnd, buffer, length + 1):
            title = buffer.value.strip()
            if title:
                titles.append(title)
        return len(titles) < limit

    user32.EnumWindows(visit, 0)
    return titles
