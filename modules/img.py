from discord import File
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.model import ContextMenuType
from discord_slash.context import SlashContext, MenuContext
from discord_slash.utils.manage_commands import create_option
from typing import Union
from aiohttp import ClientSession
from xml.dom.minidom import parseString
from io import BytesIO

class Img( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot

    def make_safe_filename( self, s ):
        return ''.join( ( c if c.isalnum() or c == '.' else '_') for c in s )

    @cog_ext.cog_slash(
        name = 'img',
        description = 'Wyszukuje hujowo małe obrazki',
        options = [
            create_option(
                name = 'q',
                description = 'Search query',
                option_type = 3,
                required = True
            )
        ]
    )
    async def _img( self, ctx: Union[ SlashContext, MenuContext ], q: str ):
        await ctx.defer()

        try:
            async with ClientSession( headers = {'User-Agent': 'degenerat-bot/2137'} ) as s:
                async with s.get('https://www.google.com/search', params = {'tbm': 'isch', 'q': q } ) as r:
                    if not r.ok:
                        raise Exception(f'{ r.url } got { r.status }')
                    
                    text = await r.text()
                
                doc = parseString( text )

                img = [ x.getAttribute('src') for x in doc.getElementsByTagName('img') ]
                img = img[ 1:4 ]
                
                files = []
                
                for k, v in enumerate( img ):
                    async with s.get( v ) as r:
                        if r.ok:
                            files.append( File( BytesIO( await r.read() ), f'{ self.make_safe_filename( q ) }{ k }.jpg') )
                        
            
            await ctx.send( files = files )
            
        except Exception as e:
            await ctx.send(f'**Coś poszło nie tak:** { str( e ) }')

    @cog_ext.cog_context_menu(
        name = 'Image Search',
        target = ContextMenuType.MESSAGE
    )
    async def _img_context( self, ctx: MenuContext ):
        if ctx.target_message.content:
            await self._img.func( self, ctx, ctx.target_message.content )
        else:
            await ctx.send('**Błąd: Wiadomość bez treści**', hidden = True )    

def setup( bot: Bot ):
    bot.add_cog( Img( bot ) )