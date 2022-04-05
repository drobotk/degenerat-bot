import random

import discord
from discord.ext import commands, tasks

from ..bot import DegeneratBot


class Activities(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

        self.activities = [
            discord.Game("tomb rajder"),
            discord.Game("Hentai Nazi"),
            discord.Game("Ventti z Drabikiem"),
            discord.Game("My Summer Car"),
            discord.Activity(
                type=discord.ActivityType.watching, name="niemieckie porno"
            ),
            discord.Activity(
                type=discord.ActivityType.watching, name="mcskelli.tk/item4.html"
            ),
            discord.Activity(
                type=discord.ActivityType.watching, name="fish spinning for 68 years"
            ),
            discord.Activity(type=discord.ActivityType.watching, name="jak bartek sra"),
            discord.Activity(
                type=discord.ActivityType.watching, name="bartek walking meme.mp4"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="Young Leosia - Jungle Girl"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="Young Leosia - Szklanki"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="Dream - Mask (Sus Remix)"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="loud indian 10h bass boosted"
            ),
            discord.Activity(type=discord.ActivityType.listening, name="loud arabic"),
        ]

        self.update.start()

    def cog_unload(self):
        self.update.stop()

    @tasks.loop(minutes=1.0)
    async def update(self):
        await self.bot.wait_until_ready()

        me = self.bot.guilds[0].me
        if me is None:
            return

        while True:
            activity = random.choice(self.activities)

            if activity != me.activity:
                break

        await self.bot.change_presence(activity=activity)


async def setup(bot: DegeneratBot):
    await bot.add_cog(Activities(bot))
