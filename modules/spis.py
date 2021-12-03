from discord import Embed, Color
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext

# TODO

class PaginationView:
    def __init__( self, pages: list[Embed] ):
        self.components = []
        self.pages = pages
        self.current = 0

    def next

class Spis( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot

    @cog_ext.cog_slash(
        name = 'spis',
        description = 'Spis ludności'
    )
    async def _spis( self, ctx: SlashContext ):
        e = Embed( title = 'Spis Ludności', color = ctx.me.color )
        icon = str( ctx.guild.icon_url )
        icon = icon[ :icon.find('?') ] + '?size=32' # ?size=*   => ?size=32
        e.set_footer( text = ctx.guild.name, icon_url = icon )
    
        names = ''
        discs = ''
        ids = ''
        
        for i, m in enumerate( ctx.guild.members ):
            if ( 
                len( ids + str( m.id ) ) > 1024
                or len( names + m.name ) > 1024
                or len( discs + m.discriminator ) > 1024
            ):
                break
        
            names += m.name + '\n'
            discs += m.discriminator + '\n'
            ids += str( m.id ) + '\n'
        
        
        
        e.add_field( name = 'Name', value = names.strip("\n"), inline = True )
        e.add_field( name = 'Discriminator', value = discs.strip("\n"), inline = True )
        e.add_field( name = 'ID', value = ids.strip("\n"), inline = True )
        
        await ctx.send( embed = e )

    @cog_ext.cog_component(
        use_callback_name = False,
        components = ["_spis_prev", "_spis_next"]
    )
    async def _spis_click( self, ctx: ComponentContext ):
        pass

def setup( bot: Bot ):
    bot.add_cog( Spis( bot ) )