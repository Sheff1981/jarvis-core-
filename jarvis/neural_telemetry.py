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
    succeeded: bool = True


def measured_inference(adapter, prompt, clock=perf_counter,
                       memory_probe=current_process_memory):
    before = memory_probe()
    start = clock()
    result = None
    succeeded = False
    try:
        result = adapter.infer(prompt)
        succeeded = True
        return result, InferenceTelemetry(
            max(0.0, (clock() - start) * 1000),
            before.rss_bytes, memory_probe().rss_bytes,
            result.backend, succeeded)
    finally:
        # The caller retains the original inference exception. No transcripts
        # or prompts are logged by this measurement layer.
        pass
