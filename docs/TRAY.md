# Windows tray UI (experimental)

The optional tray module adds a visible icon and two controls:
- Toggle microphone mute state.
- Request application exit.

The pure-Python controller can be unit-tested without a display or audio
hardware. The icon requires optional `pystray` and `Pillow` packages.

**Not yet integrated into the running voice process.** In particular,
changing the controller's mute flag alone does not stop the microphone.
A subsequent integration must connect the flag to the audio capture callback
and the exit request to the voice session stop event. Do not describe this
as a working microphone privacy switch until that integration is tested.

No tray window, microphone, or background process starts on import.
