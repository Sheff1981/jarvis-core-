"""Offline voice processing quality counters and acceptance thresholds.

This module records aggregate numbers only; it does not store audio or text.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceQuality:
    received_chunks: int
    lost_chunks: int
    accepted_utterances: int
    rejected_utterances: int
    queue_depth: int

    @property
    def loss_ratio(self):
        total = self.received_chunks + self.lost_chunks
        return self.lost_chunks / total if total else 0.0

    def health(self, max_loss_ratio=0.01):
        if not 0 <= max_loss_ratio <= 1:
            raise ValueError("invalid loss ratio limit")
        if self.lost_chunks and self.loss_ratio > max_loss_ratio:
            return "degraded"
        return "ok"


def assess_worker(worker):
    return VoiceQuality(
        received_chunks=worker.received_chunks,
        lost_chunks=worker.dropped_chunks,
        accepted_utterances=worker.accepted,
        rejected_utterances=worker.rejected,
        queue_depth=worker.queue.qsize(),
    )
