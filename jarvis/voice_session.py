"""Thread-safe voice coordinator with microphone mute and feedback gating."""
import queue
import threading


class VoiceSession:
    def __init__(self, assistant, input_device, controller=None):
        self.assistant = assistant
        self.input_device = input_device
        self.controller = controller
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.busy_event = threading.Event()

    def listening_allowed(self):
        return (not self.stop_event.is_set() and not self.busy_event.is_set()
                and not (self.controller and self.controller.muted))

    def request_stop(self):
        self.stop_event.set()

    def run(self, on_event):
        def capture():
            try:
                def recognized(phrase):
                    if self.listening_allowed():
                        self.events.put(("speech", phrase))
                self.input_device.listen(recognized, self.stop_event,
                                         should_listen=self.listening_allowed)
            except Exception as exc:
                self.events.put(("error", str(exc)))
            finally:
                self.events.put(("ended", ""))

        microphone = threading.Thread(target=capture, daemon=True)
        microphone.start()
        try:
            while not self.stop_event.is_set():
                if self.controller and self.controller.exit_requested:
                    break
                try:
                    kind, value = self.events.get(timeout=0.2)
                except queue.Empty:
                    continue
                if kind == "speech":
                    if self.controller and self.controller.muted:
                        continue
                    self.busy_event.set()
                    try:
                        on_event("heard", value)
                        answer = self.assistant.respond(value)
                        on_event("answer", answer)
                        if answer == "Останавливаюсь.":
                            self.stop_event.set()
                    except Exception as exc:
                        on_event("error", "Ошибка обработки команды: " + str(exc))
                        self.stop_event.set()
                    finally:
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
