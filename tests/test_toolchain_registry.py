"""Multi-language toolchain discovery and execution safety tests."""
import unittest
from jarvis.toolchain_registry import ToolchainRegistry, TOOLCHAINS


class ToolchainRegistryTests(unittest.TestCase):
    def test_languages_covered(self):
        for name in ("Java", "C++", "JavaScript", "PHP", "Rust", "Go"):
            self.assertIn(name, TOOLCHAINS)

    def test_missing_toolchain_blocked(self):
        registry = ToolchainRegistry(finder=lambda name: None)
        self.assertTrue(all(not item.available for item in registry.discover()))
        self.assertEqual(registry.plan("Java")["status"], "blocked")

    def test_execution_requires_approval_and_sandbox(self):
        registry = ToolchainRegistry(finder=lambda name: "/tools/" + name)
        self.assertEqual(registry.plan("C++")["status"], "blocked")
        self.assertEqual(registry.plan("C++", owner_approved=True)["status"], "blocked")
        result = registry.plan("C++", owner_approved=True, sandbox_ready=True)
        self.assertEqual(result["status"], "ready_for_isolated_runner")

    def test_unsupported_language(self):
        registry = ToolchainRegistry(finder=lambda name: "/tools/" + name)
        self.assertEqual(registry.plan("unknown")["status"], "unsupported")


if __name__ == "__main__":
    unittest.main()
