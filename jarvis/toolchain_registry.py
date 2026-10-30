"""Multi-language practice planning and toolchain discovery.

Never executes arbitrary downloaded source. Real compilation requires a
separately provisioned OS/container sandbox and owner approval.
"""
from dataclasses import dataclass
import shutil


@dataclass(frozen=True)
class Toolchain:
    language: str
    executable: str
    available: bool
    execution_policy: str = "isolated_runner_required"


TOOLCHAINS = {
    "Python": ("python", "py"),
    "Java": ("javac",),
    "C++": ("g++", "clang++"),
    "C": ("gcc", "clang"),
    "JavaScript": ("node",),
    "TypeScript": ("tsc",),
    "PHP": ("php",),
    "Go": ("go",),
    "Rust": ("rustc",),
    "C#": ("dotnet",),
    "Kotlin": ("kotlinc",),
    "Ruby": ("ruby",),
    "Dart": ("dart",),
    "Swift": ("swift",),
}


class ToolchainRegistry:
    def __init__(self, finder=None):
        self.finder = finder or shutil.which

    def discover(self):
        results = []
        for language, executables in TOOLCHAINS.items():
            found = next((path for name in executables
                          if (path := self.finder(name))), None)
            results.append(Toolchain(language, found or executables[0], bool(found)))
        return results

    def plan(self, language, *, owner_approved=False, sandbox_ready=False):
        if language not in TOOLCHAINS:
            return {"status": "unsupported", "reason": "No toolchain profile"}
        tool = next(item for item in self.discover() if item.language == language)
        if not tool.available:
            return {"status": "blocked", "reason": "Compiler/interpreter not installed"}
        if not owner_approved:
            return {"status": "blocked", "reason": "Owner approval required"}
        if not sandbox_ready:
            return {"status": "blocked", "reason": "Verified OS isolation required"}
        return {"status": "ready_for_isolated_runner", "language": language,
                "executable": tool.executable}
