"""Wake phrase dispatcher; microphone capture is managed separately."""
import random
import re
import threading
import time
import webbrowser

GREETINGS = ("Привет, Александр!", "Привет, Саня!", "Здравствуй, Санёк!",
             "Привет, Шурик!", "Привет, мой друг!", "Рад тебя слышать, Александр!")
WAKE_WORDS = frozenset(("джарвис", "джервис", "жарвис", "jarvis"))


def is_wake_phrase(text):
    if not isinstance(text, str):
        return False
    words = re.findall(r"[а-яёa-z]+", text.casefold())
    return bool(words and words[0] in WAKE_WORDS)


class WakeDispatcher:
    def __init__(self, url="http://127.0.0.1:8765", open_fn=None,
                 say_fn=None, choice_fn=None, clock=None, cooldown=8.0):
        if cooldown < 0:
            raise ValueError("cooldown must not be negative")
        self.url = url
        self.open_fn = open_fn or webbrowser.open
        self.say_fn = say_fn
        self.choice_fn = choice_fn or random.choice
        self.clock = clock or time.monotonic
        self.cooldown = cooldown
        self._last = float("-inf")
        self._lock = threading.Lock()

    def handle(self, text):
        if not is_wake_phrase(text):
            return False
        with self._lock:
            now = self.clock()
            if now - self._last < self.cooldown:
                return False
            self._last = now
        try:
            self.open_fn(self.url)
        except Exception as exc:
            print("JARVIS: не удалось открыть браузер:", exc)
        if self.say_fn is not None:
            try:
                self.say_fn(self.choice_fn(GREETINGS))
            except Exception as exc:
                print("JARVIS: голосовое приветствие недоступно:", exc)
        return True
