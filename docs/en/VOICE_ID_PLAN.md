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

## Package 3 — local profile (2026-10-16)
Added jarvis/speaker_profile.py and tests/test_speaker_profile.py. The profile requires at least three vectors **provided by an external embedding extractor**, normalizes and averages them, then atomically saves JSON with model_id. Loading, incompatible model detection, deletion and cosine comparison are implemented. Threshold 0.78 is provisional and needs calibration against real positive and negative samples. Raw audio is not persisted here. **There is no real speaker embedding extractor, audio enrollment or TV rejection yet**; synthetic test vectors are not biometric verification. Treat profile data as sensitive and keep it out of GitHub.

## Package 4 — real local ECAPA integration (2026-10-16)
Added jarvis/speaker_ecapa.py (CPU SpeechBrain ECAPA with local model files only), jarvis_voice_enroll.py (16kHz mono PCM16 WAV validation, >=5 owner samples, observed FAR/FRR on **separate** held-out audio), opt-in --voice-id-model-dir/--voice-id-profile/--voice-id-threshold flags in voice_chat.py, and tests. No runtime cloud model download is intended. Model files and optional dependencies must be prepared on the laptop; installation commands are held until “Выгружаем”.
Limitations: speaker verification runs **after Vosk AcceptWaveform** but before VoiceSession. VAD remains diagnostic. Calibration does not guarantee rejection of TV audio, replay or synthesized voices; small observed error rates are not population-level guarantees. Threshold is not applied automatically. Missing model/profile never falls back to accepting unknown voices. Physical testing remains outstanding.
