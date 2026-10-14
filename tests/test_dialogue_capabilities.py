"""Verify JARVIS describes only capabilities actually wired to the text channel."""
import tempfile
import unittest
from pathlib import Path

from jarvis.dialogue import Dialogue
from jarvis.local_llm import SYSTEM_PROMPT


class CapturingModel:
    def __init__(self):
        self.messages = None

    def reply(self, messages):
        self.messages = messages
        return "Я могу обсудить задачу."


class CapabilitiesPromptTests(unittest.TestCase):
    def test_text_mode_explains_voice_is_separate(self):
        with tempfile.TemporaryDirectory() as folder:
            model = CapturingModel()
            dialogue = Dialogue(db_path=str(Path(folder) / "jarvis.db"), model=model)
            try:
                dialogue.respond("Как подключить голос?")
                prompt = model.messages[0]["content"]
                self.assertIn("voice_chat.py", prompt)
                self.assertIn("интернету", prompt)
                self.assertIn("не запущен", prompt)
            finally:
                dialogue.close()

    def test_unified_prompt_does_not_claim_unsupported_tools(self):
        self.assertIn("подтверждённого подключённого инструмента", SYSTEM_PROMPT)
        self.assertIn("отдельными модулями", SYSTEM_PROMPT)


if __name__ == "__main__":
    unittest.main()
