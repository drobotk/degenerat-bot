from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.model import ContextMenuType
from discord_slash.context import SlashContext, MenuContext
from discord_slash.utils.manage_commands import create_option
from typing import Union
from unicodedata import normalize
from io import BytesIO
import discord
import math
import base64
import json

class Bartek:
    def __init__( self ):
        self.masa = float('inf')

class Oblicz( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot

        self.illegal_keywords = [
            'eval',
            'exec',
            'getattr',
            'builtins',
            'open',
            'import',
            'token',
        ]

        self.bartek = Bartek()

    @cog_ext.cog_slash(
        name = 'oblicz',
        description = 'Oblicza wyrażenia',
        options = [
            create_option(
                name = 'expr',
                description = 'Wyrażenie do obliczenia',
                option_type = 3,
                required = True
            )
        ]
    )
    async def _oblicz( self, ctx: Union[ SlashContext, MenuContext ], expr: str ):
        code = normalize('NFKD', expr ).encode('utf-8', 'ignore').decode('utf-8')
        
        for cep in self.illegal_keywords:
            if cep in code:
                await ctx.send(f'`{ cep }` **się skończyło, jest tylko falafel.**')
                return

        await ctx.defer()

        b = ctx.bot

        if ctx.author.id != 360781251579346944:
            ctx.bot = None
        
        glbls = { **vars( base64 ), **vars( math ), 'json': json, 'discord': discord, 'bartek': self.bartek }
        lcls = {'ctx': ctx, 'expr': expr, 'code': code }
        
        if ctx.author.id == 360781251579346944:
            lcls['cog'] = self

        try:
            if expr[ 0 ] == '(': # hack
                wynik = str( await eval( code, glbls, lcls ) )
            else:
                wynik = str( eval( code, glbls, lcls ) )
            
        except Exception as e:
            ctx.bot = b
            await ctx.send(f'**Co ty damian, pedał jesteś?** { str( e ) }')
            return
        
        ctx.bot = b
        
        if self.bot.http.token in wynik or self.bot.http.token[ ::-1 ] in wynik or 'ODMwNDIxOTE3NDc0NDg4MzUw' in wynik or 'wUzM4gDN0cDN3ETOxIDNwMDO' in wynik:
            await ctx.send(f'**Nie sprzedam baraniny!**')
            return
        
        wynik = f'`{ expr }` = { wynik }'
        
        try:
            if len( wynik ) <= 2000:
                await ctx.send( wynik )
                
            elif len( wynik ) <= ctx.guild.filesize_limit:
                await ctx.send( file = discord.File( BytesIO( wynik.encode() ), 'wynik.txt') )
                
            else:
                await ctx.send('**Kapusta.** (Rozmiar wyniku przekracza limit tego serwera.)')
                
        except Exception as e:
            await ctx.send(f'**O skubany, jak to zrobiłeś?** { str( e ) }')

    @cog_ext.cog_context_menu(
        name = 'Oblicz',
        target = ContextMenuType.MESSAGE
    )
    async def _oblicz_context( self, ctx: MenuContext ):
        if ctx.target_message.content:
            await self._oblicz.func( self, ctx, ctx.target_message.content )
        else:
            await ctx.send('**Błąd: Wiadomość bez treści**', hidden = True )

def setup( bot: Bot ):
    bot.add_cog( Oblicz( bot ) )