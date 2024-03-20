from bs4 import BeautifulSoup
import aiohttp
import logging

from .text_handler import TextHandler


class GenericUrlHandler:
    def __init__(
        self,
        log: logging.Logger,
        textHandler: TextHandler,
        session: aiohttp.ClientSession,
    ) -> None:
        self.textHandler: TextHandler = textHandler
        self.log: logging.Logger = log
        self.session: aiohttp.ClientSession = session

    async def isOffending(self, url: str) -> bool:

        async with self.session.get(url) as resp:
            if not resp.ok:
                self.log.error(f"{url} status code {resp.status}")
                return False
            page_txt: str = await resp.text()

        page_text: str = BeautifulSoup(page_txt, "html.parser").get_text()

        return self.textHandler.isOffending(page_text)
