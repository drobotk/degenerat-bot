import discord
from discord.ext.commands import Bot
from discord.ext import tasks
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle, ContextMenuType

import os
import io
import sys
import math
import aiohttp
import unicodedata
import base64
import asyncssh
import random
from pyfiglet import Figlet
from xml.dom.minidom import parseString
from urllib.parse import urlparse

from fixed_shit import YouTube
from fixed_shit import SlashCommand

intents = discord.Intents.default()
intents.members = True

# activity = discord.Activity( type = discord.ActivityType.watching, name = 'jak sie jacek myje')
bot = Bot( command_prefix = ',', self_bot = True, help_command = None, intents = intents )

slash = SlashCommand( bot, sync_commands = True )

@bot.event
async def on_ready():
    print(f'Logged in as { str( bot.user ) }')
    
    if not MusicQueuesUpdate.is_running():
        MusicQueuesUpdate.start()
        
    if not UpdateActivityStatus.is_running():
        UpdateActivityStatus.start()
        
@bot.event
async def on_guild_join( guild ):
    print(f'Joined { str( guild ) } - syncing commands')
    await slash.sync_all_commands()

sshopts = asyncssh.SSHClientConnectionOptions( known_hosts = None, username = "degenerat-stoi", password = "japierdole")

@slash.slash( name = 'stoi', description = 'Sprawdza czy kutas stoi')
async def stoi( ctx ):
    await ctx.defer()

    try:
        async with asyncssh.connect('62.122.235.235', port = 2200, options = sshopts ) as _:
            await ctx.send('**Tak :white_check_mark:**')
    
    except:# Exception as e:
        # print( e )
        if ctx.guild.get_member( 473849794381611021 ):
            await ctx.send('**Nie :x: <@473849794381611021> :exclamation:**')
        else:
            await ctx.send('**Nie :x:**')
    
    headers = {
        'content-type':     'application/x-www-form-urlencoded',
        'cache-control':    'no-cache'
    }
    payload = f'api_key={ os.environ["uptime"] }&format=json&all_time_uptime_ratio=1'
    
    async with aiohttp.ClientSession() as s:
        async with s.post('https://api.uptimerobot.com/v2/getMonitors', data = payload, headers = headers ) as r:
            if not r.ok:
                return
                
            j = await r.json()
            if j['stat'] != 'ok':
                return
    
    content = ctx.message.content + '\n'
    
    typesToString = {
        1:  'HTTP',
        2:  'Keyword',
        3:  'Ping',
        4:  'Port',
        5:  'Heartbeat'
    }
    
    for m in j['monitors']:
        content += '**Uptime ('
        content += typesToString.get( m["type"], str( m["type"] ) ) 
        content += f'):** { float( m["all_time_uptime_ratio"] ) }%\n'
        
    await ctx.message.edit( content = content )


def robert_kurwa( arg ):
    return unicodedata.normalize('NFKD', arg ).encode('utf-8', 'ignore').decode('utf-8')

illegal_keywords = [
    'eval',
    'exec',
    'getattr',
    'builtins',
    'open',
    'import',
    'token',
]

