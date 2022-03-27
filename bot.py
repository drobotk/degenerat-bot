import discord
from discord.ext import commands

import os
import asyncio
import logging


_log = logging.getLogger(__name__)

intents = discord.Intents.all()
intents.presences = False
intents.typing = False
bot = commands.Bot(command_prefix=",", help_command=None, intents=intents)


@bot.event
async def on_ready():
    _log.info(f'Logged in as "{bot.user}"')
    for g in bot.guilds:
        bot.tree.copy_global_to(guild=g)


@bot.command()
@commands.is_owner()
async def syncall(ctx: commands.Context):
    msg = await ctx.send("Syncing all app commands to all guilds...")
    for n, g in enumerate(bot.guilds, 1):
        await bot.tree.sync(guild=g)
        await asyncio.sleep(n)

    await msg.edit("Done")


@bot.event
async def on_guild_join(guild: discord.Guild):
    _log.info(f'Joined guild "{guild}"')

    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)


async def runner():
    async with bot:
        await bot.load_extension("jishaku")
        await bot.load_extension("modules.stoi")
        await bot.load_extension("modules.activities")
        await bot.load_extension("modules.figlet")
        await bot.load_extension("modules.cow")
        await bot.load_extension("modules.react")
        await bot.load_extension("modules.img")
        await bot.load_extension("modules.ryj")
        await bot.load_extension("modules.music.cog")
        await bot.load_extension("modules.status")
        await bot.load_extension("modules.triggers")
        await bot.load_extension("modules.info")
        await bot.load_extension("modules.ttt")

        await bot.start(os.getenv("DISCORD_TOKEN"))


def main():
    logging.basicConfig(
        level=logging.INFO,
        format="%(name)s [%(levelname)s] %(message)s",
    )

    try:
        asyncio.run(runner())
    except KeyboardInterrupt:
        return


if __name__ == "__main__":
    main()
