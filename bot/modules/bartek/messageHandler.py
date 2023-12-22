import discord
import logging
from .textHandler import TextHandler
from .imageHandler import ImageHandler


class MessageHandler:
    def __init__(self, log: logging.Logger, path: str) -> None:
        self.log: logging.Logger = log

        self.textHandler: TextHandler = TextHandler(log, path)
        self.imageHandler: ImageHandler = ImageHandler(log, self.textHandler)

    async def isOffending(self, message: discord.Message) -> bool:
        if message.content:
            if self.textHandler.isOffending(message.content):
                self.log.info(f"Offending message: {message.content}")
                return True
            if "http" in message.content:
                # todo
                pass

            return False

        if message.attachments:
            for attachment in message.attachments:
                if not attachment.filename.split(".")[-1] in {
                    "jpeg",
                    "png",
                    "bmp",
                    "tiff",
                }:
                    continue

                if await self.imageHandler.isOffending(await attachment.read()):
                    return True

        return False
