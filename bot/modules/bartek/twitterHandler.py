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

        # bullshit for getting description
        description_text = str(twitter_page.find_all("meta", property="og:description"))

        return self.textHandler.isOffending(description_text)


if __name__ == "__main__":
    links = {
        "https://fxtwitter.com/i/status/1737831908795351359",
        "https://fxtwitter.com/i/status/1737542665028178158",
        "https://fxtwitter.com/i/status/1737531507571376480",
        "https://fxtwitter.com/i/status/1737468694916153618",
    }

    th = TextHandler(logging.getLogger(), "data/polityka/")
    yth = TwitterHandler(logging.getLogger(), th)
    for link in links:
        print(yth.isOffending(link))
