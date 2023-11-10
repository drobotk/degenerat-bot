import re
import os
import json
import pathlib
import logging
from dataclasses import dataclass
from typing import Any

import discord

import yt_dlp
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

        download_path: str = f"./{__name__}/download"
        pathlib.Path(download_path).mkdir(parents=True, exist_ok=True)

        _, _, _, params = yt_dlp.parse_options(
            ("--no-colors", "--sponsorblock-remove", "music_offtopic")
        )

        params.update(
            {
                "format": self.format_selector,
                "logger": self.log,
                "outtmpl": f"{download_path}/%(id)s.%(ext)s",
            }
        )
        self.ydl = yt_dlp.YoutubeDL(params)

        self.limit_mb = 100

        self.re_link = re.compile(
            r"(?:https?:\/\/)?(?:www\.|m\.)?youtu(?:\.be\/|be.com\/\S*(?:watch|embed)(?:(?:(?=\/[^&\s\?]+(?!\S))\/)|(?:\S*v=|v\/)))([^\"\'&\s\?]+)"
        )

        self.re_json: re.Pattern[str] = re.compile(r">var ytInitialData = (\{.+?\});<")

    def format_selector(self, ctx: dict) -> list[dict]:
        formats: list[dict] = ctx["formats"]
        formats = [f for f in formats if f.get("acodec") == "opus"]
        if len(formats) <= 1:
            return formats

        # sort by audio bitrate and return second best
        formats.sort(key=lambda a: a["abr"])
        return [formats[-2]]

    def extract_yt_url(self, text: str) -> str | None:
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

        renderers: list[dict[str, Any]] | None = traverse_obj(data, ("twoColumnSearchResultsRenderer", "primaryContents", "sectionListRenderer", "contents", ..., "itemSectionRenderer", "contents", ..., "videoRenderer"))  # type: ignore (no idea how to type correctly)
        if not renderers:
            self.log.error(f"Search error: traverse_obj returned nothing")
            return []

        result = []
        for ren in renderers:
            titles: list[str] | None = traverse_obj(ren, ("title", "runs", ..., "text"))  # type: ignore (no idea how to type correctly)
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
                raise Exception("YoutubeDL.extract_info: no info")

            title: str = info["title"]
            filesize: int = info["filesize"]
            thumb: str = info["thumbnail"]

        except Exception as err:
            e = discord.Embed(
                title="**Wystąpił błąd**",
                description=f"{err.__class__.__name__}: {err}",
                color=discord.Colour.red(),
            )
            await reply(embed=e)
            return

        e.title = "Odtwarzanie" if vc.is_standby else "Dodano do kolejki"
        e.description = title
        e.set_thumbnail(url=thumb)

        filename = self.ydl.prepare_filename(info)

        if os.path.exists(filename):
            msg = await reply(embed=e)
        else:
            if filesize > self.limit_mb * 1_000_000:
                e.title = f"**Rozmiar pliku przekracza rozsądny limit {self.limit_mb}MB**"
                e.color = discord.Colour.red()
                await reply(embed=e)
                return

            e.title = "Pobierańsko..."
            await reply(embed=e)
            
            success, _ = await self.bot.loop.run_in_executor(
                None, lambda: self.ydl.dl(filename, info)
            )

            if not success:
                e.title = "**Wystąpił błąd podczas pobierania pliku**"
                e.color = discord.Colour.red()
                await interaction.edit_original_response(embed=e)
                return

            try:
                await self.bot.loop.run_in_executor(
                    None, lambda: self.ydl.post_process(filename, info)
                )
            except Exception as err:
                self.log.error(f"YoutubeDL.post_process: {err.__class__.__name__}: {err}")
                
            msg = await interaction.edit_original_response(embed=e)

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

        await vc.add_entry(filename, opus=True, titles=titles, message=msg)
