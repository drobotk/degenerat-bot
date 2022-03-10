import discord
from discord.ext import commands
from discord import app_commands

import io


class Ryj(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @app_commands.command(description="Wysyła losowy ryj")
    async def ryj(self, interaction: discord.Interaction):
        await interaction.response.defer()

        async with self.bot.http._HTTPClient__session.get(
            "https://thispersondoesnotexist.com/image"
        ) as r:
            if r.ok:
                await interaction.followup.send(
                    file=discord.File(io.BytesIO(await r.read()), "ryj.jpg")
                )

            else:
                await interaction.followup.send("**Coś poszło nie tak**")


def setup(bot: commands.Bot):
    bot.add_cog(Ryj(bot))
