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

        self.ydl_params = {
            "no_color": True,
            "logger": self.log,
        }

        self.download_path: str = f"./{__name__}/download"
        pathlib.Path(self.download_path).mkdir(parents=True, exist_ok=True)

        self.processed_messages: list[int] = []

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

            params = {
                **self.ydl_params,
                "outtmpl": f"{self.download_path}/%(id)s.%(ext)s",
            }

            def download():
                with YoutubeDL(params=params) as ydl:
                    info = ydl.extract_info(url)
                    return ydl.prepare_filename(info)

            try:
                filename = await self.bot.loop.run_in_executor(None, download)
                if not filename:
                    raise Exception
            except:
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
