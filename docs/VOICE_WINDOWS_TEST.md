# Windows: isolated voice smoke test (no permanent installation)

Existing application: `voice_chat.py`, `jarvis/voice.py` (Vosk),
`jarvis/voice_session.py` (activation/mute), `jarvis/speech.py` (SAPI),
`jarvis/assistant.py` (reasoning and approved actions). Do not install as
a service or configure autostart during this test.

## Dependencies

Use a **64-bit** Python and an isolated virtual environment on D:.
The voice requirements include Vosk, sounddevice, pyttsx3 and the optional tray.
Tested Python CI is 3.11; other Python versions require on-device verification.

```powershell
python -m venv D:\JARVIS-test\venv-voice
D:\JARVIS-test\venv-voice\Scripts\python.exe -m pip install -r requirements-voice.txt
D:\JARVIS-test\venv-voice\Scripts\python.exe -c "import vosk, sounddevice, pyttsx3, pystray; print('Audio imports OK')"
```

## Offline Russian recognition model

Download the small Russian Vosk model from its official distribution:
https://alphacephei.com/vosk/models/vosk-model-small-ru-0.22.zip

Extract it to `D:\JARVIS-test\voice\vosk-model-small-ru-0.22`.
The `--model` parameter must be the **extracted directory**, not the ZIP.

Before the first real recording, inspect your microphone permissions and
make sure your Windows default input device is the intended microphone.

## Audio device inspection (without opening microphone)

```powershell
D:\JARVIS-test\venv-voice\Scripts\python.exe -c "import sounddevice as sd; print(sd.query_devices())"
```

## Voice smoke test

From the extracted source directory:

```powershell
D:\JARVIS-test\venv-voice\Scripts\python.exe voice_chat.py --model "D:\JARVIS-test\voice\vosk-model-small-ru-0.22" --llm-model "qwen2.5:3b-instruct-q6_K" --db "D:\JARVIS-test\data\jarvis-test.db" --cpu-only --speak
```

Start with "Джарвис, привет". Follow-up speech does not need the name for
five minutes of inactivity. Say "спи" to return to wake-required mode.
Press Ctrl+C to terminate; voice capture stops. Do **not** pass
`--always-listen` unless you explicitly want to omit the wake gate.

The laptop with NVIDIA MX150 reported incompatible CUDA PTX toolchain;
use `--cpu-only` to prevent Ollama from attempting CUDA. The
8-GB RAM machine may still be slow. Speech synthesis depends on the
Windows SAPI voices installed; Russian voices may need to be enabled in Windows.
