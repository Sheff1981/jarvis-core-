# JARVIS — N0 Voice Core Acceptance Protocol
Prepared: 2026-10-16. Status: AWAITING MANUAL VERIFICATION.

## Sources and gate
JARVIS_CORE_MASTER_ROADMAP_2026-10-16.pdf; JARVIS_CORE_ENGINEERING_SPECIFICATION_2026-10-16.pdf; JARVIS_NATIVE_NEURAL_CORE_TECHNICAL_SPECIFICATION_2_2026-10-16.pdf. N0 requires CI, device E2E, defect log and signed-off acceptance record.

## Verified
Commit a7a707c; GitHub Actions #1000 passed on Windows and Ubuntu 24.04. This does NOT prove microphone, TTS, performance or stability on the target laptop.

## Manual checks (Windows 10, D:\\JARVIS-test)
Record date/time, tested commit, PASS/FAIL, actual behavior and errors. Never publish secrets or private dialogue.

- [ ] 1. Vosk recognizes “Привет, Джарвис” and receives the expected answer.
- [ ] 2. Piper Ruslan speaks clearly without missing words.
- [ ] 3. Ten consecutive voice exchanges complete without hangs.
- [ ] 4. Unrelated speech does not trigger wake.
- [ ] 5. Sleep and stop commands work.
- [ ] 6. Muted microphone does not execute speech commands.
- [ ] 7. Allowed conversational context survives restart.
- [ ] 8. Errors in recognition, model or speech do not cause unrecoverable failure.
- [ ] 9. CPU, RAM and response latency are measured on the laptop.
- [ ] 10. Restart after shutdown works.

## Decision
PASS only when all mandatory checks pass, no critical defects remain, latest CI passes, and the log and acceptance record are completed.
FAIL/BLOCKED: record reproduction, fix commit and retest.

Tested commit: NOT RECORDED
Test date/time: NOT RECORDED
Ten dialogues: NOT VERIFIED
Wake/stop/mute: NOT VERIFIED
Memory after restart: NOT VERIFIED
Recovery: NOT VERIFIED
Decision: N0 NOT ACCEPTED — physical E2E pending.
Next: laptop validation after owner says “Выгружаем”.


## Automated verification freshness — 2026-10-16
- Latest Memory Core functional commit: c801dc4; GitHub Actions #1403 (run 38923733530): Windows and Ubuntu success, full Python test workflow.
- This CI confirms the automated suite for the current code but does not replace physical Vosk/Piper/Ollama end-to-end testing on the laptop.
- Checkpoint/idea/decision/export commands are available in Dialogue. Their integration into the VoiceSession path is not confirmed; do not treat them as voice commands before verifying the route.
