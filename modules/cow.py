from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from cowsay import get_output_string


class Cow(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="cow", description="Mądrości krowy")
    async def _cow(self, ctx: SlashContext):
        await ctx.defer()

        async with self.bot.http._HTTPClient__session.get(
            "https://evilinsult.com/generate_insult.php?lang=en&type=json"
        ) as r:
            if not r.ok:
                await ctx.send(f"**Error:** insult status code { r.status }")
                return

            j = await r.json()

        english = j["insult"]

        params = {"client": "gtx", "dt": "t", "sl": "en", "tl": "pl", "q": english}

        async with self.bot.http._HTTPClient__session.get(
            "https://translate.googleapis.com/translate_a/single", params=params
        ) as r:
            if not r.ok:
                await ctx.send(f"**Error:** translate status code { r.status }")
                return

            j = await r.json()

        polish = "".join(
            [a[0] for a in j[0]]
        )  # jebać czytelność, zjebany internal endpoint

        msg = get_output_string("cow", polish).replace("`", "'")
        msg = "```\n" + msg[:1992] + "\n```"
        await ctx.send(msg)


def setup(bot: Bot):
    bot.add_cog(Cow(bot))
