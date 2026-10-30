"""Explicit conversational modes. Chat mode never invokes computer tools."""
import re


CHAT_START = re.compile(r"^(?:джарвис[,! ]+)?(?:давай (?:просто )?(?:поговорим|поболтаем)|поговорим|режим разговора)[.! ]*$", re.I)
WORK_START = re.compile(r"^(?:джарвис[,! ]+)?(?:давай (?:что-нибудь )?(?:создадим|сделаем)|давай поработаем|рабочий режим|перейдём к работе)[.! ]*$", re.I)


class ModeController:
    def __init__(self):
        self.mode = "work"

    def switch(self, phrase):
        if CHAT_START.fullmatch(phrase.strip()):
            self.mode = "chat"
            return "Давай поговорим. Как у тебя сегодня дела?"
        if WORK_START.fullmatch(phrase.strip()):
            self.mode = "work"
            return "Давай. Что хочешь создать или сделать?"
        return None
