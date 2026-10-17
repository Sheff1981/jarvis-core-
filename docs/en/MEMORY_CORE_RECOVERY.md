# Memory Core — Backup and Recovery

Status: the software procedure is documented; a physical rehearsal on the laptop awaits the owner's “Выгружаем” instruction.

## What is protected

JARVIS's primary SQLite database contains projects, checkpoints, decisions, ideas and conversation history. The private journal remains a separate opt-in store and is not included in project export.

## Backup

1. Stop JARVIS processes that may write to the database.
2. Create a backup at a new destination using Projects.backup(destination). It uses SQLite's backup API and checks PRAGMA integrity_check.
3. Verify that the source database was not modified and that the backup file exists.
4. Do not keep the only backup on the same physical disk as the source.

## Restore without overwriting

1. Never restore over the active database.
2. Use Projects.restore_backup(source, destination) with a new destination path. It rejects a missing source, identical paths and existing destination files; it checks database integrity and the projects table.
3. Open the restored database through Projects(destination) and verify projects, checkpoints and next steps.
4. If the backup includes conversation history, open the same file through ConversationMemory(destination) and inspect several recent entries.
5. Switch the application to the restored file only after data verification and after preserving the current working database separately.

## Limitations

- Automated tests cover backup creation and restore to a new file in Windows and Ubuntu CI.
- A physical rehearsal on the target laptop has not been performed.
- Do not delete the source database or backup before manual verification is complete.
- JSON project export is a selective portable export, not a full backup of conversation history.
