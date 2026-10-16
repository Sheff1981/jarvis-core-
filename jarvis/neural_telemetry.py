"""Read-only neural runtime diagnostics; no transcripts or audio stored."""
from dataclasses import dataclass
from time import perf_counter

from jarvis.process_memory import current_process_memory


@dataclass(frozen=True)
class InferenceTelemetry:
    duration_ms: float
    rss_before_bytes: int | None
    rss_after_bytes: int | None
    backend: str


def measured_inference(adapter, prompt, clock=perf_counter,
                       memory_probe=current_process_memory):
    before = memory_probe()
    start = clock()
    try:
        result = adapter.infer(prompt)
    finally:
        elapsed = max(0.0, (clock() - start) * 1000)
    after = memory_probe()
    return result, InferenceTelemetry(
        elapsed, before.rss_bytes, after.rss_bytes, result.backend)
