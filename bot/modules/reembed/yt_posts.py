import json
import logging
import re
from io import BytesIO
from typing import Any

import discord
from discord.ext import commands
from PIL import Image, ImageSequence
from yt_dlp.utils import traverse_obj

from ...bot import DegeneratBot
from ... import utils


RE_LINK: re.Pattern[str] = re.compile(
    r"https:\/\/(?:www\.)?youtube\.com\/(?:post\/|channel\/[a-zA-Z0-9_\-]{24}\/community\?lb=)[a-zA-Z0-9_\-]{36}"
)
RE_JSON: re.Pattern[str] = re.compile(r">var ytInitialData = (\{.+?\});<")


class YoutubePostsReEmbed(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = logging.getLogger(__name__)

        self.processed_messages: list[int] = []

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content:
            return

        urls: set[str] = {l.strip() for l in RE_LINK.findall(message.content)}

        for url in urls:
            embeds: list[discord.Embed] = []
            files: list[discord.File] = []

            self.log.info(url)

            await message.channel.typing()

            async with self.bot.session.get(
                url,
                cookies={
                    "SOCS": "CAESNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjMwMzE0LjA2X3AxGgJwbCACGgYIgNvOoAY",
                    "YSC": "LvvlUwB2Uko",
                    "__Secure-YEC": "Cgt1S1A1WjY1VTZDZyick9OgBg%3D%3D",
                    "CONSENT": "PENDING+757",
                },
            ) as r:
                if not r.ok:
                    self.log.error(f"{url} status code {r.status}")
                    continue

                text = await r.text()

            m = RE_JSON.search(text)
            if not m:
                self.log.error(f"{url} didn't match ytInitialData ({r.url=})")
                continue

            try:
                # this is expensive af but regexing json is :moyai:
                data = json.loads(m.group(1)).pop("contents")
            except (json.JSONDecodeError, KeyError) as err:
                self.log.error(f"{url} {err.__class__.__name__}: {err}")
                continue

            post: dict[str, Any] | None = traverse_obj(data, ("twoColumnBrowseResultsRenderer", "tabs", 0, "tabRenderer", "content", "sectionListRenderer", "contents", 0, "itemSectionRenderer", "contents", 0, "backstagePostThreadRenderer", "post", "backstagePostRenderer"))  # type: ignore (no idea how to type correctly)
            if not post:
                self.log.error(f"{url} traverse_obj returned None")
                continue

            embed = discord.Embed(
                color=message.guild.me.color if message.guild else None
            )

            author: str | None = traverse_obj(post, ("authorText", "runs", 0, "text"))  # type: ignore (no idea how to type correctly)
            if author:
                thumbnail: str | None = traverse_obj(post, ("authorThumbnail", "thumbnails", 0, "url"))  # type: ignore (no idea how to type correctly)
                if thumbnail:
                    thumbnail = "https:" + thumbnail

                author_urls: list[str] | None = traverse_obj(post, ("authorEndpoint", (("commandMetadata", "webCommandMetadata", "url"), ("browseEndpoint", "canonicalBaseUrl"))))  # type: ignore (no idea how to type correctly)
                embed.set_author(
                    name=author,
                    icon_url=thumbnail,
                    url=(
                        f"https://www.youtube.com{author_urls[0]}"
                        if author_urls
                        else None
                    ),
                )

            texts: list[str] | None = traverse_obj(post, ("contentText", "runs", ..., "text"))  # type: ignore (no idea how to type correctly)
            embed.description = (
                utils.dots_after("".join(texts), 4096) if texts else None
            )

            images: list[dict[str, Any]] | None = traverse_obj(post, ("backstageAttachment", "backstageImageRenderer", "image", "thumbnails"))  # type: ignore (no idea how to type correctly)
            if images:
                images.sort(key=lambda x: x["width"])
                imgurl = images[-1]["url"]

                async with self.bot.session.get(imgurl) as r:
                    if not r.ok:
                        self.log.error(f"{url} image fetch failed - wtf?")
                    elif r.content_type != "image/webp":
                        embed.set_image(url=imgurl)
                    else:
                        webp = BytesIO(await r.read())
                        gif = BytesIO()
                        with Image.open(webp) as image:
                            frames: list[Image.Image] = []
                            for frame in ImageSequence.Iterator(image):
                                im2 = Image.new("RGB", frame.size, (255, 255, 255))
                                bands = frame.split()
                                mask = bands[3] if len(bands) > 3 else None
                                im2.paste(frame, mask=mask)
                                frames.append(im2.convert("RGB"))

                            frames[0].save(
                                gif,
                                format="gif",
                                save_all=True,
                                append_images=frames[1:],
                                optimize=True,
                                duration=image.info.get("duration", 10),
                                loop=image.info.get("loop", 0),
                                quality=100,
                            )

                        gif.seek(0)
                        fn = f'{post["postId"]}.gif'
                        files.append(discord.File(gif, fn))
                        embed.set_image(url=f"attachment://{fn}")

            poll: dict[str, Any] | None = traverse_obj(post, ("backstageAttachment", "pollRenderer"))  # type: ignore (no idea how to type correctly)
            if poll:
                votes: str | None = traverse_obj(poll, ("totalVotes", "simpleText"))  # type: ignore (no idea how to type correctly)
                choices: list[str] = traverse_obj(poll, ("choices", ..., "text", "runs", 0, "text")) or []  # type: ignore (no idea how to type correctly)
                embed.add_field(
                    name=f"Ankieta: {votes}",
                    value="\n".join([f"🔹 {c}" for c in choices]),
                )

            likes: str | None = traverse_obj(post, ("voteCount", "simpleText"))  # type: ignore (no idea how to type correctly)
            if likes:
                embed.set_footer(text=f"👍 {likes}")

            embeds.append(embed)

            if embeds:
                await message.reply(embeds=embeds, files=files, mention_author=False)
