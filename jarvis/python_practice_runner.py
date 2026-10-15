"""Constrained Python practice runner.

Only executes locally authored, owner-approved exercises. Python process
is NOT an OS security sandbox: do not run downloaded or adversarial code.
"""
from dataclasses import dataclass
from pathlib import Path
import os
import subprocess
import sys
import tempfile
import time


@dataclass(frozen=True)
class RunResult:
    passed: bool
    tests_run: int
    elapsed_seconds: float
    output: str
    reason: str


class PythonPracticeRunner:
    def __init__(self, *, timeout_seconds=8, max_output_bytes=16000):
        if not 1 <= timeout_seconds <= 30:
            raise ValueError("Invalid timeout")
        self.timeout_seconds = timeout_seconds
        self.max_output_bytes = max_output_bytes

    def run(self, source, tests, *, owner_approved=False):
        if not owner_approved:
            raise PermissionError("Owner approval required to run local code")
        if not isinstance(source, str) or not isinstance(tests, str):
            raise ValueError("Source and tests must be text")
        if len(source.encode("utf-8")) > 100000 or len(tests.encode("utf-8")) > 100000:
            raise ValueError("Exercise exceeds size limit")
        with tempfile.TemporaryDirectory(prefix="jarvis-practice-") as directory:
            root = Path(directory)
            (root / "solution.py").write_text(source, encoding="utf-8")
            (root / "test_solution.py").write_text(tests, encoding="utf-8")
            env = {"PYTHONPATH": str(root), "PYTHONDONTWRITEBYTECODE": "1",
                   "PYTHONNOUSERSITE": "1", "PATH": os.path.dirname(sys.executable)}
            started = time.monotonic()
            try:
                completed = subprocess.run(
                    [sys.executable, "-I", "-B", "-c",
                     "import sys,unittest; sys.path.insert(0,sys.argv[1]); "
                     "unittest.main(module=None,argv=[\u0027unittest\u0027,\u0027discover\u0027,\u0027-s\u0027,sys.argv[1],\u0027-p\u0027,\u0027test_solution.py\u0027,\u0027-v\u0027])",
                     str(root)],
                    cwd=str(root), env=env, stdin=subprocess.DEVNULL,
                    capture_output=True, timeout=self.timeout_seconds, check=False)
                output = (completed.stdout + completed.stderr)[:self.max_output_bytes].decode(
                    "utf-8", errors="replace")
                # unittest emits its test count to stderr; failures never pass.
                import re
                match = re.search(r"Ran (\d+) tests?", output)
                count = int(match.group(1)) if match else 0
                passed = completed.returncode == 0 and count > 0
                reason = "passed" if passed else "tests_failed"
            except subprocess.TimeoutExpired:
                output, count, passed, reason = "Time limit exceeded", 0, False, "timeout"
            return RunResult(passed, count, round(time.monotonic() - started, 3), output, reason)
