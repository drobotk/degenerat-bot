import logging
import pathlib
import re

import discord
from discord.ext import commands

from ..bot import DegeneratBot
from yt_dlp import YoutubeDL


class IGReels(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = logging.getLogger(__name__)

        self.re_link: re.Pattern[str] = re.compile(
            r"^https:\/\/(?:www\.)?instagram\.com\/(?:p|reel|reels)\/([a-zA-Z0-9_\-]{11})"
        )

        params = {
            "no_color": True,
            "logger": self.log,
        }
        self.ydl = YoutubeDL(params)

        self.download_path: str = f"./{__name__}/download"
        pathlib.Path(self.download_path).mkdir(parents=True, exist_ok=True)

        self.processed_messages: list[int] = []

    async def process_message(self, message: discord.Message):
        files: list[discord.File] = []
        for e in message.embeds:
            if not e.url:
                continue

            m = self.re_link.match(e.url)
            if not m:
                continue

            id = m.group(1)
            self.log.info(id)

            url = f"https://www.instagram.com/reel/{id}"

            try:
                info = await self.bot.loop.run_in_executor(
                    None, lambda: self.ydl.extract_info(url, download=False)
                )
                if not info:
                    return
            except:
                self.log.error(f"{url} failed to extract info")
                return

            filename = f"{self.download_path}/{self.ydl.prepare_filename(info, outtmpl='%(id)s.%(ext)s')}"
            success, _ = await self.bot.loop.run_in_executor(
                None, lambda: self.ydl.dl(filename, info)
            )
            if success:
                files.append(discord.File(filename))

        if files:
            self.processed_messages.append(message.id)
            await message.reply(files=files, mention_author=False)
            await message.edit(suppress=True)

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
    await bot.add_cog(IGReels(bot))
