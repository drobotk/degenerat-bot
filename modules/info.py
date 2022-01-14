import discord
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.model import CommandObject
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle
import sys


class Info(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="info", description="Info o bocie")
    async def _info(self, ctx: SlashContext):
        e = discord.Embed(color=ctx.me.color)

        icon = str(ctx.me.avatar_url)
        icon = icon[: icon.find("?")] + "?size=32"
        e.set_author(name=str(ctx.me), icon_url=icon)

        e.add_field(name="Stworzony przez", value="RoboT#2675", inline=False)
        e.add_field(name="Serwery", value=str(len(self.bot.guilds)))

        cmds = [
            a
            for a in self.bot.slash.commands.values()
            if isinstance(a, CommandObject) and a._type == 1
        ]
        e.add_field(name="Komendy", value=str(len(cmds)))

        e.add_field(name="Hosting", value="Heroku", inline=False)
        e.add_field(name="Python", value=sys.version, inline=False)
        e.add_field(name="discord.py", value=discord.__version__, inline=False)

        link = f"https://discord.com/api/oauth2/authorize?client_id={ ctx.me.id }&permissions=412857396288&scope=bot%20applications.commands"
        components = [
            create_actionrow(
                create_button(style=ButtonStyle.URL, label="Dodaj do serwera", url=link)
            )
        ]

        await ctx.send(embed=e, components=components)


def setup(bot: Bot):
    bot.add_cog(Info(bot))
