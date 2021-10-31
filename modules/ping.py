from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext

class Ping( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot

    @cog_ext.cog_slash(
        name = 'ping',
        description = 'Test bota'
    )
    async def _ping( self, ctx: SlashContext ):
        await ctx.send(f'**Pong!** Websocket Latency: { round( self.bot.latency * 1000 ) } ms')

def setup( bot: Bot ):
    bot.add_cog( Ping( bot ) )