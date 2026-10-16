# JARVIS CORE — mandatory development protocol
Effective: 2026-10-16. Working branch: feature/dialogue-project-memory. Do not change main.

## Single source of progress
Before working, read docs/JARVIS_ROADMAP.md, docs/en/CURRENT_STATUS.md and the latest entry in docs/en/DAILY_LOG.md. Russian mirrors are in docs/ru/. Verified commits, test results and observed runtime behavior override documentation claims.

## One active stage
Work on one task at a time. Queue new ideas without changing scope. Switch only after explicit owner approval. Close a stage only after acceptance criteria, CI and required laptop/server verification.

## At the end of every work session
Update CURRENT_STATUS and DAILY_LOG in both languages. Record date, time and timezone if known, completed changes, commit SHAs, tests and outcomes, blockers, exact stopping point and one next action. Never invent times, tests or achievements. Label unverified items as such. Do not commit secrets or private data.

## Synchronization
GitHub holds source and documentation, not live SQLite memory or secrets. Update laptop/server only after tests with backups and rollback. Do not install into D:\\JARVIS without separate approval.

## Training
Collecting data and dictionaries is not model-weight training. LoRA/QLoRA is a later separate stage requiring approved data, baselines, rented GPU, evaluation and rollback.
