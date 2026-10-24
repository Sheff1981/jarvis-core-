# Persistent local conversation history

JARVIS stores successful general LLM question/answer exchanges in the
`conversation_turns` SQLite table of the configured local database.
The latest eight exchanges are restored into the Ollama backend on restart.

Project commands are handled by the existing project subsystem and are
not added to this LLM history. Failed Ollama requests are not saved.
The `Assistant.clear_conversation()` method deletes saved conversation
turns and clears the model's in-memory history. A user-facing delete
control is still required.

Privacy and release limitations:
- Conversation contents are plaintext in the local SQLite file. Do not
  store passwords or sensitive secrets in chat until encryption and
  privacy controls have been implemented.
- Only the last eight exchanges are supplied as LLM context; this is not
  semantic retrieval, summarization, or training a new model.
- The complete saved history grows without retention limits for now.
- The feature needs real Windows tests, backup/recovery tests and a
  user-facing export/delete workflow before a production release.
