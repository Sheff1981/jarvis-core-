"""Explicitly authorized clipboard hotkeys for the active Windows window."""
import platform
from jarvis.commands import parse_command

def execute_command(text, *, approved=False, keyboard=None):
    command = parse_command(text)
    intent = command["intent"]
    if intent in ("unknown", "stop"):
        return {"status": intent}
    if not approved:
        return {"status": "confirmation_required", "intent": intent}
    if platform.system() != "Windows":
        return {"status": "unsupported_platform"}
    if keyboard is None:
        import pyautogui
        keyboard = pyautogui
    keyboard.FAILSAFE = True
    if intent == "copy_selection":
        keyboard.hotkey("ctrl", "c")
    elif intent == "paste":
        keyboard.hotkey("ctrl", "v")
    return {"status": "executed", "intent": intent}
