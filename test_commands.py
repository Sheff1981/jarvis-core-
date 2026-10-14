import unittest
from unittest.mock import patch
from jarvis.commands import parse_command
from jarvis.actions import execute_command

class FakeKeyboard:
    FAILSAFE = False
    def __init__(self): self.calls = []
    def hotkey(self, *keys): self.calls.append(keys)

class TestCommands(unittest.TestCase):
    def test_parse(self):
        self.assertEqual(parse_command("Джарвис, стоп")["intent"], "stop")
        self.assertEqual(parse_command("скопируй выделенное")["intent"], "copy_selection")
        self.assertEqual(parse_command("вставь сюда")["intent"], "paste")
    def test_no_implicit_execution(self):
        kb = FakeKeyboard()
        self.assertEqual(execute_command("вставь", keyboard=kb)["status"], "confirmation_required")
        self.assertEqual(kb.calls, [])
    @patch("jarvis.actions.platform.system", return_value="Windows")
    def test_explicit_execution(self, _):
        kb = FakeKeyboard()
        self.assertEqual(execute_command("скопируй", approved=True, keyboard=kb)["status"], "executed")
        self.assertEqual(kb.calls, [("ctrl", "c")])
    def test_unknown_never_executes(self):
        kb = FakeKeyboard()
        self.assertEqual(execute_command("удали всё", approved=True, keyboard=kb)["status"], "unknown")
        self.assertEqual(kb.calls, [])

if __name__ == "__main__":
    unittest.main()
