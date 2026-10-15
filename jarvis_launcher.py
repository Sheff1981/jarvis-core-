"""Single-command JARVIS launcher; no Windows startup changes."""
import argparse
import threading
import queue
import webbrowser
import time
import urllib.request

from jarvis.dashboard import serve
from jarvis.wake import WakeDispatcher


def open_when_ready(url, stop, timeout=15, opener=None):
    opener = opener or webbrowser.open
    deadline = time.monotonic() + timeout
    while not stop.is_set() and time.monotonic() < deadline:
        try:
            with urllib.request.urlopen(url + '/api/session', timeout=0.5) as response:
                if response.status == 200:
                    opener(url)
                    return True
        except (OSError, ValueError):
            pass
        stop.wait(0.2)
    return False


def run(port=8765, db_path="jarvis.db", vosk_model=None, speak=False,
        open_browser=False, voice_factory=None, speaker_factory=None):
    if not 1024 <= port <= 65535:
        raise ValueError("Invalid port")
    stop = threading.Event()
    listener = None
    if vosk_model:
        from jarvis.voice import VoiceInput
        voice = voice_factory(vosk_model) if voice_factory else VoiceInput(vosk_model)
        say_fn = None
        if speak:
            if speaker_factory:
                speaker = speaker_factory()
            else:
                from jarvis.speech import Speaker
                speaker = Speaker(enabled=True, backend="sapi")
            say_fn = speaker.say
        wake = WakeDispatcher(url="http://127.0.0.1:%d" % port, say_fn=say_fn)
        phrases = queue.Queue(maxsize=8)
        def enqueue(text):
            try:
                phrases.put_nowait(text)
            except queue.Full:
                pass
        def dispatch():
            while not stop.is_set():
                try:
                    phrase = phrases.get(timeout=0.2)
                except queue.Empty:
                    continue
                try:
                    wake.handle(phrase)
                except Exception as exc:
                    print('JARVIS: ошибка обработки команды:', exc)
        threading.Thread(target=dispatch, name='jarvis-wake-actions', daemon=True).start()
        def listen():
            failures = 0
            while not stop.is_set():
                try:
                    voice.listen(enqueue, stop)
                    if stop.is_set():
                        break
                    raise RuntimeError("Слушатель неожиданно завершился")
                except Exception as exc:
                    failures += 1
                    print("JARVIS: ошибка микрофона (попытка %d): %s" % (failures, exc))
                    if stop.wait(min(60, 2 ** min(failures, 6))):
                        break
        listener = threading.Thread(target=listen, name="jarvis-wake", daemon=True)
        listener.start()
    url = "http://127.0.0.1:%d" % port
    print("JARVIS:", url)
    print("Микрофон:", "активен" if vosk_model else "выключен")
    if open_browser:
        threading.Thread(target=open_when_ready, args=(url, stop),
                         name='jarvis-browser', daemon=True).start()
    try:
        serve(port=port, db_path=db_path)
    finally:
        stop.set()
        if listener:
            listener.join(timeout=3)


def main(argv=None):
    parser = argparse.ArgumentParser(description="JARVIS dashboard and wake listener")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--db", default="jarvis.db")
    parser.add_argument("--vosk-model", help="Enable local wake recognition using this model directory")
    parser.add_argument("--speak", action="store_true", help="Speak greetings via Windows SAPI")
    parser.add_argument("--open-browser", action="store_true", help="Open dashboard immediately")
    args = parser.parse_args(argv)
    try:
        run(port=args.port, db_path=args.db, vosk_model=args.vosk_model,
            speak=args.speak, open_browser=args.open_browser)
    except KeyboardInterrupt:
        print("JARVIS остановлен")


if __name__ == "__main__":
    main()
