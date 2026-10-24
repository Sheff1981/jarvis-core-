import unittest

from jarvis.response_pipeline import consume_response
from jarvis.speech_chunks import SpeechChunker
from jarvis.speech_queue import SpeechQueue


class SpeechPipelineTests(unittest.TestCase):
    def test_sentence_split_across_chunks(self):
        splitter = SpeechChunker()
        self.assertEqual(splitter.feed("Привет, как де"), [])
        self.assertEqual(splitter.feed("ла? Всё хорошо. Продолжаем"), ["Привет, как дела?", "Всё хорошо."])
        self.assertEqual(splitter.flush(), ["Продолжаем"])

    def test_pipeline_preserves_full_text(self):
        spoken = []
        written = []
        metrics = consume_response(["Привет. ", "Работаем дальше!"],
                                   speak=spoken.append, write=written.append)
        self.assertEqual(spoken, ["Привет.", "Работаем дальше!"])
        self.assertEqual(metrics["text"], "".join(written))
        self.assertEqual(metrics["sentences"], 2)

    def test_speech_queue_order(self):
        spoken = []
        queue = SpeechQueue(spoken.append, max_pending=2)
        queue.submit("Первое.")
        queue.submit("Второе.")
        queue.finish()
        self.assertEqual(spoken, ["Первое.", "Второе."])
        with self.assertRaises(RuntimeError):
            queue.submit("Третье.")


if __name__ == "__main__":
    unittest.main()
