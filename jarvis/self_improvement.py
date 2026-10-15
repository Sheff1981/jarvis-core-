"""Safe local self-improvement staging: propose, validate, and atomically replace.

No arbitrary command execution or unattended Git pushes. Changes are restricted
to an explicitly designated workspace, with backups and test gating.
"""
from pathlib import Path
import shutil
import subprocess
import tempfile


class SelfImprovement:
    def __init__(self, workspace, *, allowed=("jarvis", "tests")):
        self.workspace = Path(workspace).resolve(strict=True)
        self.allowed = tuple(allowed)

    def _target(self, relative_path):
        if not isinstance(relative_path, str) or not relative_path.endswith(".py"):
            raise ValueError("Only Python source files can be staged")
        rel = Path(relative_path)
        if rel.is_absolute() or ".." in rel.parts or not rel.parts or rel.parts[0] not in self.allowed:
            raise ValueError("Path outside approved source directories")
        target = (self.workspace / rel).resolve()
        if not target.is_relative_to(self.workspace) or not target.is_file() or target.is_symlink():
            raise ValueError("Target is missing or unsafe")
        return target

    def stage(self, relative_path, source):
        target = self._target(relative_path)
        if not isinstance(source, str) or not source.strip() or len(source) > 250_000:
            raise ValueError("Invalid candidate source")
        compile(source, str(target), "exec")
        staging = Path(tempfile.mkdtemp(prefix="jarvis-candidate-"))
        shutil.copytree(self.workspace, staging / "project", ignore=shutil.ignore_patterns(
            ".git", ".venv", "__pycache__", "*.db", "models", "backups", ".env"))
        candidate = staging / "project" / relative_path
        candidate.parent.mkdir(parents=True, exist_ok=True)
        candidate.write_text(source, encoding="utf-8")
        return staging

    def validate(self, staging, *, timeout=180):
        root = Path(staging).resolve() / "project"
        if not root.is_dir():
            raise ValueError("Invalid candidate workspace")
        result = subprocess.run(
            ["python", "-m", "unittest", "discover", "-s", "tests"],
            cwd=root, capture_output=True, text=True, timeout=timeout, check=False)
        return {"passed": result.returncode == 0,
                "output": (result.stdout + result.stderr)[-8000:]}

    def apply(self, staging, relative_path, *, validated=False):
        if not validated:
            raise PermissionError("Changes require successful validation")
        target = self._target(relative_path)
        candidate = Path(staging).resolve() / "project" / relative_path
        if not candidate.is_file() or candidate.is_symlink():
            raise ValueError("Candidate missing")
        compile(candidate.read_text(encoding="utf-8"), str(candidate), "exec")
        backup = target.with_suffix(target.suffix + ".jarvis-backup")
        shutil.copy2(target, backup)
        try:
            shutil.copy2(candidate, target)
        except Exception:
            shutil.copy2(backup, target)
            raise
        return backup
