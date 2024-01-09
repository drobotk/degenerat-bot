from bs4 import BeautifulSoup
from requests import get
import logging

from .text_handler import TextHandler


class TwitterHandler:
    def __init__(self, log: logging.Logger, textHandler: TextHandler) -> None:
        self.log: logging.Logger = log
        self.textHandler: TextHandler = textHandler

    def isOffending(self, url: str) -> bool:
        try:
            twitter_page_txt = get(url).text
        except:
            self.log.error("Bad url - twitter")

        twitter_page = BeautifulSoup(twitter_page_txt, "html.parser")

        # bullshit for getting description
        description_text = str(twitter_page.find_all("meta", property="og:description"))

        return self.textHandler.isOffending(description_text)
