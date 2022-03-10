import discord
from discord.ext.commands import Bot

import os

import logging

logging.basicConfig(
    level=logging.DEBUG,
    format="%(name)s [%(levelname)s] %(message)s",
)
_log = logging.getLogger(__name__)

intents = discord.Intents.default()
intents.message_content = True  # jsk

bot = Bot(command_prefix=".", help_command=None, intents=intents)


async def sync_commands(guild: discord.Guild):
    if guild.id in bot.tree._guild_commands:
        bot.tree._guild_commands[guild.id].update(bot.tree._global_commands)
    else:
        bot.tree._guild_commands[guild.id] = bot.tree._global_commands

    await bot.tree.sync(guild=guild)


@bot.event
async def on_ready():
    _log.info(f'Logged in as "{bot.user}"')

    for g in bot.guilds:
        await sync_commands(g)


@bot.event
async def on_guild_join(guild: discord.Guild):
    _log.info(f'Joined guild "{guild}"')

    await sync_commands(guild)


def main():
    try:
        bot.load_extension("jishaku")
        bot.load_extension("modules.stoi")
        bot.load_extension("modules.activities")
        # bot.load_extension("modules.figlet")
        # bot.load_extension("modules.oblicz")
        bot.load_extension("modules.cow")
        # bot.load_extension("modules.react")
        # bot.load_extension("modules.img")
        bot.load_extension("modules.ryj")
        # bot.load_extension("modules.ttt")
        # bot.load_extension("modules.music.cog")
        bot.load_extension("modules.status")
        bot.load_extension("modules.triggers")
        bot.load_extension("modules.info")

        bot.run(os.getenv("DISCORD_TOKEN"))

    except KeyboardInterrupt:
        exit()


if __name__ == "__main__":
    main()