@slash.slash(
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
async def oblicz( ctx, expr : str ):
    code = robert_kurwa( expr )
    
    for cep in illegal_keywords:
        if cep in code:
            await ctx.send(f'**Nielegalny keyword:** { cep }')
            return

    await ctx.defer()

    b = ctx.bot

    if ctx.author.id != 360781251579346944:
        ctx.bot = None
    
    glbls = { **vars( base64 ), **vars( math ), 'Embed': discord.Embed }
    lcls = {'ctx': ctx, 'expr': expr }

    try:
        if expr[ 0 ] == '(': # hack
            wynik = str( await eval( code, glbls, lcls ) )
        else:
            wynik = str( eval( code, glbls, lcls ) )
        
    except Exception as e:
        ctx.bot = b
        await ctx.send(f'**Zjebałeś:** { str( e ) }')
        return
    
    ctx.bot = b
    
    if bot.http.token in wynik or bot.http.token[ ::-1 ] in wynik or 'ODMwNDIxOTE3NDc0NDg4MzUw' in wynik or 'wUzM4gDN0cDN3ETOxIDNwMDO' in wynik:
        await ctx.send(f'**Wykryto token bota w wyniku. Spierdalaj!**')
        return
    
    wynik = f'`{ expr }` = { wynik }'
    
    try:
        if len( wynik ) <= 2000:
            await ctx.send( wynik )
            
        elif len( wynik ) <= ctx.guild.filesize_limit:
            await ctx.send( file = discord.File( io.BytesIO( wynik.encode() ), 'wynik.txt') )
            
        else:
            await ctx.send('**Zjebałeś:** Rozmiar wyniku przekracza limit tego serwera.')
            
    except Exception as e:
        await ctx.send(f'**Coś poszło nie tak:** { str( e ) }')

@slash.context_menu(
    target = ContextMenuType.MESSAGE,
    name = 'Oblicz',
)
async def msgmenu_oblicz( ctx ):
    if ctx.target_message.content:
        await oblicz.func( ctx, ctx.target_message.content )
    else:
        await ctx.send('**Błąd: Wiadomość bez treści**', hidden = True )

fig = Figlet()

@slash.slash(
    name = 'figlet',
    description = 'FIGlet bruh',
    options = [
        create_option(
            name = 'text',
            description = 'Tekst do wyfigletowania',
            option_type = 3,
            required = True
        )
    ]
)
async def figlet( ctx, text : str ):
    txt = robert_kurwa( text )
    msg = fig.renderText( txt ).replace('`', '\'')
    msg = '```\n' + msg[ :1992 ] + '\n```'
    await ctx.send( msg )
    
@slash.context_menu(
    target = ContextMenuType.MESSAGE,
    name = 'Figlet',
)
async def msgmenu_figlet( ctx ):
    if ctx.target_message.content:
        await figlet.func( ctx, ctx.target_message.content )
    else:
        await ctx.send('**Błąd: Wiadomość bez treści**', hidden = True )


@slash.slash( name = 'spis', description = 'Spis ludności')
async def spis( ctx ):
    await ctx.defer()

    ids = []
    names = []
    discs = []
    
    async for m in ctx.guild.fetch_members( limit = None ):
        ids.append( str( m.id ) )
        names.append( m.name )
        discs.append('#' + m.discriminator )
        
    e = discord.Embed( title = 'Spis ludności', color = discord.Color.blurple() )
    
    e.add_field( name = 'Name', value = '\n'.join( names ), inline = True )
    e.add_field( name = 'Discriminator', value = '\n'.join( discs ), inline = True )
    e.add_field( name = 'ID', value = '\n'.join( ids ), inline = True )
    
    icon = str( ctx.guild.icon_url )
    icon = icon[ :icon.find('?') ] + '?size=32' # ?size=*   => ?size=32
    
    e.set_footer( text = ctx.guild.name, icon_url = icon )
    
    await ctx.send( embed = e )
    
@slash.slash( name = 'ryj', description = 'Wysyła losowy ryj')
async def ryj( ctx ):
    await ctx.defer()
    
    async with aiohttp.ClientSession() as s:
        async with s.get('https://thispersondoesnotexist.com/image') as r:
            if r.ok:
                await ctx.send( file = discord.File( io.BytesIO( await r.read() ), 'ryj.jpg') )
                
            else:
                await ctx.send('**Coś poszło nie tak**')

def make_safe_filename( s ):
    return ''.join( ( c if c.isalnum() or c == '.' else '_') for c in s )

@slash.slash(
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
async def img( ctx, q : str ):
    await ctx.defer()

    try:
        async with aiohttp.ClientSession( headers = {'User-Agent': 'degenerat-bot/2137'} ) as s:
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
                        files.append( discord.File( io.BytesIO( await r.read() ), f'{ make_safe_filename( q ) }{ k }.jpg') )
                    
        
        await ctx.send( files = files )
        
    except Exception as e:
        await ctx.send(f'**Coś poszło nie tak:** { str( e ) }')

@slash.context_menu(
    target = ContextMenuType.MESSAGE,
    name = 'Image Search',
)
async def msgmenu_img( ctx ):
    if ctx.target_message.content:
        await img.func( ctx, ctx.target_message.content )
    else:
        await ctx.send('**Błąd: Wiadomość bez treści**', hidden = True )

@slash.slash( name = 'ttt', description = 'Kółko i krzyżyk')
async def ttt( ctx ):
    components = []

    for i in range( 3 ):
        buttons = []
        
        for j in range( 3 ):
            buttons.append( create_button( style = ButtonStyle.blue, label = '---', custom_id = f'ttt{ i * 3 + j }') )
        
        components.append( create_actionrow( *buttons ) )

    await ctx.send('Ruch: krzyżyk', components = components )

async def ttt_click( ctx ):
    id = int( ctx.custom_id[ 3 ] ) # ttt4 => 4
    i = int( id / 3 )
    j = id % 3

    components = ctx.origin_message.components
 
    button = components[ i ]['components'][ j ]
    button['disabled'] = True
    button['style'] = ButtonStyle.grey
    
    content = ctx.origin_message.content
    
    if content == 'Ruch: krzyżyk':
        button['label'] = '❌'
        content = 'Ruch: kółko'
        
    elif content == 'Ruch: kółko':
        button['label'] = '⭕'
        content = 'Ruch: krzyżyk'
    
    result = ttt_check_win( components )
    if result:
        winner = 'krzyżyk' if result['win'] == 1 else 'kółko'
        content = 'Wygrywa: ' + winner
        
        for i in range( 3 ):
            for j in range( 3 ):
                components[ i ]['components'][ j ]['disabled'] = True
                components[ i ]['components'][ j ]['style'] = ButtonStyle.grey

        for i in result['buttons']:
            components[ i[ 0 ] ]['components'][ i[ 1 ] ]['style'] = ButtonStyle.green
            
    elif ttt_check_stale( components ):
        content = 'Koniec gry - remis'
    
    await ctx.edit_origin( content = content, components = components )

def ttt_check_stale( components ):
    for i in range( 3 ):
        for j in range( 3 ):
            if not components[ i ]['components'][ j ].get('disabled', False ):
                return False
                
    return True

def ttt_check_win( components ):
    if (
        components[ 0 ]['components'][ 0 ]['label'] == '❌'
        and components[ 0 ]['components'][ 1 ]['label'] == '❌'
        and components[ 0 ]['components'][ 2 ]['label'] == '❌'
    ):
        return {'win': 1, 'buttons': ( (0,0) , (0,1) , (0,2) ) }
        
    if (
        components[ 1 ]['components'][ 0 ]['label'] == '❌'
        and components[ 1 ]['components'][ 1 ]['label'] == '❌'
        and components[ 1 ]['components'][ 2 ]['label'] == '❌'
    ):
        return {'win': 1, 'buttons': ( (1,0) , (1,1) , (1,2) ) }
    
    if (
        components[ 2 ]['components'][ 0 ]['label'] == '❌'
        and components[ 2 ]['components'][ 1 ]['label'] == '❌'
        and components[ 2 ]['components'][ 2 ]['label'] == '❌'
    ):
        return {'win': 1, 'buttons': ( (2,0) , (2,1) , (2,2) ) }
        
    if (
        components[ 0 ]['components'][ 0 ]['label'] == '❌'
        and components[ 1 ]['components'][ 0 ]['label'] == '❌'
        and components[ 2 ]['components'][ 0 ]['label'] == '❌'
    ):
        return {'win': 1, 'buttons': ( (0,0) , (1,0) , (2,0) ) }
        
    if (
        components[ 0 ]['components'][ 1 ]['label'] == '❌'
        and components[ 1 ]['components'][ 1 ]['label'] == '❌'
        and components[ 2 ]['components'][ 1 ]['label'] == '❌'
    ):
        return {'win': 1, 'buttons': ( (0,1) , (1,1) , (2,1) ) }
        
    if (
        components[ 0 ]['components'][ 2 ]['label'] == '❌'
        and components[ 1 ]['components'][ 2 ]['label'] == '❌'
        and components[ 2 ]['components'][ 2 ]['label'] == '❌'
    ):
        return {'win': 1, 'buttons': ( (0,2) , (1,2) , (2,2) ) }
        
    if (
        components[ 0 ]['components'][ 0 ]['label'] == '❌'
        and components[ 1 ]['components'][ 1 ]['label'] == '❌'
        and components[ 2 ]['components'][ 2 ]['label'] == '❌'
    ):
        return {'win': 1, 'buttons': ( (0,0) , (1,1) , (2,2) ) }
        
    if (
        components[ 0 ]['components'][ 2 ]['label'] == '❌'
        and components[ 1 ]['components'][ 1 ]['label'] == '❌'
        and components[ 2 ]['components'][ 0 ]['label'] == '❌'
    ):
        return {'win': 1, 'buttons': ( (0,2) , (1,1) , (2,0) ) }
        
        
        
    if (
        components[ 0 ]['components'][ 0 ]['label'] == '⭕'
        and components[ 0 ]['components'][ 1 ]['label'] == '⭕'
        and components[ 0 ]['components'][ 2 ]['label'] == '⭕'
    ):
        return {'win': 2, 'buttons': ( (0,0) , (0,1) , (0,2) ) }
        
    if (
        components[ 1 ]['components'][ 0 ]['label'] == '⭕'
        and components[ 1 ]['components'][ 1 ]['label'] == '⭕'
        and components[ 1 ]['components'][ 2 ]['label'] == '⭕'
    ):
        return {'win': 2, 'buttons': ( (1,0) , (1,1) , (1,2) ) }
    
    if (
        components[ 2 ]['components'][ 0 ]['label'] == '⭕'
        and components[ 2 ]['components'][ 1 ]['label'] == '⭕'
        and components[ 2 ]['components'][ 2 ]['label'] == '⭕'
    ):
        return {'win': 2, 'buttons': ( (2,0) , (2,1) , (2,2) ) }
        
    if (
        components[ 0 ]['components'][ 0 ]['label'] == '⭕'
        and components[ 1 ]['components'][ 0 ]['label'] == '⭕'
        and components[ 2 ]['components'][ 0 ]['label'] == '⭕'
    ):
        return {'win': 2, 'buttons': ( (0,0) , (1,0) , (2,0) ) }
        
    if (
        components[ 0 ]['components'][ 1 ]['label'] == '⭕'
        and components[ 1 ]['components'][ 1 ]['label'] == '⭕'
        and components[ 2 ]['components'][ 1 ]['label'] == '⭕'
    ):
        return {'win': 2, 'buttons': ( (0,1) , (1,1) , (2,1) ) }
        
    if (
        components[ 0 ]['components'][ 2 ]['label'] == '⭕'
        and components[ 1 ]['components'][ 2 ]['label'] == '⭕'
        and components[ 2 ]['components'][ 2 ]['label'] == '⭕'
    ):
        return {'win': 2, 'buttons': ( (0,2) , (1,2) , (2,2) ) }
        
    if (
        components[ 0 ]['components'][ 0 ]['label'] == '⭕'
        and components[ 1 ]['components'][ 1 ]['label'] == '⭕'
        and components[ 2 ]['components'][ 2 ]['label'] == '⭕'
    ):
        return {'win': 2, 'buttons': ( (0,0) , (1,1) , (2,2) ) }
        
    if (
        components[ 0 ]['components'][ 2 ]['label'] == '⭕'
        and components[ 1 ]['components'][ 1 ]['label'] == '⭕'
        and components[ 2 ]['components'][ 0 ]['label'] == '⭕'
    ):
        return {'win': 2, 'buttons': ( (0,2) , (1,1) , (2,0) ) }
    
    return False

@slash.component_callback()
async def ttt0( ctx ):
    await ttt_click( ctx )
@slash.component_callback()
async def ttt1( ctx ):
    await ttt_click( ctx )
@slash.component_callback()
async def ttt2( ctx ):
    await ttt_click( ctx )
@slash.component_callback()
async def ttt3( ctx ):
    await ttt_click( ctx )
@slash.component_callback()
async def ttt4( ctx ):
    await ttt_click( ctx )
@slash.component_callback()
async def ttt5( ctx ):
    await ttt_click( ctx )
@slash.component_callback()
async def ttt6( ctx ):
    await ttt_click( ctx )
@slash.component_callback()
async def ttt7( ctx ):
    await ttt_click( ctx )
@slash.component_callback()
async def ttt8( ctx ):
    await ttt_click( ctx )
    

#
#   MUSIC   
#

async def get_voice_client_for_channel( ch : discord.VoiceChannel, stop_playing = False ):
    vc = [ a for a in bot.voice_clients if a.channel.guild == ch.guild ]
    vc = vc[ 0 ] if len( vc ) else None
    
    if vc:
        if vc.channel != ch:
            await vc.move_to( ch )

        if stop_playing and vc.is_playing():
            vc.stop()
            
    else:
        vc = await ch.connect()
        
    return vc

class MusicQueue:
    def __init__( self, voice_channel, message_channel ):
        self.voice_channel = voice_channel
        self.message_channel = message_channel
        
        self.vc = None
        
        self._entries = []
        self._cleared = True
        
    def add_entry( self, entry ):
        self._cleared = False
        self._entries.append( entry )
        
    @property
    def num_entries( self ):
        return len( self._entries )
        
    @property
    def empty( self ):
        return self._cleared or ( self.vc is not None and not self.vc.is_playing() and not self.vc.is_paused() )
        
    @property
    def entries( self ):
        return [ entry.title for entry in self._entries ]

    def remove( self, index ):
        if index >= 0 and index < len( self._entries ):
            entry = self._entries.pop( index )
            entry.cleanup()
            
    def get_next( self ):
        return self._entries.pop( 0 ) if len( self._entries ) > 0 else None
        
    def clear( self ):
        self._cleared = True
        
        for entry in self._entries:
            entry.cleanup()
                
        self._entries = []
        
    @property
    def cleared( self ):
        return self._cleared

class MusicQueueEntry:
    def __init__( self, title, audio_source, message, after = None ):
        self.title = title
        self.audio_source = audio_source
        self.message = message
        self.after = after
        
    def cleanup( self ):  
        if self.audio_source is not None:
            self.audio_source.cleanup()
            
        if self.after is not None:
            self.after( None )

musicQueues = {}

def is_url( x ):
    try:
        result = urlparse( x )
        return all( [ result.scheme, result.netloc ] )
        
    except:
        return False

@slash.slash(
    name = 'play',
    description = 'Odtwarza muzykę w twoim kanale głosowym',
    options = [
        create_option(
            name = 'q',
            description = 'Search query/URL',
            option_type = 3,
            required = True
        )
    ]
)
async def play( ctx, q : str ):
    ch = ctx.author.voice.channel if ctx.author.voice != None else None

    if ch == None:
        await ctx.send('**Musisz być połączony z kanałem głosowym**', hidden = True )
        return
        
    await ctx.defer()

    queue = musicQueues.get( ctx.guild.id, None )

    if queue is None:
        queue = MusicQueue( ch, ctx.channel )

        musicQueues[ ctx.guild.id ] = queue
        
    elif queue.message_channel != ctx.channel or queue.voice_channel != ch:
        queue.message_channel = ctx.channel
        queue.voice_channel = ch

    if is_url( q ):
        if q.startswith('https://www.youtube.com/watch?v=') or q.startswith('https://youtu.be/'):
            async with aiohttp.ClientSession() as s:
                await queue_youtube( ctx, queue, q, s )

        else: # arbitrary url
            audio = discord.FFmpegPCMAudio( q )
            e = discord.Embed( description = q, color = discord.Color.blurple() )
            e.title = 'Odtwarzanie' if queue.empty else 'Dodano do kolejki'
            
            msg = await ctx.send( embed = e )
            
            entry = MusicQueueEntry( q, audio, msg )
            queue.add_entry( entry )
            

    else: # Search query
        e = discord.Embed( description = f'Wyszukiwanie `{ q }`...', color = discord.Color.blurple() )

        await ctx.send( embed = e )
        
        async with aiohttp.ClientSession( headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'} ) as s:
            async with s.get('https://www.youtube.com/results', params = {'search_query': q } ) as r:
                if not r.ok:
                    await ctx.message.edit( content = f'**Coś poszło nie tak:** { r.status }')
                    return
                    
                text = await r.text()
                
            at = text.find('/watch?v=')
            if at == -1:
                e = discord.Embed( description = f'Brak wyników wyszukiwania dla: `{ q }`', color = discord.Color.blurple() )
                
                await ctx.message.edit( embed = e )
                return
            
            url = 'https://www.youtube.com' + text[ at:at + 20 ]
            
            await queue_youtube( ctx, queue, url, s )
            
@slash.context_menu(
    target = ContextMenuType.MESSAGE,
    name = 'Dodaj do kolejki',
)
async def msgmenu_play( ctx ):
    if ctx.target_message.content:
        await play.func( ctx, ctx.target_message.content )
    elif ctx.target_message.embeds and ctx.target_message.embeds[0].description:
        await play.func( ctx, ctx.target_message.embeds[0].description )
    else:
        await ctx.send('**Błąd: Wiadomość bez treści**', hidden = True )

async def queue_youtube( ctx, queue, url, session = None ):
    reply = ctx.message.edit if ctx.message else ctx.send

    try:
        yt = YouTube( url, session = session )
        
    except Exception as e:
        await reply( content = str( e ) )
        return

    title = await yt.title

    try:
        s = await yt.streams
        if len( s ) < 1:
            raise Exception()
            
        s = s.filter( type = 'audio').order_by('abr').desc()
        if len( s ) < 1:
            raise Exception()
        
    except:
        e = discord.Embed( description = f'{ title } ({ url }): **Brak dostępnych streamów audio**', color = discord.Color.blurple() )
        await reply( embed = e )
        return
    
    if len( s ) > 1:
        s = s[ -2 ]
    else:
        s = s.first()

    filesize = await s.filesize

    if filesize > 10_000_000:
        e = discord.Embed( description = f'{ title } ({ url }): **Rozmiar pliku przekracza rozsądny limit 10MB**', color = discord.Color.blurple() )
        await reply( embed = e )
        return

    e = discord.Embed( description = 'Pobierańsko...', color = discord.Color.blurple() )
    e.set_thumbnail( url = f'https://i.ytimg.com/vi/{ yt.video_id }/mqdefault.jpg')
    
    await reply( embed = e )

    errors = 0

    for i in range( 3 ):
        try:
            path = await s.download( filename = str( ctx.message.id ), skip_existing = False )
            
        except:
            print('failed to download stream')
            errors += 1
            
        else:
            break
        
    if errors == 3:
        await ctx.message.edit( content = 'Wystąpił błąd podczas pobierania pliku. (dawid to cep)')
        return
        
    after = lambda e: os.remove( path )
    
    audio = await discord.FFmpegOpusAudio.from_probe( path )
 
    e.description = title
    e.title = 'Odtwarzanie' if queue.empty else 'Dodano do kolejki'
    
    await ctx.message.edit( embed = e )
    
    entry = MusicQueueEntry( title, audio, ctx.message, after )
    queue.add_entry( entry )

@tasks.loop( seconds = 3.0 )
async def MusicQueuesUpdate():
    for guild in bot.guilds:
        queue = musicQueues.get( guild.id )
        if queue is None or queue.cleared or queue.num_entries <= 0:
            continue
            
        queue.vc = await get_voice_client_for_channel( queue.voice_channel )
        if queue.vc is None or queue.vc.is_playing() or queue.vc.is_paused():
            continue
            
        next = queue.get_next()
        if next is None: # is this possible?
            continue
            
        queue.vc.play( next.audio_source, after = next.after )
        
        msg = next.message
        e = msg.embeds[ 0 ]
        if e.title != 'Odtwarzanie':
            e.title = 'Odtwarzanie'
            if queue.message_channel.last_message_id == msg.id:
                await msg.edit( embed = e )
            else:
                await queue.message_channel.send( embed = e )

@bot.event
async def on_voice_state_update( member, before, after ):
    if member.id != bot.user.id:
        return
    
    if after.channel != before.channel:
        if before.channel == None: # joined voice channel
            print(f'joined { after.channel }')
            
        elif after.channel == None: # left voice channel
            print(f'left { before.channel }')
            
            queue = musicQueues.get( before.channel.guild.id )
            if queue is not None:
                queue.clear()
            
        else: # moved to other channel
            print(f'moved to { after.channel }')

@slash.slash( name = 'disconnect', description = 'Rozłącza bota od kanału głosowego')
async def disconnect( ctx ):
    for vc in bot.voice_clients:
        if vc.channel.guild == ctx.guild:
            await vc.disconnect()
            await ctx.send(':wave:')
            return

    await ctx.send('**Nie połączono**', hidden = True )

@slash.slash( name = 'pause', description = 'Pauzuje odtwarzanie muzyki')
async def pause( ctx ):
    for vc in bot.voice_clients:
        if vc.channel.guild == ctx.guild:
            vc.pause()
            await ctx.send(':ok_hand:')
            return

    await ctx.send('**Nie połączono**', hidden = True )
    
@slash.slash( name = 'resume', description = 'Wznawia odtwarzanie muzyki')
async def resume( ctx ):
    for vc in bot.voice_clients:
        if vc.channel.guild == ctx.guild:
            vc.resume()
            await ctx.send(':ok_hand:')
            return

    await ctx.send('**Nie połączono**', hidden = True )
    
@slash.slash( name = 'stop', description = 'Zakańcza odtwarzanie muzyki i czyści kolejkę')
async def stop( ctx ):
    for vc in bot.voice_clients:
        if vc.channel.guild == ctx.guild:
            queue = musicQueues.get( ctx.guild.id )
            if queue is not None:
                queue.clear()
        
            vc.stop()
            await ctx.send(':ok_hand:')
            return

    await ctx.send('**Nie połączono**', hidden = True )

@slash.slash( name = 'clear', description = 'Czyści kolejkę')
async def clear( ctx ):
    queue = musicQueues.get( ctx.guild.id )
    if queue is not None:
        queue.clear()

    await ctx.send(':ok_hand:')
    
@slash.slash( name = 'skip', description = 'Pomija aktualnie odtwarzany element kolejki')
async def skip( ctx ):
    for vc in bot.voice_clients:
        if vc.channel.guild == ctx.guild:
            vc.stop()
            await ctx.send(':ok_hand:')
            return

    await ctx.send('**Nie połączono**', hidden = True )
    
@slash.slash( name = 'queue', description = 'Wyświetla zawartość kolejki')
async def queue( ctx ):
    queue = musicQueues.get( ctx.guild.id )
    if queue is None:
        await ctx.send('**Brak kolejki**', hidden = True )
        return

    if queue.num_entries < 1:
        await ctx.send('**W kolejce pusto jak w głowie Jacka**', hidden = True )
        return

    e = discord.Embed( title = 'Kolejka', color = discord.Color.blurple() )
    
    e.add_field( inline = True, name = '#', value = '\n'.join( [ str( n + 1 ) for n in range( queue.num_entries ) ] ) )
    e.add_field( inline = True, name = 'Tytuł', value = '\n'.join( queue.entries ) )
    
    await ctx.send( embed = e )

@slash.slash(
    name = 'remove',
    description = 'Usuwa pozycję z kolejki',
    options = [
        create_option(
            name = 'pos',
            description = 'Element kolejki',
            option_type = 4,
            required = True
        )
    ]
)
async def remove( ctx, pos : int ):
    queue = musicQueues.get( ctx.guild.id )
    if queue is None:
        await ctx.send('**Brak kolejki**', hidden = True )
        return

    if queue.num_entries < 1:
        await ctx.send('**W kolejce pusto jak w głowie Jacka**', hidden = True )
        return
        
    if pos < 1 or pos > queue.num_entries:
        await ctx.send('**Nieprawidłowy element kolejki**', hidden = True )
        return
    
    queue.remove( pos - 1 )
    
    await ctx.send(':ok_hand:')

@slash.slash( name = 'ping', description = 'Test bota')
async def ping( ctx ):
    await ctx.send(f'**Pong!** Latency: { math.floor( bot.latency * 1000 ) } ms')


activities = [
    discord.Game('tomb rajder'),
    discord.Game('Hentai Nazi'),
    discord.Game('Ventti z Drabikiem'),
    
    discord.Activity( type = discord.ActivityType.watching, name = 'niemieckie porno'),
    discord.Activity( type = discord.ActivityType.watching, name = 'mcskelli.tk/item4.html'),
    discord.Activity( type = discord.ActivityType.watching, name = 'fish spinning for 68 years'),
    discord.Activity( type = discord.ActivityType.watching, name = 'jak bartek sra'),
    discord.Activity( type = discord.ActivityType.watching, name = 'bartek walking meme.mp4'),
    
    discord.Activity( type = discord.ActivityType.listening, name = 'Young Leosia - Jungle Girl'),
    discord.Activity( type = discord.ActivityType.listening, name = 'Young Leosia - Szklanki'),
    discord.Activity( type = discord.ActivityType.listening, name = 'Dream - Mask (Sus Remix)'),
    discord.Activity( type = discord.ActivityType.listening, name = 'loud indian 10h bass boosted'),
    discord.Activity( type = discord.ActivityType.listening, name = 'loud arabic'),
]

@tasks.loop( seconds = 10.0 )
async def UpdateActivityStatus():
    me = bot.guilds[ 0 ].me
    if me is None:
        return
    
    while True:
        activity = random.choice( activities )
        
        if activity != me.activity:
            break

    await bot.change_presence( activity = activity )


try:
    bot.run( base64.b64decode( os.environ["cep"].encode() ).decode() )
    
except:
    raise
    
finally:
    print('\nCleanup')

    for q in musicQueues.values():
        q.clear()
        
    sys.exit()