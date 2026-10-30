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


def focus_window_exact(title):
    """Focus only a uniquely matching visible window; never guess among duplicates."""
    if os.name != "nt":
        raise OSError("Window switching is supported only on Windows")
    if not isinstance(title, str) or not title.strip() or len(title) > 4096:
        raise ValueError("A nonempty exact window title is required")
    user32 = ctypes.windll.user32
    matches = []
    callback_type = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    @callback_type
    def visit(hwnd, unused):
        if not user32.IsWindowVisible(hwnd):
            return True
        length = user32.GetWindowTextLengthW(hwnd)
        if length <= 0 or length > 4096:
            return True
        buffer = ctypes.create_unicode_buffer(length + 1)
        if user32.GetWindowTextW(hwnd, buffer, length + 1) and buffer.value == title:
            matches.append(hwnd)
        return len(matches) < 2

    user32.EnumWindows(visit, 0)
    if len(matches) != 1:
        raise ValueError("Expected exactly one visible window with that title")
    if not user32.SetForegroundWindow(matches[0]):
        raise OSError("Windows refused to activate the requested window")
    return {"focused": title}
