"""Thread-safe voice coordinator with microphone mute and feedback gating."""
import queue
import threading
import time

from jarvis.wake_word import extract_command


class VoiceSession:
    def __init__(self, assistant, input_device, controller=None, require_wake=False,
                 idle_seconds=300, clock=None):
        self.assistant = assistant
        if not isinstance(idle_seconds, (int, float)) or idle_seconds <= 0:
            raise ValueError("idle_seconds must be positive")
        self.active = not require_wake
        self.require_wake = require_wake
        self.idle_seconds = idle_seconds
        self.clock = clock if clock is not None else time.monotonic
        self.active_until = 0
        self.input_device = input_device
        self.controller = controller
        self.events = queue.Queue()
        self.stop_event = threading.Event()
        self.busy_event = threading.Event()
        self.capture_finished = threading.Event()
        self.last_timings = None

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
                    activated, command = extract_command(value)
                    now = self.clock()
                    if self.require_wake and self.active and now >= self.active_until:
                        self.active = False
                    if not self.active and not activated:
                        continue
                    if activated:
                        self.active = True
                        # Keep the exact named greeting for Assistant.
                        greeting = " ".join(value.casefold().replace(",", " ").split()).strip(" .!?:;")
                        value = ("привет джарвис" if greeting == "привет джарвис"
                                 else command)
                    if self.require_wake:
                        self.active_until = now + self.idle_seconds
                    if value.casefold() in ("спи", "засыпай") or not value:
                        self.last_timings = None
                        sleeping = bool(value)
                        if sleeping:
                            self.active = False
                        # Control replies use TTS too: block microphone feedback.
                        self.busy_event.set()
                        try:
                            if sleeping:
                                self.assistant.action_dialogue.close()
                            on_event("answer", "Перехожу в режим ожидания." if sleeping
                                     else "Слушаю.")
                        except Exception:
                            # A failed control reply must not leave the session
                            # active with an unreliable microphone state.
                            self.stop_event.set()
                            raise
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
                        continue
                    self.busy_event.set()
                    try:
                        self.last_timings = None
                        on_event("heard", value)
                        llm = getattr(self.assistant, "llm", None)
                        if llm is not None and hasattr(llm, "last_metrics"):
                            llm.last_metrics = None
                        started = time.perf_counter()
                        answer = self.assistant.respond(value)
                        assistant_ms = round((time.perf_counter() - started) * 1000, 1)
                        self.last_timings = {"assistant_ms": assistant_ms,
                                             "llm_used": bool(getattr(llm, "last_metrics", None))}
                        on_event("answer", answer)
                        if answer == "Останавливаюсь.":
                            self.stop_event.set()
                    except Exception as exc:
                        try:
                            on_event("error", "Ошибка обработки команды: " + str(exc))
                        finally:
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
