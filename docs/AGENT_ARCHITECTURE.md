# JARVIS Agent Architecture (incremental integration)

The project remains local-first. No autonomous OS execution is enabled by default.

1. **Intelligence:** `jarvis/local_llm.py` (Ollama). Model suggestions are untrusted; they cannot grant permissions.
2. **Perception:** `jarvis/voice.py` (Vosk). Screen capture and GUI understanding are not yet implemented.
3. **Memory:** `jarvis/conversation_store.py`, `jarvis/facts.py`, `jarvis/projects.py` (SQLite).
4. **Windows actions:** `jarvis/windows_actions.py` currently supports approved read-only directory listing and file metadata. Opening Explorer, apps, or manipulating windows is pending.
5. **Authorization:** `jarvis/permissions.py` single-use exact action approvals; `jarvis/action_dialogue.py` handles user confirmation.
6. **Agent planning:** `jarvis/agent_core.py` accepts bounded explicit plans, pauses before each step and cancels on denial. Not yet wired to the LLM or UI.
7. **Proactivity/personality:** not implemented yet. Future background monitoring must be opt-in and observable.

Security invariants: no model-generated authorization, no silent screen/microphone access, no automatic destructive actions, no UAC bypass, no upload of local private data without explicit approval. Approval of one step never approves the next. Current action audit is in-memory; persistent audit and expiry are pending.

Release gates: CI tests, mock integration tests, and a real Windows 10 laptop test of microphone, tray, UI permissions, Explorer and error recovery before any stable release.
