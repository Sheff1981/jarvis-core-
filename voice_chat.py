"""Offline voice JARVIS with optional visible tray controls."""
import argparse
import threading
import time

from jarvis.assistant import Assistant
from jarvis.local_llm import LocalLLM
from jarvis.speech import Speaker
from jarvis.tray import TrayController, run_tray
from jarvis.voice import VoiceInput
from jarvis.voice_session import VoiceSession
from jarvis.wake_word import extract_command


class WakeAssistant:
    def __init__(self, assistant, idle_seconds=300, clock=None):
        self.assistant = assistant
        self.idle_seconds = idle_seconds
        self.clock = clock if clock is not None else time.monotonic
        self.active_until = 0

    def respond(self, phrase):
        activated, command = extract_command(phrase)
        now = self.clock()
        if activated:
            self.active_until = now + self.idle_seconds
            return self.assistant.respond(command)
        if now >= self.active_until:
            return None
        self.active_until = now + self.idle_seconds
        return self.assistant.respond(phrase)


def main():
    parser = argparse.ArgumentParser(description="Offline JARVIS voice assistant")
    parser.add_argument("--model", required=True, help="Extracted Vosk Russian model directory")
    parser.add_argument("--llm-model", default="qwen2.5:3b")
    parser.add_argument("--db", default="jarvis.db")
    parser.add_argument("--always-listen", action="store_true",
                        help="Opt in to processing speech without wake-word activation")
    parser.add_argument("--speak", action="store_true")
    parser.add_argument("--tts", choices=("sapi", "piper"), default="sapi",
                        help="Offline speech engine; SAPI stays default")
    parser.add_argument("--piper-bin", default=None,
                        help="Path to the local Piper executable")
    parser.add_argument("--piper-voice", default=None,
                        help="Path to a local Piper .onnx voice model")
    parser.add_argument("--cpu-only", action="store_true",
                        help="Run Ollama on CPU with a low-memory profile (no CUDA)")
    parser.add_argument("--tray", action="store_true", help="Show a system tray with mute and exit")
    args = parser.parse_args()
    if args.speak and args.tts == "piper" and (
        not args.piper_bin or not args.piper_voice
    ):
        parser.error("--tts piper requires --piper-bin and --piper-voice")

    controller = TrayController()
    worker_done = threading.Event()

    def voice_worker():
        # SQLite and Windows speech objects must be created and closed on
        # their owning thread, not on the tray's GUI thread.
        assistant = None
        speaker = None
        try:
            if args.cpu_only:
                assistant = Assistant(
                    db_path=args.db, model=args.llm_model,
                    llm=LocalLLM(model=args.llm_model, timeout=120, cpu_only=True),
                )
            else:
                assistant = Assistant(db_path=args.db, model=args.llm_model)
            speaker = Speaker(enabled=args.speak, backend=args.tts,
                              piper_exe=args.piper_bin, voice_model=args.piper_voice)
            # One wake gate in VoiceSession. Wrapping WakeAssistant here used to
            # consume the wake phrase twice, dropping the first user command.
            session = VoiceSession(
                assistant, VoiceInput(args.model), controller=controller,
                require_wake=not args.always_listen,
            )

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
