from discord.ext.commands import Bot
from bs4 import BeautifulSoup

class Genius:
    bot: Bot

    async def get_genius_lyrics(self, q) -> tuple[str, str]:
        async with self.bot.http._HTTPClient__session.get("https://genius.com/api/search/song", params={"q": q}) as r:
            if not r.ok:
                return

            res = await r.json()
            if res["meta"]["status"] != 200:
                return

        try:
            song = res["response"]["sections"][0]["hits"][0]["result"]
        except (IndexError, KeyError):
            return

        async with self.bot.http._HTTPClient__session.get(song["url"]) as r:
            if not r.ok:
                return

            text = await r.text()

        soup = BeautifulSoup(text.replace("<br/>", "\n"), "lxml")
        tags = soup.select("div[data-lyrics-container=true]")
        return song["full_title"], "\n".join([tag.text for tag in tags])