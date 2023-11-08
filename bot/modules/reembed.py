import logging
import pathlib
import re

import discord
from discord.ext import commands

from ..bot import DegeneratBot
from yt_dlp import YoutubeDL


class ReEmbed(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = logging.getLogger(__name__)

        self.patterns: dict[str, str | None] = {
            r"https:\/\/(?:www\.)?instagram\.com\/(?:p|reel|reels)\/(.{11})": r"https://www.instagram.com/reel/\1",
            r"https:\/\/(?:www\.)?reddit\.com\/r\/.+?\/(?:comment)?s\/.*": None,
        }

        download_path: str = f"./{__name__}/download"
        pathlib.Path(download_path).mkdir(parents=True, exist_ok=True)

        self.ydl = YoutubeDL(
            params={
                "no_color": True,
                "logger": self.log,
                "outtmpl": f"{download_path}/%(id)s.%(ext)s",
            }
        )

        self.processed_messages: list[int] = []

    def _download(self, url: str) -> str:
        info = self.ydl.extract_info(url)
        return self.ydl.prepare_filename(info)

    def download(self, url: str):
        return self.bot.loop.run_in_executor(None, lambda: self._download(url))

    async def process_message(self, message: discord.Message):
        files: list[discord.File] = []

        for e in message.embeds:
            if not e.url:
                continue

            url = None
            for p, s in self.patterns.items():
                m = re.match(p, e.url)
                if m:
                    url = m.group()
                    if s:
                        url = re.sub(p, s, url)

                    break

            if not url:
                continue

            self.log.info(url)

            try:
                filename = await self.download(url)
                if not filename:
                    raise Exception
            except Exception:
                self.log.error(f"{url} failed to download")
                continue

            files.append(discord.File(filename))

        if files:
            self.processed_messages.append(message.id)
            await message.reply(files=files, mention_author=False)
            try:
                await message.edit(suppress=True)
            except discord.Forbidden:
                pass

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
    await bot.add_cog(ReEmbed(bot))
