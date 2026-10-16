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
