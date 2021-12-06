from discord import Game, Activity, ActivityType
from discord.ext.commands import Bot, Cog
from discord.ext.tasks import loop
from random import choice as randomchoice

class Activities( Cog ):
    def __init__( self, bot: Bot ):
        self.bot = bot

        self.activities = [
            Game('tomb rajder'),
            Game('Hentai Nazi'),
            Game('Ventti z Drabikiem'),
            Game('My Summer Car'),
            
            Activity( type = ActivityType.watching, name = 'niemieckie porno'),
            Activity( type = ActivityType.watching, name = 'mcskelli.tk/item4.html'),
            Activity( type = ActivityType.watching, name = 'fish spinning for 68 years'),
            Activity( type = ActivityType.watching, name = 'jak bartek sra'),
            Activity( type = ActivityType.watching, name = 'bartek walking meme.mp4'),
            
            Activity( type = ActivityType.listening, name = 'Young Leosia - Jungle Girl'),
            Activity( type = ActivityType.listening, name = 'Young Leosia - Szklanki'),
            Activity( type = ActivityType.listening, name = 'Dream - Mask (Sus Remix)'),
            Activity( type = ActivityType.listening, name = 'loud indian 10h bass boosted'),
            Activity( type = ActivityType.listening, name = 'loud arabic'),
        ]

    @Cog.listener()
    async def on_ready( self ):
        if not self.update.is_running():
            self.update.start()

    def cog_unload( self ):
        self.update.cancel()

    @loop( minutes = 1.0 )
    async def update( self ):
        me = self.bot.guilds[ 0 ].me
        if me is None:
            return
        
        while True:
            activity = randomchoice( self.activities )
            
            if activity != me.activity:
                break

        await self.bot.change_presence( activity = activity )

def setup( bot: Bot ):
    bot.add_cog( Activities( bot ) )