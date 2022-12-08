import asyncio
import os
import subprocess

import discord
from discord.ext import commands
from discord import app_commands

from ..bot import DegeneratBot

KULA_COMMAND: str = """gimp -n -c -i -d -b '(gimp-file-load RUN-NONINTERACTIVE "{input}" "")' -b "(gimp-image-scale 1 (* (car (gimp-image-width 1)) (min (/ 500 (car (gimp-image-width 1)))(/ 500 (car (gimp-image-height 1))))) (* (car (gimp-image-height 1)) (min (/ 500 (car (gimp-image-width 1)))(/ 500 (car (gimp-image-height 1))))))" -b "(script-fu-spinning-globe 1 1 24 24 1 63 0 1)" -b '(file-gif-save 1 1 1 "{output}" "" FALSE TRUE 42 0)' -b "(gimp-quit TRUE)" """.strip()

async def kula_handler(interaction: discord.Interaction, input: discord.Attachment) -> discord.File:
    if not input.content_type.startswith("image/"):
        return await interaction.response.send_message("**Błąd: można zrobić kulę tylko z obrazów**", ephemeral=True)

    await interaction.response.defer()

    in_name = f"{input.id}.{input.filename}"
    out_name = f"{input.id}.gif"

    await input.save(in_name)

    try:
        cmd = KULA_COMMAND.format(input=in_name, output=out_name)
        await asyncio.get_running_loop().run_in_executor(None, lambda: subprocess.run(cmd, shell=True, check=False, capture_output=False))

        if not os.path.exists(out_name):
            return await interaction.followup.send("**Coś poszło nie tak, kula się nie zrobiła**")

        await interaction.followup.send(file=discord.File(out_name, description=f"{input.filename} jako kula"))
        os.remove(out_name)

    finally:
        os.remove(in_name)

class Kula(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

    @app_commands.command(description="Tworzy obracającą się kulę z obrazu")
    @app_commands.describe(img="Obraz")
    async def kula(self, interaction: discord.Interaction, img: discord.Attachment):
        await kula_handler(interaction, img)

# i hate how these can't be in cogs
@app_commands.context_menu(name="Kula")
async def kula_context(interaction: discord.Interaction, message: discord.Message):
    if not message.attachments:
        return await interaction.response.send_message("**Błąd: wiadomość nie zawiera załączników**", ephemeral=True)

    file = message.attachments[0]
    await kula_handler(interaction, file)

async def setup(bot: DegeneratBot):
    cog = Kula(bot)

    bot.tree.add_command(kula_context)

    await bot.add_cog(cog)
