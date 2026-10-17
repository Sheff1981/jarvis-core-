# Conversation context — development notes

The optional Ollama adapter now includes a **bounded in-memory conversation**.
By default, the previous eight successful user/assistant exchanges are
provided with each new question. This makes follow-up questions meaningful.

## Limits
- The context is **not persistent** across application restarts.
- Only questions routed to the LLM are in this history. Project commands are
  handled separately by the SQLite project tracker.
- This is not model training or fine-tuning.
- Requests still go only to the local Ollama loopback endpoint.
- Long replies may exceed the selected model's context window. Token-based
  trimming and durable, privacy-aware memory are future tasks.
- The LLM cannot execute shell commands or manipulate files.

## Next engineering tasks
1. Prevent microphone feedback while JARVIS speaks.
2. Implement local text-to-speech interruption and mute.
3. Add opt-in durable conversation summaries.
4. Verify Windows CI and test real audio hardware before packaging.
