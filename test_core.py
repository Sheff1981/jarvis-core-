import tempfile
import unittest
from pathlib import Path
from jarvis.core import Memory
from jarvis.windows import replay


class TestMemory(unittest.TestCase):
    def test_save_get_list(self):
        with tempfile.TemporaryDirectory() as folder:
            with Memory(str(Path(folder) / 'test.db')) as db:
                steps = [{'action': 'click', 'x': 1, 'y': 2, 'button': 'left', 'delay': 0.1}]
                sid = db.save('example', 'windows', steps)
                self.assertEqual(db.get(sid)['steps'], steps)
                self.assertEqual(db.list()[0][0], sid)
                replay(steps, dry_run=True)

    def test_close_is_idempotent(self):
        with tempfile.TemporaryDirectory() as folder:
            db = Memory(str(Path(folder) / 'test.db'))
            db.close()
            db.close()
            self.assertIsNone(db.db)


if __name__ == '__main__':
    unittest.main()
