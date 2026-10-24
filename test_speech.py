import unittest
from jarvis.speech import Speaker


class FakeEngine:
    def __init__(self):
        self.messages = []
        self.ran = False
        self.stopped = False

    def say(self, message):
        self.messages.append(message)

    def runAndWait(self):
        self.ran = True

    def stop(self):
        self.stopped = True


class SpeakerTests(unittest.TestCase):
    def test_disabled_never_initializes_engine(self):
        speaker = Speaker()
        self.assertFalse(speaker.say("Привет"))
        self.assertIsNone(speaker._engine)

    def test_speaks_and_closes_with_fake_engine(self):
        engine = FakeEngine()
        speaker = Speaker(enabled=True)
        speaker._engine = engine
        self.assertTrue(speaker.say("Привет"))
        self.assertEqual(engine.messages, ["Привет"])
        self.assertTrue(engine.ran)
        speaker.close()
        self.assertTrue(engine.stopped)


if __name__ == "__main__":
    unittest.main()
