from discord import AudioSource, Message, VoiceChannel, TextChannel, VoiceClient
from typing import Callable, Any, Optional


class MusicQueueEntry:
    def __init__(
        self,
        title: str,
        alt_titles: Optional[list[str]],
        audio_source: AudioSource,
        message: Message,
        after: Optional[Callable[[Exception], Any]] = None,
    ):
        self.title = title
        self._titles = alt_titles
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

        self._entries: list[MusicQueueEntry] = []
        self._cleared = True

        self.latest_track: str = ""

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
        if not self._entries:
            return

        entry = self._entries.pop(0)
        self.latest_track = entry._titles

        return entry

    def clear(self):
        self._cleared = True

        for entry in self._entries:
            entry.cleanup()

        self._entries = []

    @property
    def cleared(self) -> bool:
        return self._cleared
