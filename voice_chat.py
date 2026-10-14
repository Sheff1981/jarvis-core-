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

    controller = TrayController()
    worker_done = threading.Event()

    def voice_worker():
        # SQLite and Windows speech objects must be created and closed on
        # their owning thread, not on the tray's GUI thread.
        assistant = None
        speaker = None
        try:
            assistant = Assistant(db_path=args.db, model=args.llm_model)
            speaker = Speaker(enabled=args.speak)
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

            session.run(show_event)
        except Exception as exc:
            print("JARVIS: Ошибка запуска:", exc, flush=True)
            controller.request_exit()
        finally:
            controller.request_exit()
            try:
                if speaker is not None:
                    speaker.close()
            finally:
                if assistant is not None:
                    assistant.close()
                worker_done.set()
                print("JARVIS: Микрофон выключен.", flush=True)

    print("JARVIS: Голосовой режим запускается.", flush=True)
    if args.tray:
        worker = threading.Thread(target=voice_worker, daemon=False)
        worker.start()
        try:
            run_tray(controller, worker_done=worker_done)
        except KeyboardInterrupt:
            controller.request_exit()
        finally:
            controller.request_exit()
            worker.join(timeout=5)
    else:
        voice_worker()


if __name__ == "__main__":
    main()
