from bs4 import BeautifulSoup
import aiohttp
import logging

from .textHandler import TextHandler


class TwitterHandler:
    def __init__(self, log: logging.Logger, textHandler: TextHandler) -> None:
        self.log: logging.Logger = log
        self.textHandler: TextHandler = textHandler

    async def isOffending(self, url: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                twitter_page_resp = session.get(url)
                twitter_page_txt = await twitter_page_resp.text()

        except:
            self.log.error("Bad url - twitter")

        twitter_page = BeautifulSoup(twitter_page_txt, "html.parser")

        # bullshit for getting description
        description_text = str(twitter_page.find_all("meta", property="og:description"))

        return self.textHandler.isOffending(description_text)
