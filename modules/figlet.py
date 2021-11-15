from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.model import ContextMenuType, AutocompleteOptionData
from discord_slash.context import SlashContext, MenuContext, AutocompleteContext
from discord_slash.utils.manage_commands import create_option
from discord_slash.utils.manage_commands import create_choice
from typing import Union
from unicodedata import normalize
from pyfiglet import Figlet as Fig

class Figlet( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot
        self.figlet = Fig()
        
        self.autocomplete = [
            "Bartek to huj",
            "Bartek to gej",
        ]

    @cog_ext.cog_slash(
        name = 'figlet',
        description = 'FIGlet bruh',
        options = [
            create_option(
                name = 'text',
                description = 'Tekst do wyfigletowania',
                option_type = 3,
                required = True,
                autocomplete = True
            )
        ]
    )
    async def _figlet( self, ctx: Union[ SlashContext, MenuContext ], text: str ):
        txt = normalize('NFKD', text ).encode('utf-8', 'ignore').decode('utf-8')
        msg = self.figlet.renderText( txt ).replace('`', '\'')
        msg = '```\n' + msg[ :1992 ] + '\n```'
        await ctx.send( msg )
        
    @cog_ext.cog_context_menu(
        name = 'Figlet',
        target = ContextMenuType.MESSAGE
    )
    async def _figlet_context( self, ctx: MenuContext ):
        if ctx.target_message.content:
            await self._figlet.func( self, ctx, ctx.target_message.content )
        else:
            await ctx.send('**Błąd: Wiadomość bez treści**', hidden = True )
            
    @cog_ext.cog_autocomplete(
        name = 'figlet'
    )
    async def _figlet_autocomplete( self, ctx: AutocompleteContext, options: dict[str, AutocompleteOptionData] ):
        choices = []

        text = options["text"].value
        if text:
            for a in self.autocomplete:
                if a.lower().startswith( text.lower() ):
                    choices.append( create_choice( name = a, value = a ) )
            
        await ctx.send( choices )

def setup( bot: Bot ):
    bot.add_cog( Figlet( bot ) )