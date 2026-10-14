# Offline voice input (experimental)

Requires Windows 10/11, a working microphone, Python 3.11+ and an extracted
**Russian Vosk speech recognition model**.

1. Install dependencies: `py -m pip install -r requirements-voice.txt`
2. Download a Russian-language model from the official Vosk models catalogue:
   https://alphacephei.com/vosk/models
3. Extract the model to a local folder such as `models/vosk-ru`.
4. Run: `py voice_chat.py --model models/vosk-ru`
5. Say `привет`, `добавь проект Название`, `какие проекты`, or `стоп`.

This is offline speech-to-text with **text replies only**. It is not a general
language model, does not support free-form planning and does not automatically
control your computer. The microphone is used only while the program runs.
No raw audio is saved or uploaded. Do not use in sensitive conversations.

The real microphone path is not yet verified on Windows. Speech accuracy depends
on the chosen model, hardware and noise. Model files are not committed.
