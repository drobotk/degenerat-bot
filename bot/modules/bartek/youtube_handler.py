import aiohttp
import logging
import re
import json
from typing import Any

from .text_handler import TextHandler
from yt_dlp.utils import traverse_obj


class YoutubeHandler:
    def __init__(
        self,
        log: logging.Logger,
        textHandler: TextHandler,
        session: aiohttp.ClientSession,
    ) -> None:
        self.textHandler: TextHandler = textHandler
        self.log: logging.Logger = log
        self.session: aiohttp.ClientSession = session

        # pattern to hopefully recieve json with wanted data
        self.re_json: re.Pattern[str] = re.compile(r">var ytInitialData = (\{.+?\});<")

    async def isOffending(self, url: str) -> bool:

        async with self.session.get(url) as resp:
            if not resp.ok:
                self.log.error(f"{url} status code {resp.status}")
                return False

            yt_page_txt: str = await resp.text()

        m: object = self.re_json.search(yt_page_txt)

        if not m:
            self.log.error(f"{url} didn't match ytInitialData ({resp.url=})")
            return False
        
        try:
            # this is expensive af but regexing json is :moyai:
            json_data = json.loads(m.group(1))
        except (json.JSONDecodeError, KeyError) as err:
            self.log.error(f"{url} {err.__class__.__name__}: {err}")
            return False

        # 💀 and hope they wont change anything
        post: dict[str, Any] | None = traverse_obj(
            json_data,
            (
                "contents",
                "twoColumnWatchNextResults",
                "results",
                "results",
                "contents",
            ),
        )
        if not post:
            self.log.error("YoutubeHandler: Bad json data format!")
            return False

        string_to_check: str = ""

        title: str | None = traverse_obj(
            post,
            (
                0,
                "videoPrimaryInfoRenderer",
                "title",
                "runs",
                0,
                "text",
            ),
        )
        if title:
            string_to_check += title + " "
        else:
            self.log.debug(f"{url} - no title found")

        description: str | None = traverse_obj(
            post, (1, "videoSecondaryInfoRenderer", "attributedDescription", "content")
        )
        if description:
            string_to_check += description + " "
        else:
            self.log.debug(f"{url} - no decription found")

        return self.textHandler.isOffending(string_to_check)
