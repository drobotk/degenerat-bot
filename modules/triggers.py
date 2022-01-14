from discord import Message, AllowedMentions
from discord.ext.commands import Bot, Cog


class Triggers(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

        # eq
        self.triggers = {
            "sus": "amogus",
            "amogus": "ඞ",
            "czy sex?": "*Jeszcze nie.*",
            "czy sex ?": "*Jeszcze nie.*",
            "czy seks?": "*Jeszcze nie.*",
            "czy seks ?": "*Jeszcze nie.*",
        }

        # eq or ends with
        self.end_triggers = {
            "huj": "ci w dupę",
            "chuj": "ci w dupę",
            "można?": "*Można. Jak najbardziej. Jeszcze jak.*",
            "można ?": "*Można. Jak najbardziej. Jeszcze jak.*",
            "dobrze?": "*Moim zdaniem to nie ma tak, że dobrze albo że nie dobrze. Gdybym miał powiedzieć, co cenię w życiu najbardziej, powiedziałbym, że ludzi. Ekhm... Ludzi, którzy podali mi pomocną dłoń, kiedy sobie nie radziłem, kiedy byłem sam. I co ciekawe, to właśnie przypadkowe spotkania wpływają na nasze życie. Chodzi o to, że kiedy wyznaje się pewne wartości, nawet pozornie uniwersalne, bywa, że nie znajduje się zrozumienia, które by tak rzec, które pomaga się nam rozwijać. Ja miałem szczęście, by tak rzec, ponieważ je znalazłem. I dziękuję życiu. Dziękuję mu, życie to śpiew, życie to taniec, życie to miłość. Wielu ludzi pyta mnie o to samo, ale jak ty to robisz?, skąd czerpiesz tę radość? A ja odpowiadam, że to proste, to umiłowanie życia, to właśnie ono sprawia, że dzisiaj na przykład buduję maszyny, a jutro... kto wie, dlaczego by nie, oddam się pracy społecznej i będę ot, choćby sadzić... znaczy... marchew.*",
            "dobrze ?": "*Moim zdaniem to nie ma tak, że dobrze albo że nie dobrze. Gdybym miał powiedzieć, co cenię w życiu najbardziej, powiedziałbym, że ludzi. Ekhm... Ludzi, którzy podali mi pomocną dłoń, kiedy sobie nie radziłem, kiedy byłem sam. I co ciekawe, to właśnie przypadkowe spotkania wpływają na nasze życie. Chodzi o to, że kiedy wyznaje się pewne wartości, nawet pozornie uniwersalne, bywa, że nie znajduje się zrozumienia, które by tak rzec, które pomaga się nam rozwijać. Ja miałem szczęście, by tak rzec, ponieważ je znalazłem. I dziękuję życiu. Dziękuję mu, życie to śpiew, życie to taniec, życie to miłość. Wielu ludzi pyta mnie o to samo, ale jak ty to robisz?, skąd czerpiesz tę radość? A ja odpowiadam, że to proste, to umiłowanie życia, to właśnie ono sprawia, że dzisiaj na przykład buduję maszyny, a jutro... kto wie, dlaczego by nie, oddam się pracy społecznej i będę ot, choćby sadzić... znaczy... marchew.*",
            "skąd litwini wracają?": "*Skąd Litwini wracali? Z nocnej wracali wycieczki,\nWieźli łupy bogate, w zamkach i cerkwiach zdobyte.\nTłumy brańców niemieckich z powiązanemi rękami,\nZe stryczkami na szyjach, biegą przy koniach zwycięzców:\nPoglądają ku Prusom — i zalewają się łzami,\nPoglądają na Kowno — i polecają się Bogu!\nW mieście Kownie pośrodku ciągnie się błonie Peruna,\nTam książęta litewscy, gdy po zwycięstwie wracają,\nZwykli rycerzy niemieckich palić na stosie ofiarnym.\nDwaj rycerze pojmani jadą bez trwogi do Kowna,\nJeden młody i piękny, drugi latami schylony;\nOni sami śród bitwy, hufce niemieckie rzuciwszy,\nMiędzy Litwinów uciekli, książę Kiejstut ich przyjął,\nAle strażą otoczył, w zamek za sobą prowadził.\nPyta, z jakiej krainy, w jakich zamiarach przybyli.\n„Nie wiem, rzecze młodzieniec, jaki mój ród i nazwisko,\nBo dziecięciem od Niemców byłem w niewolą schwytany.\nPomnę tylko, że kędyś w Litwie śród miasta wielkiego\nStał dom moich rodziców; było to miasto drewniane\nNa pagórkach wyniosłych, dom był z cegły czerwonej.\nWkoło pagórków na błoniach puszcza szumiała jodłowa,\nŚrodkiem lasów daleko białe błyszczało jezioro.\nRazu jednego w nocy wrzask nas ze snu przebudził,\nDzień ognisty zaświtał w okna, trzaskały się szyby,\nKłęby dymu buchnęły po gmachu, wybiegliśmy w bramę,\nPłomień wiał po ulicach, iskry sypały się gradem,\nKrzyk okropny: „Do broni! Niemcy są w mieście, do broni!“\nOjciec wypadł z orężem, wypadł i więcej nie wrócił.\nNiemcy wpadli do domu, jeden wypuścił się za mną,\nZgonił, porwał mię na koń; nie wiem, co stało się dalej,\nTylko krzyk mojej matki długo, długo słyszałem.\nPośród szczęku oręża, domów runących łoskotu,\nKrzyk ten ścigał mię długo, krzyk ten pozostał w mem uchu.\nTeraz jeszcze, gdy widzę pożar i słyszę wołania,\nKrzyk ten budzi się w duszy, jako echo w jaskini\nZa odgłosem piorunu; oto jest wszystko, co z Litwy,\nCo od rodziców wywiozłem. W sennych niekiedy marzeniach\nWidzę postać szanowną matki i ojca i braci*",
            "skąd litwini wracają ?": "*Skąd Litwini wracali? Z nocnej wracali wycieczki,\nWieźli łupy bogate, w zamkach i cerkwiach zdobyte.\nTłumy brańców niemieckich z powiązanemi rękami,\nZe stryczkami na szyjach, biegą przy koniach zwycięzców:\nPoglądają ku Prusom — i zalewają się łzami,\nPoglądają na Kowno — i polecają się Bogu!\nW mieście Kownie pośrodku ciągnie się błonie Peruna,\nTam książęta litewscy, gdy po zwycięstwie wracają,\nZwykli rycerzy niemieckich palić na stosie ofiarnym.\nDwaj rycerze pojmani jadą bez trwogi do Kowna,\nJeden młody i piękny, drugi latami schylony;\nOni sami śród bitwy, hufce niemieckie rzuciwszy,\nMiędzy Litwinów uciekli, książę Kiejstut ich przyjął,\nAle strażą otoczył, w zamek za sobą prowadził.\nPyta, z jakiej krainy, w jakich zamiarach przybyli.\n„Nie wiem, rzecze młodzieniec, jaki mój ród i nazwisko,\nBo dziecięciem od Niemców byłem w niewolą schwytany.\nPomnę tylko, że kędyś w Litwie śród miasta wielkiego\nStał dom moich rodziców; było to miasto drewniane\nNa pagórkach wyniosłych, dom był z cegły czerwonej.\nWkoło pagórków na błoniach puszcza szumiała jodłowa,\nŚrodkiem lasów daleko białe błyszczało jezioro.\nRazu jednego w nocy wrzask nas ze snu przebudził,\nDzień ognisty zaświtał w okna, trzaskały się szyby,\nKłęby dymu buchnęły po gmachu, wybiegliśmy w bramę,\nPłomień wiał po ulicach, iskry sypały się gradem,\nKrzyk okropny: „Do broni! Niemcy są w mieście, do broni!“\nOjciec wypadł z orężem, wypadł i więcej nie wrócił.\nNiemcy wpadli do domu, jeden wypuścił się za mną,\nZgonił, porwał mię na koń; nie wiem, co stało się dalej,\nTylko krzyk mojej matki długo, długo słyszałem.\nPośród szczęku oręża, domów runących łoskotu,\nKrzyk ten ścigał mię długo, krzyk ten pozostał w mem uchu.\nTeraz jeszcze, gdy widzę pożar i słyszę wołania,\nKrzyk ten budzi się w duszy, jako echo w jaskini\nZa odgłosem piorunu; oto jest wszystko, co z Litwy,\nCo od rodziców wywiozłem. W sennych niekiedy marzeniach\nWidzę postać szanowną matki i ojca i braci*",
            "jak pan jezus powiedział?": "*Tak jak Pan Jezus powiedział*",
            "jak pan jezus powiedział ?": "*Tak jak Pan Jezus powiedział*",
            "erika": "*Auf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\nHeiß von hunderttausend kleinen Bienelein\nWird umschwärmt:\nErika\nDenn ihr Herz ist voller Süßigkeit\nZarter Duft entströmt dem Blütenkleid\nAuf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\n\nIn der Heimat wohnt ein kleines Mädelein\nUnd das heißt:\nErika\nDieses Mädel ist mein treues Schätzelein\nUnd mein Glück\nErika\nWenn das Heidekraut rot-lila blüht\nSinge ich zum Gruß ihr dieses Lied\nAuf der Heide blüht ein kleines Blümelein\nUnd das heißt:\nErika\n\nIn mein´m Kämmerlein blüht auch ein Blümelein\nUnd das heißt:\nErika\nSchon beim Morgengrau´n sowie beim Dämmerschein\nSchaut´s mich an\nErika\nUnd dann ist es mir als spräch´ es laut:\nDenkst du auch an deine kleine Braut?\nIn der Heimat weint um dich ein Mädelein\nUnd das heißt:\nErika*",
        }

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

    def spellcheck(self, input: str) -> str:
        words = input.split(" ")
        corrected = " ".join(
            set([self.spelling[t] for t in self.spelling if t in words])
        )
        if corrected:
            corrected += ", debilu głupi"

        return corrected

    def check_triggers(self, input: str) -> str:
        # end triggers first
        for t in self.end_triggers:
            if input == t or input.endswith(" " + t):
                return self.end_triggers[t]

        for t in self.triggers:
            if input == t:
                return self.triggers[t]

        return self.spellcheck(input)

    @Cog.listener()
    async def on_message(self, message: Message):
        if message.author.bot or not message.content:
            return

        if message.content.startswith(self.bot.command_prefix):
            return

        res = self.check_triggers(message.content.lower())
        if res:
            await message.reply(
                res, allowed_mentions=AllowedMentions(replied_user=False)
            )


def setup(bot: Bot):
    bot.add_cog(Triggers(bot))
