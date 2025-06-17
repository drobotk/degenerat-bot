import asyncio
from enum import Enum, auto
import re

import discord
from discord.ext import commands

from ..bot import DegeneratBot


class TriggerType(Enum):
    TEXT_TEXT = auto()
    TEXT_REACTION = auto()
    REACTION_TEXT = auto()
    REACTION_REACTION = auto()


class Trigger:
    def __init__(self, type: TriggerType, input: str, output: str):
        self.type = type
        self.pattern = re.compile(input)
        self.output = output

    def match(self, input: str) -> bool:
        return self.pattern.search(input) is not None


class Triggers(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

        self.triggers = [
            Trigger(TriggerType.TEXT_TEXT, r"^sus$", "amogus"),
            Trigger(TriggerType.TEXT_TEXT, r"^amogus$", "ඞ"),
            Trigger(
                TriggerType.TEXT_TEXT,
                r"(?:^|\W|_)erika(?:$|\W|_)",
                "*Auf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\nHeiß von hunderttausend kleinen Bienelein\nWird umschwärmt:\nErika\nDenn ihr Herz ist voller Süßigkeit\nZarter Duft entströmt dem Blütenkleid\nAuf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\n\nIn der Heimat wohnt ein kleines Mädelein\nUnd das heißt:\nErika\nDieses Mädel ist mein treues Schätzelein\nUnd mein Glück\nErika\nWenn das Heidekraut rot-lila blüht\nSinge ich zum Gruß ihr dieses Lied\nAuf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\n\nIn mein´m Kämmerlein blüht auch ein Blümelein\nUnd das heißt:\nErika\nSchon beim Morgengrau´n sowie beim Dämmerschein\nSchaut´s mich an\nErika\nUnd dann ist es mir als spräch´ es laut:\nDenkst du auch an deine kleine Braut?\nIn der Heimat weint um dich ein Mädelein\nUnd das heißt:\nErika*",
            ),
            Trigger(
                TriggerType.TEXT_TEXT,
                r"(?:^|\W)czy (?:juras|festo|seks|sex|widać) ?\?+?(?:$|\W)",
                "*Jeszcze nie.*",
            ),
            Trigger(
                TriggerType.TEXT_TEXT,
                r"(?:^|\W|_)(?:tesco|bri(?:t|')?ish)(?:$|\W|_)",
                "```\nOI OI OI!\n\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀ \n⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣠⣾⣷⣿⣿⣿⣷⣄⠄⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⢅⠀⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⡀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡗⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠘⢿⣿⠁⣩⣿⣿⣿⠿⣿⡿⢿⣿⣿⣿⠛⣿⡟⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⢷⣾⣿⣋⡡⠤⣀⣷⣄⠠⠤⣉⣿⣷⣽⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⣿⣿⡻⣾⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣟⢋⣰⣯⠉⠉⣿⢄⠉⢻⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀ \n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣿⢿⣷⣶⠤⠔⣶⣶⠿⢾⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⢀⡀⠠⠀⠂⠀⠀⣧⡚⢿⣿⡶⢶⡿⠟⣠⣿⣿⠀⠀⠀⠀⠄⣀⡀⠀⠀ \n⠒⠒⠋⠁⠀⠀⠀⠀⠀⠀⢿⣷⣄⡀⠀⠀⠀⣈⣴⣿⣿⠀⠀⠀⠀⠀⠀⠀⠉⠒ \n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⡿⠒⠐⠺⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀ \n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⢿⣋⣀⡄⠠⣢⣀⣩⣛⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀\nWOTS ALL THIS???\n\n🇬🇧🇬🇧🇬🇧\n\nYER POISTIN LOICENSE HAS EXPOIRED!!!! 🇬🇧🇬🇧🇬🇧🇬🇧\n\nONE HUNNIT TESCO CLUBCARD POINTS 'AVE BIN DEDUCTED FROM YER ACCOUN'!!!!! 🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n\nYER THREE QUID MEAL DEAL IS GONNA BE A FIVER FROM NOW ON!!!! 🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n\nYER WILL ALSO ONLY BE ABLE TER CHOOSE FROM A CHICKEN OR 'AM SANDWICH!!!! 🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n\nFAILURE TO RENEW YER LOICENCE IS GONNA RESUL' IN THA LOSS OV MORE CLUBCARD POINTS!!!!!!!! 🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n\n🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n```",
            ),
            Trigger(
                TriggerType.TEXT_TEXT,
                r"(?:^|\W|_)(?:taiwan|taiwanese|tajwan|tajwanu|tajwanowi|tajwanem|tajwanie)(?:$|\W|_)",
                "```\n⣿⣿⣿⣿⣿⠟⠋⠄⠄⠄⠄⠄⠄⠄⢁⠈⢻⢿⣿⣿⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⠃⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠈⡀⠭⢿⣿⣿⣿⣿\n⣿⣿⣿⣿⡟⠄⢀⣾⣿⣿⣿⣷⣶⣿⣷⣶⣶⡆⠄⠄⠄⣿⣿⣿⣿\n⣿⣿⣿⣿⡇⢀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠄⠄⢸⣿⣿⣿⣿\n⣿⣿⣿⣿⣇⣼⣿⣿⠿⠶⠙⣿⡟⠡⣴⣿⣽⣿⣧⠄⢸⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣾⣿⣿⣟⣭⣾⣿⣷⣶⣶⣴⣶⣿⣿⢄⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣿⣿⣿⡟⣩⣿⣿⣿⡏⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣿⣹⡋⠘⠷⣦⣀⣠⡶⠁⠈⠁⠄⣿⣿⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣿⣍⠃⣴⣶⡔⠒⠄⣠⢀⠄⠄⠄⡨⣿⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣿⣿⣦⡘⠿⣷⣿⠿⠟⠃⠄⠄⣠⡇⠈⠻⣿⣿⣿⣿\n⣿⣿⣿⣿⡿⠟⠋⢁⣷⣠⠄⠄⠄⠄⣀⣠⣾⡟⠄⠄⠄⠄⠉⠙⠻\n⡿⠟⠋⠁⠄⠄⠄⢸⣿⣿⡯⢓⣴⣾⣿⣿⡟⠄⠄⠄⠄⠄⠄⠄⠄\n⠄⠄⠄⠄⠄⠄⠄⣿⡟⣷⠄⠹⣿⣿⣿⡿⠁⠄⠄⠄⠄⠄⠄⠄⠄\nATTENTION CITIZEN! 市民请注意!\nThis is the Central Intelligentsia of the Chinese Communist Party. 您的 Internet 浏览器历史记录和活动引起了我们的注意。 YOUR INTERNET ACTIVITY HAS ATTRACTED OUR ATTENTION. 因此，您的个人资料中的 11115 ( -11115 Social Credits) 个社会积分将打折。 DO NOT DO THIS AGAIN! 不要再这样做! If you do not hesitate, more Social Credits ( -11115 Social Credits )will be subtracted from your profile, resulting in the subtraction of ration supplies. (由人民供应部重新分配 CCP) You'll also be sent into a re-education camp in the Xinjiang Uyghur Autonomous Zone. 如果您毫不犹豫，更多的社会信用将从您的个人资料中打折，从而导致口粮供应减少。 您还将被送到新疆维吾尔自治区的再教育营。\n为党争光! Glory to the CCP!  \n```",
            ),
            Trigger(TriggerType.TEXT_TEXT, r"(?:^| )c?huj$", "ci w dupę"),
            Trigger(
                TriggerType.TEXT_TEXT,
                r"(?:^|\W)mo(?:z|ż)na(?:$|\W)",
                "*Można. Jak najbardziej. Jeszcze jak.*",
            ),
            Trigger(
                TriggerType.TEXT_TEXT,
                r"(?:^|\W)dobrze(?:$|\W)",
                "*Moim zdaniem to nie ma tak, że dobrze albo że nie dobrze. Gdybym miał powiedzieć, co cenię w życiu najbardziej, powiedziałbym, że ludzi. Ekhm... Ludzi, którzy podali mi pomocną dłoń, kiedy sobie nie radziłem, kiedy byłem sam. I co ciekawe, to właśnie przypadkowe spotkania wpływają na nasze życie. Chodzi o to, że kiedy wyznaje się pewne wartości, nawet pozornie uniwersalne, bywa, że nie znajduje się zrozumienia, które by tak rzec, które pomaga się nam rozwijać. Ja miałem szczęście, by tak rzec, ponieważ je znalazłem. I dziękuję życiu. Dziękuję mu, życie to śpiew, życie to taniec, życie to miłość. Wielu ludzi pyta mnie o to samo, ale jak ty to robisz?, skąd czerpiesz tę radość? A ja odpowiadam, że to proste, to umiłowanie życia, to właśnie ono sprawia, że dzisiaj na przykład buduję maszyny, a jutro... kto wie, dlaczego by nie, oddam się pracy społecznej i będę ot, choćby sadzić... znaczy... marchew.*",
            ),
            Trigger(
                TriggerType.TEXT_TEXT,
                r"(?:^|\W)sk(?:a|ą)d litwini wraca(?:ją|ja|li)(?:$|\W)",
                "*Skąd Litwini wracali? Z nocnej wracali wycieczki,\nWieźli łupy bogate, w zamkach i cerkwiach zdobyte.\nTłumy brańców niemieckich z powiązanemi rękami,\nZe stryczkami na szyjach, biegą przy koniach zwycięzców:\nPoglądają ku Prusom — i zalewają się łzami,\nPoglądają na Kowno — i polecają się Bogu!\nW mieście Kownie pośrodku ciągnie się błonie Peruna,\nTam książęta litewscy, gdy po zwycięstwie wracają,\nZwykli rycerzy niemieckich palić na stosie ofiarnym.\nDwaj rycerze pojmani jadą bez trwogi do Kowna,\nJeden młody i piękny, drugi latami schylony;\nOni sami śród bitwy, hufce niemieckie rzuciwszy,\nMiędzy Litwinów uciekli, książę Kiejstut ich przyjął,\nAle strażą otoczył, w zamek za sobą prowadził.\nPyta, z jakiej krainy, w jakich zamiarach przybyli.\n„Nie wiem, rzecze młodzieniec, jaki mój ród i nazwisko,\nBo dziecięciem od Niemców byłem w niewolą schwytany.\nPomnę tylko, że kędyś w Litwie śród miasta wielkiego\nStał dom moich rodziców; było to miasto drewniane\nNa pagórkach wyniosłych, dom był z cegły czerwonej.\nWkoło pagórków na błoniach puszcza szumiała jodłowa,\nŚrodkiem lasów daleko białe błyszczało jezioro.\nRazu jednego w nocy wrzask nas ze snu przebudził,\nDzień ognisty zaświtał w okna, trzaskały się szyby,\nKłęby dymu buchnęły po gmachu, wybiegliśmy w bramę,\nPłomień wiał po ulicach, iskry sypały się gradem,\nKrzyk okropny: „Do broni! Niemcy są w mieście, do broni!“\nOjciec wypadł z orężem, wypadł i więcej nie wrócił.\nNiemcy wpadli do domu, jeden wypuścił się za mną,\nZgonił, porwał mię na koń; nie wiem, co stało się dalej,\nTylko krzyk mojej matki długo, długo słyszałem.\nPośród szczęku oręża, domów runących łoskotu,\nKrzyk ten ścigał mię długo, krzyk ten pozostał w mem uchu.\nTeraz jeszcze, gdy widzę pożar i słyszę wołania,\nKrzyk ten budzi się w duszy, jako echo w jaskini\nZa odgłosem piorunu; oto jest wszystko, co z Litwy,\nCo od rodziców wywiozłem. W sennych niekiedy marzeniach\nWidzę postać szanowną matki i ojca i braci*",
            ),
            Trigger(
                TriggerType.TEXT_TEXT,
                r"(?:^|\W)jak pan jezus powiedzia(?:l|ł)(?:$|\W)",
                "*Tak jak Pan Jezus powiedział*",
            ),
            Trigger(TriggerType.TEXT_TEXT, r"^\d*$", "Wiela???"),
            Trigger(TriggerType.TEXT_REACTION, "💀|czacha", "💀"),
            Trigger(TriggerType.REACTION_REACTION, "💀", "💀"),
            Trigger(TriggerType.TEXT_TEXT, r"(?i)(?:solid.*|snake|w(?:a|ą)(?:z|ż)|metal ?gear|metalowa ?przek(?:ł|l)adnia|invisible|nie ?widzia(?:l|ł).*|invincible|m ?g ?s)\W", "https://media.discordapp.net/attachments/713452179436077229/1316894797256196196/IE40lPkma2UTQZmaX_AEapEt8tke4FwgPN0Hha_RcfE.gif?ex=6852951a&is=6851439a&hm=07d5168887a428947f1d40786775873b0e4720dfe8e72087f58cf259943b6c16&=")
        ]

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content:
            return

        if isinstance(self.bot.command_prefix, str) and message.content.startswith(
            self.bot.command_prefix
        ):
            return

        content = message.content.lower()

        for t in self.triggers:
            if not t.match(content):
                continue

            if t.type is TriggerType.TEXT_TEXT:
                await message.reply(t.output, mention_author=False)
            elif t.type is TriggerType.TEXT_REACTION:
                await message.add_reaction(t.output)
            else:
                continue

            await asyncio.sleep(1)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        if payload.user_id == self.bot.user.id or not payload.emoji.name:  # type: ignore - bot.user can't be None here
            return

        channel = self.bot.get_partial_messageable(payload.channel_id)
        message = discord.PartialMessage(channel=channel, id=payload.message_id)

        for t in self.triggers:
            if not t.match(payload.emoji.name):
                continue

            if t.type is TriggerType.REACTION_TEXT:
                await channel.send(t.output, reference=message, mention_author=False)
            elif t.type is TriggerType.REACTION_REACTION:
                await message.add_reaction(t.output)
            else:
                continue

            await asyncio.sleep(1)


async def setup(bot: DegeneratBot):
    await bot.add_cog(Triggers(bot))
