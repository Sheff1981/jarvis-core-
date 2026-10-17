"""Background learning worker with bounded, interruptible periodic checks."""
import threading
from jarvis.autonomous_learning import AutonomousLearningLoop


def learning_worker(stop, db_path, *, interval_seconds=900, loop_factory=AutonomousLearningLoop,
                    on_result=None):
    if not 60 <= interval_seconds <= 86400:
        raise ValueError("Invalid learning interval")
    loop = loop_factory(db_path)
    while not stop.is_set():
        try:
            result = loop.tick(enabled=True, max_pages=2)
            if on_result:
                on_result(result)
        except Exception as exc:
            if on_result:
                on_result({"status": "error", "reason": type(exc).__name__})
        if stop.wait(interval_seconds):
            break


def start_learning_worker(stop, db_path, *, interval_seconds=900):
    thread = threading.Thread(
        target=learning_worker, args=(stop, db_path),
        kwargs={"interval_seconds": interval_seconds},
        name="jarvis-learning", daemon=True)
    thread.start()
    return thread
