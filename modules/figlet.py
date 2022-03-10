import discord
from discord.ext import commands
from discord import app_commands

import unicodedata
import pyfiglet


class Figlet(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.fig = pyfiglet.Figlet()

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

    # TODO: uncomment once context commands in cogs get fixed
    #
    # @app_commands.context_menu(name="Figlet")
    # async def figlet_context(
    #     self, interaction: discord.Interaction, message: discord.Message
    # ):
    #     if message.content:
    #         await self.figlet.callback(self, interaction, message.content)
    #     else:
    #         await interaction.response.send_message(
    #             "**Błąd: Wiadomość bez treści**", ephemeral=True
    #         )


def setup(bot: commands.Bot):
    bot.add_cog(Figlet(bot))
