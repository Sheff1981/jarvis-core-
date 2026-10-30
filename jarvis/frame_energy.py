"""Lightweight frame energy detector; not a speaker or speech classifier."""
from array import array
import math
import sys


class FrameEnergyDetector:
    def __init__(self, threshold=350):
        if threshold <= 0:
            raise ValueError("threshold must be positive")
        self.threshold = threshold

    def __call__(self, pcm16):
        if len(pcm16) % 2 or not pcm16:
            raise ValueError("invalid PCM16 frame")
        values = array("h")
        values.frombytes(pcm16)
        if sys.byteorder != "little":
            values.byteswap()
        rms = math.sqrt(sum(x * x for x in values) / len(values))
        return rms >= self.threshold
