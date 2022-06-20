from __future__ import annotations
from enum import Enum, auto

import discord
from discord.ext import commands
from discord import app_commands, ui

from ..bot import DegeneratBot
from .. import utils


class TTTState(Enum):
    Gameplay = auto()
    XWon = auto()
    OWon = auto
    Tie = auto()


class TTTGameView(ui.View):
    children: list[TTTButton]
    message: discord.InteractionMessage

    header: str = "**--- Kółko i Krzyżyk ---**\n--- {} vs. {} ---\n\n"
    gameplay: str = "Ruch: {}"
    win: str = "Koniec gry! Wygrywa: {}"
    tie: str = "Koniec gry - remis!"
    timedout: str = "Gra wygasła! Użyj komendy `/ttt`, aby zagrać ponownie"
    Empty: str = "▪️"
    X: str = "❌"
    O: str = "⭕"

    win_states: list[tuple[int, int, int]] = [
        # horizontal
        (0, 1, 2),
        (3, 4, 5),
        (6, 7, 8),
        # vertical
        (0, 3, 6),
        (1, 4, 7),
        (2, 5, 8),
        # diagonal
        (0, 4, 8),
        (2, 4, 6),
    ]

    def __init__(self, player1: discord.User, player2: discord.User):
        super().__init__(timeout=300)
        for i in range(9):
            self.add_item(
                TTTButton(
                    style=discord.ButtonStyle.blurple, label=self.Empty, row=int(i / 3)
                )
            )

        self.players = [player1, player2]
        self.moves = 0
        self.state: TTTState = TTTState.Gameplay

        self.header = self.header.format(player1.mention, player2.mention)

    async def on_timeout(self):
        text = self.header + self.timedout
        for b in self.children:
            b.disabled = True

        await self.message.edit(content=text, view=self)

    @property
    def current_move(self) -> discord.User:
        return self.players[self.moves % 2]

    @classmethod
    async def send_game(
        cls,
        interaction: discord.Interaction,
        player1: discord.User,
        player2: discord.User,
    ):
        game = cls(player1, player2)
        text = cls.header.format(
            player1.mention, player2.mention
        ) + cls.gameplay.format(player1.mention)
        await interaction.response.send_message(text, view=game)
        game.message = await interaction.original_message()

    def update_state(self) -> TTTState:
        btns: list[TTTButton] = []
        for indices in self.win_states:
            btns = [self.children[i] for i in indices]
            if all([b.label == self.X for b in btns]):
                self.state = TTTState.XWon
                break
            elif all([b.label == self.O for b in btns]):
                self.state = TTTState.OWon
                break

        if self.state is not TTTState.Gameplay:
            for b in self.children:
                b.disabled = True
                b.style = discord.ButtonStyle.gray

            for b in btns:
                b.style = discord.ButtonStyle.green

        elif all([b.disabled for b in self.children]):
            self.state = TTTState.Tie

        return self.state


class TTTButton(ui.Button):
    view: TTTGameView

    async def callback(self, interaction: discord.Interaction):
        if interaction.user not in self.view.players:
            await interaction.response.send_message(
                f"Nie dla psa! Tutaj grają {self.view.players[0].mention} i {self.view.players[1].mention}. Aby zagrać, użyj komendy `/ttt`",
                ephemeral=True,
            )
            return

        if self.view.current_move != interaction.user:
            await interaction.response.send_message(
                f"Poczekaj na swój ruch!", ephemeral=True
            )
            return

        self.disabled = True
        self.style = discord.ButtonStyle.gray
        if self.view.moves % 2:
            self.label = self.view.O
        else:
            self.label = self.view.X

        state = self.view.update_state()
        if state is TTTState.Gameplay:
            self.view.moves += 1
            text = self.view.header + self.view.gameplay.format(
                self.view.current_move.mention
            )

        elif state is TTTState.Tie:
            self.view.stop()
            text = self.view.header + self.view.tie

        else:
            self.view.stop()
            text = self.view.header + self.view.win.format(
                self.view.current_move.mention
            )

        await interaction.response.edit_message(content=text, view=self.view)


class TicTacToe(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

    @app_commands.command(description="Gra w kółko i krzyżyk")
    @app_commands.describe(opponent="Twój przeciwnik")
    @app_commands.guild_only
    async def ttt(self, interaction: discord.Interaction, opponent: discord.User):
        await TTTGameView.send_game(interaction, interaction.user, opponent)


async def setup(bot: DegeneratBot):
    cog = TicTacToe(bot)

    @app_commands.context_menu(name="Zagraj w kółko i krzyżyk")
    @app_commands.guild_only
    async def ttt_context(interaction: discord.Interaction, opponent: discord.User):
        await TTTGameView.send_game(interaction, interaction.user, opponent)

    bot.tree.add_command(ttt_context)

    await bot.add_cog(cog)
