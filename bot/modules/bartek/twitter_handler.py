import aiohttp
import logging
import json
import re

from .text_handler import TextHandler


class TwitterHandler:
    def __init__(self, log: logging.Logger, textHandler: TextHandler) -> None:
        self.log: logging.Logger = log
        self.textHandler: TextHandler = textHandler

    async def isOffending(self, url: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    "https://publish.twitter.com/oembed?url=" + url
                ) as resp:  # returns json embed data
                    twitter_embed_data_json = await resp.text()

        except:
            self.log.error("Bad url - twitter")

        twitter_data = json.loads(twitter_embed_data_json)

        # this wierd url returns a json with some embeded data
        # i hope it will work
        # author name + html from embed (there should be some description)
        string_to_check = twitter_data["author_name"] + " " + twitter_data["html"]

        return self.textHandler.isOffending(string_to_check)
