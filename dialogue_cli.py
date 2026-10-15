"""Interactive project dialogue CLI for local Ollama."""
import argparse
import sys

from jarvis.ollama_dialogue import OllamaError, ask_project
from jarvis.projects import Projects


def main(argv=None, input_fn=input, output_fn=print, ask_fn=ask_project):
    parser = argparse.ArgumentParser(description="JARVIS local project chat")
    parser.add_argument("project_id", help="Existing project UUID")
    parser.add_argument("--db", default="jarvis.db")
    parser.add_argument("--model", default="qwen2.5:1.5b")
    parser.add_argument("--timeout", type=float, default=120)
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    projects = Projects(args.db)
    try:
        project = next((p for p in projects.list(include_done=True)
                        if p["id"] == args.project_id), None)
    finally:
        projects.close()
    if project is None:
        output_fn("Project not found. Run: python projects_cli.py list --all")
        return 2
    output_fn("JARVIS: " + project["name"])
    output_fn("Type /exit to leave. Dialogue is saved locally.")
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
        try:
            answer = ask_fn(args.project_id, question, db_path=args.db,
                            model=args.model, timeout=args.timeout)
        except (OllamaError, OSError) as exc:
            output_fn("JARVIS: Local model unavailable. Check Ollama and retry.")
            continue
        output_fn("JARVIS: " + answer)


if __name__ == "__main__":
    sys.exit(main())
