import logging
import discord
from discord.ext import commands

from ..bot import DegeneratBot

import csv
import os
from datetime import date

PATH = "./data/polityka"

class Bartek(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

        guild_id = os.getenv("GUILD_ID")
        if not guild_id:
            return logging.fatal("GUILD_ID environment variable not set!")

        bartek_id = os.getenv("BARTEK_ID")
        if not bartek_id:
            return logging.fatal("BARTEK_ID environment variable not set!")

        self.bartekCount = 0
        self.blacklist = []
        self.previousDate = date.today()

        for file in os.listdir(PATH):
            with open(f"{PATH}/{file}", "r") as f:
                self.blacklist.extend(list(csv.reader(f, delimiter=";"))[0][:-1])

        self.blacklist = set(self.blacklist)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        print(message.content)

        if message.author.bot or not message.content:
            return

        if message.content.startswith(self.bot.command_prefix):  # type: ignore (error: Argument of type "PrefixType[BotT@__init__]" cannot be assigned to parameter "__prefix" of type "str | tuple[str, ...]" in function "startswith"  - bruh)
            return

        if message.guild.id != guild_id:
            return

        if message.author.id != bartek_id:
            return

        if not set(message.content.lower().split()).intersection(self.blacklist):
            return

        if self.previousDate != date.today():
            self.bartekCount = 0
            self.previousDate = date.today()

        if self.bartekCount >= 2:
            await message.delete()
            return

        self.bartekCount += 1
        return


async def setup(bot: DegeneratBot):
    await bot.add_cog(Bartek(bot))
