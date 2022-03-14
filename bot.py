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

    if guild.id in bot.tree._guild_commands:
        bot.tree._guild_commands[guild.id].update(bot.tree._global_commands)
    else:
        bot.tree._guild_commands[guild.id] = bot.tree._global_commands

    context_cmds = {}
    for info, cmd in bot.tree._context_menus.items():
        if info[1] is None:
            new_info = (info[0], guild.id, info[2])
            context_cmds[new_info] = cmd

    bot.tree._context_menus.update(context_cmds)

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
