import aiohttp
import logging
import json
import re

from .text_handler import TextHandler


class TwitterHandler:
    def __init__(
        self,
        log: logging.Logger,
        textHandler: TextHandler,
        session: aiohttp.ClientSession,
    ) -> None:
        self.log: logging.Logger = log
        self.textHandler: TextHandler = textHandler
        self.session: aiohttp.ClientSession = session

    async def isOffending(self, url: str) -> bool:
        try:
            # returns json embed data with some kind of description
            async with self.session.get(
                "https://publish.twitter.com/oembed?url=" + url
            ) as resp:
                twitter_embed_data_json: str = await resp.text()

        except:
            self.log.error("Bad url - twitter")
            return False

        twitter_data: object = json.loads(twitter_embed_data_json)

        # this wierd url returns a json with some embeded data
        # i hope it will work
        # author name + html from embed (there should be some description)
        string_to_check: str = twitter_data["author_name"] + " " + twitter_data["html"]

        return self.textHandler.isOffending(string_to_check)
