"""Offline voice JARVIS with optional visible tray controls."""
import argparse
import threading

from jarvis.assistant import Assistant
from jarvis.speech import Speaker
from jarvis.tray import TrayController, run_tray
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
    parser.add_argument("--llm-model", default="qwen2.5:3b")
    parser.add_argument("--db", default="jarvis.db")
    parser.add_argument("--require-wake-word", action="store_true")
    parser.add_argument("--speak", action="store_true")
    parser.add_argument("--tray", action="store_true", help="Show a system tray with mute and exit")
    args = parser.parse_args()

    assistant = Assistant(db_path=args.db, model=args.llm_model)
    speaker = Speaker(enabled=args.speak)
    controller = TrayController()
    router = WakeAssistant(assistant) if args.require_wake_word else assistant
    session = VoiceSession(router, VoiceInput(args.model), controller=controller)

    def show_event(kind, value):
        if kind == "heard":
            print("Вы:", value, flush=True)
        elif kind == "answer" and value is not None:
            print("JARVIS:", value, flush=True)
            try:
                speaker.say(value)
            except RuntimeError as exc:
                print("JARVIS: Ошибка голоса:", exc, flush=True)
        elif kind == "error":
            print("JARVIS: Ошибка микрофона:", value, flush=True)
            controller.request_exit()
        elif kind == "ended":
            print("JARVIS: Голосовой ввод завершён.", flush=True)
            controller.request_exit()

    worker = None
    try:
        print("JARVIS: Слушаю. Для остановки нажми Ctrl+C.", flush=True)
        if args.tray:
            # Tray UI runs on the main thread; audio and SQLite stay on worker.
            worker = threading.Thread(target=session.run, args=(show_event,), daemon=True)
            worker.start()
            try:
                run_tray(controller)
            finally:
                session.request_stop()
                worker.join(timeout=3)
        else:
            session.run(show_event)
    except KeyboardInterrupt:
        session.request_stop()
    finally:
        session.request_stop()
        if worker is not None and worker.is_alive():
            worker.join(timeout=3)
        speaker.close()
        assistant.close()
        print("JARVIS: Микрофон выключен.", flush=True)


if __name__ == "__main__":
    main()
