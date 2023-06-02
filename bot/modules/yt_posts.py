from io import BytesIO
import json
import logging
import re
from typing import Any, Optional
from PIL import Image, ImageSequence

import discord
from discord.ext import commands

from ..bot import DegeneratBot
from ..utils import dots_after
from yt_dlp.utils import traverse_obj


class YTPosts(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = logging.getLogger(__name__)

        self.re_link: re.Pattern[str] = re.compile(
            r"https:\/\/www\.youtube\.com\/(?:post\/|channel\/[a-zA-Z0-9_\-]{24}\/community\?lb=)[a-zA-Z0-9_\-]{36}"
        )
        self.re_json: re.Pattern[str] = re.compile(r">var ytInitialData = (\{.+?\});<")

        self.processed_messages: list[int] = []

    async def process_message(self, message: discord.Message):
        new_embeds: list[discord.Embed] = []
        files: list[discord.File] = []
        for e in message.embeds:
            if not e.url:
                continue

            if not self.re_link.fullmatch(e.url):
                continue

            self.log.info(e.url)

            async with self.bot.session.get(
                e.url,
                cookies={
                    "SOCS": "CAESNQgDEitib3FfaWRlbnRpdHlmcm9udGVuZHVpc2VydmVyXzIwMjMwMzE0LjA2X3AxGgJwbCACGgYIgNvOoAY",
                    "YSC": "LvvlUwB2Uko",
                    "__Secure-YEC": "Cgt1S1A1WjY1VTZDZyick9OgBg%3D%3D",
                    "CONSENT": "PENDING+757",
                },
            ) as r:
                if not r.ok:
                    self.log.error(f"{e.url} status code {r.status}")
                    continue

                text = await r.text()

            m = self.re_json.search(text)
            if not m:
                self.log.error(f"{e.url} didn't match ytInitialData ({r.url=})")
                continue

            try:
                # this is expensive af but regexing json is :moyai:
                data = json.loads(m.group(1)).pop("contents")
            except (json.JSONDecodeError, KeyError) as e:
                self.log.error(f"{e.url} {e.__class__.__name__}: {e}")
                continue

            post: Optional[dict[str, Any]] = traverse_obj(data, ("twoColumnBrowseResultsRenderer", "tabs", 0, "tabRenderer", "content", "sectionListRenderer", "contents", 0, "itemSectionRenderer", "contents", 0, "backstagePostThreadRenderer", "post", "backstagePostRenderer"))  # type: ignore (no idea how to type correctly)
            if not post:
                self.log.error(f"{e.url} traverse_obj returned None")
                continue

            embed = discord.Embed(
                color=message.guild.me.color if message.guild else None
            )

            author: Optional[str] = traverse_obj(post, ("authorText", "runs", 0, "text"))  # type: ignore (no idea how to type correctly)
            if author:
                thumbnail: Optional[str] = traverse_obj(post, ("authorThumbnail", "thumbnails", 0, "url"))  # type: ignore (no idea how to type correctly)
                if thumbnail:
                    thumbnail = "https:" + thumbnail

                urls: Optional[list[str]] = traverse_obj(post, ("authorEndpoint", (("commandMetadata", "webCommandMetadata", "url"), ("browseEndpoint", "canonicalBaseUrl"))))  # type: ignore (no idea how to type correctly)
                embed.set_author(
                    name=author,
                    icon_url=thumbnail,
                    url=f"https://www.youtube.com{urls[0]}" if urls else None,
                )

            texts: Optional[list[str]] = traverse_obj(post, ("contentText", "runs", ..., "text"))  # type: ignore (no idea how to type correctly)
            embed.description = dots_after("".join(texts), 4096) if texts else None

            images: Optional[list[dict[str, Any]]] = traverse_obj(post, ("backstageAttachment", "backstageImageRenderer", "image", "thumbnails"))  # type: ignore (no idea how to type correctly)
            if images:
                images.sort(key=lambda x: x["width"])
                url = images[-1]["url"]

                async with self.bot.session.get(url) as r:
                    if not r.ok:
                        self.log.error(f"{e.url} image fetch failed - wtf?")
                    elif r.content_type != "image/webp":
                        embed.set_image(url=url)
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

            poll: Optional[dict[str, Any]] = traverse_obj(post, ("backstageAttachment", "pollRenderer"))  # type: ignore (no idea how to type correctly)
            if poll:
                votes: Optional[str] = traverse_obj(poll, ("totalVotes", "simpleText"))  # type: ignore (no idea how to type correctly)
                choices: list[str] = traverse_obj(poll, ("choices", ..., "text", "runs", 0, "text")) or []  # type: ignore (no idea how to type correctly)
                embed.add_field(
                    name=f"Ankieta: {votes}",
                    value="\n".join([f"🔹 {c}" for c in choices]),
                )

            likes: Optional[str] = traverse_obj(post, ("voteCount", "simpleText"))  # type: ignore (no idea how to type correctly)
            if likes:
                embed.set_footer(text=f"👍 {likes}")

            new_embeds.append(embed)

        if new_embeds:
            await message.reply(embeds=new_embeds, files=files, mention_author=False)
            self.processed_messages.append(message.id)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content or not message.embeds:
            return

        await self.process_message(message)

    @commands.Cog.listener()
    async def on_message_edit(self, _: discord.Message, after: discord.Message):
        if (
            after.id in self.processed_messages
            or after.author.bot
            or not after.content
            or not after.embeds
        ):
            return

        await self.process_message(after)


async def setup(bot: DegeneratBot):
    await bot.add_cog(YTPosts(bot))
