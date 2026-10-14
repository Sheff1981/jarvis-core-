"""Thread-safe voice event coordinator with speech feedback gating."""
import queue
import threading


class VoiceSession:
    def __init__(self, assistant, input_device):
        self.assistant = assistant
        self.input_device = input_device
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.busy_event = threading.Event()

    def run(self, on_event):
        def capture():
            try:
                def recognized(phrase):
                    # Ignore finalized phrases while processing or speaking.
                    if not self.stop_event.is_set() and not self.busy_event.is_set():
                        self.events.put(("speech", phrase))
                self.input_device.listen(recognized, self.stop_event)
            except Exception as exc:
                self.events.put(("error", str(exc)))
            finally:
                self.events.put(("ended", ""))

        microphone = threading.Thread(target=capture, daemon=True)
        microphone.start()
        try:
            while not self.stop_event.is_set():
                try:
                    kind, value = self.events.get(timeout=0.2)
                except queue.Empty:
                    continue
                if kind == "speech":
                    self.busy_event.set()
                    try:
                        on_event("heard", value)
                        answer = self.assistant.respond(value)
                        on_event("answer", answer)
                        if answer == "Останавливаюсь.":
                            self.stop_event.set()
                    finally:
                        # Discard phrases queued before the busy flag was set.
                        retained = []
                        while True:
                            try:
                                queued = self.events.get_nowait()
                            except queue.Empty:
                                break
                            if queued[0] != "speech":
                                retained.append(queued)
                        for item in retained:
                            self.events.put(item)
                        self.busy_event.clear()
                else:
                    on_event(kind, value)
                    break
        finally:
            self.stop_event.set()
            microphone.join(timeout=2)
