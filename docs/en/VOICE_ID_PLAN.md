# JARVIS Voice ID — offline owner recognition package
Date: 2026-10-16. Status: CONTRACT IMPLEMENTED; FULL INTEGRATION PENDING.

Goal: reject TV audio, other speakers and ambient conversations without cloud services. Vosk is speech-to-text, not speaker verification; EnergyVAD is not identity recognition.

## Delivery scope
1. Local consent-based enrollment with several owner speech samples; choose whether to retain raw recordings.
2. CPU-friendly local speaker embedding model, calibrated verification threshold, false-accept tests.
3. Verify identity **before** queuing a VoiceSession command; unknown voices are ignored silently.
4. Negative tests: TV, background speech, noise, playback/replay of owner's voice. Biometric-only verification cannot guarantee replay protection; sensitive actions need extra confirmation.
5. Preserve existing microphone, Vosk, wake, Ollama and Piper behavior. Default remains unchanged; enabled without enrollment fails closed.
6. Store private voice data locally, never commit it to GitHub; support local profile deletion.
7. Windows/Ubuntu CI, then physical laptop acceptance after owner says “Выгружаем”.

## Implemented
- jarvis/speaker_gate.py: fail-closed SpeakerGate and SpeakerDecision contract.
- tests/test_speaker_gate.py: unit coverage.
**Not implemented yet:** actual enrollment, speaker embedding model, microphone integration, or reliable TV rejection. Do not mark this feature as delivered.

## Integration package 2 (2026-10-16)
VoiceInput now accepts optional speaker_gate, buffers up to 15 seconds of PCM16 per Vosk utterance, and verifies identity **before** forwarding text to VoiceSession. Missing verifier or failures deny the command. Disabled mode preserves current behavior. Tests cover owner acceptance and unknown-speaker rejection. **Important:** no real local speaker embedding model or owner enrollment exists yet; enabled without a verifier blocks every command. Do not enable by default or mark the product complete.
