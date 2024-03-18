from bs4 import BeautifulSoup
import aiohttp
import logging

from .text_handler import TextHandler


class GenericUrlHandler:
    def __init__(self, log: logging.Logger, textHandler: TextHandler) -> None:
        self.textHandler: TextHandler = textHandler
        self.log: logging.Logger = log

    async def isOffending(self, url: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    page_txt = resp.text()
        except:
            self.log.error("Bad url - generic")

        page = BeautifulSoup(page_txt, "html.parser")

        return self.textHandler.isOffending(page.get_text())
