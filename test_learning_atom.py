import unittest
from jarvis.learning_collector import parse_feed

ATOM = b'''<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Python 3 release</title><link rel="alternate" href="https://github.com/python/cpython/releases/tag/v3"/></entry></feed>'''

class AtomParsingTests(unittest.TestCase):
    def test_atom_release(self):
        self.assertEqual(parse_feed(ATOM), [('Python 3 release', 'https://github.com/python/cpython/releases/tag/v3')])
