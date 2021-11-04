from discord import Embed, Color
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext

class Spis( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot

    @cog_ext.cog_slash(
        name = 'spis',
        description = 'Spis ludności'
    )
    async def _spis( self, ctx: SlashContext ):
        ids = []
        names = []
        discs = []
        
        async for m in ctx.guild.fetch_members( limit = None ):
            ids.append( str( m.id ) )
            names.append( m.name )
            discs.append('#' + m.discriminator )
            
        e = Embed( title = 'Spis Ludności', color = ctx.me.color )
        
        e.add_field( name = 'Name', value = '\n'.join( names ), inline = True )
        e.add_field( name = 'Discriminator', value = '\n'.join( discs ), inline = True )
        e.add_field( name = 'ID', value = '\n'.join( ids ), inline = True )
        
        icon = str( ctx.guild.icon_url )
        icon = icon[ :icon.find('?') ] + '?size=32' # ?size=*   => ?size=32
        
        e.set_footer( text = ctx.guild.name, icon_url = icon )
        
        await ctx.send( embed = e )

def setup( bot: Bot ):
    bot.add_cog( Spis( bot ) )