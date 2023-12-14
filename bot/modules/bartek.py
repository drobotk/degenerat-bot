import discord
from discord.ext import commands

from ..bot import DegeneratBot

import csv
from os import popen
from datetime import date

GUILD_ID = 1121557176390012958 #Alfa romeo
USER_ID = 410891559052247050 #Bartosz Tokarski ID


class Bartek(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

        self.bartekCount = 0
        self.blacklist = []
        self.previousDate = date.today()

        files = popen("ls bot/modules/_polityka/").read().split("\n")[:-1]

        for file in files:
            with open(f"bot/modules/_polityka/{file}", "r") as f:  
                self.blacklist.extend(list(csv.reader(f, delimiter=";"))[0][:-1])
        
        self.blacklist = set(self.blacklist)
        print(self.blacklist)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):

        print(message.content)

        if message.author.bot or not message.content:
            return

        if message.content.startswith(self.bot.command_prefix):  # type: ignore (error: Argument of type "PrefixType[BotT@__init__]" cannot be assigned to parameter "__prefix" of type "str | tuple[str, ...]" in function "startswith"  - bruh)
            return

        if message.guild.id != GUILD_ID:
            return

        if message.author.id != USER_ID:
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