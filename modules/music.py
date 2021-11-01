from discord import Embed, Color, VoiceChannel, VoiceClient, TextChannel, Member
from discord import AudioSource, Message, FFmpegPCMAudio, FFmpegOpusAudio, VoiceState
from discord.ext.commands import Bot, Cog
from discord.ext.tasks import loop
from discord_slash import cog_ext
from discord_slash.model import ContextMenuType
from discord_slash.context import SlashContext, MenuContext
from discord_slash.utils.manage_commands import create_option
from typing import Union, Callable, Any
from aiohttp import ClientSession
from urllib.parse import urlparse
from pytube import YouTube
from os import remove as osremove

class MusicQueueEntry:
    def __init__( self, title: str, audio_source: AudioSource, message: Message, after: Callable[[Exception], Any] = None ):
        self.title = title
        self.audio_source = audio_source
        self.message = message
        self.after = after
        
    def cleanup( self ):  
        if self.audio_source is not None:
            self.audio_source.cleanup()
            
        if self.after is not None:
            self.after( None )

class MusicQueue:
    def __init__( self, voice_channel: VoiceChannel, message_channel: TextChannel ):
        self.voice_channel = voice_channel
        self.message_channel = message_channel
        
        self.vc: VoiceClient = None
        
        self._entries = []
        self._cleared = True
        
    def add_entry( self, entry: MusicQueueEntry ):
        self._cleared = False
        self._entries.append( entry )
        
    @property
    def num_entries( self ) -> int:
        return len( self._entries )
        
    @property
    def empty( self ) -> bool:
        return self._cleared or ( self.vc is not None and not self.vc.is_playing() and not self.vc.is_paused() )
        
    @property
    def entries( self ) -> list[ str ]:
        return [ entry.title for entry in self._entries ]

    def remove( self, index: int ):
        if index >= 0 and index < len( self._entries ):
            entry = self._entries.pop( index )
            entry.cleanup()
            
    def get_next( self ) -> MusicQueueEntry:
        return self._entries.pop( 0 ) if len( self._entries ) > 0 else None
        
    def clear( self ):
        self._cleared = True
        
        for entry in self._entries:
            entry.cleanup()
                
        self._entries = []
        
    @property
    def cleared( self ) -> bool:
        return self._cleared

