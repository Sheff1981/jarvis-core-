# Local voice output — experimental

JARVIS can speak replies offline via `pyttsx3` and the operating system's
installed speech synthesis voices. Windows SAPI voices are the intended first
backend. A Russian voice must be installed in Windows for good Russian speech.

The speech output is optional, disabled by default, and must be explicitly
enabled by the application. No paid API or internet service is required to
synthesize speech once the Windows voice is available.

Known limitations:
- Voice quality depends on the installed Windows voices.
- Speaking is currently synchronous; future versions need interruptibility
  and protection against microphone feedback.
- No user-specific voice cloning or imitation of fictional character voices.
- Real Windows audio playback is not yet verified.
