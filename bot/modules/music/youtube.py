import re
import json
import pathlib
import logging
from dataclasses import dataclass
from typing import Optional, Any

import discord

from yt_dlp import YoutubeDL
from yt_dlp.utils import traverse_obj

from ...bot import DegeneratBot
from ... import utils
from .music_queue import MusicQueueVoiceClient


@dataclass
class YoutubeVideo:
    id: str
    title: str

    @property
    def url(self) -> str:
        return f"https://www.youtube.com/watch?v={self.id}"


class Youtube:
    bot: DegeneratBot

    def __init__(self):
        self.log: logging.Logger = logging.getLogger(__name__)

        params = {
            "no_color": True,
            "format": self.format_selector,
            "logger": self.log,
        }
        self.ydl = YoutubeDL(params)

        self.limit_mb = 100

        self.re_link = re.compile(
            r"(?:https?:\/\/)?(?:www\.|m\.)?youtu(?:\.be\/|be.com\/\S*(?:watch|embed)(?:(?:(?=\/[^&\s\?]+(?!\S))\/)|(?:\S*v=|v\/)))([^\"\'&\s\?]+)"
        )

        self.re_json: re.Pattern[str] = re.compile(r">var ytInitialData = (\{.+?\});<")

        self.download_path: str = f"./{__name__}/download"
        pathlib.Path(self.download_path).mkdir(parents=True, exist_ok=True)

    def format_selector(self, ctx: dict) -> list[dict]:
        formats: list[dict] = ctx["formats"]
        formats = [a for a in formats if a["acodec"] == "opus"]
        if len(formats) <= 1:
            return formats

        # sort by audio bitrate and return second best
        formats.sort(key=lambda a: a["abr"])
        return [formats[-2]]

    def extract_yt_url(self, text: str) -> Optional[str]:
        m = self.re_link.search(text)
        return f"https://www.youtube.com/watch?v={m.group(1)}" if m else None

    async def youtube_search(self, q: str, amount: int) -> list[YoutubeVideo]:
        async with self.bot.session.get(
            "https://www.youtube.com/results", params={"search_query": q}
        ) as r:
            if not r.ok:
                self.log.error(f"Search error: {r.status=}")
                return []

            text = await r.text()

        m = self.re_json.search(text)
        if not m:
            self.log.error(f"Search error: no json")
            return []

        try:
            # this is expensive af, but will probably be more robust longterm (regexing json is :moyai:)
            data = json.loads(m.group(1)).pop("contents")
        except (json.JSONDecodeError, KeyError) as e:
            self.log.error(f"Search error: {e.__class__.__name__}: {e}")
            return []

        renderers: Optional[list[dict[str, Any]]] = traverse_obj(data, ("twoColumnSearchResultsRenderer", "primaryContents", "sectionListRenderer", "contents", ..., "itemSectionRenderer", "contents", ..., "videoRenderer"))  # type: ignore (no idea how to type correctly)
        if not renderers:
            self.log.error(f"Search error: traverse_obj returned nothing")
            return []

        result = []
        for ren in renderers:
            titles: Optional[list[str]] = traverse_obj(ren, ("title", "runs", ..., "text"))  # type: ignore (no idea how to type correctly)
            if not titles:
                continue

            result.append(YoutubeVideo(id=ren["videoId"], title="".join(titles)))

            if len(result) >= amount:
                break

        return result

    def clean_title(self, t: str) -> str:
        return utils.sub_before(utils.sub_before(t, " ["), " (")

    async def queue_youtube(
        self, interaction: discord.Interaction, vc: MusicQueueVoiceClient, url: str
    ):
        reply = (
            interaction.message.edit
            if interaction.message
            else interaction.followup.send
        )

        e = discord.Embed(color=interaction.guild.me.color)  # type: ignore (command is guild only, guild can't be None here)
        e.set_footer(text=url)

        try:
            info = await self.bot.loop.run_in_executor(
                None, lambda: self.ydl.extract_info(url, download=False)
            )
            if not info:
                raise Exception("info is None")

            title: str = info["title"]
            filesize: int = info["filesize"]
            thumb: str = info["thumbnail"]

        except Exception as err:
            e = discord.Embed(
                title="**Wystąpił błąd**",
                description=str(err),
                color=discord.Colour.red(),
            )
            await reply(embed=e)
            return

        e.description = title
        e.set_thumbnail(url=thumb)

        if filesize > self.limit_mb * 1_000_000:
            e.title = f"**Rozmiar pliku przekracza rozsądny limit {self.limit_mb}MB**"
            e.color = discord.Colour.red()
            await reply(embed=e)
            return

        e.title = "Pobierańsko..."
        await reply(embed=e)

        filename = f"{self.download_path}/{self.ydl.prepare_filename(info, outtmpl='%(id)s.%(ext)s')}"
        success, _ = await self.bot.loop.run_in_executor(
            None, lambda: self.ydl.dl(filename, info)
        )
        if not success:
            e.title = "**Wystąpił błąd podczas pobierania pliku**"
            e.color = discord.Colour.red()
            await interaction.edit_original_response(embed=e)
            return

        titles = []
        if "artist" in info and "track" in info:
            artist: str = info["artist"]
            track: str = info["track"]
            titles.append(f"{artist} - {track}")
            if "|" in artist:
                for sub in artist.split("|"):
                    titles.append(f"{sub} - {track}")

            titles.append(track)  # last resort

        titles.append(title)
        titles = list(dict.fromkeys([self.clean_title(t) for t in titles]))

        e.title = "Odtwarzanie" if vc.is_standby else "Dodano do kolejki"
        msg = await interaction.edit_original_response(embed=e)

        await vc.add_entry(filename, opus=True, titles=titles, message=msg)
