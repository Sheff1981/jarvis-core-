# Planned Windows automatic startup (not yet enabled)

The target behavior is: after Windows user login, start JARVIS in the user's
session, initialize offline speech recognition, and wait for a wake phrase.
Recognized names include 'Джарвис' and 'Чат'. The wake phrase gate is a
text-level prototype; speech detection still depends on the Vosk model.

Before enabling autostart:
- Package and verify the application on Windows.
- Add a visible microphone-on indicator and an immediate mute/stop control.
- Add an opt-in installer option for per-user startup (not a Windows service).
- Add a per-user disable/uninstall path.
- Test login, sleep/wake, missing microphone and offline model failures.
- Avoid collecting or persisting raw microphone audio.

No startup entry, registry key or scheduled task is created by this commit.
