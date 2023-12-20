import os
import logging
from datetime import date

import discord
from discord.ext import commands

from .message_handler import MessageHandler

from ...bot import DegeneratBot

PATH: str = "data/polityka/"

TEST = "BTH"


class Bartek(commands.Cog):
    def __init__(
        self, bot: DegeneratBot, log: logging.Logger, guild_id: int, user_id: int
    ):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = log
        self.handler: MessageHandler = MessageHandler(log, PATH, bot.session)

        self.guild_id: int = guild_id
        self.user_id: int = user_id

        self.bartek_count: int = 0
        self.previous_date: date = date.today()

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or message.author.id != self.user_id:
            return

        if not message.guild or message.guild.id != self.guild_id:
            return

        if message.content.startswith(self.bot.command_prefix):  # type: ignore (error: Argument of type "PrefixType[BotT@__init__]" cannot be assigned to parameter "__prefix" of type "str | tuple[str, ...]" in function "startswith"  - bruh)
            return

        if not await self.handler.isOffending(message):
            return

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
