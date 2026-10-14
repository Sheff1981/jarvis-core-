"""Run the local text-first JARVIS conversation: python chat.py"""
import argparse
from jarvis.dialogue import Dialogue
from jarvis.local_model import Ollama
from jarvis.assistant import Assistant
from jarvis.local_llm import LocalLLM

def main():
    parser = argparse.ArgumentParser(description='JARVIS local dialogue')
    parser.add_argument('--model', default=None, help='Local Ollama model name (e.g. qwen3:4b)')
    parser.add_argument('--db', default='jarvis.db', help='Local SQLite memory file')
    parser.add_argument('--assistant', action='store_true', help='Use unified assistant with memory, modes and approval-gated tools')
    parser.add_argument('--cpu-only', action='store_true', help='Force Ollama to use CPU with low-memory settings; useful if CUDA fails')
    args = parser.parse_args()
    if args.assistant:
        model_name = args.model or "qwen2.5:3b"
        if args.cpu_only:
            jarvis = Assistant(
                db_path=args.db, model=model_name,
                llm=LocalLLM(model=model_name, timeout=120, cpu_only=True),
            )
        else:
            jarvis = Assistant(db_path=args.db, model=model_name)
    else:
        model = None
        if args.model:
            model = Ollama(model=args.model, timeout=120, cpu_only=True) if args.cpu_only else Ollama(model=args.model)
        jarvis = Dialogue(db_path=args.db, model=model)
    print("JARVIS: Готов. Напиши 'привет', 'добавь проект ...', 'какие проекты' или 'стоп'.")
    try:
        while True:
            try:
                message = input("Вы: ")
            except EOFError:
                break
            answer = jarvis.respond(message)
            print("JARVIS:", answer)
            if answer == "Останавливаюсь.":
                break
    except KeyboardInterrupt:
        print("\nJARVIS: Останавливаюсь.")
    finally:
        jarvis.close()

if __name__ == "__main__":
    main()
