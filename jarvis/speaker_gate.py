"""Offline speaker-verification gate: deny by default, no cloud dependency.

A recognizer can supply a verified speaker decision through the checker.
Until enrollment and a local verifier exist, voice commands are NOT authorized
by this gate. Never use text recognition as evidence of speaker identity.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class SpeakerDecision:
    accepted: bool
    reason: str


class SpeakerGate:
    def __init__(self, checker=None, enabled=False):
        self.checker = checker
        self.enabled = bool(enabled)

    def verify(self, pcm16, sample_rate=16000):
        if not self.enabled:
            return SpeakerDecision(True, "speaker gate disabled")
        if self.checker is None:
            return SpeakerDecision(False, "owner voice not enrolled")
        if not isinstance(pcm16, bytes) or not pcm16 or len(pcm16) % 2:
            return SpeakerDecision(False, "invalid PCM16 audio")
        if sample_rate not in (8000, 16000, 32000, 48000):
            return SpeakerDecision(False, "unsupported sample rate")
        try:
            result = self.checker(pcm16, sample_rate)
        except Exception:
            return SpeakerDecision(False, "speaker verifier failure")
        if type(result) is not bool:
            return SpeakerDecision(False, "invalid verifier result")
        return SpeakerDecision(result, "owner verified" if result else "speaker mismatch")
