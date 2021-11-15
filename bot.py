from sys import argv, exit

import logging
logging.basicConfig(
    level = logging.DEBUG if len( argv ) > 1 else logging.INFO,
    format = '%(name)s [%(levelname)s] %(message)s'
)
_log = logging.getLogger( __name__ )

from discord import Intents
from discord.ext.commands import Bot
from discord_slash import SlashCommand

from base64 import b64decode
from os import environ

bot = Bot( command_prefix = ',', help_command = None, intents = Intents.all() )
slash = SlashCommand( bot )

async def sync():
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
async def on_ready():
    _log.info(f'Logged in as "{ str( bot.user ) }"')
    
    await sync()

@bot.event
async def on_guild_join( guild ):
    _log.info(f'Joined guild "{ str( guild ) }"')
    
    await sync()


# APPLICATION_COMMAND_AUTOCOMPLETE: {
    # 'version': 1,
    # 'type': 4,
    # 'token': '...',
    # 'member': {
        # 'user': {
            # 'username': 'RoboT', 'public_flags': 0, 'id': '360781251579346944', 'discriminator': '2675', 'avatar': '8392ceb0bc882151cd4624a49749699f'
        # }, 
        # 'roles': ['776550379080515584', '776551245682180196', '776555414077964329', '776551616647397386', '776551116300615691', '776551038970232843', '776551683151888404', '776550782744264735'],
        # 'premium_since': None,
        # 'permissions': '1099511627775',
        # 'pending': False,
        # 'nick': '-><- is for me?',
        # 'mute': False,
        # 'joined_at': '2019-07-09T11:25:33.910000+00:00',
        # 'is_pending': False,
        # 'deaf': False,
        # 'communication_disabled_until': None,
        # 'avatar': None
    # },
    # 'id': '909857221284859904',
    # 'guild_id': '598112506338344973',
    # 'data': {
        # 'type': 1,
        # 'options': [
            # {'value': 'avbaaaa', 'type': 3, 'name': 'text', 'focused': True}
        # ],
        # 'name': 'figlet',
        # 'id': '904158109805731880'
    # },
    # 'channel_id': '830466268062285866',
    # 'application_id': '830421917474488350'
# }

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
        
        bot.run( b64decode( environ["cep"] ).decode() )
        
    except KeyboardInterrupt:
        exit()
        
if __name__ == "__main__":
    main()