import discord
from discord.ext import commands

import os
import re
import logging
from yt_dlp import YoutubeDL
from aiohttp import ClientSession

from .queue import MusicQueue, MusicQueueEntry


def sub_before(a: str, b: str, c: str = None) -> str:
    idx = a.find(b)
    if idx < 0:
        return c or a
    return a[:idx]


class Youtube:
    bot: commands.Bot

    def __init__(self):
        params = {
            "no_color": True,
            "format": self.format_selector,
            "logger": logging.getLogger(__name__),
        }
        self.ydl = YoutubeDL(params)

        self.re_link = re.compile(
            r"(?:https?:\/\/)?(?:www\.|m\.)?youtu(?:\.be\/|be.com\/\S*(?:watch|embed)(?:(?:(?=\/[^&\s\?]+(?!\S))\/)|(?:\S*v=|v\/)))([^\"\'&\s\?]+)"
        )

        self.re_search_results = re.compile(
            r'"videoRenderer":{"videoId":"(.{11})"(?:.+?)"title":{"runs":\[{"text":"(.+?)"}\],"accessibility"'
        )

    def format_selector(self, ctx: dict) -> list[dict]:
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
        session: ClientSession = self.bot.http._HTTPClient__session
        async with session.get(
            "https://www.youtube.com/results", params={"search_query": q}
        ) as r:
            if not r.ok:
                return

            text = await r.text()

        return self.extract_search_results(text, amount)

    def clean_title(self, t: str) -> str:
        return sub_before(sub_before(t, " ["), " (")

    async def queue_youtube(
        self, interaction: discord.Interaction, queue: MusicQueue, q: str
    ):
        msg = await interaction.original_message()
        reply = interaction.edit_original_message if msg else interaction.followup.send

        e = discord.Embed()
        e.set_footer(text=q)

        try:
            info = await self.bot.loop.run_in_executor(
                None, lambda: self.ydl.extract_info(q, download=False)
            )
            title: str = info["title"]
            filesize: str = info["filesize"]
            thumb: str = info["thumbnail"]

        except Exception as err:
            e = discord.Embed(
                title="**Wystąpił błąd**",
                description=str(err),
                color=discord.Colour.red(),
            )
            await reply(embed=e)
            return

        alt_titles = []
        if "artist" in info and "track" in info:
            artist: str = info["artist"]
            track: str = info["track"]
            alt_titles.append(f"{artist} - {track}")
            if "|" in artist:
                for sub in artist.split("|"):
                    alt_titles.append(f"{sub} - {track}")

            alt_titles.append(track)  # last resort

        alt_titles.append(title)
        alt_titles = list(dict.fromkeys([self.clean_title(t) for t in alt_titles]))

        e.description = title
        e.set_thumbnail(url=thumb)

        if filesize > self.limit_mb * 1_000_000:
            e.title = f"**Rozmiar pliku przekracza rozsądny limit {self.limit_mb}MB**"
            e.color = discord.Colour.red()
            await reply(embed=e)
            return

        e.title = "Pobierańsko..."
        e.color = interaction.guild.me.color
        await reply(embed=e)

        try:
            os.mkdir("./yt")
        except FileExistsError:
            pass

        filename = f"./yt/{self.ydl.prepare_filename(info)}"
        success, _ = await self.bot.loop.run_in_executor(
            None, lambda: self.ydl.dl(filename, info)
        )
        if not success:
            e.title = "**Wystąpił błąd podczas pobierania utworu**"
            e.color = discord.Colour.red()
            await interaction.edit_original_message(embed=e)
            return

        audio = await discord.FFmpegOpusAudio.from_probe(filename)

        e.title = "Odtwarzanie" if queue.empty else "Dodano do kolejki"
        await interaction.edit_original_message(embed=e)

        entry = MusicQueueEntry(title, alt_titles, audio, await interaction.original_message())
        queue.add_entry(entry)
