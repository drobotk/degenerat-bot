import logging
import pathlib
import re

import discord
from discord.ext import commands
from yt_dlp import YoutubeDL

from ...bot import DegeneratBot

RE_LINKS: tuple[re.Pattern[str], ...] = (
    re.compile(
        r"https:\/\/(?:www\.)?instagram\.com\/(?:.+?\/)?(?:p|reel|reels)\/.{11}"
    ),
    re.compile(r"https:\/\/(?:www\.)?reddit\.com\/r\/.+?\/(?:comment)?s\/.+?(?:\s|$)"),
    re.compile(r"https:\/\/(?:www\.)?facebook\.com\/(?:reel|share\/r)\/.+?(?:\s|$)"),
    re.compile(r"https:\/\/vm\.tiktok\.com\/.{9}"),
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
            }
        )

    def download(self, url: str):
        return self.bot.loop.run_in_executor(
            None, lambda: self.ydl.prepare_filename(self.ydl.extract_info(url))
        )

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

            await message.reply(files=[discord.File(filename)], mention_author=False)
