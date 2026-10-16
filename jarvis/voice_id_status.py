"""Privacy-safe counters for local Voice ID.

No microphone audio, transcripts or embeddings are stored.
"""
from dataclasses import dataclass


@dataclass(frozen=True)
class VoiceIDStatus:
    state: str
    queued: int
    dropped: int
    accepted: int
    rejected: int
    generation: int


def snapshot(worker):
    if worker.error is not None:
        state = "error"
    elif worker.stop_requested.is_set():
        state = "stopped"
    elif worker.invalidated.is_set():
        state = "recovering"
    elif worker.thread is not None and worker.thread.is_alive():
        state = "running"
    else:
        state = "idle"
    return VoiceIDStatus(state, worker.queue.qsize(), worker.dropped_chunks,
                         worker.accepted, worker.rejected, worker._generation)
