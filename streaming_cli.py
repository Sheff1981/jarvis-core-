"""Streaming terminal dialogue for local JARVIS."""
import argparse
import sys

from jarvis.ollama_dialogue import OllamaError
from jarvis.ollama_stream import stream_project
from jarvis.projects import Projects


def main(argv=None, input_fn=input, output_fn=print, stream_fn=stream_project):
    parser = argparse.ArgumentParser(description="JARVIS streaming chat")
    parser.add_argument("project_id")
    parser.add_argument("--db", default="jarvis.db")
    parser.add_argument("--model", default="qwen2.5:1.5b")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    projects = Projects(args.db)
    try:
        found = any(p["id"] == args.project_id for p in projects.list(include_done=True))
    finally:
        projects.close()
    if not found:
        output_fn("Project not found")
        return 2
    output_fn("JARVIS streaming mode. /exit to quit.")
    while True:
        try:
            question = input_fn("You: ")
        except (EOFError, KeyboardInterrupt):
            output_fn("")
            return 0
        if question.strip().lower() in ("/exit", "/quit"):
            return 0
        if not question.strip():
            continue
        output_fn("JARVIS: ", end="", flush=True)
        try:
            for chunk in stream_fn(args.project_id, question, db_path=args.db,
                                   model=args.model, timeout=args.timeout):
                output_fn(chunk, end="", flush=True)
            output_fn("")
        except OllamaError:
            output_fn("\nLocal Ollama unavailable or response interrupted.")


if __name__ == "__main__":
    sys.exit(main())
