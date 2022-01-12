from discord import Embed, Color
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from asyncssh import SSHClientConnectionOptions
from asyncssh import connect as sshconnect
from os import environ
from logging import getLogger

class Stoi( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot
        self.log = getLogger( __name__ )
        self.sshopts = SSHClientConnectionOptions(
            username = "degenerat-stoi",
            password = "japierdole",
            known_hosts = None,
            login_timeout = 5
        )

    def get_duration_str( self, seconds: int ) -> str:
        days, r = divmod( seconds, 86400 )
        hours, r = divmod( r, 3600 )
        mins, secs = divmod( r, 60 )
        
        dur = ''
        
        if days:
            dur += f'{ days }d '
        
        if hours or days:
            dur += f'{ hours }h '
            
        if mins or hours or days:
            dur += f'{ mins }m '
        
        if secs or mins or hours or days:
            dur += f'{ secs }s'

        return dur

    @cog_ext.cog_slash(
        name = 'stoi',
        description = 'Sprawdza czy debil stoi',
        guild_ids = [ 655112863391940618, 751455317568651294, 598112506338344973 ] # jfl, ex, cmg
    )
    async def _stoi( self, ctx: SlashContext ):
        await ctx.defer()

        e = Embed()
        content = ""

        try:
            async with sshconnect('62.122.235.235', port = 2200, options = self.sshopts ) as _:
                e.color = Color.green()
                e.title = '**Tak :white_check_mark:**'
        
        except:
            e.color = Color.red()
            e.title = '**Nie :x:**'
            
            if ctx.guild.get_member( 911698452457611334 ):
                content = '<@911698452457611334> :exclamation:'
        
        finally:
            await ctx.send( content, embed = e )

        typesToString = {
            1:  'HTTP',
            2:  'Keyword',
            3:  'Ping',
            4:  'Port',
            5:  'Heartbeat'
        }
        
        async with self.bot.http._HTTPClient__session.post('https://api.uptimerobot.com/v2/getMonitors', data = f'api_key={ environ["UPTIME_TOKEN"] }&format=json&logs=1', headers = {'content-type':'application/x-www-form-urlencoded','cache-control':'no-cache'} ) as r:
            if not r.ok:
                return
                
            j = await r.json()
            
        if j['stat'] != 'ok':
            self.log.error( j )
            return

        for m in j['monitors']:
            typ = typesToString.get( m["type"], str( m["type"] ) )
            status = m['logs'][0]['reason']['detail']
            
            dur = m['logs'][0]['duration']
            
            dur = self.get_duration_str( dur )
            
            e.add_field( name = typ, value = f'**{ status }** - { dur }', inline = False )
        
        e.description = '_ _'
        
        await ctx.message.edit( embed = e )

def setup( bot: Bot ):
    bot.add_cog( Stoi( bot ) )