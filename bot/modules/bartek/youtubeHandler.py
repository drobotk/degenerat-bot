import aiohttp
import logging
import re
import json

from .textHandler import TextHandler


class YoutubeHandler:
    def __init__(self, log: logging.Logger, textHandler: TextHandler) -> None:
        self.textHandler: TextHandler = textHandler
        self.log: logging.Logger = log

    async def isOffending(self, url: str) -> bool:
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as resp:
                    yt_page_txt = await resp.text()
        except:
            self.log.error("Bad url - youtube")

        # pattern to hopefully recieve json with wanted data
        re_json: re.Pattern[str] = re.compile(r">var ytInitialData = (\{.+?\});<")
        json_data = json.loads(re_json.search(yt_page_txt).group(1))

        # 💀 and hope they wont change anything
        string_to_check = json_data["contents"]["twoColumnWatchNextResults"]["results"]["results"
        ]["contents"][0]["videoPrimaryInfoRenderer"]["title"]["runs"][0]["text"] # title

        string_to_check += " " + json_data["contents"]["twoColumnWatchNextResults"]["results"
        ]["results"]["contents"][1]["videoSecondaryInfoRenderer"]["attributedDescription"]["content"]  # description

        return self.textHandler.isOffending(string_to_check)
