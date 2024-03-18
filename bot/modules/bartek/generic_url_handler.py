from bs4 import BeautifulSoup
from requests import get
import logging

from .text_handler import TextHandler


class GenericUrlHandler:
    def __init__(self, log: logging.Logger, textHandler: TextHandler) -> None:
        self.textHandler: TextHandler = textHandler
        self.log: logging.Logger = log

    def isOffending(self, url: str) -> bool:
        try:
            page_txt = get(url).text
        except:
            self.log.error("Bad url - generic")

        page = BeautifulSoup(page_txt, "html.parser")

        return self.textHandler.isOffending(page.get_text())
