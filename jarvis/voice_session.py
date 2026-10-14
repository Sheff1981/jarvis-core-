"""Thread-safe voice event coordinator independent of microphone hardware."""
import queue
import threading


class VoiceSession:
    def __init__(self, assistant, input_device):
        self.assistant = assistant
        self.input_device = input_device
        self.events = queue.Queue()
        self.stop_event = threading.Event()

    def run(self, on_event):
        def capture():
            try:
                self.input_device.listen(
                    lambda phrase: self.events.put(("speech", phrase)), self.stop_event
                )
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
                    on_event("heard", value)
                    answer = self.assistant.respond(value)
                    on_event("answer", answer)
                    if answer == "Останавливаюсь.":
                        self.stop_event.set()
                else:
                    on_event(kind, value)
                    break
        finally:
            self.stop_event.set()
            microphone.join(timeout=2)
