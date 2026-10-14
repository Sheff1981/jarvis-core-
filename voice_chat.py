"""Local voice-in/text-out JARVIS. Speech and errors pass through a thread-safe queue."""
import argparse
import queue
import threading

from jarvis.dialogue import Dialogue
from jarvis.voice import VoiceInput


def main():
    parser = argparse.ArgumentParser(description="Offline JARVIS microphone chat")
    parser.add_argument("--model", required=True, help="Extracted Russian Vosk model directory")
    parser.add_argument("--db", default="jarvis.db")
    args = parser.parse_args()
    events = queue.Queue()
    stop = threading.Event()
    jarvis = Dialogue(args.db)

    def capture():
        try:
            VoiceInput(args.model).listen(lambda phrase: events.put(("speech", phrase)), stop)
        except Exception as exc:
            events.put(("error", str(exc)))
        finally:
            events.put(("ended", ""))

    microphone = threading.Thread(target=capture, daemon=True)
    try:
        microphone.start()
        print("JARVIS: Слушаю. Скажи 'стоп' или нажми Ctrl+C.", flush=True)
        while not stop.is_set():
            try:
                kind, value = events.get(timeout=0.2)
            except queue.Empty:
                continue
            if kind == "error":
                print(f"JARVIS: Ошибка микрофона: {value}", flush=True)
                break
            if kind == "ended":
                print("JARVIS: Голосовой ввод завершён.", flush=True)
                break
            print("Вы:", value, flush=True)
            answer = jarvis.respond(value)
            print("JARVIS:", answer, flush=True)
            if answer == "Останавливаюсь.":
                stop.set()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        microphone.join(timeout=2)
        jarvis.close()
        print("JARVIS: Микрофон выключен.", flush=True)


if __name__ == "__main__":
    main()
