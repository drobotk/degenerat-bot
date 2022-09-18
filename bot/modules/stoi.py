import os
import logging

import discord
from discord.ext import commands
from discord import app_commands

import asyncssh

from ..bot import DegeneratBot


class Stoi(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.log = logging.getLogger(__name__)
        self.sshopts = asyncssh.SSHClientConnectionOptions(
            username=os.getenv("DEBIL_SSH_LOGIN"),
            password=os.getenv("DEBIL_SSH_PASSWD"),
            known_hosts=None,
            login_timeout=5,
            connect_timeout=5,
        )

    def get_duration_str(self, seconds: int) -> str:
        days, r = divmod(seconds, 86400)
        hours, r = divmod(r, 3600)
        mins, secs = divmod(r, 60)

        dur = ""

        if days:
            dur += f"{days}d "

        if hours or days:
            dur += f"{hours}h "

        if mins or hours or days:
            dur += f"{mins}m "

        if secs or mins or hours or days:
            dur += f"{secs}s"

        return dur

    @app_commands.command(description="Sprawdza status debila")
    @app_commands.guilds(655112863391940618, 598112506338344973)  # jfl, cmb
    async def stoi(self, interaction: discord.Interaction):
        await interaction.response.defer()

        e = discord.Embed()
        content = ""

        try:
            async with asyncssh.connect(
                host=os.getenv("DEBIL_IP"),
                port=int(os.getenv("DEBIL_SSH_PORT")),  # type: ignore
                options=self.sshopts,
            ) as _:
                e.color = discord.Colour.green()
                e.title = "**Tak** :white_check_mark:"

        except:
            e.color = discord.Colour.red()
            e.title = "**Nie** :x:"

            if interaction.guild.get_member(911698452457611334):
                content = ":exclamation: <@911698452457611334> :exclamation:"

        finally:
            await interaction.followup.send(content, embed=e)

        typesToString = {1: "HTTP", 2: "Keyword", 3: "Ping", 4: "Port", 5: "Heartbeat"}

        async with self.bot.session.post(
            "https://api.uptimerobot.com/v2/getMonitors",
            data={"api_key": os.getenv("UPTIME_TOKEN"), "format": "json", "logs": "1"},
            headers={"cache-control": "no-cache"},
        ) as r:
            if not r.ok:
                return

            j = await r.json()

        if j["stat"] != "ok":
            self.log.error(j)
            return

        if not j["monitors"]:
            return

        for m in j["monitors"]:
            typ = typesToString.get(m["type"], str(m["type"]))
            status = m["logs"][0]["reason"]["detail"]

            dur = self.get_duration_str(m["logs"][0]["duration"])

            e.add_field(
                name=f'**{typ}** - {m["friendly_name"]}',
                value=f"**{status}** - {dur}",
                inline=False,
            )

        e.description = "_ _"

        await interaction.edit_original_message(embed=e)


async def setup(bot: DegeneratBot):
    await bot.add_cog(Stoi(bot))
