"""Speech-only preview must not create a microphone or load the LLM."""
import sys
import unittest
from unittest.mock import patch

import voice_chat


class VoicePreviewTests(unittest.TestCase):
    def test_male_preview_works_without_vosk_model_or_ollama(self):
        argv = ["voice_chat.py", "--voice-preview", "--tts", "piper",
                "--piper-bin", "D:/piper/piper.exe",
                "--piper-voice", "D:/voice/ru_RU-dmitri-medium.onnx"]
        with patch.object(sys, "argv", argv), \
             patch("voice_chat.Speaker") as speaker, \
             patch("voice_chat.Assistant") as assistant, \
             patch("voice_chat.VoiceInput") as mic, \
             patch("voice_chat.VoiceSession") as session:
            voice_chat.main()
        speaker.assert_called_once_with(
            enabled=True, backend="piper",
            piper_exe="D:/piper/piper.exe",
            voice_model="D:/voice/ru_RU-dmitri-medium.onnx",
        )
        speaker.return_value.say.assert_called_once()
        self.assertIn("Привет", speaker.return_value.say.call_args.args[0])
        speaker.return_value.close.assert_called_once()
        assistant.assert_not_called()
        mic.assert_not_called()
        session.assert_not_called()

    def test_slow_serious_voice_preview_forwards_pacing(self):
        argv = [
            "voice_chat.py", "--voice-preview", "--tts", "piper",
            "--piper-bin", "D:/piper/piper.exe",
            "--piper-voice", "D:/voice/ru_RU-ruslan-medium.onnx",
            "--piper-length-scale", "1.16",
            "--piper-sentence-silence", "0.35",
        ]
        with patch.object(sys, "argv", argv), \
             patch("voice_chat.Speaker") as speaker:
            voice_chat.main()
        self.assertEqual(speaker.call_args.kwargs["piper_length_scale"], 1.16)
        self.assertEqual(speaker.call_args.kwargs["piper_sentence_silence"], 0.35)

    def test_listening_mode_still_requires_vosk_path(self):
        with patch.object(sys, "argv", ["voice_chat.py", "--speak"]):
            with self.assertRaises(SystemExit) as error:
                voice_chat.main()
        self.assertEqual(error.exception.code, 2)


if __name__ == "__main__":
    unittest.main()
