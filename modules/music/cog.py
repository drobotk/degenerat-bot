from discord import Embed, Colour, VoiceChannel, VoiceClient, Member
from discord import FFmpegPCMAudio, VoiceState
from discord.ext.commands import Bot, Cog
from discord.ext.tasks import loop
from discord_slash import cog_ext
from discord_slash.model import ContextMenuType, AutocompleteOptionData
from discord_slash.context import SlashContext, MenuContext, AutocompleteContext
from discord_slash.utils.manage_commands import create_option, create_choice
from typing import Union
from urllib.parse import urlparse
from logging import getLogger

from .genius import Genius
from .youtube import Youtube
from .queue import MusicQueue, MusicQueueEntry


class Music(Cog, Youtube, Genius):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.log = getLogger(__name__)
        self.queues: dict[int, MusicQueue] = {}

        self.limit_mb = 100

        self.last_track: str = ""

        Youtube.__init__(self)

    @Cog.listener()
    async def on_ready(self):
        if not self.update.is_running():
            self.update.start()

    def cog_unload(self):
        self.update.cancel()

        for q in self.queues.values():
            q.clear()

    async def get_voice_client_for_channel(
        self, ch: VoiceChannel, stop_playing: bool = False
    ) -> VoiceClient:
        vc = ch.guild.voice_client

        if vc:
            if vc.channel != ch:
                await vc.move_to(ch)

            if stop_playing and vc.is_playing():
                vc.stop()

        else:
            vc = await ch.connect()

        return vc

    def is_url(self, x: str) -> bool:
        try:
            result = urlparse(x)
            return all([result.scheme, result.netloc])

        except:
            return False

    @cog_ext.cog_slash(
        name="play",
        description="Odtwarza muzykę w twoim kanale głosowym",
        options=[
            create_option(
                name="q",
                description="Search query/URL",
                option_type=3,
                required=True,
                autocomplete=True,
            )
        ],
    )
    async def _play(self, ctx: Union[SlashContext, MenuContext], q: str):
        ch = ctx.author.voice.channel if ctx.author.voice is not None else None

        if ch is None:
            await ctx.send("**Musisz być połączony z kanałem głosowym**", hidden=True)
            return

        await ctx.defer()

        queue = self.queues.get(ctx.guild.id, None)

        if queue is None:
            queue = MusicQueue(ch, ctx.channel)
            self.queues[ctx.guild.id] = queue

        elif queue.message_channel != ctx.channel or queue.voice_channel != ch:
            queue.message_channel = ctx.channel
            queue.voice_channel = ch

        url = self.extract_yt_url(q)
        if url:
            await self.queue_youtube(ctx, queue, url)

        elif self.is_url(q):
            audio = FFmpegPCMAudio(q)
            e = Embed(description=q, color=ctx.me.color)
            e.title = "Odtwarzanie" if queue.empty else "Dodano do kolejki"

            msg = await ctx.send(embed=e)

            entry = MusicQueueEntry(q, "", audio, msg)
            queue.add_entry(entry)

        else:  # Search query
            e = Embed(description=f"Wyszukiwanie `{ q }`...", color=ctx.me.color)
            await ctx.send(embed=e)

            results = await self.youtube_search(q, 1)
            if not results:
                e = Embed(
                    description=f"Brak wyników wyszukiwania dla: `{ q }`",
                    color=Colour.red(),
                )
                await ctx.message.edit(embed=e)
                return

            await self.queue_youtube(ctx, queue, results[0][0])

    @cog_ext.cog_autocomplete(name="play")
    async def _play_autocomplete(
        self, ctx: AutocompleteContext, options: dict[str, AutocompleteOptionData]
    ):
        q = options["q"].value
        if not q:
            await ctx.send([])
            return

        if q.startswith("http://") or q.startswith("https://"):
            await ctx.send([create_choice(name=q[:100], value=q)])
            return

        results = await self.youtube_search(q, 5)
        if not results:
            await ctx.send([])
            return

        await ctx.send([create_choice(name=r[1][:100], value=r[0]) for r in results])

    @cog_ext.cog_context_menu(name="Dodaj do kolejki", target=ContextMenuType.MESSAGE)
    async def _play_context(self, ctx: MenuContext):
        if ctx.target_message.content:
            url = self.extract_yt_url(ctx.target_message.content)
            await self._play.func(self, ctx, url or ctx.target_message.content)

        elif ctx.target_message.embeds:
            e = ctx.target_message.embeds[0]
            text = str(e.to_dict())

            url = self.extract_yt_url(text)
            if url:
                await self._play.func(self, ctx, url)

            elif e.description or e.title:
                await self._play.func(self, ctx, e.description or e.title)

        else:
            await ctx.send("**Błąd: Nie wykryto pasującej treści**", hidden=True)

    @loop(seconds=3.0)
    async def update(self):
        for guild in self.bot.guilds:
            queue = self.queues.get(guild.id)
            if queue is None or queue.cleared or queue.num_entries <= 0:
                if (
                    guild.voice_client
                    and not guild.voice_client.is_playing()
                    and len(guild.voice_client.channel.members) == 1
                ):
                    if queue and queue.message_channel:
                        e = Embed(
                            description=f"Poszedłem sobie z { guild.voice_client.channel.mention } bo zostałem sam",
                            color=guild.me.color,
                        )
                        await queue.message_channel.send(embed=e)

                    await guild.voice_client.disconnect()

                continue

            queue.vc = await self.get_voice_client_for_channel(queue.voice_channel)
            if queue.vc is None or queue.vc.is_playing() or queue.vc.is_paused():
                continue

            next = queue.get_next()
            if next is None:  # is this possible?
                continue

            self.last_track = next.meta_title
            queue.vc.play(next.audio_source, after=next.after)

            msg = next.message
            e = msg.embeds[0]
            if e.title != "Odtwarzanie":
                e.title = "Odtwarzanie"
                if queue.message_channel.last_message_id == msg.id:
                    await msg.edit(embed=e)
                else:
                    await queue.message_channel.send(embed=e)

    @Cog.listener()
    async def on_voice_state_update(
        self, member: Member, before: VoiceState, after: VoiceState
    ):
        if member != self.bot.user:
            return

        if after.channel != before.channel:
            if before.channel is None:  # joined voice channel
                self.log.info(
                    f'Joined vc "{ after.channel }" ({ after.channel.guild.name })'
                )

            elif after.channel is None:  # left voice channel
                self.log.info(
                    f'Left vc "{ before.channel }" ({ before.channel.guild.name })'
                )

                queue = self.queues.get(before.channel.guild.id)
                if queue is not None:
                    queue.clear()

            else:  # moved to other channel
                queue = self.queues.get(after.channel.guild.id)
                if queue is not None:
                    queue.voice_channel = after.channel

                self.log.info(
                    f'Moved to vc "{ after.channel }" ({ after.channel.guild.name })'
                )

        if not after.self_deaf:
            await member.guild.change_voice_state(channel=after.channel, self_deaf=True)

    @cog_ext.cog_slash(
        name="disconnect", description="Rozłącza bota od kanału głosowego"
    )
    async def _disconnect(self, ctx: SlashContext):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send("**Nie połączono**", hidden=True)
            return

        await vc.disconnect()
        await ctx.send(":wave:")

    @cog_ext.cog_slash(name="pause", description="Pauzuje odtwarzanie muzyki")
    async def _pause(self, ctx: SlashContext):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send("**Nie połączono**", hidden=True)
            return

        vc.pause()
        await ctx.send(":ok_hand:")

    @cog_ext.cog_slash(name="resume", description="Wznawia odtwarzanie muzyki")
    async def _resume(self, ctx: SlashContext):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send("**Nie połączono**", hidden=True)
            return

        vc.resume()
        await ctx.send(":ok_hand:")

    @cog_ext.cog_slash(
        name="stop", description="Zakańcza odtwarzanie muzyki i czyści kolejkę"
    )
    async def _stop(self, ctx: SlashContext):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send("**Nie połączono**", hidden=True)
            return

        queue = self.queues.get(ctx.guild.id)
        if queue is not None:
            queue.clear()

        vc.stop()
        await ctx.send(":ok_hand:")

    @cog_ext.cog_slash(name="clear", description="Czyści kolejkę")
    async def _clear(self, ctx: SlashContext):
        queue = self.queues.get(ctx.guild.id)
        if queue is not None:
            queue.clear()

        await ctx.send(":ok_hand:")

    @cog_ext.cog_slash(
        name="skip", description="Pomija aktualnie odtwarzany element kolejki"
    )
    async def _skip(self, ctx: SlashContext):
        vc = ctx.guild.voice_client
        if not vc:
            await ctx.send("**Nie połączono**", hidden=True)
            return

        vc.stop()
        await ctx.send(":ok_hand:")

    @cog_ext.cog_slash(name="queue", description="Wyświetla zawartość kolejki")
    async def _queue(self, ctx: SlashContext):
        queue = self.queues.get(ctx.guild.id)
        if queue is None:
            await ctx.send("**Brak kolejki**", hidden=True)
            return

        if queue.num_entries < 1:
            await ctx.send("**W kolejce pusto jak w głowie Jacka**", hidden=True)
            return

        e = Embed(title="Kolejka", color=ctx.me.color)

        e.add_field(
            inline=True,
            name="#",
            value="\n".join([str(n + 1) for n in range(queue.num_entries)]),
        )
        e.add_field(inline=True, name="Tytuł", value="\n".join(queue.entries))

        await ctx.send(embed=e)

    @cog_ext.cog_slash(
        name="remove",
        description="Usuwa pozycję z kolejki",
        options=[
            create_option(
                name="pos", description="Element kolejki", option_type=4, required=True
            )
        ],
    )
    async def _remove(self, ctx: SlashContext, pos: int):
        queue = self.queues.get(ctx.guild.id)
        if queue is None:
            await ctx.send("**Brak kolejki**", hidden=True)
            return

        if queue.num_entries < 1:
            await ctx.send("**W kolejce pusto jak w głowie Jacka**", hidden=True)
            return

        if pos < 1 or pos > queue.num_entries:
            await ctx.send("**Nieprawidłowy element kolejki**", hidden=True)
            return

        queue.remove(pos - 1)

        await ctx.send(":ok_hand:")

    
    @cog_ext.cog_slash(
        name="lyrics",
        description="Pobiera tekst piosenki",
        options=[
            create_option(
                name="q",
                description="Search query",
                option_type=3,
                required=False
            )
        ],
    )
    async def _lyrics(self, ctx: SlashContext, q: str = None):
        if not q:
            q = self.last_track

        if not q:
            await ctx.send("**Brak ostatnio odtwarzanego utworu**", hidden=True)
            return

        await ctx.defer()

        resolved, lyrics = await self.get_genius_lyrics(q)
        if not lyrics:
            await ctx.send("**Tekst piosenki niedostępny**")
            return

        await ctx.send(f"**Tekst dla** `{resolved}`")  # empty response

        # pagination for discord 2000 character limit
        pages = [lyrics[i:i+2000] for i in range(0, len(lyrics), 2000)]
        for p in pages:
            await ctx.channel.send(p)

def setup(bot: Bot):
    bot.add_cog(Music(bot))
