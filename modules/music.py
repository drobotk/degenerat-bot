from discord import Embed, Colour, VoiceChannel, VoiceClient, TextChannel, Member
from discord import AudioSource, Message, FFmpegPCMAudio, FFmpegOpusAudio, VoiceState
from discord.ext.commands import Bot, Cog
from discord.ext.tasks import loop
from discord_slash import cog_ext
from discord_slash.model import ContextMenuType, AutocompleteOptionData
from discord_slash.context import SlashContext, MenuContext, AutocompleteContext
from discord_slash.utils.manage_commands import create_option, create_choice
from typing import Union, Callable, Any
from urllib.parse import urlparse
from logging import getLogger
from yt_dlp import YoutubeDL
from os import mkdir
import re


class MusicQueueEntry:
    def __init__(
        self,
        title: str,
        audio_source: AudioSource,
        message: Message,
        after: Callable[[Exception], Any] = None,
    ):
        self.title = title
        self.audio_source = audio_source
        self.message = message
        self.after = after

    def cleanup(self):
        if self.audio_source is not None:
            self.audio_source.cleanup()

        if self.after is not None:
            self.after(None)


class MusicQueue:
    def __init__(self, voice_channel: VoiceChannel, message_channel: TextChannel):
        self.voice_channel = voice_channel
        self.message_channel = message_channel

        self.vc: VoiceClient = None

        self._entries = []
        self._cleared = True

    def add_entry(self, entry: MusicQueueEntry):
        self._cleared = False
        self._entries.append(entry)

    @property
    def num_entries(self) -> int:
        return len(self._entries)

    @property
    def empty(self) -> bool:
        return self._cleared or (
            self.vc is not None and not self.vc.is_playing() and not self.vc.is_paused()
        )

    @property
    def entries(self) -> list[str]:
        return [entry.title for entry in self._entries]

    def remove(self, index: int):
        if index >= 0 and index < len(self._entries):
            entry = self._entries.pop(index)
            entry.cleanup()

    def get_next(self) -> MusicQueueEntry:
        return self._entries.pop(0) if len(self._entries) > 0 else None

    def clear(self):
        self._cleared = True

        for entry in self._entries:
            entry.cleanup()

        self._entries = []

    @property
    def cleared(self) -> bool:
        return self._cleared


class Music(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot
        self.log = getLogger(__name__)
        self.queues: dict[int, MusicQueue] = {}

        self.limit_mb = 25

        params = {
            "no_color": True,
            "format": self.format_selector,
            "logger": getLogger(__name__ + ".ydl"),
        }
        self.ydl = YoutubeDL(params)

        self.re_title = re.compile(
            r'"title":{"runs":\[{"text":".{1,100}"}\],"accessibility'
        )

        # rmtree("./yt", ignore_errors = True ) # remove previously downloaded audio

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

    def format_selector(self, ctx: dict) -> list:
        formats = ctx["formats"]
        formats = [a for a in formats if a["acodec"] == "opus"]
        if len(formats) <= 1:
            return formats

        # sort by audio bitrate and return second best
        formats.sort(key=lambda a: a["abr"])
        return [formats[-2]]

    def extract_yt_url(self, text: str) -> str:
        at = text.find("/watch?v=")
        if at > -1:
            return "https://www.youtube.com" + text[at : at + 20]

        at = text.find("youtu.be/")
        if at > -1:
            return "https://www.youtube.com/watch?v=" + text[at + 9 : at + 20]

    def extract_video_title(self, text: str) -> str:
        hit = self.re_title.search(text)
        if hit:
            return hit.group()[26:-18]

    async def youtube_search(self, q: str) -> tuple[str, str]:
        async with self.bot.http._HTTPClient__session.get(
            "https://www.youtube.com/results", params={"search_query": q}
        ) as r:
            if not r.ok:
                return

            text = await r.text()

        text = text[170000:]

        return self.extract_video_title(text), self.extract_yt_url(text)

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

        if self.is_url(q):
            if q.startswith("https://www.youtube.com/watch?v=") or q.startswith(
                "https://youtu.be/"
            ):
                await self.queue_youtube(ctx, queue, q)

            else:  # arbitrary url, TODO: actually download the file and read metadata to put in embed (this would kill playing web streams tho?)
                audio = FFmpegPCMAudio(q)
                e = Embed(description=q, color=ctx.me.color)
                e.title = "Odtwarzanie" if queue.empty else "Dodano do kolejki"

                msg = await ctx.send(embed=e)

                entry = MusicQueueEntry(q, audio, msg)
                queue.add_entry(entry)

        else:  # Search query
            e = Embed(description=f"Wyszukiwanie `{ q }`...", color=ctx.me.color)
            await ctx.send(embed=e)

            _, url = await self.youtube_search(q)
            if not url:
                e = Embed(
                    description=f"Brak wyników wyszukiwania dla: `{ q }`",
                    color=Colour.red(),
                )
                await ctx.message.edit(embed=e)
                return

            await self.queue_youtube(ctx, queue, url)

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

        title, url = await self.youtube_search(q)
        if not url:
            await ctx.send([])
            return

        await ctx.send([create_choice(name=(title or url)[:100], value=url)])

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

    async def queue_youtube(
        self, ctx: Union[SlashContext, MenuContext], queue: MusicQueue, url: str
    ):
        reply = ctx.message.edit if ctx.message else ctx.send

        e = Embed()
        e.set_footer(text=url)

        try:
            info = await self.bot.loop.run_in_executor(
                None, lambda: self.ydl.extract_info(url, download=False)
            )
            title = info["title"]
            filesize = info["filesize"]
            thumb = info["thumbnail"]

        except Exception as err:
            e = Embed(
                title="**Wystąpił błąd**", description=str(err), color=Colour.red()
            )
            await reply(embed=e)
            return

        e.description = title
        e.set_thumbnail(url=thumb)

        if filesize > self.limit_mb * 1_000_000:
            e.title = f"**Rozmiar pliku przekracza rozsądny limit {self.limit_mb}MB**"
            e.color = Colour.red()
            await reply(embed=e)
            return

        e.title = "Pobierańsko..."
        e.color = ctx.me.color
        await reply(embed=e)

        try:
            mkdir("./yt")
        except FileExistsError:
            pass

        filename = f"./yt/{ self.ydl.prepare_filename( info ) }"
        success, _ = await self.bot.loop.run_in_executor(
            None, lambda: self.ydl.dl(filename, info)
        )
        if not success:
            e.title = "**Wystąpił błąd podczas pobierania pliku**"
            e.color = Colour.red()
            await ctx.message.edit(embed=e)
            return

        audio = await FFmpegOpusAudio.from_probe(filename)

        e.title = "Odtwarzanie" if queue.empty else "Dodano do kolejki"
        await ctx.message.edit(embed=e)

        entry = MusicQueueEntry(title, audio, ctx.message)
        queue.add_entry(entry)

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


def setup(bot: Bot):
    bot.add_cog(Music(bot))
