import tempfile
import unittest
from pathlib import Path
from jarvis.projects import Projects

class TestProjects(unittest.TestCase):
    def test_persistence(self):
        with tempfile.TemporaryDirectory() as folder:
            path = str(Path(folder) / "projects.db")
            store = Projects(path)
            pid = store.add("Demo", "Write tests")
            store.close()
            store = Projects(path)
            self.assertEqual(store.list()[0]["next_step"], "Write tests")
            store.update(pid, status="done")
            self.assertEqual(store.list(), [])
            self.assertEqual(len(store.list(include_done=True)), 1)
            store.close()

if __name__ == "__main__":
    unittest.main()
