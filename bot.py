import discord
from discord.ext.commands import Bot

import os
import asyncio
import logging


_log = logging.getLogger(__name__)

intents = discord.Intents.all()
intents.presences = False
bot = Bot(command_prefix=",", help_command=None, intents=intents)

# go ahead and hate me for this
async def sync_globals_to(guild: discord.Guild):
    _log.info(f'Syncing commands to guild "{guild}"')
    bot.tree.copy_global_to(guild=guild)
    await bot.tree.sync(guild=guild)


@bot.event
async def on_ready():
    _log.info(f'Logged in as "{bot.user}"')

    if not hasattr(bot, "has_synced_commands"):
        for g in bot.guilds:
            await sync_globals_to(g)
            await asyncio.sleep(1)

        bot.has_synced_commands = True


@bot.event
async def on_guild_join(guild: discord.Guild):
    _log.info(f'Joined guild "{guild}"')

    await sync_globals_to(guild)


async def runner():
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
