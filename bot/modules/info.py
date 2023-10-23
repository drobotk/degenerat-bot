import os
import sys

import discord
from discord.ext import commands
from discord import app_commands, utils

from ..bot import DegeneratBot


class Info(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

    @app_commands.command(description="Info o bocie")
    async def info(self, interaction: discord.Interaction):
        e = discord.Embed()

        if interaction.guild is not None:
            e.colour = interaction.guild.me.colour

        avatar = self.bot.user.avatar.url if self.bot.user.avatar else None  # type: ignore (bot.user will never be None here)
        e.set_author(name=str(self.bot.user), icon_url=avatar)

        e.add_field(name="Stworzony przez", value="drobotk (RoboT#2675)", inline=False)
        e.add_field(name="Serwery", value=len(self.bot.guilds))

        cmds = [
            c
            for c in self.bot.tree._global_commands.values()
            if isinstance(c, app_commands.Command)
        ]
        e.add_field(name="Komendy", value=len(cmds))

        uname = os.uname()
        e.add_field(
            name="OS",
            value=f"{uname.sysname} {uname.release} {uname.machine}",
            inline=False,
        )
        e.add_field(name="Python", value=sys.version, inline=False)
        e.add_field(name="discord.py", value=discord.__version__, inline=False)

        app_info = await self.bot.application_info()
        if not app_info.install_params:
            return await interaction.response.send_message(embed=e)

        invite_url = utils.oauth_url(
            self.bot.user.id,  # type: ignore (bot.user will never be None here)
            permissions=app_info.install_params.permissions,
            scopes=app_info.install_params.scopes,
        )

        view = discord.ui.View()
        view.add_item(discord.ui.Button(label="Dodaj do serwera", url=invite_url))

        await interaction.response.send_message(embed=e, view=view)


async def setup(bot: DegeneratBot):
    await bot.add_cog(Info(bot))
