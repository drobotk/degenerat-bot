import unicodedata

import discord
from discord.ext import commands
from discord import app_commands

import pyfiglet

from ..bot import DegeneratBot


class Figlet(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.fig: pyfiglet.Figlet = pyfiglet.Figlet()

    @app_commands.command(description="FIGlet bruh")
    @app_commands.describe(text="Tekst do wyfigletowania")
    async def figlet(self, interaction: discord.Interaction, text: str):
        txt = (
            unicodedata.normalize("NFKD", text)
            .encode("utf-8", "ignore")
            .decode("utf-8")
        )
        msg = self.fig.renderText(txt).replace("`", "'")
        msg = "```\n" + msg[:1992] + "\n```"
        await interaction.response.send_message(msg)


async def setup(bot: DegeneratBot):
    cog = Figlet(bot)

    # ugly, i hate how these can't be in cogs
    @app_commands.context_menu(name="Figlet")
    async def figlet_context(
        interaction: discord.Interaction, message: discord.Message
    ):
        if message.content:
            await cog.figlet.callback(cog, interaction, message.content)  # type: ignore (Expected 2 positional arguments - type checker bug?)
        else:
            await interaction.response.send_message(
                "**Błąd: Wiadomość bez treści**", ephemeral=True
            )

    bot.tree.add_command(figlet_context)

    await bot.add_cog(cog)
