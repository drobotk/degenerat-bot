import asyncio

from ...bot import DegeneratBot
from .allegro import AllegroReEmbed
from .videos import VideosReEmbed
from .yt_posts import YoutubePostsReEmbed


async def setup(bot: DegeneratBot):
    await asyncio.gather(
        bot.add_cog(AllegroReEmbed(bot)),
        bot.add_cog(VideosReEmbed(bot)),
        bot.add_cog(YoutubePostsReEmbed(bot)),
    )
