"""Local Voice ID enrollment and calibration from owner-controlled WAV files.

No recordings are uploaded. ECAPA model must be preinstalled locally.
"""
import argparse
import json
import wave
from pathlib import Path

from jarvis.speaker_ecapa import LocalECAPAExtractor
from jarvis.speaker_profile import SpeakerProfileStore


def read_wav(path):
    with wave.open(str(path), "rb") as file:
        if file.getnchannels() != 1 or file.getframerate() != 16000 or file.getsampwidth() != 2:
            raise ValueError(f"{path}: expected 16 kHz mono 16-bit PCM WAV")
        frames = file.getnframes()
        if frames < 16000 or frames > 16000 * 15:
            raise ValueError(f"{path}: expected 1-15 seconds of audio")
        return file.readframes(frames)


def wav_files(folder):
    directory = Path(folder)
    if not directory.is_dir():
        raise FileNotFoundError(f"audio directory not found: {directory}")
    return sorted(directory.glob("*.wav"))


def evaluate_scores(owner_scores, impostor_scores, target_far=0.01):
    """Choose a threshold minimizing FRR while respecting observed FAR.

    Small datasets cannot establish population-level FAR; return counts so the
    operator can see the limits. Scores are computed from HELD-OUT recordings.
    """
    if not owner_scores or not impostor_scores:
        raise ValueError("both owner and impostor holdout scores required")
    scores = list(owner_scores) + list(impostor_scores)
    if any(not -1 <= x <= 1 for x in scores):
        raise ValueError("invalid cosine score")
    if not 0 <= target_far <= 1:
        raise ValueError("invalid target FAR")
    candidates = sorted(set(scores + [1.000001]))
    valid = []
    for threshold in candidates:
        false_accepts = sum(x >= threshold for x in impostor_scores)
        false_rejects = sum(x < threshold for x in owner_scores)
        far = false_accepts / len(impostor_scores)
        frr = false_rejects / len(owner_scores)
        if far <= target_far:
            valid.append((frr, far, threshold, false_accepts, false_rejects))
    frr, far, threshold, fa, fr = min(valid)
    return {"threshold": threshold, "observed_far": far, "observed_frr": frr,
            "false_accepts": fa, "false_rejects": fr,
            "owner_trials": len(owner_scores), "impostor_trials": len(impostor_scores),
            "target_far": target_far}


def cosine(profile, probe):
    normalized = SpeakerProfileStore._vector(probe)
    if len(normalized) != len(profile):
        raise ValueError("speaker embedding dimension mismatch")
    return sum(a * b for a, b in zip(profile, normalized))


def main():
    parser = argparse.ArgumentParser(description="Offline JARVIS owner voice enrollment")
    parser.add_argument("--model-dir", required=True, help="Local SpeechBrain ECAPA model directory")
    parser.add_argument("--profile", required=True, help="Private profile JSON path outside repository")
    parser.add_argument("--owner", help="Folder of owner enrollment WAV files (>=5)")
    parser.add_argument("--owner-holdout", help="Different owner WAV files for calibration")
    parser.add_argument("--other-holdout", help="Other speakers' WAV files for calibration")
    parser.add_argument("--delete-profile", action="store_true")
    args = parser.parse_args()
    store = SpeakerProfileStore(args.profile)
    if args.delete_profile:
        store.delete()
        print("Local voice profile deleted")
        return
    if not args.owner:
        parser.error("--owner is required unless --delete-profile")
    files = wav_files(args.owner)
    if len(files) < 5:
        parser.error("at least 5 owner enrollment WAV files required")
    extractor = LocalECAPAExtractor(args.model_dir)
    vectors = [extractor(read_wav(path), 16000) for path in files]
    store.enroll(vectors, extractor.model_id)
    print(f"Local owner profile saved: {len(vectors)} enrollment samples")
    if args.owner_holdout and args.other_holdout:
        profile = store.load(extractor.model_id)
        own = [cosine(profile, extractor(read_wav(p), 16000))
               for p in wav_files(args.owner_holdout)]
        other = [cosine(profile, extractor(read_wav(p), 16000))
                 for p in wav_files(args.other_holdout)]
        print(json.dumps(evaluate_scores(own, other), ensure_ascii=False, indent=2))
        print("Threshold is a calibration suggestion, NOT a verified security guarantee.")


if __name__ == "__main__":
    main()
