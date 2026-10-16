"""Bounded producer/consumer pipeline for offline speaker verification.

Audio callbacks only enqueue PCM chunks. The worker owns VAD segmentation,
speaker embedding inference, and Vosk. On overflow the pipeline fails closed:
discard buffered audio and reset segment state.
"""
import json
import queue
import threading

from jarvis.frame_energy import FrameEnergyDetector
from jarvis.utterance_segmenter import UtteranceSegmenter


class VoiceIDWorker:
    def __init__(self, gate, recognizer_factory, on_text, sample_rate=16000,
                 queue_size=32, detector=None, should_listen=None):
        if gate is None or not gate.enabled:
            raise ValueError("enabled speaker gate required")
        if sample_rate != 16000 or queue_size < 2:
            raise ValueError("unsupported Voice ID worker configuration")
        self.gate = gate
        self.recognizer_factory = recognizer_factory
        self.on_text = on_text
        self.sample_rate = sample_rate
        self.should_listen = should_listen
        self.queue = queue.Queue(maxsize=queue_size)
        self.segmenter = UtteranceSegmenter(detector or FrameEnergyDetector())
        self.invalidated = threading.Event()
        self._queue_lock = threading.Lock()
        self._generation = 0
        self.stop_requested = threading.Event()
        self.error = None
        self.dropped_chunks = 0
        self.accepted = 0
        self.rejected = 0
        self.thread = None

    def submit(self, audio):
        if self.stop_requested.is_set():
            return False
        with self._queue_lock:
            if self.invalidated.is_set() or self.stop_requested.is_set():
                return False
            try:
                self.queue.put_nowait((self._generation, bytes(audio)))
                return True
            except queue.Full:
                self.dropped_chunks += 1
                self._generation += 1
                self.invalidated.set()
                return False

    def start(self):
        if self.thread is not None:
            raise RuntimeError("worker already started")
        self.thread = threading.Thread(target=self._run, name="jarvis-voice-id", daemon=True)
        self.thread.start()

    def _run(self):
        try:
            while not self.stop_requested.is_set():
                if self.invalidated.is_set():
                    with self._queue_lock:
                        self.segmenter.reset()
                        while True:
                            try:
                                self.queue.get_nowait()
                            except queue.Empty:
                                break
                        self.invalidated.clear()
                try:
                    generation, audio = self.queue.get(timeout=0.05)
                except queue.Empty:
                    continue
                if generation != self._generation:
                    self.segmenter.reset()
                    continue
                if self.should_listen is not None and not self.should_listen():
                    self.segmenter.reset()
                    continue
                for utterance in self.segmenter.push(audio):
                    if self.stop_requested.is_set() or self.invalidated.is_set() or generation != self._generation:
                        break
                    if not self.gate.verify(utterance, self.sample_rate).accepted:
                        self.rejected += 1
                        continue
                    if self.invalidated.is_set() or self.stop_requested.is_set() or generation != self._generation:
                        break
                    recognizer = self.recognizer_factory()
                    recognizer.AcceptWaveform(utterance)
                    phrase = json.loads(recognizer.FinalResult()).get("text", "").strip()
                    if phrase and not self.stop_requested.is_set() and not self.invalidated.is_set() and generation == self._generation:
                        if self.should_listen is None or self.should_listen():
                            self.accepted += 1
                            self.on_text(phrase)
        except Exception as exc:
            self.error = exc
            self.stop_requested.set()

    def stop(self):
        self.stop_requested.set()
        if self.thread is not None:
            self.thread.join(timeout=2)
            if self.thread.is_alive():
                raise RuntimeError("Voice ID worker failed to stop")
