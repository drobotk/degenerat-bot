import time

import discord
from discord.ext import commands
from discord import app_commands

from ..bot import DegeneratBot


class Status(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

    @app_commands.command(description="Status bota")
    async def status(self, interaction: discord.Interaction):
        start = time.perf_counter()
        await interaction.response.send_message("_ _")
        end = time.perf_counter()
        res_time = end - start

        e = discord.Embed(title="Status Bota")

        if interaction.guild is not None:
            e.colour = interaction.guild.me.colour

        e.add_field(
            name="Uruchomiony", value=f"<t:{self.bot.start_time}:R>", inline=False
        )

        e.add_field(
            name="Opóźnienie Websocketa",
            value=f"{round(self.bot.latency * 1000)} ms",
            inline=True,
        )
        e.add_field(
            name="Czas odpowiedzi",
            value=f"{round(res_time * 1000)} ms",
            inline=True,
        )

        e.add_field(
            name="Aktywne Cogi",
            value="\n".join([f":small_blue_diamond:{a}" for a in self.bot.cogs]),
            inline=False,
        )

        await interaction.edit_original_response(content=None, embed=e)


async def setup(bot: DegeneratBot):
    await bot.add_cog(Status(bot))
