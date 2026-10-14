# JARVIS system tray — experimental integration

The optional `--tray` mode now connects the tray controller to the
voice session. It offers:
- Microphone mute: skips incoming audio frames before Vosk transcription.
- Resume: resets the recognizer after blocked audio.
- Exit: requests voice-session shutdown.

Voice responses also gate transcription to reduce self-triggering.
The microphone stream itself remains open while muted; this is **software
muting**, not hardware disconnection. For stronger privacy, future versions
should close and reopen the capture stream on mute/unmute.

The tray runs on the UI thread and the voice session on a worker thread.
Actual Windows GUI and audio tests have **not** been performed.

Known issues to resolve before release:
- Tray must close itself if the voice worker ends or crashes.
- Avoid closing SQLite while an unresponsive worker is still running.
- Verify pystray/Pillow/pyttsx3 behavior and device recovery on Windows.
- Verify wake-phrase false activations and microphone permissions.
- Add a persistent visual microphone state indicator.
- Implement an explicit installer and an autostart entry for the tray variant.

No automatic startup or background recording is enabled by this commit.
