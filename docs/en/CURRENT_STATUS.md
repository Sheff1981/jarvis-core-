# JARVIS CORE — current stopping point
Checked: 2026-10-16. Time not recorded. Status: IN PROGRESS.

## Active stage
Stabilize the existing conversational and voice core; do not add features.

## Verified
- Repository Sheff1981/jarvis-core-, branch feature/dialogue-project-memory.
- Audit HEAD: 88fac0d7d76de5d1351f61bdc82cc46dc6f122f0.
- GitHub Actions run #983: success.
- Assistant, JarvisConversation, LocalLLM, VoiceSession, Vosk/Piper, SQLite stores, corpus/export modules exist.
- Branch was 510 commits ahead of main when checked.

## Incomplete / unverified
- End-to-end voice test on the actual Windows laptop after recent changes.
- The “Привет, Джарвис” path through VoiceSession to Assistant has an integration test and passed CI run #1000 on Windows and Ubuntu; physical laptop verification remains outstanding.
- Unified memory design: ConversationStore, Dialogue, Brain and PrivateSessionJournal overlap.
- GitHub–laptop–server delivery; server deployment is not verified.
- Custom trained voice and LoRA are NOT implemented.

## One next action
Audit wake_word → VoiceSession → Assistant → Ollama → Piper and add/fix integration tests without changing main. Then CI and a real laptop test.

## Backlog, do not switch
- GitHub → laptop/server updates with backups.
- Durable task checkpoints within JARVIS.
- Curated training corpus, then LoRA/QLoRA and custom voice.

## Target architecture (owner decision, 2026-10-16)
JARVIS CORE's long-term objective is its own neural network and native engines for language processing, memory, learning, and dialogue. Qwen/Ollama are temporary prototype components, not the target architecture. Native trained weights and engines have not yet been implemented. The current active task remains unchanged: complete and validate the voice core without breaking existing functions.

## N0 progress checkpoint — 2026-10-16
- Ten sequential utterances: CI #1043, Windows/Ubuntu success.
- Microphone failure: CI #1041, Windows/Ubuntu success.
- TTS exception handling: 6c6403b; next-response Piper failure regression: 2fefe03; CI #1047 Windows/Ubuntu jobs passed.
- Safe update checklist: 7fbc653; CI #1049 Windows/Ubuntu success.
- Bilingual logs updated: edff334, 6a85de0.
- N0 NOT ACCEPTED: physical Windows 10 Vosk/Piper/Ollama test, resource metrics, and acceptance record remain outstanding.
- Single next action: only after the owner says “Выгружаем”, back up and update D:\\JARVIS-test using PowerShell, then complete docs/ru/VOICE_N0_ACCEPTANCE.md.

## N0 addendum — 2026-10-16
- Event queue: CI #1058 passed (microphone error retained), #1060 passed (speech during answer discarded), #1062 passed (busy gate cleared).
- Consecutive dialogue without repeating wake word: CI #1066 passed on Windows and Ubuntu, commit 8bb705d.
- Physical Windows 10 acceptance remains outstanding; N0 is not closed.
- Next: wait for “Выгружаем”, back up, update D:\\JARVIS-test via PowerShell, and run hardware checks.


## Memory Core — 2026-10-16
Added project_checkpoints to the existing Projects SQLite database with checkpoint/latest_checkpoint methods. Commits 471084f and 756631d. CI verification and main dialogue integration are not yet confirmed. The contour is NOT accepted. Next action: verify CI and integrate with Dialogue.


## Memory Core acceptance update — 2026-10-16
Dialogue integration: ccf7cf7; recovery tests: 55a8d74; CI #1331 SUCCESS (before backup changes). SQLite backup: 511eb58; backup/restore test: 4fca822. Final CI for 4fca822 is not yet confirmed. Software contour awaits final acceptance; hardware validation is separate.
