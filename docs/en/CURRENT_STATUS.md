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


## Documentation reconciliation — 2026-10-16 (Stage 03)
Requirements source: JARVIS CORE ENGINEERING SPECIFICATION, Stage 03 «Memory and project continuity». Earlier entries above are historical snapshots, not the latest status.
- Durable checkpoints and restart recovery: 471084f, 756631d, ccf7cf7, 55a8d74.
- SQLite backup and restore test: 511eb58, 4fca822.
- Decision journal and deferred idea queue: a03f630, 96489e2.
- JSON project export and confirmed deletion: ae13729, b6504d6.
- Legacy schema migration and repeat initialization: b7d2ecf.
- GitHub Actions #1357 (38920294025): success; ubuntu-24.04 success, windows-latest success at b7d2ecf.
- Limitation: idea queue is available via Projects API, but the end-to-end voice interaction for proposing a new idea is not demonstrated. Backup restore was tested by opening the snapshot; a complete disaster recovery procedure and physical device acceptance are not verified.
- Decision: documentation reconciliation COMPLETE; Stage 03 NOT ACCEPTED pending remaining acceptance criteria, device testing where required and owner approval. Voice N0 remains NOT ACCEPTED.
- Native Neural Core has NO trained proprietary model weights; an architecture specification does not establish a trained neural network.
- Do not modify main or update the laptop until the owner says «Выгружаем».


### Memory Core — update after Dialogue integration (2026-10-16)
- Russian dialogue commands for checkpoint creation, decision recording and deferred ideas: 2311b93, bcdd927.
- Dialogue command regression tests: 8c35ef7, df57c9a.
- Explicit SQLite `restore_backup`: cf002f6; portable SQLite path fix: f29be4b; restore regression test: c9fd67c.
- Last confirmed CI #1357 applies to b7d2ecf, not these later changes. CI for the latest changes is pending; Stage 03 remains NOT ACCEPTED until all jobs pass.


### Memory Core — dialogue operations (2026-10-16)
- Dialogue can save a checkpoint with `контрольная точка: stage; task; status; next step; blockers (optional)` (2311b93).
- Deferred ideas and decisions use Russian commands (bcdd927); project export and two-step confirmed deletion are available through Dialogue (3d01a19).
- Regression tests cover checkpoint, idea/decision and export/delete: 8c35ef7, df57c9a, c81fd92.
- CI #1386 for restore portability fix: Windows and Ubuntu success. CI #1393 for dialogue export/delete: Ubuntu success, Windows still running at time of writing.
- Do not close Stage 03 until CI #1393 finishes and the latest final commit is rechecked.


### CI confirmation — 2026-10-16
- GitHub Actions #1403 (run 38923733530) for deletion-safety fix: Ubuntu 24.04 success, Windows success; commit c801dc4.
- Automated Memory Core checks passed on Windows/Ubuntu at the latest functional commit. Laptop hardware testing and manual disaster-recovery procedure remain outstanding; software CI acceptance is confirmed, but full owner acceptance is not claimed.


### Stage 03 and roadmap dependency decision — 2026-10-16
- Stage 03 software criteria are covered: checkpoint persistence/recovery after restart and SQLite transfer; deferred ideas do not change next_step; legacy schema migration is tested; backup/restore targets a new file; export and confirmed deletion are isolated from conversation history.
- CI #1403 for c801dc4: Windows and Ubuntu success. RU/EN recovery runbooks added: c06947d, b67a381.
- Status: Memory Core software implementation and automated checks are complete. Physical laptop restore rehearsal and owner sign-off remain outstanding; do not claim full product sign-off.
- Sequence from the source documents: N0 — physical voice-core acceptance; N1 — server training audit; N2 — unified memory/knowledge base; N3 — Dataset Factory; N4 — JARVIS MicroModel with its own tokenizer. Do not skip to N4.
- Single next action: wait for “Выгружаем”, then perform the safe update and N0 Windows 10 protocol.

## Verification checkpoint — 2026-10-25
- Branch checkpoint for `feature/dialogue-project-memory`: `8c8e2d007a79e5b1594206625e21b239bcc4194d`.
- The inspected documentation commits were limited to `docs/ru/DAILY_LOG.md` (`27646b794b61895d2814ef9e72f251ef582e6a19`) and `docs/en/DAILY_LOG.md` (`8c8e2d007a79e5b1594206625e21b239bcc4194d`). Functional code and tests were not changed by these commits.
- GitHub Actions #1453 (run ID `40067653084`, pull-request run): `test (windows-latest)` and `test (ubuntu-24.04)` succeeded.
- This confirms automated checks for the referenced commit, not physical acceptance. Existing blockers remain: Voice Core N0 hardware acceptance and Windows 10 resource measurements; manual Memory Core backup-restore rehearsal and owner sign-off.
- `main` and the active roadmap stage remain unchanged.
- The next task is unchanged: after the owner says “Выгружаем”, back up the test installation and follow `docs/ru/VOICE_N0_ACCEPTANCE.md`.

## Verification checkpoint — 2026-10-26
- Audited HEAD on `feature/dialogue-project-memory` before this entry: `3ab6d0aa8e229f262b4d9d28501b86f9b64533f5`; comparison with the branch returned `identical`, with no commits after the checkpoint.
- GitHub Actions #1459 (run ID `40166245759`) for this SHA completed successfully: `test (windows-latest)` and `test (ubuntu-24.04)`, including the `Run unit tests` step, succeeded.
- This confirms automated checks for the referenced SHA, not physical acceptance. Blockers remain: Voice Core N0 hardware acceptance and Windows 10 resource measurements; manual Memory Core backup-restore rehearsal and owner sign-off.
- `main` and the roadmap stage were not changed.
- Next task remains: after the owner says “Выгружаем”, back up the test installation and follow `docs/ru/VOICE_N0_ACCEPTANCE.md`.

