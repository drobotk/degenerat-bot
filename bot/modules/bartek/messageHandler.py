import discord
import logging
from .textHandler import TextHandler


class MessageHandler:
    def __init__(self, log: logging.Logger, path: str) -> None:
        self.log: logging.Logger = log

        self.textHandler: TextHandler = TextHandler(log, path)

    def isOffending(self, message: discord.Message) -> bool:
        if message.content:
            if self.textHandler.isOffending(message.content):
                self.log.info(f"Offending message: {message.content}")

            if "http" in message.content:
                # todo
                pass

            return False

        if message.attachments:
            # todo
            pass

        return True
