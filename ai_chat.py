"""Text JARVIS with deterministic project memory and optional local Ollama."""
import argparse
from jarvis.dialogue import Dialogue
from jarvis.local_llm import LocalLLM


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--db", default="jarvis.db")
    args = parser.parse_args()
    dialogue = Dialogue(args.db)
    llm = LocalLLM(model=args.model)
    print("JARVIS: Готов. Проекты веду локально; остальные вопросы — локальной модели.")
    try:
        while True:
            try:
                phrase = input("Вы: ").strip()
            except EOFError:
                break
            if not phrase:
                continue
            # Deterministic routing handles supported project commands.
            answer = dialogue.respond(phrase)
            if answer.startswith("Пока не умею"):
                try:
                    answer = llm.ask(phrase)
                except RuntimeError as exc:
                    answer = str(exc)
            print("JARVIS:", answer)
            if answer == "Останавливаюсь.":
                break
    except KeyboardInterrupt:
        print("\nJARVIS: Останавливаюсь.")
    finally:
        dialogue.close()


if __name__ == "__main__":
    main()
