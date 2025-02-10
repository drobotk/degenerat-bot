import json
import logging
import pathlib
import re
import subprocess
from typing import Any

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL
from yt_dlp.utils import traverse_obj

from ...bot import DegeneratBot

RE_LINKS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"https:\/\/(?:www\.)?instagram\.com\/(?:.+?\/)?(?:p|reel|reels)\/.{11}"
    ),
    re.compile(r"https:\/\/(?:www\.)?reddit\.com\/r\/.+?\/(?:comment)?s\/.+?(?:\s|$)"),
    re.compile(
        r"https:\/\/(?:www\.)?facebook\.com\/(?:reel|share\/(?:r|v))\/.+?(?:\s|$)"
    ),
    re.compile(r"https:\/\/vm\.tiktok\.com\/.{9}"),
    re.compile(r"https:\/\/(?:www\.)?tiktok\.com\/.+?\/video\/.+?(?:\s|$)"),
    re.compile(r"https:\/\/pin\.it\/.{9}"),
    re.compile(r"https:\/\/(?:www\.)?pinterest\.com\/pin\/\d{15}"),
)


class VideosReEmbed(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = logging.getLogger(__name__)

        download_path: str = f"./{__name__}/download"
        pathlib.Path(download_path).mkdir(parents=True, exist_ok=True)

        self.ydl = YoutubeDL(
            params={
                "no_color": True,
                "logger": self.log,
                "outtmpl": f"{download_path}/%(id)s.%(ext)s",
                "format": self.format_selector,
            }
        )

        self.default_format_selector = self.ydl.build_format_selector(
            "bestvideo*+bestaudio/best"
        )

    def format_selector(self, ctx: dict[str, Any]):
        formats: list[dict[str, Any]] = ctx["formats"]
        fb_hd = discord.utils.find(
            lambda f: f["format_id"] == "hd" and "fbcdn" in f["url"], formats
        )
        if fb_hd:
            return [fb_hd]

        return self.default_format_selector(ctx)

    def download(self, url: str):
        return self.bot.loop.run_in_executor(
            None, lambda: self.ydl.prepare_filename(self.ydl.extract_info(url))
        )

    def ffprobe_streams(self, filename: str):
        return self.bot.loop.run_in_executor(
            None,
            lambda: subprocess.run(
                (
                    "ffprobe",
                    "-v",
                    "quiet",
                    "-print_format",
                    "json",
                    "-show_streams",
                    filename,
                ),
                stdout=subprocess.PIPE,
                text=True,
                check=True,
            ),
        )

    def ffmpeg_transcode_to_h264(self, inp: str, out: str):
        return self.bot.loop.run_in_executor(
            None,
            lambda: subprocess.run(
                (
                    "ffmpeg",
                    "-v",
                    "quiet",
                    "-y",
                    "-i",
                    inp,
                    "-c:a",
                    "copy",
                    "-c:v",
                    "libx264",
                    out,
                ),
                check=True,
            ),
        )

    async def process_video(self, before: str) -> str:
        before_p = pathlib.Path(before)
        after_p = before_p.with_stem(f"{before_p.stem}_h264")
        after = str(after_p)
        if after_p.exists():
            return after

        try:
            result = await self.ffprobe_streams(before)
            data = json.loads(result.stdout)

        except subprocess.CalledProcessError:
            self.log.error(f"{before} ffprobe failed")
            return before

        except json.JSONDecodeError:
            self.log.error(f"{before} ffprobe JSON parse failed")
            return before

        codecs: list[str] | None = traverse_obj(data, ("streams", ..., "codec_name"))  # type: ignore
        if not codecs or "av1" not in codecs:
            return before

        self.log.info(f"{before} transcoding to h264")

        try:
            await self.ffmpeg_transcode_to_h264(before, after)

        except subprocess.CalledProcessError:
            self.log.error(f"{before} ffmpeg transcode failed")
            return before

        return after

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content:
            return

        urls: set[str] = {
            l.strip() for p in RE_LINKS for l in p.findall(message.content)
        }

        for url in urls:
            self.log.info(url)

            await message.channel.typing()

            try:
                filename = await self.download(url)
                if not filename:
                    raise Exception
            except Exception:
                self.log.error(f"{url} failed to download")
                continue

            filename = await self.process_video(filename)

            await message.reply(files=[discord.File(filename)], mention_author=False)
