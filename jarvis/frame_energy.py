"""Lightweight energy detector for optional pre-ASR segmentation.

This detector distinguishes signal energy, NOT speakers or speech from TV.
Owner verification remains mandatory for every segmented utterance.
"""
import audioop


class FrameEnergyDetector:
    def __init__(self, threshold=350):
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.threshold = threshold

    def __call__(self, pcm16):
        if len(pcm16) % 2:
            raise ValueError("invalid PCM16 frame")
        return audioop.rms(pcm16, 2) >= self.threshold
