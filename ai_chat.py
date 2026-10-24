"""Text JARVIS: same assistant core as microphone mode."""
import argparse
from jarvis.assistant import Assistant


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--model", default="qwen2.5:3b")
    parser.add_argument("--db", default="jarvis.db")
    args = parser.parse_args()
    assistant = Assistant(db_path=args.db, model=args.model)
    print("JARVIS: Готов. Проекты сохраняю локально, вопросы передаю локальной модели.")
    try:
        while True:
            try:
                phrase = input("Вы: ").strip()
            except EOFError:
                break
            if not phrase:
                continue
            answer = assistant.respond(phrase)
            print("JARVIS:", answer)
            if answer == "Останавливаюсь.":
                break
    except KeyboardInterrupt:
        print("\nJARVIS: Останавливаюсь.")
    finally:
        assistant.close()


if __name__ == "__main__":
    main()
