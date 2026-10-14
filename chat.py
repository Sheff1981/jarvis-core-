"""Run the local text-first JARVIS conversation: python chat.py"""
import argparse
from jarvis.dialogue import Dialogue
from jarvis.local_model import Ollama
from jarvis.assistant import Assistant

def main():
    parser = argparse.ArgumentParser(description='JARVIS local dialogue')
    parser.add_argument('--model', default=None, help='Local Ollama model name (e.g. qwen3:4b)')
    parser.add_argument('--db', default='jarvis.db', help='Local SQLite memory file')
    parser.add_argument('--assistant', action='store_true', help='Use unified assistant with memory, modes and approval-gated tools')
    args = parser.parse_args()
    if args.assistant:
        jarvis = Assistant(db_path=args.db, model=args.model or "qwen2.5:3b")
    else:
        jarvis = Dialogue(db_path=args.db, model=Ollama(model=args.model) if args.model else None)
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
