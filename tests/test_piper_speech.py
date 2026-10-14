"""Neural male TTS integration tests; no actual Piper binary or audio needed."""
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import MagicMock, patch

from jarvis.speech import Speaker


class PiperSpeakerTests(unittest.TestCase):
    def setUp(self):
        self.folder = tempfile.TemporaryDirectory()
        root = pathlib.Path(self.folder.name)
        self.exe = root / "piper.exe"
        self.exe.write_bytes(b"stand-in")
        self.model = root / "ru_RU-dmitri-medium.onnx"
        self.model.write_bytes(b"stand-in")
        self.config = pathlib.Path(str(self.model) + ".json")
        self.config.write_text("{}", encoding="utf-8")

    def tearDown(self):
        self.folder.cleanup()

    def test_offline_piper_receives_utf8_and_generates_temp_audio(self):
        playback = MagicMock()
        received = []

        def fake_run(args, **kwargs):
            received.append((args, kwargs))
            output = pathlib.Path(args[args.index("--output_file") + 1])
            output.write_bytes(b"RIFF" + b"x" * 80)
            return subprocess.CompletedProcess(args, 0)

        speaker = Speaker(enabled=True, backend="piper",
                          piper_exe=str(self.exe), voice_model=str(self.model))
        with patch("subprocess.run", side_effect=fake_run), \
             patch.dict(sys.modules, {"winsound": playback}):
            self.assertTrue(speaker.say("Привет, Джарвис!"))
        self.assertEqual(len(received), 1)
        command, kwargs = received[0]
        self.assertEqual(command[0], str(self.exe))
        self.assertEqual(command[command.index("--model") + 1], str(self.model))
        self.assertEqual(command[command.index("--config") + 1], str(self.config))
        self.assertEqual(kwargs["input"], "Привет, Джарвис!\n".encode("utf-8"))
        self.assertTrue(kwargs["check"])
        self.assertLessEqual(kwargs["timeout"], 60)
        self.assertNotIn("shell", kwargs)
        playback.PlaySound.assert_called_once()
        self.assertFalse(pathlib.Path(command[command.index("--output_file") + 1]).exists())
        self.assertTrue(self.model.exists())

    def test_deliberate_pacing_and_unicode_without_clipping(self):
        playback = MagicMock()
        recorded = []
        long_phrase = "Джарвис. " + "Проверяем полное произношение слов. " * 42

        def fake_run(args, **kwargs):
            recorded.append((args, kwargs))
            output = pathlib.Path(args[args.index("--output_file") + 1])
            output.write_bytes(b"RIFF" + b"x" * 80)
            return subprocess.CompletedProcess(args, 0)

        speaker = Speaker(
            enabled=True, backend="piper",
            piper_exe=str(self.exe), voice_model=str(self.model),
            piper_length_scale=1.16, piper_sentence_silence=0.35,
        )
        with patch("subprocess.run", side_effect=fake_run), \
             patch.dict(sys.modules, {"winsound": playback}):
            self.assertTrue(speaker.say(long_phrase))
        args, kwargs = recorded[0]
        self.assertEqual(kwargs["input"], (long_phrase + "\n").encode("utf-8"))
        self.assertEqual(args[args.index("--length_scale") + 1], "1.16")
        self.assertEqual(args[args.index("--sentence_silence") + 1], "0.35")

    def test_rejects_invalid_pacing(self):
        for scale in (-1, 0, 0.6, 1.7, float("nan")):
            with self.subTest(scale=scale), self.assertRaises(ValueError):
                Speaker(backend="piper", piper_length_scale=scale)
        for seconds in (-1, 3, float("nan")):
            with self.subTest(seconds=seconds), self.assertRaises(ValueError):
                Speaker(backend="piper", piper_sentence_silence=seconds)

    def test_missing_model_config_is_explicit_error(self):
        self.config.unlink()
        speaker = Speaker(enabled=True, backend="piper",
                          piper_exe=str(self.exe), voice_model=str(self.model))
        with self.assertRaisesRegex(RuntimeError, "конфигурация"):
            speaker.say("Привет")

    def test_missing_piper_binary_is_explicit_error(self):
        speaker = Speaker(enabled=True, backend="piper",
                          piper_exe=str(self.exe) + "-missing",
                          voice_model=str(self.model))
        with self.assertRaisesRegex(RuntimeError, "piper.exe"):
            speaker.say("Привет")

    def test_process_timeout_returns_readable_error(self):
        speaker = Speaker(enabled=True, backend="piper",
                          piper_exe=str(self.exe), voice_model=str(self.model))
        with patch("subprocess.run", side_effect=subprocess.TimeoutExpired("piper", 60)), \
             patch.dict(sys.modules, {"winsound": MagicMock()}):
            with self.assertRaisesRegex(RuntimeError, "голос Piper"):
                speaker.say("Привет")

    def test_no_wav_output_is_not_reported_as_success(self):
        speaker = Speaker(enabled=True, backend="piper",
                          piper_exe=str(self.exe), voice_model=str(self.model))
        with patch("subprocess.run", return_value=None), \
             patch.dict(sys.modules, {"winsound": MagicMock()}):
            with self.assertRaisesRegex(RuntimeError, "не создал звуковой файл"):
                speaker.say("Привет")

    def test_disabled_piper_never_invokes_external_process(self):
        speaker = Speaker(backend="piper")
        with patch("subprocess.run") as run:
            self.assertFalse(speaker.say("Привет"))
            run.assert_not_called()

    def test_unrecognized_backend_rejected(self):
        with self.assertRaises(ValueError):
            Speaker(enabled=True, backend="cloud")


if __name__ == "__main__":
    unittest.main()
