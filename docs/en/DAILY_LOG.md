# JARVIS CORE — daily development log

## 2026-10-16 — time not recorded
**Task:** audit current status and establish a single development workflow.
**Verified:** key modules and documents on feature/dialogue-project-memory reviewed; HEAD 88fac0d7d76de5d1351f61bdc82cc46dc6f122f0; GitHub Actions #983 succeeded; branch 510 commits ahead of main.
**Findings:** overlapping memory components, unverified end-to-end voice behavior, unverified laptop–GitHub–server synchronization, no actual LoRA or custom-trained voice.
**Process update:** introduced Russian and English protocol, status and log. Documentation does not prove runtime functionality.
**Stopping point:** before wake-word → VoiceSession → Assistant → Ollama → Piper integration audit.
**Next action:** inspect this path and regression tests; do not add new subsystems.
**Real laptop testing:** not performed in this session.

**2026-10-16 addendum (time not recorded):** preserved “Привет, Джарвис” through VoiceSession (5211767); added regression test (7b2f428). GitHub Actions for latest commit not yet verified; real microphone test not performed. **Next:** confirm CI and run a laptop voice test.

**2026-10-16 — CI verification:** GitHub Actions run #1000 for commit a7a707c: Windows success, Ubuntu 24.04 success. The greeting fix passed automated tests. Microphone, Ollama and Piper have not been tested on the laptop. Next: physical voice test.

**2026-10-16 — N0 checkpoint:** bilingual acceptance protocols added (2adad7f, 66a72e7). GitHub Actions #1015 passed on Windows and Ubuntu 24.04. Physical laptop E2E has not been performed. Next: prepare and test code remotely, then run laptop acceptance after 20:00 when available.

**2026-10-16 — N0 greeting regression:** normalized “Привет, Джарвис” punctuation (f6c5ce6); added punctuation/case regression cases (efc099e). CI #1025 passed Windows and Ubuntu; both jobs of #1027 passed (workflow overall still in_progress when checked). Physical laptop E2E pending. No JARVIS EXE installer; PowerShell-only updates.

**2026-10-16 — N0 stabilization:** Added sleep/mute/stop, SQLite conversation restoration, microphone failure, and ten sequential dialogue tests. CI #1043 passed on Windows/Ubuntu. Broadened TTS exception handling (6c6403b), added Piper-failure next-response regression (2fefe03), CI #1047: both jobs passed. Added safe PowerShell update checklist (7fbc653), CI #1049: success. No physical laptop E2E was performed; N0 is NOT accepted. Next: upon explicit “Выгружаем”, back up and update the test installation, then complete the ten-point acceptance protocol.

**2026-10-16 — N0 / queue and dialogue continuation:** CI #1058 (65af004) passed on Windows/Ubuntu, microphone errors are retained during queue cleanup; CI #1060 (f207035) both jobs passed, speech during reply is discarded; CI #1062 (16392c9) passed, busy gate clears; CI #1066 (8bb705d) passed, a follow-up utterance without another wake word is processed. Physical end-to-end testing has not occurred. Next: after “Выгружаем”, back up, update, and perform N0 laptop acceptance.

**2026-10-16 — N0 / batched VAD stabilization:** Implemented opt-in diagnostic pipeline EnergyVAD → AudioFrameBuffer → SpeechActivityTracker → VADStream. VoiceInput has --vad-diagnostics counters and fail-open handling for detector creation, reset and frame processing failures. Vosk still receives unfiltered PCM. Regression tests cover VAD crashes, streaming and recovery. CI #1122 passed Windows/Ubuntu; latest batch CI needs confirmation. This is **not** neural VAD, barge-in or physical N0 acceptance. Do not update the laptop until the owner says “Выгружаем”.
