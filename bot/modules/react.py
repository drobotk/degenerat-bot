import typing

import discord
from discord.ext import commands
from discord import app_commands, ui

from ..bot import DegeneratBot

l_to_e = {
    "A": ("๐ฆ", "๐ฐ๏ธ"),
    "B": ("๐ง", "๐ฑ๏ธ"),
    "C": ("๐จ",),
    "D": ("๐ฉ", "โถ๏ธ"),
    "E": ("๐ช",),  # need moar!!!
    "F": ("๐ซ",),
    "G": ("๐ฌ",),
    "H": ("๐ญ",),
    "I": ("๐ฎ", "โน๏ธ", "1โฃ"),
    "J": ("๐ฏ",),
    "K": ("๐ฐ",),
    "L": ("๐ฑ",),
    "M": ("๐ฒ", "โ๏ธ"),
    "N": ("๐ณ",),
    "O": ("๐ด", "๐พ๏ธ", "0โฃ"),
    "P": ("๐ต", "๐ฟ๏ธ"),
    "Q": ("๐ถ",),
    "R": ("๐ท",),
    "S": ("๐ธ", "5โฃ"),  # kinda meh using 5 as S
    "T": ("๐น",),
    "U": ("๐บ",),
    "V": ("๐ป",),
    "W": ("๐ผ",),
    "X": ("๐ฝ", "โ", "โ"),
    "Y": ("๐พ",),
    "Z": ("๐ฟ",),
    "0": ("0โฃ", "๐ด"),
    "1": ("1โฃ", "๐ฎ"),
    "2": ("2โฃ",),
    "3": ("3โฃ",),
    "4": ("4โฃ",),
    "5": ("5โฃ",),
    "6": ("6โฃ",),
    "7": ("7โฃ",),
    "8": ("8โฃ",),
    "9": ("9โฃ",),
    "?": ("โ", "โ"),
    "!": ("โ", "โ"),
    "#": ("#๏ธโฃ",),
    "*": ("*๏ธโฃ",),
    "10": ("๐",),
    "AB": ("๐",),
    "WC": ("๐พ",),
    "CL": ("๐",),
    "VS": ("๐",),
    "NG": ("๐",),
    "OK": ("๐",),
    "ID": ("๐",),
    "!!": ("โผ๏ธ",),
    "!?": ("โ๏ธ",),
    "UP": ("๐",),
    "ABC": ("๐ค",),
    "SOS": ("๐",),
    "NEW": ("๐",),
    "UP!": ("๐",),
    # basically unreadable as a reaction
    # "COOL": ("๐", ),
    # "FREE": ("๐", ),
}

pl = {
    "ฤ": "A",
    "ฤ": "C",
    "ฤ": "E",
    "ล": "L",
    "ล": "N",
    "ร": "O",
    "ล": "S",
    "ลน": "Z",
    "ลป": "Z",
}


def text_to_emojis(text: str) -> list[str]:
    text = text.upper()
    text = "".join([pl.get(x, x) for x in text])  # replace polish characters
    text = "".join(
        [x for x in text if x in l_to_e.keys()]
    )  # remove any characters we dont have emojis for

    out = []

    while text:
        r = 1  # number of chars consumed (for combos)

        e: typing.Optional[str] = None
        for i in [3, 2, 1]:
            s = l_to_e.get(text[:i], ())
            e = next(
                (x for x in s if x not in out), None
            )  # get first element of tuple that isnt in out, None if all already are
            if e is not None:
                r = i
                break

        if e is None:
            return []

        out.append(e)
        if len(out) > 20:
            return []

        text = text[r:]

    return out


class React(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

    @commands.command()
    async def react(
        self, ctx: commands.Context, *, text: str
    ):  # good luck using slash commands
        if not ctx.message.reference:
            return

        target = discord.PartialMessage(
            channel=ctx.channel, id=ctx.message.reference.message_id
        )

        if ctx.guild is not None:
            await ctx.message.delete()

        out = text_to_emojis(text)
        if not out:
            return False

        if ctx.guild is not None:  # can't clear reactions in DMs
            await target.clear_reactions()

        for x in out:
            await target.add_reaction(x)


class ReactionModal(ui.Modal):
    text = ui.TextInput(label="Tekst")

    def __init__(self, message: discord.Message):
        super().__init__(title="Dodaj reakcje")
        self.target = message

    async def on_submit(self, interaction: discord.Interaction):
        out = text_to_emojis(self.text.value)
        if not out:
            return await interaction.response.send_message(
                "**Bลฤd: nie da siฤ dodaฤ takiej reakcji**", ephemeral=True
            )

        await interaction.response.defer()

        if interaction.guild is not None:  # can't clear reactions in DMs
            await self.target.clear_reactions()

        for x in out:
            await self.target.add_reaction(x)


# i hate how these can't be in cogs
@app_commands.context_menu(name="Dodaj reakcje")
async def react_context(interaction: discord.Interaction, message: discord.Message):
    await interaction.response.send_modal(ReactionModal(message))


async def setup(bot: DegeneratBot):
    cog = React(bot)

    bot.tree.add_command(react_context)

    await bot.add_cog(cog)
