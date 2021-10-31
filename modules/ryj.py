from discord import File
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from aiohttp import ClientSession
from io import BytesIO

class Ryj( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot

    @cog_ext.cog_slash(
        name = 'ryj',
        description = 'Wysyła losowy ryj'
    )
    async def _ryj( self, ctx: SlashContext ):
        await ctx.defer()
        
        async with ClientSession() as s:
            async with s.get('https://thispersondoesnotexist.com/image') as r:
                if r.ok:
                    await ctx.send( file = File( BytesIO( await r.read() ), 'ryj.jpg') )
                    
                else:
                    await ctx.send('**Coś poszło nie tak**')

def setup( bot: Bot ):
    bot.add_cog( Ryj( bot ) )