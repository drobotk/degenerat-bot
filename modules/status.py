import discord
from discord.ext import commands
from discord import app_commands

import time


class Status(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.start_time = round(time.time())

    @app_commands.command(description="Status bota")
    async def status(self, interaction: discord.Interaction):
        start = time.perf_counter()
        await interaction.response.send_message("_ _")
        end = time.perf_counter()
        res_time = end - start

        e = discord.Embed(title="Status Bota", color=interaction.guild.me.color)
        e.add_field(name="Uruchomiony", value=f"<t:{self.start_time}:R>", inline=False)

        e.add_field(
            name="Opóźnienie Websocketa",
            value=f"{round(self.bot.latency * 1000) } ms",
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

        e.set_footer(text="Degenerat Bot")

        await interaction.edit_original_message(content=None, embed=e)


def setup(bot: commands.Bot):
    bot.add_cog(Status(bot))
