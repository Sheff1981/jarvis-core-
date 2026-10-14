"""Run the local text-first JARVIS conversation: python chat.py"""
from jarvis.dialogue import Dialogue

def main():
    jarvis = Dialogue()
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
