"""Ensure the existing voice pipeline selects the requested local speech engine."""
import sys
import unittest
from unittest.mock import patch

import voice_chat


class VoiceTtsEntrypointTests(unittest.TestCase):
    def test_piper_voice_uses_existing_voice_session_and_cpu_llm(self):
        argv = [
            "voice_chat.py", "--model", "D:/JARVIS-test/voice/vosk",
            "--db", "D:/JARVIS-test/data/jarvis-test.db",
            "--llm-model", "qwen2.5:3b-instruct-q6_K", "--cpu-only",
            "--speak", "--tts", "piper", "--piper-bin", "D:/piper/piper.exe",
            "--piper-voice", "D:/voices/ru_RU-dmitri-medium.onnx",
        ]
        with patch.object(sys, "argv", argv), \
             patch("voice_chat.Assistant") as assistant, \
             patch("voice_chat.VoiceInput"), \
             patch("voice_chat.VoiceSession") as session, \
             patch("voice_chat.Speaker") as speaker:
            voice_chat.main()
        self.assertEqual(speaker.call_args.kwargs, {
            "enabled": True, "backend": "piper",
            "piper_exe": "D:/piper/piper.exe",
            "voice_model": "D:/voices/ru_RU-dmitri-medium.onnx",
        })
        self.assertTrue(assistant.call_args.kwargs["llm"].cpu_only)
        self.assertIs(session.call_args.args[0], assistant.return_value)
        self.assertTrue(session.call_args.kwargs["require_wake"])

    def test_default_speech_engine_remains_sapi(self):
        with patch.object(sys, "argv", ["voice_chat.py", "--model", "vosk", "--speak"]), \
             patch("voice_chat.Assistant"), \
             patch("voice_chat.VoiceInput"), \
             patch("voice_chat.VoiceSession"), \
             patch("voice_chat.Speaker") as speaker:
            voice_chat.main()
        self.assertEqual(speaker.call_args.kwargs["backend"], "sapi")

    def test_piper_requires_explicit_paths(self):
        with patch.object(sys, "argv", ["voice_chat.py", "--model", "vosk",
                                        "--speak", "--tts", "piper"]):
            with self.assertRaises(SystemExit) as error:
                voice_chat.main()
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
