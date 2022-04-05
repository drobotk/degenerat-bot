import discord
from discord.ext import commands
from discord import app_commands

import cowsay

from ..bot import DegeneratBot


class Cow(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

    @app_commands.command(description="Mądrości krowy")
    async def cow(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with self.bot.session.get(
            "https://evilinsult.com/generate_insult.php?lang=en&type=json"
        ) as r:
            if not r.ok:
                await interaction.followup.send(
                    f"**Error:** insult status code {r.status}"
                )
                return

            j = await r.json()

        english = j["insult"]

        params = {"client": "gtx", "dt": "t", "sl": "en", "tl": "pl", "q": english}

        async with self.bot.session.get(
            "https://translate.googleapis.com/translate_a/single", params=params
        ) as r:
            if not r.ok:
                await interaction.followup.send(
                    f"**Error:** translate status code { r.status }"
                )
                return

            j = await r.json()

        polish = "".join(
            [a[0] for a in j[0]]
        )  # jebać czytelność, zjebany internal endpoint

        msg = cowsay.get_output_string("cow", polish).replace("`", "'")
        msg = "```\n" + msg[:1992] + "\n```"
        await interaction.followup.send(msg)


async def setup(bot: DegeneratBot):
    await bot.add_cog(Cow(bot))
