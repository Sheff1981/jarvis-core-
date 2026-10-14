"""The existing voice entrypoint must reuse the CPU fallback verified on Windows."""
import sys
import unittest
from unittest.mock import MagicMock, patch

import voice_chat


class VoiceCpuEntrypointTests(unittest.TestCase):
    def test_cpu_mode_passes_bounded_llm_to_assistant(self):
        argv = [
            "voice_chat.py", "--model", r"D:\\JARVIS-test\\vosk-ru",
            "--llm-model", "qwen2.5:3b-instruct-q6_K", "--cpu-only",
            "--db", r"D:\\JARVIS-test\\data\\jarvis-test.db",
        ]
        with patch.object(sys, "argv", argv), \
             patch("voice_chat.Assistant") as assistant, \
             patch("voice_chat.VoiceInput") as microphone, \
             patch("voice_chat.VoiceSession") as session, \
             patch("voice_chat.Speaker") as speaker:
            assistant.return_value = MagicMock()
            voice_chat.main()
        llm = assistant.call_args.kwargs["llm"]
        self.assertTrue(llm.cpu_only)
        self.assertEqual(llm.model, "qwen2.5:3b-instruct-q6_K")
        self.assertEqual(llm.timeout, 120)
        self.assertEqual(assistant.call_args.kwargs["db_path"],
                         r"D:\\JARVIS-test\\data\\jarvis-test.db")
        self.assertTrue(microphone.called)
        self.assertTrue(session.called)
        self.assertTrue(speaker.called)
        assistant.return_value.close.assert_called_once()

    def test_default_voice_mode_preserves_existing_configuration(self):
        with patch.object(sys, "argv", ["voice_chat.py", "--model", "vosk-ru"]), \
             patch("voice_chat.Assistant") as assistant, \
             patch("voice_chat.VoiceInput"), \
             patch("voice_chat.VoiceSession"), \
             patch("voice_chat.Speaker"):
            voice_chat.main()
        self.assertNotIn("llm", assistant.call_args.kwargs)


if __name__ == "__main__":
    unittest.main()
