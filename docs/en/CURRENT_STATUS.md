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
- Whether the wake phrase “Привет, Джарвис” reaches Assistant correctly through VoiceSession.
- Unified memory design: ConversationStore, Dialogue, Brain and PrivateSessionJournal overlap.
- GitHub–laptop–server delivery; server deployment is not verified.
- Custom trained voice and LoRA are NOT implemented.

## One next action
Audit wake_word → VoiceSession → Assistant → Ollama → Piper and add/fix integration tests without changing main. Then CI and a real laptop test.

## Backlog, do not switch
- GitHub → laptop/server updates with backups.
- Durable task checkpoints within JARVIS.
- Curated training corpus, then LoRA/QLoRA and custom voice.
