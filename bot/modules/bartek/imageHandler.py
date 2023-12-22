import logging
import easyocr
from .textHandler import TextHandler
from requests import get

MAX_LENGTH = 30


class ImageHandler:
    def __init__(self, log: logging.Logger, textHandler: TextHandler) -> None:
        self.log: logging.Logger = log
        self.textHandler: TextHandler = textHandler
        self.reader: easyocr.Reader = easyocr.Reader(["pl"])

    async def isOffending(self, image_data: bytes) -> bool:
        image_content = self.reader.readtext(image_data)
        image_content = " ".join(map(lambda x: x[1], image_content))

        if len(image_content.split(" ")) > MAX_LENGTH:
            self.log.info(f"Deleting image. Cause: Word count over {MAX_LENGTH}.")
            self.log.info(f"Detected text:\n{image_content}")
            return True

        if self.textHandler.isOffending(image_content):
            self.log.info("Deleting image. Cause: Containts offending words.")
            self.log.info(f"Detected text:\n{image_content}")
            return True

        return False
