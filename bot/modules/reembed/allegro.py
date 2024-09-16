import json
import logging
import re
from typing import Any

import discord
from discord.ext import commands
from bs4 import BeautifulSoup
from bs4.element import Tag
from yt_dlp.utils import traverse_obj

from ...bot import DegeneratBot

PRELOAD_URL = "https://allegro.pl/"
RE_LINK = re.compile(r"https:\/\/(?:www\.)?allegro\.pl\/oferta\/.+?(?:\s|$)")


def get_tag_single_value(tag: Tag, key: str, default: Any = None) -> str | None:
    vals = tag.get(key)
    if not vals:
        return default

    if isinstance(vals, list):
        return vals[0]

    return vals


# recenzjx
def review_count_suffix(count: int) -> str:
    if count == 1:
        return "a"

    units = str(count)[-1]
    if units in ("2", "3", "4"):
        return "e"

    return "i"


class AllegroReEmbed(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = logging.getLogger(__name__)

    async def cog_load(self) -> None:
        self.log.info("Preloading Allegro cookies")
        async with self.bot.session.get(PRELOAD_URL) as r:
            self.log.info(f"GET https://allegro.pl/ got {r.status}")
            if r.ok:
                return

            text = await r.text()
            soup = BeautifulSoup(text, "lxml")
            self.log.info(soup.select("body")[0].text)

        async with self.bot.session.get(PRELOAD_URL) as r:
            self.log.info(f"GET https://allegro.pl/ got {r.status}")
            if r.ok:
                self.log.info("Preloaded successfully")
            else:
                self.log.error(
                    "Failed to preload Allegro cookies - requests will likely fail"
                )

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content:
            return

        urls: set[str] = {l.strip() for l in RE_LINK.findall(message.content)}

        for url in urls:
            embeds: list[discord.Embed] = []

            self.log.info(url)

            await message.channel.typing()

            async with self.bot.session.get(url) as r:
                if not r.ok:
                    self.log.error(f"{url} status code {r.status}")
                    continue

                text = await r.text()

            soup = BeautifulSoup(text, "lxml")

            # tags = soup.select('script[type="application/json"]')
            # json = '{' + ','.join(['"'+get_tag_single_value(t, "data-serialize-box-id", "bth")+'":' + t.text for t in tags]) + '}'
            # with open("allegro.json", "w") as f:
            #     f.write(json)

            # likely an achilles heel
            tags = soup.select(
                'script[data-serialize-box-id="LUo64bt1RQOuwIphdVaomw==J64T9_eXQfScfS4Od98bMQ==m04cZ1kSTB6116aJB0jTWw=="]'
            )
            if not tags:
                self.log.error(f"{url} JSON script tag not found")
                continue

            data: dict[str, Any] = json.loads(tags[0].text)

            offer: dict[str, Any] | None = data.get("offer")
            if not offer:
                self.log.error(f"{url} no offer in JSON")
                continue

            embed = discord.Embed(
                color=message.guild.me.color if message.guild else None,
                url=url,
                title=offer.get("name"),
            )

            seller: str | None = traverse_obj(offer, ("seller", "name"))  # type: ignore (fuck u yt-dlp)
            seller_rating: str | None = traverse_obj(offer, ("seller", "ratings", "lastYear", "positive", "percentage"))  # type: ignore (fuck u yt-dlp)

            if seller:
                if seller_rating:
                    seller += f" | poleca {seller_rating}%"
                embed.set_footer(text=seller)

            price: str | None = traverse_obj(offer, ("sellingMode", "buyNow", "price", "sale", "amount"))  # type: ignore (fuck u yt-dlp)
            if price:
                currency: str = traverse_obj(offer, ("sellingMode", "buyNow", "price", "sale", "currency")) or ""  # type: ignore (fuck u yt-dlp)
                embed.add_field(name="Cena", value=f"{price} {currency}")

            ratingItems = []

            rating: int | None = traverse_obj(offer, ("product", "rating", "averageRating", "value"))  # type: ignore (fuck u yt-dlp)
            if rating is not None:
                ratingItems.append(f"{rating:.2f}")
                # ratingItems.append("⭐" * round(rating))  # meh

            rating_count: str | None = traverse_obj(offer, ("product", "rating", "countShortLabel"))  # type: ignore (fuck u yt-dlp)
            if rating_count:
                ratingItems.append(rating_count)

            review_count: int | None = traverse_obj(offer, ("product", "reviews", "count"))  # type: ignore (fuck u yt-dlp)
            if review_count:
                ratingItems.append(
                    f"{review_count} recenzj{review_count_suffix(review_count)}"
                )

            embed.add_field(name="Ocena", value=" | ".join(ratingItems) or "brak")

            # here already for image ordering
            embeds.append(embed)

            imgs: list[str] | None = traverse_obj(offer, ("images", ..., "url"))  # type: ignore (fuck u yt-dlp)
            if imgs:
                embed.set_image(url=imgs.pop(0))
                for i in imgs[:3]:
                    e = discord.Embed(url=url)
                    e.set_image(url=i)
                    embeds.append(e)

            if embeds:
                await message.reply(embeds=embeds, mention_author=False)
