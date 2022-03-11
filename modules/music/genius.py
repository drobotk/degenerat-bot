from discord.ext import commands
from aiohttp import ClientSession
from bs4 import BeautifulSoup


class Genius:
    bot: commands.Bot

    async def get_genius_lyrics(self, q) -> tuple[str, str]:
        session: ClientSession = self.bot.http._HTTPClient__session
        async with session.get(
            "https://genius.com/api/search/song", params={"q": q}
        ) as r:
            if not r.ok:
                return q, None

            res = await r.json()
            if res["meta"]["status"] != 200:
                return q, None

        try:
            song = res["response"]["sections"][0]["hits"][0]["result"]
        except (IndexError, KeyError):
            return q, None

        title = song["full_title"]

        async with session.get(song["url"]) as r:
            if not r.ok:
                return title, None

            text = await r.text()

        soup = BeautifulSoup(text.replace("<br/>", "\n"), "lxml")
        tags = soup.select("div[data-lyrics-container=true]")
        return title, "\n".join([tag.text for tag in tags])
