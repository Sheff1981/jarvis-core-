"""Voice input with optional local LLM and the same persistent project memory."""
import argparse
import queue
import threading

from jarvis.assistant import Assistant
from jarvis.voice import VoiceInput


def main():
    parser = argparse.ArgumentParser(description="Offline JARVIS voice assistant")
    parser.add_argument("--model", required=True, help="Extracted Vosk Russian model directory")
    parser.add_argument("--llm-model", default="qwen2.5:3b", help="Local Ollama model name")
    parser.add_argument("--db", default="jarvis.db")
    args = parser.parse_args()

    events = queue.Queue()
    stop = threading.Event()
    assistant = Assistant(db_path=args.db, model=args.llm_model)

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
            answer = assistant.respond(value)
            print("JARVIS:", answer, flush=True)
            if answer == "Останавливаюсь.":
                stop.set()
    except KeyboardInterrupt:
        pass
    finally:
        stop.set()
        microphone.join(timeout=2)
        assistant.close()
        print("JARVIS: Микрофон выключен.", flush=True)


if __name__ == "__main__":
    main()
