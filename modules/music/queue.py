import discord
from discord.ext import tasks

import logging


class MusicQueueAudioSource:
    titles: list[str]
    message: discord.Message


class MQFFmpegPCMAudio(MusicQueueAudioSource, discord.FFmpegPCMAudio):
    pass


class MQFFmpegOpusAudio(MusicQueueAudioSource, discord.FFmpegOpusAudio):
    pass


class MusicQueueVoiceClient(discord.VoiceClient):
    def __init__(self, client: discord.Client, channel: discord.abc.Connectable):
        super().__init__(client, channel)

        self.log = logging.getLogger(__name__)

        self.entries: list[MusicQueueAudioSource] = []
        self.text_channel: discord.TextChannel = None

        self.update.start()

    async def add_entry(
        self,
        source: str,
        *,
        opus: bool,
        titles: list[str] = None,
        message: discord.Message = None,
    ) -> bool:
        if opus:
            entry = await MQFFmpegOpusAudio.from_probe(source)
        else:
            entry = MQFFmpegPCMAudio(source)

        if not entry:
            return False

        entry.titles = titles
        entry.message = message
        self.entries.append(entry)

        return True

    def remove_entry(self, i: int):
        entry = self.entries.pop(i)
        entry.cleanup()

    def clear_entries(self):
        for e in self.entries:
            e.cleanup()

        self.entries = []

    async def disconnect(self, *, force: bool = False):
        self.update.stop()
        self.clear_entries()
        return await super().disconnect(force=force)

    @property
    def is_standby(self):
        return len(self.entries) < 1 and not self.is_playing() and not self.is_paused() 

    @tasks.loop(seconds=1.0)
    async def update(self):
        self.log.debug("MusicQueueVoiceClient update")
        if not self.is_connected():
            return

        if len(self.entries) == 0:
            if not self.is_playing() and self.channel.members == [self.guild.me]:
                await self.disconnect()
                if self.text_channel:
                    e = discord.Embed(
                        description=f"Poszedłem sobie z {self.channel.mention} bo zostałem sam",
                        color=self.guild.me.color,
                    )
                    await self.text_channel.send(embed=e)

            return

        if self.is_playing():
            return

        next = self.entries.pop(0)
        self.play(next)

        if not isinstance(next, MusicQueueAudioSource):
            return

        msg = next.message
        if not msg or not msg.embeds:
            return

        if not self.text_channel:
            self.text_channel = msg.channel

        e = next.message.embeds[0]
        if e.title != "Odtwarzanie":
            e.title = "Odtwarzanie"
            if self.text_channel.last_message_id == msg.id:
                await msg.edit(embed=e)
            else:
                await self.text_channel.send(embed=e)
