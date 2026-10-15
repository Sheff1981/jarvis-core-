"""Offline approval and no-overwrite tests for Telegram bot project scaffolding."""
import tempfile
import unittest
from pathlib import Path

from jarvis.code_scaffold import CodeDraftDialogue, BOT_SOURCE
from jarvis.assistant import Assistant


class NeverLLM:
    model = "qwen3:1.7b"
    cpu_only = True

    def ask(self, prompt):
        raise AssertionError("This request must not reach the local LLM")


class CodeScaffoldTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "data").mkdir()
        self.db = self.root / "data" / "memory.db"
        self.scaffold = CodeDraftDialogue(self.db)
        self.target = self.root / "generated" / "telegram_echo_bot"

    def test_request_never_writes_until_approved(self):
        self.assertIn("Разрешаешь", self.scaffold.respond("создай бот в телеграм"))
        self.assertFalse(self.target.exists())
        self.assertIn("отменено", self.scaffold.respond("нет"))
        self.assertFalse(self.target.exists())
        self.assertIsNone(self.scaffold.respond("разрешаю"))
        self.assertFalse(self.target.exists())

    def test_approved_project_contains_compilable_code_without_token(self):
        self.assertIn("Разрешаешь", self.scaffold.respond("сделай код телеграм бота"))
        answer = self.scaffold.respond("разрешаю")
        self.assertIn("Созданы исходники", answer)
        source = (self.target / "bot.py").read_text(encoding="utf-8")
        compile(source, "bot.py", "exec")
        self.assertEqual(source, BOT_SOURCE)
        self.assertIn("TELEGRAM_BOT_TOKEN", source)
        self.assertIn("TELEGRAM_CHAT_ID", source)
        self.assertTrue((self.target / "README.md").is_file())

    def test_repeated_request_does_not_overwrite_existing_files(self):
        self.scaffold.respond("создай бот в телеграмм")
        self.scaffold.respond("разрешаю")
        source = self.target / "bot.py"
        source.write_text("my existing code", encoding="utf-8")
        self.scaffold.respond("создай бот в телеграмм")
        refusal = self.scaffold.respond("разрешаю")
        self.assertIn("не удалось", refusal)
        self.assertEqual(source.read_text(encoding="utf-8"), "my existing code")

    def test_spoken_clarification_does_not_approve_write(self):
        self.scaffold.respond("чтобы создал какой-нибудь бот в телеграмм")
        self.assertIn("Разрешаешь", self.scaffold.respond("хочу чтобы ты сделал то есть кодом"))
        self.assertFalse(self.target.exists())
        self.scaffold.close()
        self.assertIsNone(self.scaffold.respond("разрешаю"))

    def test_assistant_routes_model_and_scaffold_without_llm(self):
        assistant = Assistant(str(self.db), llm=NeverLLM())
        try:
            self.assertIn("qwen3:1.7b", assistant.respond("какая квинт сейчас работает"))
            self.assertIn("qwen3:1.7b", assistant.respond("нет я имею в виду нейросеть квин"))
            self.assertIn("Разрешаешь", assistant.respond("создай телеграм бота"))
            self.assertFalse(self.target.exists())
            self.assertIn("Созданы исходники", assistant.respond("разрешаю"))
            self.assertTrue(self.target.exists())
        finally:
            assistant.close()

    def test_stop_revokes_pending_code_write(self):
        assistant = Assistant(str(self.db), llm=NeverLLM())
        try:
            assistant.respond("создай телеграм бота")
            self.assertIn("отменено", assistant.respond("стоп"))
            # An unrelated approval must not create files.
            self.assertFalse(assistant.code_dialogue.pending)
            self.assertFalse(self.target.exists())
        finally:
            assistant.close()


if __name__ == "__main__":
    unittest.main()
