import discord
from discord.ext import commands
from discord import app_commands

import sys


class Info(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="Info o bocie")
    async def info(self, interaction: discord.Interaction):
        e = discord.Embed(colour=interaction.guild.me.colour)

        avatar = (
            interaction.guild.me.avatar.url if interaction.guild.me.avatar else None
        )
        e.set_author(name=str(self.bot.user), icon_url=avatar)

        e.add_field(name="Stworzony przez", value="RoboT#2675", inline=False)
        e.add_field(name="Serwery", value=str(len(self.bot.guilds)))

        cmds = [
            c
            for c in self.bot.tree._global_commands.values()
            if isinstance(c, app_commands.Command)
        ]
        e.add_field(name="Komendy", value=str(len(cmds)))

        e.add_field(name="Hosting", value="Heroku", inline=False)
        e.add_field(name="Python", value=sys.version, inline=False)
        e.add_field(name="discord.py", value=discord.__version__, inline=False)

        invite_url = f"https://discord.com/api/oauth2/authorize?client_id={self.bot.user.id}&permissions=412857396288&scope=bot%20applications.commands"

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Dodaj do serwera", url=invite_url))

        await interaction.response.send_message(embed=e, view=view)


async def setup(bot: commands.Bot):
    await bot.add_cog(Info(bot))
