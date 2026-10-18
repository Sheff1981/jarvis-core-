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


## 2026-10-16 — Memory Core
Added durable project checkpoints to existing SQLite (471084f) and regression tests (756631d). CI and target-environment recovery have not been confirmed. Schema extension is non-destructive; private journal unchanged. Next action: verify CI and Dialogue integration.


## 2026-10-16 — Memory Core continuation
Integrated Dialogue (ccf7cf7), restart tests (55a8d74), CI #1331 success. Added SQLite backup (511eb58), shared-database restore test (4fca822). Final CI unconfirmed. Main branch and laptop unchanged.


## 2026-10-16 — Memory Core, decision log and idea queue
Added project_decisions and project_ideas to existing SQLite (a03f630), restart, project-isolation and active-task preservation tests (96489e2). CI for new commits awaits confirmation. Next: export/deletion and final acceptance.


## 2026-10-16 — Stage 03: export and deletion
Implemented JSON project export and explicitly confirmed transactional deletion (ae13729); isolation and shared-history regression test (b6504d6). Latest CI not yet confirmed. Durable checkpoint acceptance gate awaits final CI and migration recovery verification.


## 2026-10-16 — Stage 03 documentation reconciliation
CI #1357: Windows and Ubuntu success (b7d2ecf). CURRENT_STATUS RU/EN reconciled with evidence, limitations and acceptance state. Documentation is reconciled; Stage 03 remains open pending voice idea-queue integration, disaster recovery validation and owner acceptance. No native trained weights claimed.


## 2026-10-16 — Dialogue access to deferred ideas
Dialogue supports Russian commands to defer/list ideas and record decisions without modifying the active next step (bcdd927). Restart and missing-project regression tests added (df57c9a). Latest CI and physical voice testing remain unverified.


## 2026-10-16 — Save checkpoints through Dialogue
Added explicit `контрольная точка: stage; task; status; next step; blockers (optional)` command with status validation and SQLite persistence (2311b93). Added restart-persistence and invalid-input tests (8c35ef7). CI for this commit awaits confirmation.


## 2026-10-16 — Explicit backup restore
Added `Projects.restore_backup(source, destination)`: validates SQLite integrity and the projects table, restores only to a new path, refuses overwrite, and cleans partial output on failure (cf002f6). Added restore/validation regression test (c9fd67c). CI awaits confirmation.


## 2026-10-16 — Dialogue project export and deletion
Added Russian commands for exact-name project export and deletion gated by a separate confirmation; mismatched confirmation cancels deletion (3d01a19). Tests cover JSON export, mismatch protection and conversation-history preservation (c81fd92). CI run #1393 is in progress.


## 2026-10-16 — Deletion confirmation safety
Review found pending deletion could survive an unrelated utterance. Fixed: cancel, stop and any unrelated input clear the pending deletion; added regression test (0bb6f90, c801dc4). CI for this fix is pending.


## CI result — Memory Core, 2026-10-16
GitHub Actions #1403 passed: Windows and Ubuntu success for c801dc4. Automated regression coverage for export/deletion and cancellation of pending deletion is green. Hardware acceptance and manual restore procedure remain outstanding.


## 2026-10-16 — Memory Core recovery runbook
Added bilingual backup and restore instructions: docs/ru/MEMORY_CORE_RECOVERY.md and docs/en/MEMORY_CORE_RECOVERY.md. The runbook covers integrity checks, overwrite protection and automated-test limits; physical rehearsal remains deferred until “Выгружаем”.


## Roadmap reconciliation — 2026-10-16
Memory Core software passed CI #1403 on Windows/Ubuntu; persistence, deferred ideas, migration, export and recovery are covered by tests, and bilingual recovery runbooks are in place. Full acceptance is not claimed without physical rehearsal/owner sign-off. NNC spec order: N0 voice-core hardware acceptance; N1/N2/N3 precede first MicroModel N4. Single next action: wait for “Выгружаем” and run N0.


## 2026-10-17 — HEAD and GitHub Actions reconciliation
**Branch checked:** `feature/dialogue-project-memory`. **Audited HEAD:** `1cf6a798075bfd668cfaebf771dcff061d66228b` (commit dated 2026-10-16 15:27:32 UTC). Comparing it with functional checkpoint `c801dc47bef1bdc2bb13e1ac3b5c9e69df321b25` shows 16 subsequent documentation-only commits; no functional code changed after that checkpoint.
**Verified checks:** GitHub Actions #1403 for `c801dc4` succeeded on `windows-latest` and `ubuntu-24.04`; #1428 (push) and #1429 (pull request) for HEAD `1cf6a79` succeeded on both platforms. The latest two runs validate the current documentation revision; the functional checkpoint is covered by #1403.
**Confirmed state:** Memory Core / Stage 03 software criteria are documented as complete to the extent covered by automated tests; RU/EN recovery runbooks are present. Neural Core was not reopened. `main` was not changed.
**Blockers:** Physical Voice Core N0 acceptance on Windows 10, resource measurements and acceptance record remain outstanding; a manual Memory Core backup-recovery rehearsal and owner sign-off are also outstanding. Passing CI does not replace these checks.
**Next task (do not change stage):** wait for the owner's “Выгружаем” command, then back up the test installation and follow `docs/ru/VOICE_N0_ACCEPTANCE.md`. Do not update the laptop before authorization.


## 2026-10-18 — daily audit: no changes detected
Compared `feature/dialogue-project-memory` with the previously verified HEAD `42add2765d6c286ba188dd83761fdb276b3b4c49`; comparison returned `identical`. No new commits or file changes were found. GitHub Actions #1433 for the current HEAD completed successfully. No new test results for the past day were detected. Blockers unchanged: physical Voice Core N0 acceptance on Windows 10 and the manual Memory Core backup-restore rehearsal remain outstanding. Next task, without changing stages: after the owner says “Выгружаем”, back up the test installation and follow `docs/ru/VOICE_N0_ACCEPTANCE.md`. CURRENT_STATUS was not changed.
