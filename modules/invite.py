from discord import Embed
from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext
from discord_slash.utils.manage_components import create_button, create_actionrow
from discord_slash.model import ButtonStyle

class Invite( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot
        
    @cog_ext.cog_slash(
        name = 'invite',
        description = 'Zaproszenie bota'
    )
    async def _invite( self, ctx: SlashContext ):
        link = 'https://discord.com/api/oauth2/authorize?client_id=830421917474488350&permissions=34371529792&scope=applications.commands%20bot'
    
        components = [ create_actionrow( create_button( style = ButtonStyle.URL, label = "Invite", url = link ) ) ]
    
        await ctx.send( content = '_ _', components = components )

def setup( bot: Bot ):
    bot.add_cog( Invite( bot ) )