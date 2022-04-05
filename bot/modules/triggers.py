import re

import discord
from discord.ext import commands

from ..bot import DegeneratBot


class Triggers(commands.Cog):
    def __init__(self, bot: DegeneratBot):
        self.bot: DegeneratBot = bot

        self.triggers: dict[re.Pattern, str] = {}
        self.add_trigger(r"^sus$", "amogus")
        self.add_trigger(r"^amogus$", "ඞ")
        self.add_trigger(
            r"^erika$",
            "*Auf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\nHeiß von hunderttausend kleinen Bienelein\nWird umschwärmt:\nErika\nDenn ihr Herz ist voller Süßigkeit\nZarter Duft entströmt dem Blütenkleid\nAuf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\n\nIn der Heimat wohnt ein kleines Mädelein\nUnd das heißt:\nErika\nDieses Mädel ist mein treues Schätzelein\nUnd mein Glück\nErika\nWenn das Heidekraut rot-lila blüht\nSinge ich zum Gruß ihr dieses Lied\nAuf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\n\nIn mein´m Kämmerlein blüht auch ein Blümelein\nUnd das heißt:\nErika\nSchon beim Morgengrau´n sowie beim Dämmerschein\nSchaut´s mich an\nErika\nUnd dann ist es mir als spräch´ es laut:\nDenkst du auch an deine kleine Braut?\nIn der Heimat weint um dich ein Mädelein\nUnd das heißt:\nErika*",
        )
        self.add_trigger(r"^czy (?:juras|festo|seks|sex) ?\?+?$", "*Jeszcze nie.*")
        self.add_trigger(
            r"^tesco$",
            "```\nOI OI OI!\n\n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⡀⠀⠀⠀⠀⠀ \n⠀⠀⠀⠀⠀⠀⠀⠀⠀⢠⣠⣾⣷⣿⣿⣿⣷⣄⠄⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⣀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣷⣦⢅⠀⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⢀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣷⡄⡀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡗⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⣾⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⡆⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠘⢿⣿⠁⣩⣿⣿⣿⠿⣿⡿⢿⣿⣿⣿⠛⣿⡟⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⢷⣾⣿⣋⡡⠤⣀⣷⣄⠠⠤⣉⣿⣷⣽⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠈⣿⣿⣿⣿⣿⣿⣿⣿⡻⣾⣿⣿⣿⡟⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⠀⠀⠀⠀⠀⠙⣿⣟⢋⣰⣯⠉⠉⣿⢄⠉⢻⡟⠀⠀⠀⠀⠀⠀⠀⠀⠀ \n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠹⣿⢿⣷⣶⠤⠔⣶⣶⠿⢾⣧⠀⠀⠀⠀⠀⠀⠀⠀⠀\n⠀⠀⠀⢀⡀⠠⠀⠂⠀⠀⣧⡚⢿⣿⡶⢶⡿⠟⣠⣿⣿⠀⠀⠀⠀⠄⣀⡀⠀⠀ \n⠒⠒⠋⠁⠀⠀⠀⠀⠀⠀⢿⣷⣄⡀⠀⠀⠀⣈⣴⣿⣿⠀⠀⠀⠀⠀⠀⠀⠉⠒ \n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⣿⣿⡿⠒⠐⠺⣿⣿⣿⣿⠀⠀⠀⠀⠀⠀⠀⠀⠀ \n⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢸⢿⣋⣀⡄⠠⣢⣀⣩⣛⠇⠀⠀⠀⠀⠀⠀⠀⠀⠀\nWOTS ALL THIS???\n\n🇬🇧🇬🇧🇬🇧\n\nYER POISTIN LOICENSE HAS EXPOIRED!!!! 🇬🇧🇬🇧🇬🇧🇬🇧\n\nONE HUNNIT TESCO CLUBCARD POINTS 'AVE BIN DEDUCTED FROM YER ACCOUN'!!!!! 🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n\nYER THREE QUID MEAL DEAL IS GONNA BE A FIVER FROM NOW ON!!!! 🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n\nYER WILL ALSO ONLY BE ABLE TER CHOOSE FROM A CHICKEN OR 'AM SANDWICH!!!! 🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n\nFAILURE TO RENEW YER LOICENCE IS GONNA RESUL' IN THA LOSS OV MORE CLUBCARD POINTS!!!!!!!! 🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n\n🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧🇬🇧\n```",
        )
        self.add_trigger(
            r"^(?:taiwan|tajwan)$",
            "```\n⣿⣿⣿⣿⣿⠟⠋⠄⠄⠄⠄⠄⠄⠄⢁⠈⢻⢿⣿⣿⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⠃⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠄⠈⡀⠭⢿⣿⣿⣿⣿\n⣿⣿⣿⣿⡟⠄⢀⣾⣿⣿⣿⣷⣶⣿⣷⣶⣶⡆⠄⠄⠄⣿⣿⣿⣿\n⣿⣿⣿⣿⡇⢀⣼⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿⣧⠄⠄⢸⣿⣿⣿⣿\n⣿⣿⣿⣿⣇⣼⣿⣿⠿⠶⠙⣿⡟⠡⣴⣿⣽⣿⣧⠄⢸⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣾⣿⣿⣟⣭⣾⣿⣷⣶⣶⣴⣶⣿⣿⢄⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣿⣿⣿⡟⣩⣿⣿⣿⡏⢻⣿⣿⣿⣿⣿⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣿⣹⡋⠘⠷⣦⣀⣠⡶⠁⠈⠁⠄⣿⣿⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣿⣍⠃⣴⣶⡔⠒⠄⣠⢀⠄⠄⠄⡨⣿⣿⣿⣿⣿⣿\n⣿⣿⣿⣿⣿⣿⣿⣦⡘⠿⣷⣿⠿⠟⠃⠄⠄⣠⡇⠈⠻⣿⣿⣿⣿\n⣿⣿⣿⣿⡿⠟⠋⢁⣷⣠⠄⠄⠄⠄⣀⣠⣾⡟⠄⠄⠄⠄⠉⠙⠻\n⡿⠟⠋⠁⠄⠄⠄⢸⣿⣿⡯⢓⣴⣾⣿⣿⡟⠄⠄⠄⠄⠄⠄⠄⠄\n⠄⠄⠄⠄⠄⠄⠄⣿⡟⣷⠄⠹⣿⣿⣿⡿⠁⠄⠄⠄⠄⠄⠄⠄⠄\nATTENTION CITIZEN! 市民请注意!\nThis is the Central Intelligentsia of the Chinese Communist Party. 您的 Internet 浏览器历史记录和活动引起了我们的注意。 YOUR INTERNET ACTIVITY HAS ATTRACTED OUR ATTENTION. 因此，您的个人资料中的 11115 ( -11115 Social Credits) 个社会积分将打折。 DO NOT DO THIS AGAIN! 不要再这样做! If you do not hesitate, more Social Credits ( -11115 Social Credits )will be subtracted from your profile, resulting in the subtraction of ration supplies. (由人民供应部重新分配 CCP) You'll also be sent into a re-education camp in the Xinjiang Uyghur Autonomous Zone. 如果您毫不犹豫，更多的社会信用将从您的个人资料中打折，从而导致口粮供应减少。 您还将被送到新疆维吾尔自治区的再教育营。\n为党争光! Glory to the CCP!  \n```",
        )

        self.add_trigger(r"(?:^| )c?huj$", "ci w dupę")
        self.add_trigger(
            r"(?:^| )można ?\?+?$", "*Można. Jak najbardziej. Jeszcze jak.*"
        )
        self.add_trigger(
            r"(?:^| )dobrze ?\?+?$",
            "*Moim zdaniem to nie ma tak, że dobrze albo że nie dobrze. Gdybym miał powiedzieć, co cenię w życiu najbardziej, powiedziałbym, że ludzi. Ekhm... Ludzi, którzy podali mi pomocną dłoń, kiedy sobie nie radziłem, kiedy byłem sam. I co ciekawe, to właśnie przypadkowe spotkania wpływają na nasze życie. Chodzi o to, że kiedy wyznaje się pewne wartości, nawet pozornie uniwersalne, bywa, że nie znajduje się zrozumienia, które by tak rzec, które pomaga się nam rozwijać. Ja miałem szczęście, by tak rzec, ponieważ je znalazłem. I dziękuję życiu. Dziękuję mu, życie to śpiew, życie to taniec, życie to miłość. Wielu ludzi pyta mnie o to samo, ale jak ty to robisz?, skąd czerpiesz tę radość? A ja odpowiadam, że to proste, to umiłowanie życia, to właśnie ono sprawia, że dzisiaj na przykład buduję maszyny, a jutro... kto wie, dlaczego by nie, oddam się pracy społecznej i będę ot, choćby sadzić... znaczy... marchew.*",
        )
        self.add_trigger(
            r"(?:^| )sk(?:a|ą)d litwini wraca(?:ją|ja|li) ?\?+?$",
            "*Skąd Litwini wracali? Z nocnej wracali wycieczki,\nWieźli łupy bogate, w zamkach i cerkwiach zdobyte.\nTłumy brańców niemieckich z powiązanemi rękami,\nZe stryczkami na szyjach, biegą przy koniach zwycięzców:\nPoglądają ku Prusom — i zalewają się łzami,\nPoglądają na Kowno — i polecają się Bogu!\nW mieście Kownie pośrodku ciągnie się błonie Peruna,\nTam książęta litewscy, gdy po zwycięstwie wracają,\nZwykli rycerzy niemieckich palić na stosie ofiarnym.\nDwaj rycerze pojmani jadą bez trwogi do Kowna,\nJeden młody i piękny, drugi latami schylony;\nOni sami śród bitwy, hufce niemieckie rzuciwszy,\nMiędzy Litwinów uciekli, książę Kiejstut ich przyjął,\nAle strażą otoczył, w zamek za sobą prowadził.\nPyta, z jakiej krainy, w jakich zamiarach przybyli.\n„Nie wiem, rzecze młodzieniec, jaki mój ród i nazwisko,\nBo dziecięciem od Niemców byłem w niewolą schwytany.\nPomnę tylko, że kędyś w Litwie śród miasta wielkiego\nStał dom moich rodziców; było to miasto drewniane\nNa pagórkach wyniosłych, dom był z cegły czerwonej.\nWkoło pagórków na błoniach puszcza szumiała jodłowa,\nŚrodkiem lasów daleko białe błyszczało jezioro.\nRazu jednego w nocy wrzask nas ze snu przebudził,\nDzień ognisty zaświtał w okna, trzaskały się szyby,\nKłęby dymu buchnęły po gmachu, wybiegliśmy w bramę,\nPłomień wiał po ulicach, iskry sypały się gradem,\nKrzyk okropny: „Do broni! Niemcy są w mieście, do broni!“\nOjciec wypadł z orężem, wypadł i więcej nie wrócił.\nNiemcy wpadli do domu, jeden wypuścił się za mną,\nZgonił, porwał mię na koń; nie wiem, co stało się dalej,\nTylko krzyk mojej matki długo, długo słyszałem.\nPośród szczęku oręża, domów runących łoskotu,\nKrzyk ten ścigał mię długo, krzyk ten pozostał w mem uchu.\nTeraz jeszcze, gdy widzę pożar i słyszę wołania,\nKrzyk ten budzi się w duszy, jako echo w jaskini\nZa odgłosem piorunu; oto jest wszystko, co z Litwy,\nCo od rodziców wywiozłem. W sennych niekiedy marzeniach\nWidzę postać szanowną matki i ojca i braci*",
        )
        self.add_trigger(
            r"(?:^| )jak pan jezus powiedzia(?:l|ł) ?\?+?$",
            "*Tak jak Pan Jezus powiedział*",
        )

        self.spelling = {
            "muj": "_*mój_",
            "jóż": "_*już_",
            "józ": "_*już_",
            "joż": "_*już_",
            "ktury": "_*który_",
            "ktura": "_*która_",
            "kturego": "_*którego_",
            "kturzy": "_*którzy_",
            "twuj": "_*twój_",
            "hyba": "_*chyba_",
            "puzniej": "_*później_",
            "puźniej": "_*później_",
            "ogulnie": "_*ogólnie_",
            "ogulne": "_*ogólne_",
            "ogulny": "_*ogólny_",
            "ogulna": "_*ogólna_",
        }

    def add_trigger(self, pattern: str, response: str):
        p = re.compile(pattern)
        self.triggers[p] = response

    def spellcheck(self, input: str) -> str:
        words = input.split(" ")
        corrected = " ".join(
            list(dict.fromkeys([self.spelling[t] for t in self.spelling if t in words]))
        )
        if corrected:
            corrected += ", debilu głupi"

        return corrected

    def check_triggers(self, input: str) -> str:
        for pattern, res in self.triggers.items():
            if pattern.search(input):
                return res

        return self.spellcheck(input)

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author.bot or not message.content:
            return

        if message.content.startswith(self.bot.command_prefix):
            return

        res = self.check_triggers(message.content.lower())
        if not res:
            return

        await message.reply(res, mention_author=False)


async def setup(bot: DegeneratBot):
    await bot.add_cog(Triggers(bot))
