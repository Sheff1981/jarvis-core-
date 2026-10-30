"""Offline streaming CLI test."""
import os
import tempfile
import unittest

from jarvis.projects import Projects
from streaming_cli import main


class StreamingCliTests(unittest.TestCase):
    def test_chunks_render_in_order(self):
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "jarvis.db")
            projects = Projects(path)
            pid = projects.add("JARVIS")
            projects.close()
            outputs = []
            questions = iter(["Hello", "/exit"])

            def fake_output(*args, **kwargs):
                outputs.append("".join(str(arg) for arg in args))

            def fake_stream(pid_arg, question, **kwargs):
                self.assertEqual(pid_arg, pid)
                self.assertEqual(question, "Hello")
                yield "First "
                yield "second"

            self.assertEqual(main([pid, "--db", path], input_fn=lambda _: next(questions),
                                  output_fn=fake_output, stream_fn=fake_stream), 0)
            self.assertEqual(outputs[-3:], ["First ", "second", ""])


if __name__ == "__main__":
    unittest.main()
