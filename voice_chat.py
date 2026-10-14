"""Voice input through shared Assistant and VoiceSession, with optional wake gate."""
import argparse

from jarvis.assistant import Assistant
from jarvis.voice import VoiceInput
from jarvis.voice_session import VoiceSession
from jarvis.wake_word import extract_command


class WakeAssistant:
    def __init__(self, assistant):
        self.assistant = assistant

    def respond(self, phrase):
        activated, command = extract_command(phrase)
        if not activated:
            return None
        return self.assistant.respond(command)


def main():
    parser = argparse.ArgumentParser(description="Offline JARVIS voice assistant")
    parser.add_argument("--model", required=True, help="Extracted Vosk Russian model directory")
    parser.add_argument("--llm-model", default="qwen2.5:3b", help="Local Ollama model name")
    parser.add_argument("--db", default="jarvis.db")
    parser.add_argument("--require-wake-word", action="store_true",
                        help="Ignore speech unless it begins with JARVIS/Chat")
    args = parser.parse_args()

    assistant = Assistant(db_path=args.db, model=args.llm_model)
    router = WakeAssistant(assistant) if args.require_wake_word else assistant

    def show_event(kind, value):
        if kind == "heard":
            print("Вы:", value, flush=True)
        elif kind == "answer" and value is not None:
            print("JARVIS:", value, flush=True)
        elif kind == "error":
            print("JARVIS: Ошибка микрофона:", value, flush=True)
        elif kind == "ended":
            print("JARVIS: Голосовой ввод завершён.", flush=True)

    try:
        print("JARVIS: Слушаю. Для остановки нажми Ctrl+C.", flush=True)
        VoiceSession(router, VoiceInput(args.model)).run(show_event)
    except KeyboardInterrupt:
        pass
    finally:
        assistant.close()
        print("JARVIS: Микрофон выключен.", flush=True)


if __name__ == "__main__":
    main()
