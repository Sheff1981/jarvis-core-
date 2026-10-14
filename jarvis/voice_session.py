"""Thread-safe voice coordinator with microphone mute and feedback gating."""
import queue
import threading


class VoiceSession:
    def __init__(self, assistant, input_device, controller=None, require_wake=False):
        self.assistant = assistant
        self.active = not require_wake
        self.input_device = input_device
        self.controller = controller
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.busy_event = threading.Event()
        self.capture_finished = threading.Event()

    def listening_allowed(self):
        return (not self.stop_event.is_set() and not self.busy_event.is_set()
                and not (self.controller and self.controller.muted))

    def request_stop(self):
        self.stop_event.set()

    def run(self, on_event):
        def capture():
            try:
                def recognized(phrase):
                    if self.listening_allowed() and isinstance(phrase, str) and phrase.strip():
                        self.events.put(("speech", phrase.strip()))
                self.input_device.listen(recognized, self.stop_event,
                                         should_listen=self.listening_allowed)
            except Exception as exc:
                self.events.put(("error", str(exc)))
            finally:
                self.capture_finished.set()
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
                    if self.capture_finished.is_set():
                        break
                    continue
                if kind == "speech":
                    if not self.listening_allowed():
                        continue
                    words = value.split(maxsplit=1)
                    is_wake = words[0].casefold().rstrip(",!") in ("джарвис", "jarvis")
                    if not self.active and not is_wake:
                        continue
                    if is_wake:
                        self.active = True
                        value = words[1].strip() if len(words) > 1 else ""
                    if value.casefold() in ("спи", "засыпай"):
                        self.active = False
                        self.assistant.action_dialogue.close()
                        on_event("answer", "Перехожу в режим ожидания.")
                        continue
                    if not value:
                        on_event("answer", "Слушаю.")
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
                elif kind == "ended":
                    if self.events.empty():
                        break
                else:
                    on_event(kind, value)
                    break
        finally:
            self.stop_event.set()
            microphone.join(timeout=2)
