import os
import logging
from datetime import date

import discord
from discord.ext import commands

from ..bot import DegeneratBot

PATH = "data/polityka/"


class Bartek(commands.Cog):
    def __init__(self, bot: DegeneratBot, log: logging.Logger, guild_id: int, user_id: int):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = log

        self.guild_id = guild_id
        self.user_id = user_id

        self.bartek_count = 0
        self.blacklist: set[str] = set()
        self.previous_date = date.today()

        for file in os.listdir(PATH):
            with open(PATH + file, "r") as f:
                file_content = f.readline().split(",")
                file_content = filter(None, file_content)
                self.blacklist.update(file_content)

        self.log.info(f"Loaded {len(self.blacklist)} blacklisted keywords")

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.author.id != self.user_id:
            return

        if not message.guild or message.guild.id != self.guild_id:
            return

        if not message.content or message.content.startswith(self.bot.command_prefix):  # type: ignore (error: Argument of type "PrefixType[BotT@__init__]" cannot be assigned to parameter "__prefix" of type "str | tuple[str, ...]" in function "startswith"  - bruh)
            return

        for offending in self.blacklist:
            if offending.lower() in message.content.lower():
                break
        else:
            return

        self.log.info(f"Offending message: {message.content}")
        
        if self.previous_date != date.today():
            self.bartek_count = 0
            self.previous_date = date.today()

        if self.bartek_count >= 2:
            await message.delete()
            return

        await message.add_reaction("🤓")
        self.bartek_count += 1


async def setup(bot: DegeneratBot):
    log = logging.getLogger(__name__)

    guild_id = os.getenv("BARTEK_GUILD_ID")
    if not guild_id:
        return log.error("BARTEK_GUILD_ID environment variable is not set!")

    try:
        guild_id = int(guild_id)
    except ValueError:
        return log.error("BARTEK_GUILD_ID environment variable is not an integer!")

    user_id = os.getenv("BARTEK_USER_ID")
    if not user_id:
        return log.error("BARTEK_USER_ID environment variable is not set!")

    try:
        user_id = int(user_id)
    except ValueError:
        return log.error("BARTEK_USER_ID environment variable is not an integer!")

    await bot.add_cog(Bartek(bot, log, guild_id, user_id))
