# JARVIS release gate — do not install prematurely

Status: experimental development branch, not a verified release.

Before any user-facing Windows package:
- [ ] All unit tests pass in GitHub Actions on Windows.
- [ ] Manual test on Windows with microphone and Russian Vosk model.
- [ ] Offline Ollama dialogue verified, including missing-model failure.
- [ ] One unified text/voice command path verified.
- [ ] Stop, cancellation and microphone failure tested.
- [ ] SQLite data persists across restarts; backup and restore documented.
- [ ] No secrets or personal audio captured in logs.
- [ ] Build a reproducible distribution and test it on a clean Windows PC.
- [ ] Tag a release with a changelog and rollback instructions.

Do not announce a stable version or instruct installation before verification.
