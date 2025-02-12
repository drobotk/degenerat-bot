import asyncio
import os
import logging
import time

import discord
from discord.ext import commands

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
            reactions=True,
        )
        super().__init__(command_prefix=",", help_command=None, intents=intents)

        self.start_time = round(time.time())

    async def setup_hook(self) -> None:
        self.session: aiohttp.ClientSession = aiohttp.ClientSession(
            headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:135.0) Gecko/20100101 Firefox/135.0",
                "Accept-Language": "pl,en-US;q=0.7,en;q=0.3",
            }
        )

        await self.load_extension("jishaku")

        path = __file__.replace("/bot.py", "")
        exts = [
            f.replace(".py", "")
            for f in os.listdir(f"{path}/modules")
            if not f.startswith("_")
        ]

        async def _load(ext):
            self.log.info(f'Loading extension "{ext}"')
            await self.load_extension(f"bot.modules.{ext}")

        await asyncio.gather(*(_load(ext) for ext in exts))

    async def close(self) -> None:
        if self.session:
            await self.session.close()

        await super().close()

    async def on_ready(self) -> None:
        self.log.info(f'Ready as "{self.user}"')
