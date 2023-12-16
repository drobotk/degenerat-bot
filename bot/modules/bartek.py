import logging
import discord
from discord.ext import commands

from ..bot import DegeneratBot
import os
from datetime import date

PATH = "data/polityka/"


class Bartek(commands.Cog):
    def __init__(self, bot: DegeneratBot, guild_id: int, user_id: int):
        self.bot: DegeneratBot = bot

        self.guild_id = guild_id
        self.user_id = user_id

        self.bartek_count = 0
        self.blacklist = set()
        self.previousDate = date.today()

        for file in os.listdir(PATH):
            with open(PATH + file, "r") as f:
                file_content = f.readline().split(",")
                file_content = filter(None, file_content)
                self.blacklist.update(file_content)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content:
            return

        if message.content.startswith(self.bot.command_prefix):  # type: ignore (error: Argument of type "PrefixType[BotT@__init__]" cannot be assigned to parameter "__prefix" of type "str | tuple[str, ...]" in function "startswith"  - bruh)
            return

        if message.guild.id != self.guild_id:
            return

        if message.author.id != self.user_id:
            return

        if not set(message.content.lower().split()).intersection(self.blacklist):
            return

        if self.previousDate != date.today():
            self.bartek_count = 0
            self.previousDate = date.today()

        if self.bartek_count >= 2:
            await message.delete()
            return

        await message.add_reaction("🤓")
        self.bartek_count += 1


async def setup(bot: DegeneratBot):
    try:
        guild_id = int(os.getenv("GUILD_ID"))
    except ValueError:
        return logging.fatal("GUILD_ID environment variable is not an integer!")
    except TypeError:
        return logging.fatal("GUILD_ID environment variable is not set!")

    try:
        user_id = int(os.getenv("USER_ID"))
    except ValueError:
        return logging.fatal("USER_ID environment variable is not an integer!")
    except TypeError:
        return logging.fatal("USER_ID environment variable is not set!")

    await bot.add_cog(Bartek(bot, guild_id, user_id))
