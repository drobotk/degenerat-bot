from discord.ext.commands import Bot, Cog
from discord_slash import cog_ext
from discord_slash.context import SlashContext, ComponentContext
from discord_slash.utils.manage_components import (
    create_button,
    create_actionrow,
    emoji_to_dict,
)
from discord_slash.model import ButtonStyle


class TTT(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @cog_ext.cog_slash(name="ttt", description="Kółko i krzyżyk")
    async def _ttt(self, ctx: SlashContext):
        components = []

        for i in range(3):
            buttons = []

            for j in range(3):
                # buttons.append( create_button( style = ButtonStyle.blue, emoji = '▪️', custom_id = f'ttt{ i * 3 + j }') )
                buttons.append(
                    create_button(
                        style=ButtonStyle.blue,
                        label="▪️",
                        custom_id=f"ttt{ i * 3 + j }",
                    )
                )

            components.append(create_actionrow(*buttons))

        await ctx.send("Ruch: krzyżyk", components=components)

    @cog_ext.cog_component(
        use_callback_name=False, components=[f"ttt{ i }" for i in range(9)]
    )
    async def _ttt_click(self, ctx: ComponentContext):
        id = int(ctx.custom_id[3])  # ttt4 => 4
        i = int(id / 3)
        j = id % 3

        components = ctx.origin_message.components

        button = components[i]["components"][j]
        button["disabled"] = True
        button["style"] = ButtonStyle.grey

        content = ctx.origin_message.content

        if content == "Ruch: krzyżyk":
            # button['emoji'] = emoji_to_dict('❌')
            button["label"] = "❌"
            content = "Ruch: kółko"

        elif content == "Ruch: kółko":
            # button['emoji'] = emoji_to_dict('⭕')
            button["label"] = "⭕"
            content = "Ruch: krzyżyk"

        result = self.ttt_check_win(components)
        if result:
            winner = "krzyżyk" if result["win"] == 1 else "kółko"
            content = "Wygrywa: " + winner

            for i in range(3):
                for j in range(3):
                    components[i]["components"][j]["disabled"] = True
                    components[i]["components"][j]["style"] = ButtonStyle.grey

            for i in result["buttons"]:
                components[i[0]]["components"][i[1]]["style"] = ButtonStyle.green

        elif self.ttt_check_stale(components):
            content = "Koniec gry - remis"

        await ctx.edit_origin(content=content, components=components)

    def ttt_check_stale(self, components):
        for i in range(3):
            for j in range(3):
                if not components[i]["components"][j].get("disabled", False):
                    return False

        return True

    def ttt_check_win(self, components):
        if (
            components[0]["components"][0]["label"] == "❌"
            and components[0]["components"][1]["label"] == "❌"
            and components[0]["components"][2]["label"] == "❌"
        ):
            return {"win": 1, "buttons": ((0, 0), (0, 1), (0, 2))}

        if (
            components[1]["components"][0]["label"] == "❌"
            and components[1]["components"][1]["label"] == "❌"
            and components[1]["components"][2]["label"] == "❌"
        ):
            return {"win": 1, "buttons": ((1, 0), (1, 1), (1, 2))}

        if (
            components[2]["components"][0]["label"] == "❌"
            and components[2]["components"][1]["label"] == "❌"
            and components[2]["components"][2]["label"] == "❌"
        ):
            return {"win": 1, "buttons": ((2, 0), (2, 1), (2, 2))}

        if (
            components[0]["components"][0]["label"] == "❌"
            and components[1]["components"][0]["label"] == "❌"
            and components[2]["components"][0]["label"] == "❌"
        ):
            return {"win": 1, "buttons": ((0, 0), (1, 0), (2, 0))}

        if (
            components[0]["components"][1]["label"] == "❌"
            and components[1]["components"][1]["label"] == "❌"
            and components[2]["components"][1]["label"] == "❌"
        ):
            return {"win": 1, "buttons": ((0, 1), (1, 1), (2, 1))}

        if (
            components[0]["components"][2]["label"] == "❌"
            and components[1]["components"][2]["label"] == "❌"
            and components[2]["components"][2]["label"] == "❌"
        ):
            return {"win": 1, "buttons": ((0, 2), (1, 2), (2, 2))}

        if (
            components[0]["components"][0]["label"] == "❌"
            and components[1]["components"][1]["label"] == "❌"
            and components[2]["components"][2]["label"] == "❌"
        ):
            return {"win": 1, "buttons": ((0, 0), (1, 1), (2, 2))}

        if (
            components[0]["components"][2]["label"] == "❌"
            and components[1]["components"][1]["label"] == "❌"
            and components[2]["components"][0]["label"] == "❌"
        ):
            return {"win": 1, "buttons": ((0, 2), (1, 1), (2, 0))}

        if (
            components[0]["components"][0]["label"] == "⭕"
            and components[0]["components"][1]["label"] == "⭕"
            and components[0]["components"][2]["label"] == "⭕"
        ):
            return {"win": 2, "buttons": ((0, 0), (0, 1), (0, 2))}

        if (
            components[1]["components"][0]["label"] == "⭕"
            and components[1]["components"][1]["label"] == "⭕"
            and components[1]["components"][2]["label"] == "⭕"
        ):
            return {"win": 2, "buttons": ((1, 0), (1, 1), (1, 2))}

        if (
            components[2]["components"][0]["label"] == "⭕"
            and components[2]["components"][1]["label"] == "⭕"
            and components[2]["components"][2]["label"] == "⭕"
        ):
            return {"win": 2, "buttons": ((2, 0), (2, 1), (2, 2))}

        if (
            components[0]["components"][0]["label"] == "⭕"
            and components[1]["components"][0]["label"] == "⭕"
            and components[2]["components"][0]["label"] == "⭕"
        ):
            return {"win": 2, "buttons": ((0, 0), (1, 0), (2, 0))}

        if (
            components[0]["components"][1]["label"] == "⭕"
            and components[1]["components"][1]["label"] == "⭕"
            and components[2]["components"][1]["label"] == "⭕"
        ):
            return {"win": 2, "buttons": ((0, 1), (1, 1), (2, 1))}

        if (
            components[0]["components"][2]["label"] == "⭕"
            and components[1]["components"][2]["label"] == "⭕"
            and components[2]["components"][2]["label"] == "⭕"
        ):
            return {"win": 2, "buttons": ((0, 2), (1, 2), (2, 2))}

        if (
            components[0]["components"][0]["label"] == "⭕"
            and components[1]["components"][1]["label"] == "⭕"
            and components[2]["components"][2]["label"] == "⭕"
        ):
            return {"win": 2, "buttons": ((0, 0), (1, 1), (2, 2))}

        if (
            components[0]["components"][2]["label"] == "⭕"
            and components[1]["components"][1]["label"] == "⭕"
            and components[2]["components"][0]["label"] == "⭕"
        ):
            return {"win": 2, "buttons": ((0, 2), (1, 1), (2, 0))}

        return False


def setup(bot: Bot):
    bot.add_cog(TTT(bot))
