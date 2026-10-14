import unittest
from jarvis.tray import TrayController


class TrayControllerTests(unittest.TestCase):
    def test_mute_is_opt_in_and_reversible(self):
        controller = TrayController()
        self.assertFalse(controller.muted)
        self.assertTrue(controller.toggle_mute())
        self.assertTrue(controller.muted)
        self.assertFalse(controller.toggle_mute())
        self.assertFalse(controller.muted)

    def test_exit_is_explicit(self):
        controller = TrayController()
        self.assertFalse(controller.exit_requested)
        controller.request_exit()
        self.assertTrue(controller.exit_requested)


if __name__ == "__main__":
    unittest.main()
