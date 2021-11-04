import logging
logging.basicConfig( level = logging.INFO )
_log = logging.getLogger( __name__ )

from discord import Intents
from discord.ext.commands import Bot
from discord_slash import SlashCommand

from base64 import b64decode
from os import environ
from sys import exit

bot = Bot( command_prefix = ',', help_command = None, intents = Intents.all() )
slash = SlashCommand( bot )

@bot.event
async def on_ready():
    _log.info(f'Logged in as "{ str( bot.user ) }"')
    
    # set all commands' guilds_ids and then sync
    guild_ids = [ g.id for g in bot.guilds ]
    for name in slash.commands:
        if name == "context":
            for _name in slash.commands["context"]:
                cmd = slash.commands["context"][ _name ]
                cmd.allowed_guild_ids = guild_ids
    
            continue
            
        cmd = slash.commands[ name ]
        cmd.allowed_guild_ids = guild_ids
    
    await slash.sync_all_commands()

@bot.event
async def on_guild_join( guild ):
    _log.info(f'Joined guild "{ str( guild ) }"')
    
    await slash.sync_all_commands()

def main():
    try:
        bot.load_extension("modules.stoi")
        bot.load_extension("modules.activities")
        bot.load_extension("modules.figlet")
        bot.load_extension("modules.oblicz")
        #bot.load_extension("modules.ping") # replaced by status
        bot.load_extension("modules.cow")
        bot.load_extension("modules.react")
        bot.load_extension("modules.spis")
        bot.load_extension("modules.img")
        bot.load_extension("modules.ryj")
        bot.load_extension("modules.ttt")
        bot.load_extension("modules.music")
        bot.load_extension("modules.status")
        bot.load_extension("modules.invite")
        
        bot.run( b64decode( environ["cep"] ).decode() )
        
    except KeyboardInterrupt:
        exit()
        
if __name__ == "__main__":
    main()