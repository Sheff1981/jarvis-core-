"""Conservative Russian voice-command parsing: no arbitrary AI-generated execution."""
import re

def parse_command(text):
    normalized = re.sub(r"\s+", " ", text.strip().lower())
    if normalized in {"стоп", "джарвис стоп", "джарвис, стоп", "остановись"}:
        return {"intent": "stop"}
    if normalized in {"скопируй", "скопируй выделенное", "джарвис, скопируй"}:
        return {"intent": "copy_selection"}
    if normalized in {"вставь", "вставь сюда", "джарвис, вставь"}:
        return {"intent": "paste"}
    return {"intent": "unknown", "text": text}
