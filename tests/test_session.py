import unittest
from jarvis.session import Mode, Session


class SessionTests(unittest.TestCase):
    def test_default_is_conversation(self):
        self.assertEqual(Session().mode, Mode.CONVERSATION)

    def test_explicit_switch(self):
        session = Session()
        session.switch("work")
        self.assertEqual(session.mode, Mode.WORK)
        session.clear()
        self.assertEqual(session.mode, Mode.CONVERSATION)

    def test_history_is_bounded(self):
        session = Session()
        for i in range(60):
            session.append("user", str(i))
        self.assertEqual(len(session.history), 40)

    def test_invalid_role_rejected(self):
        with self.assertRaises(ValueError):
            Session().append("system", "unsafe")


if __name__ == "__main__":
    unittest.main()
