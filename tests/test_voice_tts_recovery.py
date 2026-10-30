"""Regression: a TTS exception must not terminate the voice worker."""
import sys
import unittest
from unittest.mock import patch

import voice_chat


class TTSErrorRecoveryTests(unittest.TestCase):
    def test_tts_failure_does_not_abort_subsequent_answers(self):
        responses = []

        class FakeSpeaker:
            def __init__(self, **kwargs):
                self.calls = 0

            def say(self, phrase):
                self.calls += 1
                responses.append(phrase)
                if self.calls == 1:
                    raise OSError("synthetic Piper failure")
                return True

            def close(self):
                pass

        class FakeSession:
            def __init__(self, assistant, input_device, **kwargs):
                self.last_timings = None

            def run(self, on_event):
                on_event("answer", "первый ответ")
                on_event("answer", "второй ответ")

        with patch.object(sys, "argv", ["voice_chat.py", "--model", "fake",
                                        "--speak", "--tts", "piper",
                                        "--piper-bin", "piper.exe",
                                        "--piper-voice", "voice.onnx"]), \
             patch("voice_chat.Assistant"), \
             patch("voice_chat.VoiceInput"), \
             patch("voice_chat.VoiceSession", FakeSession), \
             patch("voice_chat.Speaker", FakeSpeaker):
            voice_chat.main()

        self.assertEqual(responses, ["первый ответ", "второй ответ"])


if __name__ == "__main__":
    unittest.main()
