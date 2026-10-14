"""Local voice-in/text-out JARVIS prototype. Requires Vosk Russian model."""
import argparse
import threading
import queue
from jarvis.dialogue import Dialogue
from jarvis.voice import VoiceInput


def main():
    parser = argparse.ArgumentParser(description="Offline JARVIS microphone chat")
    parser.add_argument("--model", required=True, help="Path to extracted Russian Vosk model directory")
    parser.add_argument("--db", default="jarvis.db")
    args = parser.parse_args()
    stop = threading.Event()
    jarvis = Dialogue(args.db)
    phrases = queue.Queue()

    def on_text(phrase):
        # Audio callback thread must not touch SQLite or run dialogue logic.
        phrases.put(phrase)

    def worker():
        while not stop.is_set():
            try:
                phrase = phrases.get(timeout=0.2)
            except queue.Empty:
                continue
            print("Вы:", phrase, flush=True)
            answer = jarvis.respond(phrase)
            print("JARVIS:", answer, flush=True)
            if answer == "Останавливаюсь.":
                stop.set()

    print("JARVIS: Микрофон включён. Скажи 'стоп' или нажми Ctrl+C.")
    try:
        # Keep SQLite on its owning thread: microphone runs in worker thread.
        microphone = threading.Thread(
            target=VoiceInput(args.model).listen, args=(on_text, stop), daemon=True
        )
        microphone.start()
        worker()
    except KeyboardInterrupt:
        stop.set()
    finally:
        stop.set()
        jarvis.close()
        print("JARVIS: Микрофон выключен.")


if __name__ == "__main__":
    main()
