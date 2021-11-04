from discord import Embed
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from time import time, perf_counter

class Status( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot

    @Cog.listener()
    async def on_ready( self ):
        self.start_time = round(time())

    @cog_ext.cog_slash(
        name = 'status',
        description = 'Status bota'
    )
    async def _status( self, ctx: SlashContext ):
        start = perf_counter()
        await ctx.send("_ _")
        end = perf_counter()
        res_time = end - start
        
        e = Embed( title = "Status Bota", color = ctx.me.color )
        e.add_field( name = "Uruchomiony", value = f"<t:{self.start_time}:R>", inline = False )
        
        e.add_field( name = "Opóźnienie Websocketa", value = f"{round( self.bot.latency * 1000 )} ms", inline = True )
        e.add_field( name = "Czas odpowiedzi", value = f"{round( res_time * 1000 )} ms", inline = True )
        
        e.add_field( name = "Aktywne Cogi", value = "\n".join( [ ":small_blue_diamond:"+a for a in self.bot.cogs ] ), inline = False )

        e.set_footer( text = "Degenerat Bot | GitHub: drobotk/degenerat-bot")

        await ctx.message.edit( content = None, embed = e )

def setup( bot: Bot ):
    bot.add_cog( Status( bot ) )