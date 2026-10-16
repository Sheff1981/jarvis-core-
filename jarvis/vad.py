"""Dependency-free audio frame validation and VAD adapter contract.

This module does not enable VAD in the live microphone pipeline.
An actual speech detector can implement SpeechDetector.is_speech(frame).
"""
from abc import ABC, abstractmethod


class SpeechDetector(ABC):
    """One 16-bit mono PCM frame in; one speech/non-speech decision out."""

    @abstractmethod
    def is_speech(self, pcm16_frame: bytes) -> bool:
        """Return whether the frame contains speech."""


def validate_pcm16_frame(frame: bytes, sample_rate: int, frame_ms: int) -> None:
    """Validate the fixed-size frame expected by streaming VAD backends."""
    if isinstance(sample_rate, bool) or sample_rate not in (8000, 16000, 32000, 48000):
        raise ValueError("Unsupported VAD sample rate")
    if isinstance(frame_ms, bool) or frame_ms not in (10, 20, 30):
        raise ValueError("VAD frame must be 10, 20 or 30 milliseconds")
    if not isinstance(frame, bytes):
        raise TypeError("PCM frame must be bytes")
    expected = sample_rate * frame_ms // 1000 * 2
    if len(frame) != expected:
        raise ValueError(f"PCM frame must be exactly {expected} bytes")

class EnergyVAD(SpeechDetector):
    """Low-cost energy gate for optional use; not a neural speech detector.

    It detects sufficiently loud audio, including noise. It is not suitable
    as a standalone wake-word or command recognizer.
    """

    def __init__(self, threshold=450, sample_rate=16000, frame_ms=20):
        if isinstance(threshold, bool) or not isinstance(threshold, (int, float)):
            raise ValueError("threshold must be a non-negative finite number")
        import math
        if not math.isfinite(threshold) or threshold < 0:
            raise ValueError("threshold must be a non-negative finite number")
        validate_pcm16_frame(bytes(sample_rate * frame_ms // 1000 * 2),
                             sample_rate, frame_ms)
        self.threshold = threshold
        self.sample_rate = sample_rate
        self.frame_ms = frame_ms

    def is_speech(self, pcm16_frame: bytes) -> bool:
        import array
        import math
        import sys
        validate_pcm16_frame(pcm16_frame, self.sample_rate, self.frame_ms)
        samples = array.array("h")
        samples.frombytes(pcm16_frame)
        if sys.byteorder != "little":
            samples.byteswap()
        return math.sqrt(sum(sample * sample for sample in samples) / len(samples)) >= self.threshold


class AudioFrameBuffer:
    """Convert arbitrary PCM16 chunks into fixed-duration VAD frames."""

    def __init__(self, sample_rate=16000, frame_ms=20):
        validate_pcm16_frame(bytes(sample_rate * frame_ms // 1000 * 2),
                             sample_rate, frame_ms)
        self.frame_bytes = sample_rate * frame_ms // 1000 * 2
        self._pending = bytearray()

    def push(self, chunk: bytes):
        if not isinstance(chunk, bytes):
            raise TypeError("PCM chunk must be bytes")
        if len(chunk) % 2:
            raise ValueError("PCM16 chunk must contain complete samples")
        self._pending.extend(chunk)
        frames = []
        while len(self._pending) >= self.frame_bytes:
            frames.append(bytes(self._pending[:self.frame_bytes]))
            del self._pending[:self.frame_bytes]
        return frames

    def reset(self):
        """Drop incomplete audio when microphone capture is restarted."""
        self._pending.clear()

    @property
    def pending_bytes(self):
        return len(self._pending)


class SpeechActivityTracker:
    """Debounce noisy VAD decisions with attack and release frame counts.

    True means an active audio segment, not guaranteed human speech.
    """

    def __init__(self, start_frames=2, stop_frames=12):
        if (type(start_frames) is not int or start_frames < 1 or
                type(stop_frames) is not int or stop_frames < 1):
            raise ValueError("start_frames and stop_frames must be positive integers")
        self.start_frames = start_frames
        self.stop_frames = stop_frames
        self.reset()

    def reset(self):
        self.active = False
        self._speech_run = 0
        self._silence_run = 0

    def update(self, detected: bool) -> bool:
        if type(detected) is not bool:
            raise TypeError("VAD decision must be boolean")
        if detected:
            self._silence_run = 0
            self._speech_run += 1
            if self._speech_run >= self.start_frames:
                self.active = True
        else:
            self._speech_run = 0
            self._silence_run += 1
            if self._silence_run >= self.stop_frames:
                self.active = False
        return self.active
