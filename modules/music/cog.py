import discord
from discord.ext import commands
from discord import app_commands, ui

import logging
from urllib.parse import urlparse

from .queue import MusicQueueAudioSource, MusicQueueVoiceClient
from .genius import get_genius_lyrics
from .youtube import Youtube


def is_url(x: str) -> bool:
    try:
        result = urlparse(x)
        return all([result.scheme, result.netloc])

    except:
        return False


def dots_after(inp: str, length: int) -> str:
    if len(inp) <= length:
        return inp

    return inp[:97] + "..."


class MusicControls(ui.View):
    children: list[ui.Button]
    message: discord.InteractionMessage
    vc: MusicQueueVoiceClient

    async def interaction_check(self, interaction: discord.Interaction) -> bool:
        self.vc = interaction.guild.voice_client
        if not self.vc or not isinstance(self.vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return False

        return True

    @ui.button(label="Pause/Resume", emoji="⏯️")
    async def pause_resume(self, button: ui.Button, interaction: discord.Interaction):
        if self.vc.is_paused():
            self.vc.resume()
        else:
            self.vc.pause()

        await interaction.response.defer()

    @ui.button(label="Skip", emoji="⏭️")
    async def skip(self, button: ui.Button, interaction: discord.Interaction):
        self.vc.stop()
        await interaction.response.defer()

    @ui.button(label="Stop", emoji="⏹️")
    async def stop(self, button: ui.Button, interaction: discord.Interaction):
        self.vc.clear_entries()
        self.vc.stop()
        await interaction.response.defer()

    @ui.button(label="Disconnect", emoji="👋")
    async def disconnect(self, button: ui.Button, interaction: discord.Interaction):
        await self.vc.disconnect()
        await interaction.response.defer()

    async def on_timeout(self):
        for c in self.children:
            c.disabled = True

        await self.message.edit(view=self)


class Music(commands.Cog, Youtube):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.log = logging.getLogger(__name__)
        Youtube.__init__(self)

    async def get_client_for_channels(
        self, voice_channel: discord.VoiceChannel, text_channel: discord.TextChannel
    ) -> MusicQueueVoiceClient:
        vc = voice_channel.guild.voice_client
        if vc is not None and not isinstance(vc, MusicQueueVoiceClient):
            await vc.disconnect()
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

        results = await self.youtube_search(current, 10)
        if not results:
            return []

        return [
            app_commands.Choice(name=dots_after(r.title, 100), value=r.url)
            for r in results
        ]

    @app_commands.command(description="Odtwarza muzykę w twoim kanale głosowym")
    @app_commands.describe(q="Wyszukiwana fraza/URL")
    @app_commands.autocomplete(q=autocomplete_yt_search)
    async def play(self, interaction: discord.Interaction, q: str):
        if interaction.user.voice is None or interaction.user.voice.channel is None:
            await interaction.response.send_message(
                "**Musisz być połączony z kanałem głosowym**", ephemeral=True
            )
            return

        vc = await self.get_client_for_channels(
            interaction.user.voice.channel, interaction.channel
        )
        if not vc:
            await interaction.response.send_message("**Nie udało się połączyć**")
            return

        await interaction.response.defer()

        url = self.extract_yt_url(q)
        if url:
            await self.queue_youtube(interaction, vc, url)

        elif is_url(q):
            e = discord.Embed(description=q, color=interaction.guild.me.color)
            e.title = "Odtwarzanie" if vc.is_standby else "Dodano do kolejki"
            msg = await interaction.followup.send(embed=e, wait=True)

            await vc.add_entry(q, opus=False, titles=[q], message=msg)

        else:  # Search query
            e = discord.Embed(
                description=f"Wyszukiwanie `{q}`...", color=interaction.guild.me.color
            )
            interaction.message = await interaction.followup.send(embed=e, wait=True)

            results = await self.youtube_search(q, 1)
            if not results:
                e = discord.Embed(
                    description=f"Brak wyników wyszukiwania dla: `{q}`",
                    color=discord.Colour.red(),
                )
                await interaction.edit_original_message(embed=e)
                return

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
    async def disconnect(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        await vc.disconnect()
        await interaction.response.send_message(":wave:")

    @app_commands.command(name="pause", description="Pauzuje odtwarzanie muzyki")
    async def pause(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.pause()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(name="resume", description="Wznawia odtwarzanie muzyki")
    async def resume(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.resume()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Zakańcza odtwarzanie muzyki i czyści kolejkę")
    async def stop(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.clear_entries()
        vc.stop()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Czyści kolejkę muzyki")
    async def clear(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.clear_entries()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Pomija aktualnie odtwarzany element kolejki")
    async def skip(self, interaction: discord.Interaction):
        vc: discord.VoiceClient = interaction.guild.voice_client
        if not vc:
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        vc.stop()
        await interaction.response.send_message(":ok_hand:")

    @app_commands.command(description="Wyświetla zawartość kolejki")
    async def queue(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        if len(vc.entries) == 0:
            await interaction.response.send_message("**Kolejka jest pusta**")
            return

        embed = discord.Embed(title="Kolejka", color=interaction.guild.me.color)

        nums = []
        titles = []
        for i, e in enumerate(vc.entries, 1):
            nums.append(str(i))
            title = e.titles[0] if e.titles else "Nieznany"
            titles.append(title)

        embed.add_field(inline=True, name="#", value="\n".join(nums))
        embed.add_field(inline=True, name="Tytuł", value="\n".join(titles))

        await interaction.response.send_message(embed=embed)

    @app_commands.command(description="Usuwa pozycję z kolejki muzyki")
    @app_commands.describe(num="Element kolejki")
    async def remove(self, interaction: discord.Interaction, num: int):
        vc = interaction.guild.voice_client
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
    async def controls(self, interaction: discord.Interaction):
        vc = interaction.guild.voice_client
        if not vc or not isinstance(vc, MusicQueueVoiceClient):
            await interaction.response.send_message("**Nie połączono**", ephemeral=True)
            return

        view = MusicControls(timeout=300)
        await interaction.response.send_message(view=view)
        view.message = await interaction.original_message()

    @app_commands.command(
        description="Pobiera tekst piosenki aktualnie odtwarzanej lub podanej"
    )
    @app_commands.describe(q="Wyszukiwana fraza")
    async def lyrics(self, interaction: discord.Interaction, q: str = None):
        titles = [q]
        if not q:
            vc = interaction.guild.voice_client
            if (
                vc is not None
                and isinstance(vc, MusicQueueVoiceClient)
                and vc.source
                and isinstance(vc.source, MusicQueueAudioSource)
            ):
                titles = vc.source.titles

        if not any(titles):
            await interaction.response.send_message(
                "**Brak aktualnie odtwarzanego utworu**", ephemeral=True
            )
            return

        await interaction.response.defer()

        for t in titles:
            self.log.debug(f'Fetching lyrics for "{t}"')
            data = await get_genius_lyrics(self.bot.http._HTTPClient__session, q=t)
            if data:
                break

        if not data:
            await interaction.followup.send("**Tekst piosenki niedostępny**")
            return

        await interaction.followup.send(f"**Tekst dla** `{data.resolved_title}`")

        # pagination for discord 2000 character limit
        pages = [data.lyrics[i : i + 2000] for i in range(0, len(data.lyrics), 2000)]
        for p in pages:
            await interaction.channel.send(p)


async def setup(bot: commands.Bot):
    cog = Music(bot)

    # ugly, i hate how these can't be in cogs
    @app_commands.context_menu(name="Dodaj do kolejki")
    async def play_context(interaction: discord.Interaction, message: discord.Message):
        if message.content:
            url = cog.extract_yt_url(message.content)
            await cog.play.callback(cog, interaction, url or message.content)

        elif message.embeds:
            e = message.embeds[0]
            text = str(e.to_dict())

            url = cog.extract_yt_url(text)
            if url:
                await cog.play.callback(cog, interaction, url)

            elif e.description or e.title:
                await cog.play.callback(cog, interaction, e.description or e.title)

        else:
            await interaction.response.send_message(
                "**Błąd: Nie znaleziono pasującej treści**", ephemeral=True
            )

    bot.tree.add_command(play_context)

    await bot.add_cog(cog)
