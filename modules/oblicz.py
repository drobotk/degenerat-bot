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
from datetime import datetime

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
        
        self.illegal_in_output = []

        self.bartek = Bartek()

    @Cog.listener()
    async def on_ready( self ):
        self.illegal_in_output = [
            self.bot.http.token,
            *self.bot.http.token.split(".")
        ]
        self.illegal_in_output = [
            *self.illegal_in_output,
            *[ x[::-1] for x in self.illegal_in_output ]
        ]

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
        restrict = ctx.author.id != self.bot.appinfo.owner.id
    
        ######################################################
        if restrict and ( logchannel := self.bot.get_channel( 908412374673944657 ) ):
            e = discord.Embed( title = "Użył /oblicz", description = f"/oblicz `expr:{ expr }`", timestamp = datetime.utcnow(), color = ctx.me.color )

            icon = str( ctx.author.avatar_url )
            icon = icon[ :icon.find('?') ] + '?size=32'
            e.set_author( name = str( ctx.author ), icon_url = icon )
            
            icon = str( ctx.guild.icon_url )
            icon = icon[ :icon.find('?') ] + '?size=32' # ?size=*   => ?size=32
            e.set_footer( text = ctx.guild.name, icon_url = icon )
            
            await logchannel.send( embed = e )
        ######################################################
    
        code = normalize('NFKD', expr ).encode('utf-8', 'ignore').decode('utf-8')
        
        if restrict:
            for k in self.illegal_keywords:
                if k in code:
                    await ctx.send(f'**Nielegalne słowo kluczowe:** `{ k }`')
                    return

        await ctx.defer()

        b = ctx.bot

        if restrict:
            ctx.bot = None
        
        glbls = { **vars( base64 ), **vars( math ), 'json': json, 'discord': discord, 'bartek': self.bartek }
        lcls = {'ctx': ctx, 'expr': expr, 'code': code }
        
        if not restrict:
            lcls['cog'] = self

        try:
            if code.startswith('await '): # hack
                wynik = str( await eval( code[ 6: ], glbls, lcls ) )
            else:
                wynik = str( eval( code, glbls, lcls ) )
            
        except Exception as e:
            ctx.bot = b
            await ctx.send(f'**Błąd:** { str( e ) }')
            return
        
        ctx.bot = b
        
        if restrict:
            for x in self.illegal_in_output:
                if x in wynik:
                    await ctx.send(f'**Wykryto poufne treści w wyniku. Ten incident został zgłoszony do mojego administratora ({ self.bot.appinfo.owner.mention })**')
                    return
        
        wynik = f'`{ expr }` = { wynik }'
        
        try:
            if len( wynik ) <= 2000:
                await ctx.send( wynik )
                
            elif len( wynik ) <= ctx.guild.filesize_limit:
                await ctx.send( file = discord.File( BytesIO( wynik.encode() ), 'wynik.txt') )
                
            else:
                await ctx.send('**Błąd:** Rozmiar wyniku przekracza limit rozmiaru plików na tym serwerze.')
                
        except Exception as e:
            await ctx.send(f'**Nieoczekiwany błąd:** { str( e ) }')

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