"""Opt-in offline wake listener for JARVIS."""
import argparse
import threading
import queue

from jarvis.voice import VoiceInput
from jarvis.wake import WakeDispatcher


def main(argv=None):
    parser = argparse.ArgumentParser(description="Offline JARVIS wake listener")
    parser.add_argument("--vosk-model", required=True)
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--speak", action="store_true")
    args = parser.parse_args(argv)
    if not 1024 <= args.port <= 65535:
        parser.error("port must be between 1024 and 65535")
    speaker = None
    if args.speak:
        from jarvis.speech import Speaker
        speaker = Speaker(enabled=True, backend="sapi")
    dispatcher = WakeDispatcher(
        url="http://127.0.0.1:%d" % args.port,
        say_fn=speaker.say if speaker else None)
    stop = threading.Event()
    phrases = queue.Queue(maxsize=8)
    def enqueue(text):
        try:
            phrases.put_nowait(text)
        except queue.Full:
            pass
    def dispatch():
        while not stop.is_set():
            try:
                dispatcher.handle(phrases.get(timeout=0.2))
            except queue.Empty:
                continue
            except Exception as exc:
                print('JARVIS: ошибка обработки команды:', exc)
    threading.Thread(target=dispatch, name='jarvis-wake-actions', daemon=True).start()
    print("Слушаю команду: Джарвис, привет. Ctrl+C — остановить.")
    print("Панель запусти отдельно: python dashboard_cli.py")
    try:
        VoiceInput(args.vosk_model).listen(enqueue, stop)
    except KeyboardInterrupt:
        stop.set()


if __name__ == "__main__":
    main()
