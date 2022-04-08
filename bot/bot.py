import os
import logging
import typing

import discord
from discord.ext import commands
from discord import app_commands

import aiohttp


class DegeneratBot(commands.Bot):
    session: aiohttp.ClientSession

    def __init__(self) -> None:
        self.log: logging.Logger = logging.getLogger(__name__)

        intents: discord.Intents = discord.Intents(
            guilds=True,
            members=True,
            voice_states=True,
            messages=True,
            message_content=True,
        )
        super().__init__(
            command_prefix=",", help_command=None, intents=intents, tree_cls=MyTree
        )

    async def setup_hook(self) -> None:
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

        await self.load_extension("jishaku")

        path = __file__.replace("/bot.py", "")
        for f in os.listdir(f"{path}/modules"):
            if not f.startswith("_"):
                ext = f.replace(".py", "")
                self.log.info(f'Loading extension "{ext}"')
                await self.load_extension(f"bot.modules.{ext}")

    async def close(self) -> None:
        if self.session:
            await self.session.close()

        await super().close()

    async def on_ready(self) -> None:
        self.log.info(f'Ready as "{self.user}"')


class MyTree(app_commands.CommandTree[DegeneratBot]):
    async def on_error(
        self,
        interaction: discord.Interaction,
        command: typing.Optional[
            typing.Union[app_commands.ContextMenu, app_commands.Command]
        ],
        error: app_commands.AppCommandError,
    ):
        if isinstance(error, app_commands.CommandNotFound):
            return self.client.log.error(f"{error.__class__.__name__}: {str(error)}")

        if isinstance(error, app_commands.NoPrivateMessage):
            return await interaction.response.send_message(
                "**Ta komenda działa tylko na serwerach**", ephemeral=True
            )

        await super().on_error(interaction, command, error)
