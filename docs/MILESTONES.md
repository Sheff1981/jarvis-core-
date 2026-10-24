# JARVIS engineering milestones

## Implemented in source
- SQLite project tracker with CLI
- Deterministic Russian text dialogue with project listing and registration
- Minimal click recorder and preview-first replay (Windows)
- Basic copy/paste command parsing with explicit approval

## Not yet implemented
- Microphone input and offline speech recognition
- Text-to-speech output
- General language model and contextual understanding
- Secure screen awareness, semantic automation and agentic coding
- Android companion and cross-device synchronization

## Verification
Run `python -m unittest discover -v` in a checkout.
GitHub Actions provides Windows unit-test execution. A passing CI run and real
Windows desktop trials are required before marking any feature verified.
No paid APIs or server are needed for the text dialogue.
