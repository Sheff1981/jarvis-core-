"""Speech tests do not touch speakers or audio drivers."""
import sys
import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from jarvis.speech import Speaker, _russian_voice


class RussianSpeechTests(unittest.TestCase):
    def test_detect_russian_from_windows_voice_name(self):
        voice = SimpleNamespace(
            id="HKEY_LOCAL_MACHINE\\\\...\\\\Microsoft Irina Desktop",
            name="Microsoft Irina Desktop", languages=[],
        )
        self.assertTrue(_russian_voice(voice))

    def test_detect_russian_from_vosk_independent_language_tag(self):
        voice = SimpleNamespace(id="voice_1", name="Voice", languages=[b"\\x05ru-RU"])
        self.assertTrue(_russian_voice(voice))

    def test_english_voice_is_not_mistaken_for_russian(self):
        voice = SimpleNamespace(id="zira", name="Microsoft Zira Desktop", languages=["en-US"])
        self.assertFalse(_russian_voice(voice))

    def test_speaker_selects_russian_voice_and_speaks_once(self):
        english = SimpleNamespace(id="zira", name="Microsoft Zira Desktop", languages=["en-US"])
        russian = SimpleNamespace(id="irina", name="Microsoft Irina Desktop", languages=["ru-RU"])
        engine = MagicMock()
        engine.getProperty.return_value = [english, russian]
        library = MagicMock()
        library.init.return_value = engine
        with patch.dict(sys.modules, {"pyttsx3": library}):
            speaker = Speaker(enabled=True, rate=170)
            self.assertTrue(speaker.say("Привет. Я Джарвис."))
            self.assertTrue(speaker.say("Продолжаем."))
            speaker.close()
        engine.setProperty.assert_any_call("rate", 170)
        engine.setProperty.assert_any_call("voice", "irina")
        engine.say.assert_any_call("Привет. Я Джарвис.")
        self.assertEqual(engine.runAndWait.call_count, 2)
        engine.stop.assert_called_once()
        library.init.assert_called_once()

    def test_disabled_speaker_never_loads_speech_engine(self):
        with patch.dict(sys.modules, {"pyttsx3": None}):
            speaker = Speaker()
            self.assertFalse(speaker.say("Привет"))
            speaker.close()

    def test_english_only_fallback_keeps_previous_default(self):
        engine = MagicMock()
        engine.getProperty.return_value = [
            SimpleNamespace(id="zira", name="Microsoft Zira Desktop", languages=["en-US"])
        ]
        library = MagicMock()
        library.init.return_value = engine
        with patch.dict(sys.modules, {"pyttsx3": library}):
            speaker = Speaker(enabled=True)
            self.assertTrue(speaker.say("Test"))
            speaker.close()
        self.assertNotIn("voice", [call.args[0] for call in engine.setProperty.call_args_list])


if __name__ == "__main__":
    unittest.main()
