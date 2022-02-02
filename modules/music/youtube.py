from discord import Embed, Colour, FFmpegOpusAudio
from discord.ext.commands import Bot
from discord_slash import SlashContext, MenuContext
from typing import Union
from yt_dlp import YoutubeDL
from logging import getLogger
from os import mkdir
from .queue import MusicQueue, MusicQueueEntry
import re

def sub_before(a: str, b: str, c: str = None) -> str:
    idx = a.find(b)
    if idx < 0:
        return c or a
    return a[:idx]

class Youtube:
    bot: Bot

    def __init__(self):
        params = {
            "no_color": True,
            "format": self.format_selector,
            "logger": getLogger(__name__),
        }
        self.ydl = YoutubeDL(params)

        self.re_link = re.compile(
            r"(?:https?:\/\/)?(?:www\.|m\.)?youtu(?:\.be\/|be.com\/\S*(?:watch|embed)(?:(?:(?=\/[^&\s\?]+(?!\S))\/)|(?:\S*v=|v\/)))([^\"\'&\s\?]+)"
        )

        self.re_search_results = re.compile(
            r'"videoRenderer":{"videoId":"(.{11})"(?:.+?)"title":{"runs":\[{"text":"(.+?)"}\],"accessibility"'
        )

    def format_selector(self, ctx: dict) -> list:
        formats = ctx["formats"]
        formats = [a for a in formats if a["acodec"] == "opus"]
        if len(formats) <= 1:
            return formats

        # sort by audio bitrate and return second best
        formats.sort(key=lambda a: a["abr"])
        return [formats[-2]]

    def extract_yt_url(self, text: str) -> str:
        m = self.re_link.search(text)
        return f"https://www.youtube.com/watch?v={m.group(1)}" if m else None

    def extract_search_results(self, text: str, amount: int) -> list[tuple[str, str]]:
        result = []
        for i, m in enumerate(self.re_search_results.finditer(text), 1):
            vid = m.group(1)
            # remove json escape sequences :scraper_moment:
            title = re.sub(r"\\([\\\"])", "\g<1>", m.group(2))
            result.append((f"https://www.youtube.com/watch?v={vid}", title))
            if i == amount:
                break

        return result

    async def youtube_search(self, q: str, amount: int) -> list[tuple[str, str]]:
        async with self.bot.http._HTTPClient__session.get(
            "https://www.youtube.com/results", params={"search_query": q}
        ) as r:
            if not r.ok:
                return

            text = await r.text()

        return self.extract_search_results(text, amount)

    async def queue_youtube(
        self, ctx: Union[SlashContext, MenuContext], queue: MusicQueue, q: str
    ):
        reply = ctx.message.edit if ctx.message else ctx.send

        e = Embed()
        e.set_footer(text=q)

        try:
            info = await self.bot.loop.run_in_executor(
                None, lambda: self.ydl.extract_info(q, download=False)
            )
            title = info["title"]
            filesize = info["filesize"]
            thumb = info["thumbnail"]

        except Exception as err:
            e = Embed(
                title="**Wystąpił błąd**", description=str(err), color=Colour.red()
            )
            await reply(embed=e)
            return

        meta_title = (
            f"{info['artist']} - {info['track']}"
            if ("artist" in info and "track" in info)
            else sub_before(sub_before(title, " ["), " (")
        )

        e.description = title
        e.set_thumbnail(url=thumb)

        if filesize > self.limit_mb * 1_000_000:
            e.title = f"**Rozmiar pliku przekracza rozsądny limit {self.limit_mb}MB**"
            e.color = Colour.red()
            await reply(embed=e)
            return

        e.title = "Pobierańsko..."
        e.color = ctx.me.color
        await reply(embed=e)

        try:
            mkdir("./yt")
        except FileExistsError:
            pass

        filename = f"./yt/{ self.ydl.prepare_filename( info ) }"
        success, _ = await self.bot.loop.run_in_executor(
            None, lambda: self.ydl.dl(filename, info)
        )
        if not success:
            e.title = "**Wystąpił błąd podczas pobierania pliku**"
            e.color = Colour.red()
            await ctx.message.edit(embed=e)
            return

        audio = await FFmpegOpusAudio.from_probe(filename)

        e.title = "Odtwarzanie" if queue.empty else "Dodano do kolejki"
        await ctx.message.edit(embed=e)

        entry = MusicQueueEntry(title, meta_title, audio, ctx.message)
        queue.add_entry(entry)
