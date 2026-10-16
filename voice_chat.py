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
    parser.add_argument("--model", required=False, help="Extracted Vosk Russian model directory")
    parser.add_argument("--llm-model", default="qwen2.5:3b")
    parser.add_argument("--jarvis-conversation-core", action="store_true",
                        help="Opt in to the new private conversation routing")
    parser.add_argument("--db", default="jarvis.db")
    parser.add_argument("--always-listen", action="store_true",
                        help="Opt in to processing speech without wake-word activation")
    parser.add_argument("--speak", action="store_true")
    parser.add_argument("--voice-preview", action="store_true",
                        help="Speak one test phrase without starting Ollama or microphone")
    parser.add_argument("--tts", choices=("sapi", "piper"), default="sapi",
                        help="Offline speech engine; SAPI stays default")
    parser.add_argument("--piper-bin", default=None,
                        help="Path to the local Piper executable")
    parser.add_argument("--piper-voice", default=None,
                        help="Path to a local Piper .onnx voice model")
    parser.add_argument("--piper-length-scale", type=float, default=1.0,
                        help="Piper phoneme duration: 1.15 speaks more deliberately")
    parser.add_argument("--piper-sentence-silence", type=float, default=0.0,
                        help="Pause between spoken sentences in seconds")
    parser.add_argument("--ollama-keep-alive", type=int, default=0,
                        help="Keep CPU model loaded for 0-300 seconds (default: 0)")
    parser.add_argument("--llm-history-turns", type=int, default=8,
                        help="Conversation turns passed to local LLM (1-8, default: 8)")
    parser.add_argument("--llm-no-think", action="store_true",
                        help="Disable Qwen3 reasoning in Ollama for quicker voice replies")
    parser.add_argument("--cpu-only", action="store_true",
                        help="Run Ollama on CPU with a low-memory profile (no CUDA)")
    parser.add_argument("--vad-diagnostics", action="store_true",
                        help="Opt in to energy VAD activity counters; never filters Vosk audio")
    parser.add_argument("--diagnostics", action="store_true",
                        help="Print voice and Ollama latency measurements")
    parser.add_argument("--tray", action="store_true", help="Show a system tray with mute and exit")
    args = parser.parse_args()
    if not 0 <= args.ollama_keep_alive <= 300:
        parser.error("--ollama-keep-alive must be between 0 and 300 seconds")
    if not 1 <= args.llm_history_turns <= 8:
        parser.error("--llm-history-turns must be between 1 and 8")
    if args.llm_no_think and not args.cpu_only:
        parser.error("--llm-no-think requires --cpu-only")
    if (args.speak or args.voice_preview) and args.tts == "piper" and (
        not args.piper_bin or not args.piper_voice
    ):
        parser.error("--tts piper requires --piper-bin and --piper-voice")
    piper_pacing = {}
    if args.piper_length_scale != 1.0:
        piper_pacing["piper_length_scale"] = args.piper_length_scale
    if args.piper_sentence_silence != 0.0:
        piper_pacing["piper_sentence_silence"] = args.piper_sentence_silence
    if args.voice_preview:
        speaker = Speaker(
            enabled=True, backend=args.tts,
            piper_exe=args.piper_bin, voice_model=args.piper_voice,
            **piper_pacing,
        )
        try:
            phrase = (
                "Привет. Я Джарвис. Проверка мужского голоса. "
                "Давайте продолжим разработку проекта."
            )
            print("JARVIS:", phrase, flush=True)
            speaker.say(phrase)
        finally:
            speaker.close()
        return
    if not args.model:
        parser.error("--model is required outside --voice-preview")

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
                    use_conversation_core=args.jarvis_conversation_core,
                    llm=LocalLLM(model=args.llm_model, timeout=120, cpu_only=True,
                                 keep_alive_seconds=args.ollama_keep_alive,
                                 max_turns=args.llm_history_turns,
                                 think=False if args.llm_no_think else None),
                )
            else:
                assistant = Assistant(db_path=args.db, model=args.llm_model,
                                      use_conversation_core=args.jarvis_conversation_core)
            speaker = Speaker(enabled=args.speak, backend=args.tts,
                              piper_exe=args.piper_bin, voice_model=args.piper_voice,
                              **piper_pacing)
            # One wake gate in VoiceSession. Wrapping WakeAssistant here used to
            # consume the wake phrase twice, dropping the first user command.
            session = VoiceSession(
                assistant, VoiceInput(args.model, vad_diagnostics=args.vad_diagnostics),
                controller=controller,
                require_wake=not args.always_listen,
            )

            def show_event(kind, value):
                if kind == "heard":
                    print("Вы:", value, flush=True)
                elif kind == "answer" and value is not None:
                    print("JARVIS:", value, flush=True)
                    try:
                        tts_started = time.perf_counter()
                        spoken = speaker.say(value)
                        tts_ms = round((time.perf_counter() - tts_started) * 1000, 1) if spoken else None
                        if args.diagnostics:
                            timings = session.last_timings or {}
                            print("JARVIS timing: assistant={}ms tts_total={}ms".format(
                                timings.get("assistant_ms", "n/a"),
                                tts_ms if tts_ms is not None else "disabled"), flush=True)
                            if args.vad_diagnostics:
                                print("JARVIS VAD: active_frames={} total_frames={}".format(
                                    session.input_device.vad_activity_frames,
                                    session.input_device.vad_total_frames), flush=True)
                            # Avoid presenting metrics from a previous local command as current.
                            if timings.get("llm_used"):
                                metrics = getattr(assistant.llm, "last_metrics", None)
                                if metrics:
                                    print("JARVIS Ollama metrics:", metrics, flush=True)
                    except Exception as exc:
                        # A TTS failure must not terminate the microphone worker.
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
