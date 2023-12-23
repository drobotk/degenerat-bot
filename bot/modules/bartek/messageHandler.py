import discord
import logging
from validators import url
from .textHandler import TextHandler
from .imageHandler import ImageHandler
from .youtubeHandler import YoutubeHandler
from .twitterHandler import TwitterHandler


class MessageHandler:
    def __init__(self, log: logging.Logger, path: str) -> None:
        self.log: logging.Logger = log

        self.textHandler: TextHandler = TextHandler(log, path)
        self.imageHandler: ImageHandler = ImageHandler(log, self.textHandler)
        self.ytHandler: YoutubeHandler = YoutubeHandler(log, self.textHandler)
        self.twitterHandler: TwitterHandler = TwitterHandler()

    async def isOffending(self, message: discord.Message) -> bool:
        if message.content:
            if self.textHandler.isOffending(message.content):
                self.log.info(f"Offending message: {message.content}")

            # array of all words, including possible url
            words_of_message = message.content.split()
            for word in words_of_message:
                # check if url is valid
                if not url(word):
                    continue

                # maybe it's youtube
                if "youtu" in word:
                    if self.ytHandler.isOffending(word):
                        return True

                # maybe it's twitter/x
                elif "twitter" in word:
                    if self.twitterHandler.isOffending(word):
                        return True

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
