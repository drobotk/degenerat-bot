from bs4 import BeautifulSoup
from requests import get
import logging

from textHandler import TextHandler


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

        # print(twitter_page.prettify())

        # print(twitter_page.get_text())
        print(twitter_page_txt)

        return True


if __name__ == "__main__":
    links = {
        "https://fxtwitter.com/i/status/1737831908795351359",
        "https://fxtwitter.com/i/status/1737542665028178158",
    }

    th = TextHandler(logging.getLogger(), "data/polityka/")
    yth = TwitterHandler(logging.getLogger(), th)
    for link in links:
        print(yth.isOffending(link))
