# JARVIS MVP 0.1

Experimental Windows mouse-click recorder with SQLite scenario storage and opt-in replay. **Not a full AI assistant yet.** Windows 10/11 target; Android, voice, and synchronization are planned, not implemented.

## Setup

Python 3.11+ on Windows:

```powershell
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m unittest discover -v
```

## Commands

```powershell
python main.py record "My workflow"
python main.py list
python main.py replay SCENARIO_ID
python main.py replay SCENARIO_ID --execute
```

Recording is explicitly started/stopped by pressing Enter. Only mouse click coordinates and timing are captured, not keystrokes or clipboard contents. Replay is a preview unless `--execute` is supplied. Move the pointer to the top-left corner to trigger PyAutoGUI fail-safe. **Do not replay in payment, banking, security, or destructive interfaces.** Coordinate replay is fragile if windows move.

## Status

One local SQLite roundtrip/dry-run unit test passed in Linux. Real Windows GUI execution remains unverified. No Android client, voice, AI planner, encryption, or cross-device memory exists yet.

## Rights

Proprietary; see [LICENSE](LICENSE). No open-source license is granted. Third-party dependencies retain their own licenses.