class Music( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot
        
        self.queues: dict[int, MusicQueue] = {}

    @Cog.listener()
    async def on_ready( self ):
        if not self.update.is_running():
            self.update.start()
            
    def cog_unload( self ):
        self.update.cancel()
        
        for q in self.queues.values():
            q.clear()
            
    async def get_voice_client_for_channel( self, ch: VoiceChannel, stop_playing: bool = False ) -> VoiceClient:
        vc = ch.guild.voice_client
        
        if vc:
            if vc.channel != ch:
                await vc.move_to( ch )

            if stop_playing and vc.is_playing():
                vc.stop()
                
        else:
            vc = await ch.connect()
            
        return vc
        
    def is_url( self, x: str ) -> bool:
        try:
            result = urlparse( x )
            return all( [ result.scheme, result.netloc ] )
            
        except:
            return False

    def extract_yt_url( self, text: str ) -> bool:
        at = text.find('/watch?v=')
        if at > -1:
            return 'https://www.youtube.com' + text[ at:at+20 ]
        
        at = text.find('youtu.be/')
        if at > -1:
            return 'https://www.youtube.com/watch?v=' + text[ at+9:at+20 ]
            
    @cog_ext.cog_slash(
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
    async def _play( self, ctx: Union[ SlashContext, MenuContext ], q: str ):
        ch = ctx.author.voice.channel if ctx.author.voice is not None else None

        if ch == None:
            await ctx.send('**Musisz być połączony z kanałem głosowym**', hidden = True )
            return
            
        await ctx.defer()

        queue = self.queues.get( ctx.guild.id, None )

        if queue is None:
            queue = MusicQueue( ch, ctx.channel )

            self.queues[ ctx.guild.id ] = queue
            
        elif queue.message_channel != ctx.channel or queue.voice_channel != ch:
            queue.message_channel = ctx.channel
            queue.voice_channel = ch

        if self.is_url( q ):
            if q.startswith('https://www.youtube.com/watch?v=') or q.startswith('https://youtu.be/'):
                async with ClientSession() as s:
                    await self.queue_youtube( ctx, queue, q, s )

            else: # arbitrary url
                audio = FFmpegPCMAudio( q )
                e = Embed( description = q, color = Color.blurple() )
                e.title = 'Odtwarzanie' if queue.empty else 'Dodano do kolejki'
                
                msg = await ctx.send( embed = e )
                
                entry = MusicQueueEntry( q, audio, msg )
                queue.add_entry( entry )

        else: # Search query
            e = Embed( description = f'Wyszukiwanie `{ q }`...', color = Color.blurple() )

            await ctx.send( embed = e )
            
            async with ClientSession( headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:91.0) Gecko/20100101 Firefox/91.0'} ) as s:
                async with s.get('https://www.youtube.com/results', params = {'search_query': q } ) as r:
                    if not r.ok:
                        await ctx.message.edit( content = f'**Coś poszło nie tak:** { r.status }')
                        return
                        
                    text = await r.text()
                
                url = self.extract_yt_url( text )
                if not url:
                    e = Embed( description = f'Brak wyników wyszukiwania dla: `{ q }`', color = Color.red() )
                    
                    await ctx.message.edit( embed = e )
                    return

                await self.queue_youtube( ctx, queue, url, s )
                
    @cog_ext.cog_context_menu(
        name = 'Dodaj do kolejki',
        target = ContextMenuType.MESSAGE
    )
    async def _play_context( self, ctx: MenuContext ):
        if ctx.target_message.content:
            url = self.extract_yt_url( ctx.target_message.content )
            await self._play.func( self, ctx, url or ctx.target_message.content )

        elif ctx.target_message.embeds:
            e = ctx.target_message.embeds[0]
            text = str( e.to_dict() )
            
            url = self.extract_yt_url( text )
            if url:
                await self._play.func( self, ctx, url )

            elif e.description or e.title:
                await self._play.func( self, ctx, e.description or e.title )

        else:
            await ctx.send('**Błąd: Nie wykryto pasującej treści**', hidden = True )

    async def queue_youtube( self, ctx: Union[ SlashContext, MenuContext ], queue: MusicQueue, url: str, session: ClientSession = None ):
        reply = ctx.message.edit if ctx.message else ctx.send

        try:
            yt = YouTube( url, session = session )
            title = await yt.title
            
        except Exception as e:
            await reply( content = str( e ) )
            return

        try:
            s = await yt.streams
            if len( s ) < 1:
                raise Exception()
                
            s = s.filter( type = 'audio').order_by('abr').desc()
            if len( s ) < 1:
                raise Exception()
            
        except:
            e = Embed( title = f'**Brak dostępnych streamów audio**', description = f'{ title }\n({ url })', color = Color.red() )
            await reply( embed = e )
            return
        
        if len( s ) > 1:
            s = s[ -2 ]
        else:
            s = s.first()

        filesize = await s.filesize

        if filesize > 10_000_000:
            e = Embed( title = f'**Rozmiar pliku przekracza rozsądny limit 10MB**', description = f'{ title }\n({ url })', color = Color.red() )
            await reply( embed = e )
            return

        e = Embed( description = 'Pobierańsko...', color = Color.blurple() )
        e.set_thumbnail( url = f'https://i.ytimg.com/vi/{ yt.video_id }/mqdefault.jpg')
        e.set_footer( text = url )
        
        await reply( embed = e )

        errors = 0

        for i in range( 3 ):
            try:
                path = await s.download( filename = str( ctx.message.id ), skip_existing = False )
                
            except:
                print('Failed to download stream')
                errors += 1
                
            else:
                break
            
        if errors == 3:
            e = Embed( title = f'**Wystąpił błąd podczas pobierania pliku**', description = f'{ title }\n({ url })', color = Color.red() )
            await ctx.message.edit( embed = e )
            return
            
        after = lambda e: osremove( path )
        
        audio = await FFmpegOpusAudio.from_probe( path )
     
        e.description = title
        e.title = 'Odtwarzanie' if queue.empty else 'Dodano do kolejki'
        
        await ctx.message.edit( embed = e )
        
        entry = MusicQueueEntry( title, audio, ctx.message, after )
        queue.add_entry( entry )

    @loop( seconds = 3.0 )
    async def update( self ):
        for guild in self.bot.guilds:
            queue = self.queues.get( guild.id )
            if queue is None or queue.cleared or queue.num_entries <= 0:
                continue
                
            queue.vc = await self.get_voice_client_for_channel( queue.voice_channel )
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

    @Cog.listener()
    async def on_voice_state_update( self, member: Member, before: VoiceState, after: VoiceState ):
        if member.id != self.bot.user.id:
            return
        
        if after.channel != before.channel:
            if before.channel == None: # joined voice channel
                print(f'Joined vc "{ after.channel }"')
                
            elif after.channel == None: # left voice channel
                print(f'Left vc "{ before.channel }"')
                
                queue = self.queues.get( before.channel.guild.id )
                if queue is not None:
                    queue.clear()
                
            else: # moved to other channel
                print(f'Moved to vc "{ after.channel }"')

    @cog_ext.cog_slash(
        name = 'disconnect',
        description = 'Rozłącza bota od kanału głosowego'
    )
    async def _disconnect( self, ctx: SlashContext ):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send('**Nie połączono**', hidden = True )
            return
            
        await vc.disconnect()
        await ctx.send(':wave:')

    @cog_ext.cog_slash(
        name = 'pause',
        description = 'Pauzuje odtwarzanie muzyki'
    )
    async def _pause( self, ctx: SlashContext ):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send('**Nie połączono**', hidden = True )
            return
            
        vc.pause()
        await ctx.send(':ok_hand:')
        
    @cog_ext.cog_slash(
        name = 'resume',
        description = 'Wznawia odtwarzanie muzyki'
    )
    async def _resume( self, ctx: SlashContext ):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send('**Nie połączono**', hidden = True )
            return
            
        vc.resume()
        await ctx.send(':ok_hand:')
        
    @cog_ext.cog_slash(
        name = 'stop',
        description = 'Zakańcza odtwarzanie muzyki i czyści kolejkę'
    )
    async def _stop( self, ctx: SlashContext ):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send('**Nie połączono**', hidden = True )
            return
        
        queue = self.queues.get( ctx.guild.id )
        if queue is not None:
            queue.clear()
        
        vc.stop()
        await ctx.send(':ok_hand:')

    @cog_ext.cog_slash(
        name = 'clear',
        description = 'Czyści kolejkę'
    )
    async def _clear( self, ctx: SlashContext ):
        queue = self.queues.get( ctx.guild.id )
        if queue is not None:
            queue.clear()

        await ctx.send(':ok_hand:')
        
    @cog_ext.cog_slash(
        name = 'skip',
        description = 'Pomija aktualnie odtwarzany element kolejki'
    )
    async def _skip( self, ctx: SlashContext ):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send('**Nie połączono**', hidden = True )
            return
            
        vc.stop()
        await ctx.send(':ok_hand:')
        
    @cog_ext.cog_slash(
        name = 'queue',
        description = 'Wyświetla zawartość kolejki'
    )
    async def _queue( self, ctx: SlashContext ):
        queue = self.queues.get( ctx.guild.id )
        if queue is None:
            await ctx.send('**Brak kolejki**', hidden = True )
            return

        if queue.num_entries < 1:
            await ctx.send('**W kolejce pusto jak w głowie Jacka**', hidden = True )
            return

        e = Embed( title = 'Kolejka', color = Color.blurple() )
        
        e.add_field( inline = True, name = '#', value = '\n'.join( [ str( n + 1 ) for n in range( queue.num_entries ) ] ) )
        e.add_field( inline = True, name = 'Tytuł', value = '\n'.join( queue.entries ) )
        
        await ctx.send( embed = e )

    @cog_ext.cog_slash(
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
    async def _remove( self, ctx: SlashContext, pos: int ):
        queue = self.queues.get( ctx.guild.id )
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

def setup( bot: Bot ):
    bot.add_cog( Music( bot ) )