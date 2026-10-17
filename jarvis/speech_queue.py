"""Bounded background speech queue; synthesizer is injected."""
import queue
import threading


class SpeechQueue:
    def __init__(self, speak, max_pending=4):
        if not callable(speak):
            raise TypeError("speak must be callable")
        if not isinstance(max_pending, int) or isinstance(max_pending, bool) or max_pending < 1:
            raise ValueError("max_pending must be positive")
        self._queue = queue.Queue(maxsize=max_pending)
        self._speak = speak
        self._errors = []
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()
        self._closed = False

    def _run(self):
        while True:
            item = self._queue.get()
            try:
                if item is None:
                    return
                self._speak(item)
            except Exception as exc:
                self._errors.append(exc)
            finally:
                self._queue.task_done()

    def submit(self, sentence):
        if self._closed:
            raise RuntimeError("Speech queue is closed")
        if sentence.strip():
            self._queue.put(sentence)

    def finish(self):
        if not self._closed:
            self._closed = True
            self._queue.put(None)
        self._queue.join()
        self._thread.join()
        if self._errors:
            raise RuntimeError("Speech synthesis failed") from self._errors[0]
