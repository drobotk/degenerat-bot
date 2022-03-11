import discord
from discord.ext import commands, tasks
from discord import app_commands

import logging
from urllib.parse import urlparse

from .genius import Genius
from .youtube import Youtube
from .queue import MusicQueue, MusicQueueEntry


class Music(commands.Cog, Youtube, Genius):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)
        self.queues: dict[int, MusicQueue] = {}

        self.limit_mb = 100

        Youtube.__init__(self)

        self.update.start()

    def cog_unload(self):
        self.update.cancel()

        for q in self.queues.values():
            q.clear()

    async def get_voice_client_for_channel(
        self, ch: discord.VoiceChannel, stop_playing: bool = False
    ) -> discord.VoiceClient:
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

    @app_commands.command(description="Odtwarza muzykę w twoim kanale głosowym")
    @app_commands.describe(q="Wyszukiwana fraza/URL")
    async def play(self, interaction: discord.Interaction, q: str):
        ch = (
            interaction.user.voice.channel
            if interaction.user.voice is not None
            else None
        )

        if ch is None:
            await interaction.response.send_message(
                "**Musisz być połączony z kanałem głosowym**", ephemeral=True
            )
            return

        await interaction.response.defer()

        queue = self.queues.get(interaction.guild.id)

        if queue is None:
            queue = MusicQueue(ch, interaction.channel)
            self.queues[interaction.guild.id] = queue

        elif queue.message_channel != interaction.channel or queue.voice_channel != ch:
            queue.message_channel = interaction.channel
            queue.voice_channel = ch

        url = self.extract_yt_url(q)
        if url:
            await self.queue_youtube(interaction, queue, url)

        elif self.is_url(q):
            audio = discord.FFmpegPCMAudio(q)
            e = discord.Embed(description=q, color=interaction.guild.me.color)
            e.title = "Odtwarzanie" if queue.empty else "Dodano do kolejki"

            msg = await interaction.followup.send(embed=e, wait=True)

            entry = MusicQueueEntry(q, None, audio, msg)
            queue.add_entry(entry)

        else:  # Search query
            e = discord.Embed(
                description=f"Wyszukiwanie `{ q }`...", color=interaction.guild.me.color
            )
            await interaction.followup.send(embed=e)

            results = await self.youtube_search(q, 1)
            if not results:
                e = discord.Embed(
                    description=f"Brak wyników wyszukiwania dla: `{ q }`",
                    color=discord.Colour.red(),
                )
                await interaction.edit_original_message(embed=e)
                return

            await self.queue_youtube(interaction, queue, results[0][0])

    # async def _play_autocomplete(
    #     self, ctx: AutocompleteContext, options: dict[str, AutocompleteOptionData]
    # ):
    #     q = options["q"].value
    #     if not q:
    #         await ctx.send([])
    #         return

    #     if q.startswith("http://") or q.startswith("https://"):
    #         await ctx.send([create_choice(name=q[:100], value=q)])
    #         return

    #     results = await self.youtube_search(q, 5)
    #     if not results:
    #         await ctx.send([])
    #         return

    #     await ctx.send([create_choice(name=r[1][:100], value=r[0]) for r in results])

    # @cog_ext.cog_context_menu(name="Dodaj do kolejki", target=ContextMenuType.MESSAGE)
    # async def _play_context(self, ctx: MenuContext):
    #     if ctx.target_message.content:
    #         url = self.extract_yt_url(ctx.target_message.content)
    #         await self._play.func(self, ctx, url or ctx.target_message.content)

    #     elif ctx.target_message.embeds:
    #         e = ctx.target_message.embeds[0]
    #         text = str(e.to_dict())

    #         url = self.extract_yt_url(text)
    #         if url:
    #             await self._play.func(self, ctx, url)

    #         elif e.description or e.title:
    #             await self._play.func(self, ctx, e.description or e.title)

    #     else:
    #         await ctx.send("**Błąd: Nie wykryto pasującej treści**", ephemeral=True)

    @tasks.loop(seconds=2.0)
    async def update(self):
        await self.bot.wait_until_ready()

        for guild in self.bot.guilds:
            queue = self.queues.get(guild.id)
            if queue is None or queue.cleared or queue.num_entries <= 0:
                if (
                    guild.voice_client
                    and not guild.voice_client.is_playing()
                    and len(guild.voice_client.channel.members) == 1
                ):
                    if queue and queue.message_channel:
                        e = discord.Embed(
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

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member != self.bot.user:
            return

        if after.channel != before.channel:
            if before.channel is None:  # joined voice channel
                self.log.info(
                    f'Joined vc "{after.channel}" ({after.channel.guild.name})'
                )

            elif after.channel is None:  # left voice channel
                self.log.info(
                    f'Left vc "{before.channel}" ({before.channel.guild.name})'
                )

                queue = self.queues.get(before.channel.guild.id)
                if queue is not None:
                    queue.clear()

            else:  # moved to other channel
                queue = self.queues.get(after.channel.guild.id)
                if queue is not None:
                    queue.voice_channel = after.channel

                self.log.info(
                    f'Moved to vc "{after.channel}" ({after.channel.guild.name})'
                )

        if not after.self_deaf:
            await member.guild.change_voice_state(channel=after.channel, self_deaf=True)

    @app_commands.command(description="Rozłącza bota od kanału głosowego")
    async def disconnect(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        await vc.disconnect()
        await interaction.response.send_message(":wave:")

    @app_commands.command(name="pause", description="Pauzuje odtwarzanie muzyki")
    async def pause(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.pause()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(name="resume", description="Wznawia odtwarzanie muzyki")
    async def resume(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.resume()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Zakańcza odtwarzanie muzyki i czyści kolejkę")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        queue = self.queues.get(interaction.guild.id)
        if queue is not None:
            queue.clear()

        vc.stop()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Czyści kolejkę muzyki")
    async def clear(self, interaction: discord.Interaction):
        queue = self.queues.get(interaction.guild_id)
        if queue is None:
            await interaction.response.send_message("**Brak kolejki**", ephemeral=True)
            return

        queue.clear()

        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Pomija aktualnie odtwarzany element kolejki")
    async def skip(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.stop()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Wyświetla zawartość kolejki")
    async def queue(self, interaction: discord.Interaction):
        queue = self.queues.get(interaction.guild.id)
        if queue is None:
            await interaction.response.send_message("**Brak kolejki**", ephemeral=True)
            return

        if queue.num_entries < 1:
            await interaction.response.send_message(
                "**W kolejce pusto jak w głowie Jacka**", ephemeral=True
            )
            return

        e = discord.Embed(title="Kolejka", color=interaction.guild.me.color)

        e.add_field(
            inline=True,
            name="#",
            value="\n".join([str(n + 1) for n in range(queue.num_entries)]),
        )
        e.add_field(inline=True, name="Tytuł", value="\n".join(queue.entries))

        await interaction.response.send_message(embed=e)

    @app_commands.command(description="Usuwa pozycję z kolejki muzyki")
    @app_commands.describe(pos="Element kolejki")
    async def remove(self, interaction: discord.Interaction, pos: int):
        queue = self.queues.get(interaction.guild.id)
        if queue is None:
            await interaction.response.send_message("**Brak kolejki**", ephemeral=True)
            return

        if queue.num_entries < 1:
            await interaction.response.send_message(
                "**W kolejce pusto jak w głowie Jacka**", ephemeral=True
            )
            return

        if pos < 1 or pos > queue.num_entries:
            await interaction.response.send_message(
                "**Nieprawidłowy element kolejki**", ephemeral=True
            )
            return

        queue.remove(pos - 1)

        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Pobiera tekst piosenki")
    @app_commands.describe(q="Wyszukiwana fraza")
    async def lyrics(self, interaction: discord.Interaction, q: str = None):
        if q:
            tries = [q]
        else:
            queue = self.queues.get(interaction.guild.id)
            if queue:
                tries = queue.latest_track

        if not any(tries):
            await interaction.response.send_message(
                "**Brak ostatnio odtwarzanego utworu**", ephemeral=True
            )
            return

        await interaction.response.defer()

        for q in tries:
            self.log.info(f'Fetching lyrics for "{q}"')
            resolved, lyrics = await self.get_genius_lyrics(q)
            if lyrics:
                break

        if not lyrics:
            await interaction.followup.send("**Tekst piosenki niedostępny**")
            return

        await interaction.followup.send(f"**Tekst dla** `{resolved}`")

        # pagination for discord 2000 character limit
        pages = [lyrics[i : i + 2000] for i in range(0, len(lyrics), 2000)]
        for p in pages:
            await interaction.channel.send(p)


def setup(bot: commands.Bot):
    bot.add_cog(Music(bot))
