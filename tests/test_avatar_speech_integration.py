"""Static contract checks for browser speech and 3D jaw integration."""
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1] / "jarvis"


class AvatarSpeechIntegrationTests(unittest.TestCase):
    def test_mouth_is_controlled_externally(self):
        source = (ROOT / "avatar3d.js").read_text(encoding="utf-8")
        self.assertIn("setMouth(v)", source)
        self.assertIn("mouthLevel", source)
        self.assertNotIn("0.065*Math.abs(Math.sin(t*9))", source)

    def test_browser_uses_speech_boundary_events(self):
        source = (ROOT / "dashboard.js").read_text(encoding="utf-8")
        self.assertIn("utterance.onboundary", source)
        self.assertIn("avatar.setMouth(0.85)", source)
        self.assertIn("voiceGeneration", source)
        self.assertIn("saveSettings()", source)
        self.assertIn("localStorage", source)


if __name__ == "__main__":
    unittest.main()
