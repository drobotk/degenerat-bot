from bs4 import BeautifulSoup
from requests import get
import logging

from .textHandler import TextHandler


class YoutubeHandler:
    def __init__(self, log: logging.Logger, textHandler: TextHandler) -> None:
        self.textHandler: TextHandler = textHandler
        self.log: logging.Logger = log

    def isOffending(self, url: str) -> bool:
        try:
            yt_page_txt = get(url)
        except:
            self.log.error("Bad url - youtube")

        yt_page = BeautifulSoup(yt_page_txt.text, "html.parser")

        description_script = str(yt_page.find_all("script")[-5])
        description_index = (
            description_script.find("attributedDescriptionBodyText") + 43
        )

        current_index = description_index
        description_text = ""
        while True:
            if (
                description_script[current_index] == '"'
                and description_script[current_index - 1] != "\\"
            ):
                break
            description_text += description_script[current_index]
            current_index += 1

        string_to_check = yt_page.title.string + description_text

        return self.textHandler.isOffending(string_to_check)


# TODO usunac
if __name__ == "__main__":
    links = {
        "https://www.youtube.com/watch?v=yMKAFwUfe3A",
        "https://youtu.be/X-BE-Gq-D6U?si=13CjD_EeDp7wjprs",
    }

    th = TextHandler(logging.getLogger(), "data/polityka/")
    yth = YoutubeHandler(logging.getLogger(), th)
    for link in links:
        print(yth.isOffending(link))
