import discord
from discord.ext.commands import Bot

import os
import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(name)s [%(levelname)s] %(message)s",
)
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

    if not hasattr(bot, "bruh"):
        for g in bot.guilds:
            await sync_globals_to(g)

        bot.bruh = True


@bot.event
async def on_guild_join(guild: discord.Guild):
    _log.info(f'Joined guild "{guild}"')

    await sync_globals_to(guild)


@bot.event
async def setup_hook():
    bot.load_extension("jishaku")
    bot.load_extension("modules.stoi")
    bot.load_extension("modules.activities")
    bot.load_extension("modules.figlet")
    bot.load_extension("modules.cow")
    bot.load_extension("modules.react")
    bot.load_extension("modules.img")
    bot.load_extension("modules.ryj")
    bot.load_extension("modules.music.cog")
    bot.load_extension("modules.status")
    bot.load_extension("modules.triggers")
    bot.load_extension("modules.info")


def main():
    try:
        bot.run(os.getenv("DISCORD_TOKEN"))

    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
