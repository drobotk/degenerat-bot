import logging
import typing

import discord
from discord.ext import commands
from discord import app_commands, ui

from ...bot import DegeneratBot
from ... import utils

from .music_queue import MusicQueueAudioSource, MusicQueueVoiceClient
from .genius import get_genius_lyrics, LyricsData
from .youtube import Youtube


class MusicControls(ui.View):
    children: list[ui.Button]
    message: discord.InteractionMessage
    vc: MusicQueueVoiceClient

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self.vc = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not self.vc or not isinstance(self.vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return False

        return True

    @ui.button(label="Pause/Resume", emoji="⏯️")
    async def pause_resume(self, interaction: discord.Interaction, button: ui.Button):
        if self.vc.is_paused():
            self.vc.resume()
        else:
            self.vc.pause()

        await interaction.response.defer()

    @ui.button(label="Skip", emoji="⏭️")
    async def skip(self, interaction: discord.Interaction, button: ui.Button):
        self.vc.stop()
        await interaction.response.defer()

    @ui.button(label="Stop", emoji="⏹️")
    async def _stop(self, interaction: discord.Interaction, button: ui.Button):
        self.vc.clear_entries()
        self.vc.stop()
        await interaction.response.defer()

    @ui.button(label="Disconnect", emoji="👋")
    async def disconnect(self, interaction: discord.Interaction, button: ui.Button):
        await self.vc.disconnect()

        for c in self.children:
            c.disabled = True

        await interaction.response.edit_message(view=self)
        self.stop()

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True

        await self.message.edit(view=self)


class Music(commands.Cog, Youtube):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot
        self.log: logging.Logger = logging.getLogger(__name__)
        Youtube.__init__(self)

    async def get_client_for_channels(
        self, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel
    ) -> MusicQueueVoiceClient:
        vc = voice_channel.guild.voice_client
        if vc is not None and not isinstance(vc, MusicQueueVoiceClient):
            await vc.disconnect(force=False)
            vc = None

        if vc is None:
            vc = await voice_channel.connect(cls=MusicQueueVoiceClient)

        if vc.channel != voice_channel:
            await vc.move_to(voice_channel)

        vc.text_channel = text_channel

        return vc

    async def autocomplete_yt_search(
        self, interaction: discord.Interaction, current: str
    ) -> list[app_commands.Choice[str]]:
        if (
            not current
            or current.startswith("http://")
            or current.startswith("https://")
        ):
            return []

        results = await self.youtube_search(current, 25)
        if not results:
            return []

        return [
            app_commands.Choice(name=utils.dots_after(r.title, 100), value=r.url)
            for r in results
        ]

    @app_commands.command(description="Odtwarza muzykę w twoim kanale głosowym")
    @app_commands.describe(q="Wyszukiwana fraza/URL")
    @app_commands.autocomplete(q=autocomplete_yt_search)
    @app_commands.guild_only
    async def play(self, interaction: discord.Interaction, q: str):
        if interaction.user.voice is None or interaction.user.voice.channel is None:  # type: ignore (command is guild only, user will always be a Member here)
            return await interaction.response.send_message(
                "**Musisz być połączony z kanałem głosowym**", ephemeral=True
            )

        vc = await self.get_client_for_channels(
            interaction.user.voice.channel, interaction.channel  # type: ignore (command is guild only, user will always be a Member here; channel will never be None here)
        )
        if not vc:
            return await interaction.response.send_message("**Nie udało się połączyć**")

        await interaction.response.defer()

        url = self.extract_yt_url(q)
        if url:
            await self.queue_youtube(interaction, vc, url)

        elif utils.is_url(q):
            e = discord.Embed(description=q, color=interaction.guild.me.color)  # type: ignore (command is guild only, guild can't be None here)
            e.title = "Odtwarzanie" if vc.is_standby else "Dodano do kolejki"
            msg = await interaction.followup.send(embed=e, wait=True)

            await vc.add_entry(q, opus=False, titles=[q], message=msg)

        else:  # Search query
            e = discord.Embed(
                description=f"Wyszukiwanie `{q}`...", color=interaction.guild.me.color  # type: ignore (command is guild only, guild can't be None here)
            )
            interaction.message = await interaction.followup.send(embed=e, wait=True)

            results = await self.youtube_search(q, 1)
            if not results:
                e = discord.Embed(
                    description=f"Brak wyników wyszukiwania dla: `{q}`",
                    color=discord.Colour.red(),
                )
                return await interaction.edit_original_response(embed=e)

            await self.queue_youtube(interaction, vc, results[0].url)

    @commands.Cog.listener()
    async def on_voice_state_update(
        self,
        member: discord.Member,
        before: discord.VoiceState,
        after: discord.VoiceState,
    ):
        if member != self.bot.user:
            return

        if not after.self_deaf:
            await member.guild.change_voice_state(channel=after.channel, self_deaf=True)

    @app_commands.command(description="Rozłącza bota od kanału głosowego")
    @app_commands.guild_only
    async def disconnect(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        await vc.disconnect()
        await interaction.response.send_message(":wave:")

    @app_commands.command(name="pause", description="Pauzuje odtwarzanie muzyki")
    @app_commands.guild_only
    async def pause(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.pause()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(name="resume", description="Wznawia odtwarzanie muzyki")
    @app_commands.guild_only
    async def resume(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.resume()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Zakańcza odtwarzanie muzyki i czyści kolejkę")
    @app_commands.guild_only
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.clear_entries()
        vc.stop()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Czyści kolejkę muzyki")
    @app_commands.guild_only
    async def clear(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.clear_entries()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Pomija aktualnie odtwarzany element kolejki")
    @app_commands.guild_only
    async def skip(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.stop()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Wyświetla zawartość kolejki")
    @app_commands.guild_only
    async def queue(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        if len(vc.entries) == 0:
            await interaction.response.send_message("**Kolejka jest pusta**")
            return

        embed = discord.Embed(title="Kolejka", color=interaction.guild.me.color)  # type: ignore (command is guild only, guild can't be None here)

        nums = []
        titles = []
        for i, e in enumerate(vc.entries, 1):
            nums.append(str(i))
            title = e.titles[0] if e.titles else "Nieznany"
            titles.append(title)

        embed.add_field(inline=True, name="#", value="\n".join(nums))
        embed.add_field(inline=True, name="Tytuł", value="\n".join(titles))

        await interaction.response.send_message(embed=embed)

    async def autocomplete_queue_remove(
        self, interaction: discord.Interaction, current: int
    ) -> list[app_commands.Choice[int]]:
        vc = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc or not isinstance(vc, MusicQueueVoiceClient) or len(vc.entries) == 0:
            return []

        choices: list[app_commands.Choice[int]] = []

        for i, entry in enumerate(vc.entries, 1):
            if not str(i).startswith(str(current)):
                continue

            title = entry.titles[0] if entry.titles else "Nieznany"
            name = utils.dots_after(f"#{i} | {title}", 100)
            choices.append(app_commands.Choice(name=name, value=i))

            if len(choices) == 25:
                break

        return choices

    @app_commands.command(description="Usuwa pozycję z kolejki muzyki")
    @app_commands.describe(num="Element kolejki")
    @app_commands.autocomplete(num=autocomplete_queue_remove)
    @app_commands.guild_only
    async def remove(self, interaction: discord.Interaction, num: int):
        vc = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        if len(vc.entries) == 0:
            await interaction.response.send_message("**Kolejka jest pusta**")
            return

        if num < 1 or num > len(vc.entries):
            await interaction.response.send_message("**Nieprawidłowy element kolejki**")
            return

        vc.remove_entry(num - 1)

        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Panel sterowania muzyką")
    @app_commands.guild_only
    async def controls(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client  # type: ignore (command is guild only, guild can't be None here)
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        view = MusicControls(timeout=300)
        await interaction.response.send_message(view=view)
        view.message = await interaction.original_response()

    @app_commands.command(
        description="Pobiera tekst piosenki aktualnie odtwarzanej lub podanej"
    )
    @app_commands.describe(q="Wyszukiwana fraza")
    async def lyrics(
        self, interaction: discord.Interaction, q: typing.Optional[str] = None
    ):
        titles: list[str] = []
        if q is not None:
            titles.append(q)
        elif interaction.guild is not None:
            vc = interaction.guild.voice_client
            if (
                vc is not None
                and isinstance(vc, MusicQueueVoiceClient)
                and vc.source
                and isinstance(vc.source, MusicQueueAudioSource)
                and vc.source.titles is not None
            ):
                titles = vc.source.titles

        if not any(titles):
            await interaction.response.send_message(
                "**Brak aktualnie odtwarzanego utworu**", ephemeral=True
            )
            return

        await interaction.response.defer()

        data: typing.Optional[LyricsData] = None
        for t in titles:
            self.log.debug(f'Fetching lyrics for "{t}"')
            data = await get_genius_lyrics(self.bot.session, q=t)
            if data is not None:
                break

        if data is None:
            await interaction.followup.send("**Tekst piosenki niedostępny**")
            return

        text = f"**Tekst dla** `{data.resolved_title}`\n{data.lyrics}"

        # pagination for discord 2000 character limit
        pages = [text[i : i + 2000] for i in range(0, len(text), 2000)]

        # send first page as the interaction response
        await interaction.followup.send(pages[0])

        # remaining pages get sent normally
        for p in pages[1:]:
            await interaction.channel.send(p)  # type: ignore (channel will be messageable here)


async def setup(bot: DegeneratBot):
    cog = Music(bot)

    # ugly, i hate how these can't be in cogs
    @app_commands.context_menu(name="Dodaj do kolejki")
    @app_commands.guild_only
    async def play_context(interaction: discord.Interaction, message: discord.Message):
        if message.content:
            url = cog.extract_yt_url(message.content)
            await cog.play.callback(cog, interaction, url or message.content)  # type: ignore (Expected 2 positional arguments - type checker bug?)

        elif message.embeds:
            e = message.embeds[0]
            text = str(e.to_dict())

            url = cog.extract_yt_url(text)
            if url:
                await cog.play.callback(cog, interaction, url)  # type: ignore (Expected 2 positional arguments - type checker bug?)

            elif e.description or e.title:
                await cog.play.callback(cog, interaction, e.description or e.title)  # type: ignore (Expected 2 positional arguments - type checker bug?)

        else:
            await interaction.response.send_message(
                "**Błąd: Nie znaleziono pasującej treści**", ephemeral=True
            )

    bot.tree.add_command(play_context)

    await bot.add_cog(cog)
