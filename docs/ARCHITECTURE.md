# JARVIS architecture

Goal: a single user-facing assistant inspired by the *capabilities* of fictional
AI assistants, without copying protected voices, branding or characters.

## Components
1. **Interface** — text first, microphone speech-to-text, later text-to-speech.
2. **Conversation coordinator** — deterministic command routing initially;
   replaceable local language model later.
3. **Memory** — SQLite project/task history, user-approved preferences and
   evidence-backed summaries.
4. **Skills** — isolated file, browser, Git and development tools, each with
   explicit permissions.
5. **Verifier** — check command results, builds, tests and output artifacts.
6. **Safety controls** — stop command, confirmation gates, audit trail, rollback.

## Design constraints
- Offline-first: no subscription required for basic functionality.
- No autonomous execution of arbitrary language-model-generated shell commands.
- Voice and desktop actions are opt-in; do not capture secrets.
- GitHub main branch remains protected by development process and review.
- The local project tracker and text dialogue are prototypes, not general AI.
- A powerful conversational coding agent remains future work.

## Next acceptance milestone
On a real Windows 10 machine, recognize a spoken Russian phrase with a local
Vosk model, show the transcript, return a text response, and stop cleanly
on 'стоп', Ctrl+C or microphone failure.
