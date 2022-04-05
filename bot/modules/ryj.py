import io

import discord
from discord.ext import commands
from discord import app_commands

from ..bot import DegeneratBot


class Ryj(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

    @app_commands.command(description="Wysyła losowy ryj")
    async def ryj(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with self.bot.session.get(
            "https://thispersondoesnotexist.com/image"
        ) as r:
            if r.ok:
                await interaction.followup.send(
                    file=discord.File(io.BytesIO(await r.read()), "ryj.jpg")
                )

            else:
                await interaction.followup.send("**Coś poszło nie tak**")


async def setup(bot: DegeneratBot):
    await bot.add_cog(Ryj(bot))
