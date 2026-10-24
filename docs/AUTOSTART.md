# Windows autostart: experimental, opt-in only

The `jarvis.startup` module prepares a per-user Windows Startup-folder
entry and can remove the entry it created. Importing it has no side effects.
There is **no** automatic registration during installation or application launch.

The generated command starts `voice_chat.py` with a local Vosk model,
wake-phrase filtering and offline speech enabled. Ollama must be separately
installed and running for general AI responses.

## Release blockers

- Startup entry creation/removal must be verified on a real Windows system.
- The current `.cmd` approach displays a console window: it is **not** yet a
  hidden tray/background app.
- Microphone access and privacy indicator need a real user-facing toggle.
- No audio playback or hardware behavior has been verified.
- A separate explicit installer UI/CLI must call `install()`; do not register
  automatically.
- Handle sleep/resume and audio device disconnect/reconnect.
- Avoid treating phrase matching on transcribed audio as robust wake-word
  detection; test false activations.

No commands are required from the user until they request deployment.
