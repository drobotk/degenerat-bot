import random

import discord
from discord.ext import commands, tasks

from ..bot import DegeneratBot


class Activities(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

        self.activities = [
            discord.Activity(
                type=discord.ActivityType.watching, name="https://youtu.be/GJDNkVDGM_s"
            ),
            discord.Activity(
                type=discord.ActivityType.watching, name="https://youtu.be/Kg-HHXuOBlw"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="https://open.spotify.com/track/4brp8oXYkKJtkJWYuUaZ5T"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="https://open.spotify.com/track/5jFlj0Gzkk7mxdi8e4IlXx"
            ),
            discord.Activity(
                type=discord.ActivityType.listening, name="https://open.spotify.com/track/3oNKjHYfg4HAP1ivjUit9n"
            ),
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
