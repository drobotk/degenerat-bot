from sys import argv, exit
from discord import Intents
from discord.ext.commands import Bot
from discord_slash import SlashCommand
from base64 import b64decode
from os import environ

import logging
logging.basicConfig(
    level = logging.DEBUG if len( argv ) > 1 else logging.INFO,
    format = '%(name)s [%(levelname)s] %(message)s'
)
_log = logging.getLogger( __name__ )

bot = Bot( command_prefix = ',', help_command = None, intents = Intents.all() )
slash = SlashCommand( bot )

async def sync_commands():
    # set all commands' guilds_ids and then sync
    guild_ids = [ g.id for g in bot.guilds ]
    for name in list( slash.commands.keys() ):
        if name == "context":
            for _name in slash.commands["context"]:
                cmd = slash.commands["context"][ _name ]
                if not cmd.allowed_guild_ids:
                    cmd.allowed_guild_ids = guild_ids
                else:
                    cmd.allowed_guild_ids = [ i for i in cmd.allowed_guild_ids if bot.get_guild( i ) is not None ]
                    if not cmd.allowed_guild_ids:
                        _log.warning(f'Application context command { _name } has no allowed_guild_ids. Removing')
                        slash.commands["context"].pop( _name )
    
            continue
            
        cmd = slash.commands[ name ]
        if not cmd.allowed_guild_ids:
            cmd.allowed_guild_ids = guild_ids
        else:
            cmd.allowed_guild_ids = [ i for i in cmd.allowed_guild_ids if bot.get_guild( i ) is not None ]
            if not cmd.allowed_guild_ids:
                _log.warning(f"Application command { name } has no allowed_guild_ids. Removing")
                slash.commands.pop( name )
    
    _log.debug(f'Application ommands to sync: { ", ".join( slash.commands.keys() ) }')
    
    await slash.sync_all_commands()

@bot.event
async def on_ready():
    _log.info(f'Logged in as "{ str( bot.user ) }"')
    
    await sync_commands()
    
    bot.appinfo = await bot.application_info()

@bot.event
async def on_guild_join( guild ):
    _log.info(f'Joined guild "{ str( guild ) }"')
    
    await sync_commands()

def main():
    try:
        bot.load_extension("modules.stoi")
        bot.load_extension("modules.activities")
        bot.load_extension("modules.figlet")
        bot.load_extension("modules.oblicz")
        bot.load_extension("modules.cow")
        bot.load_extension("modules.react")
        #bot.load_extension("modules.spis")
        bot.load_extension("modules.img")
        bot.load_extension("modules.ryj")
        bot.load_extension("modules.ttt")
        bot.load_extension("modules.music")
        bot.load_extension("modules.status")
        bot.load_extension("modules.triggers")
        bot.load_extension("modules.info")
        
        bot.run( environ["DISCORD_TOKEN"] )
        
    except KeyboardInterrupt:
        exit()
        
if __name__ == "__main__":
    main()