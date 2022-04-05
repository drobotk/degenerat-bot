import discord
from discord.ext import commands

import os
import aiohttp
import logging


class DegeneratBot(commands.Bot):
    session: aiohttp.ClientSession

    def __init__(self) -> None:
        self.log: logging.Logger = logging.getLogger(__name__)

        intents: discord.Intents = discord.Intents.all()
        intents.presences = False
        intents.typing = False

        super().__init__(command_prefix=",", help_command=None, intents=intents)

    async def setup_hook(self) -> None:
        self.session: aiohttp.ClientSession = aiohttp.ClientSession()

        await self.load_extension("jishaku")

        path = __file__.replace("/bot.py", "")
        for f in os.listdir(f"{path}/modules"):
            if not f.startswith("_"):
                ext: str = f.replace(".py", "")
                self.log.info(f'Loading extension "{ext}"')
                await self.load_extension(f"bot.modules.{ext}")

    async def close(self) -> None:
        if self.session:
            await self.session.close()

        await super().close()

    async def on_ready(self) -> None:
        self.log.info(f'Ready as "{self.user}"')
