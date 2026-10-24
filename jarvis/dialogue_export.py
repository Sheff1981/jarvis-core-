"""Export explicitly approved dialogue examples as JSONL for offline fine-tuning.

No network access, model execution, or weight updates occur here.
"""
import argparse
import json
from pathlib import Path
from jarvis.dialogue_corpus import DialogueCorpus


def export_jsonl(db_path, output_path, *, min_examples=10):
    if type(min_examples) is not int or min_examples < 1:
        raise ValueError("Invalid minimum")
    examples = DialogueCorpus(db_path).export_approved()
    if len(examples) < min_examples:
        raise ValueError("Not enough reviewed examples for export")
    target = Path(output_path)
    if target.exists():
        raise FileExistsError("Refusing to overwrite existing training data")
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8", newline="\n") as stream:
        for example in examples:
            stream.write(json.dumps(example, ensure_ascii=False) + "\n")
    return {"examples": len(examples), "path": str(target), "trained": False}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--db", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument("--min-examples", type=int, default=10)
    args = parser.parse_args()
    print(json.dumps(export_jsonl(args.db, args.out, min_examples=args.min_examples),
                     ensure_ascii=False))


if __name__ == "__main__":
    main()
