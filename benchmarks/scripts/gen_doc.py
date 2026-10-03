# Generates a FICTITIOUS Dutch notarial sale deed as a scanned (image-only) PDF.
# All names, addresses, numbers are invented. Writes deed_scan.pdf + ground_truth.json
import json, random
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from pdf2image import convert_from_bytes
from PIL import ImageFilter, Image
import numpy as np

random.seed(7); np.random.seed(7)
pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"))
ss = getSampleStyleSheet()
body = ParagraphStyle("b", parent=ss["Normal"], fontName="DV", fontSize=10.5, leading=15, alignment=4)
h = ParagraphStyle("h", parent=body, fontName="DVB", fontSize=12, spaceBefore=10, spaceAfter=4, alignment=0)
title = ParagraphStyle("t", parent=h, fontSize=15, alignment=1)

facts = {
    "verkoper": "Hendrika Johanna van Velzenburg",
    "koper": "Bastiaan Pieter Oudewater en Marloes Anna de Kleijnhorst",
    "adres": "Lindenhofstraat 47, 9731 KX Groningen",
    "kadaster": "gemeente Groningen, sectie K, nummer 4182",
    "koopprijs": "EUR 412.500,00",
    "waarborgsom": "EUR 41.250,00",
    "datum_akte": "14 augustus 2026",
    "notaris": "mr. Ewoud Frederik Kampsteeg",
    "financieringsvoorbehoud": "1 oktober 2026",
    "levering": "31 oktober 2026",
}

paras = [
 ("t", "AKTE VAN LEVERING"),
 ("p", "Kenmerk: EFK/2026/0817-L"),
 ("p", f"Heden, {facts['datum_akte']}, verschijnen voor mij, {facts['notaris']}, notaris te Groningen:"),
 ("p", f"1. mevrouw {facts['verkoper']}, geboren te Assen op drie maart negentienhonderd achtenvijftig, wonende te 9712 AB Groningen, Oude Boteringestraat 112, zich legitimerende met paspoort nummer NX4R7T2P9, ongehuwd en geen geregistreerd partner, hierna te noemen: ‘verkoper’;"),
 ("p", "2. de heer Bastiaan Pieter Oudewater, geboren te Zwolle op negentien juni negentienhonderd negentig, en mevrouw Marloes Anna de Kleijnhorst, geboren te Leeuwarden op zeven november negentienhonderd eenennegentig, beiden wonende te 9726 CD Groningen, Herestraat 9, samen hierna te noemen: ‘koper’."),
 ("h", "Artikel 1 — Koopovereenkomst"),
 ("p", f"Verkoper en koper hebben een koopovereenkomst gesloten met betrekking tot de hierna te omschrijven onroerende zaak. Die koopovereenkomst is neergelegd in een door partijen ondertekende akte van tien juni tweeduizend zesentwintig. Ter uitvoering daarvan levert verkoper aan koper, die blijkens de koopovereenkomst gezamenlijk ieder voor de onverdeelde helft aanvaardt: het woonhuis met erf, tuin en verdere aanhorigheden, plaatselijk bekend als {facts['adres']}, kadastraal bekend {facts['kadaster']}, groot vijf are en vierendertig centiare, hierna te noemen: ‘het verkochte’."),
 ("h", "Artikel 2 — Koopprijs en betaling"),
 ("p", f"De koopprijs bedraagt {facts['koopprijs']} (vierhonderdtwaalfduizend vijfhonderd euro), kosten koper. Koper heeft ter zekerheid van nakoming een waarborgsom van {facts['waarborgsom']} gestort op de kwaliteitsrekening van de notaris. Deze waarborgsom wordt met de koopprijs verrekend. De koopprijs is voldaan door storting op de kwaliteitsrekening van de notaris, waarvoor verkoper bij deze kwijting verleent."),
 ("tbl", [["Omschrijving", "Bedrag"], ["Koopprijs", "EUR 412.500,00"], ["Roerende zaken (zonwering, vloerbedekking)", "EUR 3.750,00"], ["Overdrachtsbelasting (2%)", "EUR 8.250,00"], ["Notariskosten en kadasterrechten", "EUR 1.486,35"], ["Totaal ten laste van koper", "EUR 425.986,35"]]),
 ("h", "Artikel 3 — Opschortende en ontbindende voorwaarden"),
 ("p", f"De koopovereenkomst is aangegaan onder de ontbindende voorwaarde dat koper uiterlijk op {facts['financieringsvoorbehoud']} geen bindende toezegging heeft verkregen voor een hypothecaire geldlening van ten minste EUR 330.000,00 tegen gebruikelijke voorwaarden (financieringsvoorbehoud). Partijen verklaren dat deze voorwaarde niet in vervulling is gegaan. Voorts is de overeenkomst aangegaan onder de opschortende voorwaarde dat de gemeente Groningen geen gebruik maakt van een voorkeursrecht als bedoeld in de Wet voorkeursrecht gemeenten."),
 ("h", "Artikel 4 — Feitelijke levering en risico"),
 ("p", f"Het verkochte wordt aanvaard in de staat waarin het zich bij het sluiten van de koopovereenkomst bevond. De feitelijke levering geschiedt uiterlijk op {facts['levering']}, vrij van huur en gebruik, met overdracht van alle sleutels. Het verkochte is vanaf de ondertekening van deze akte voor rekening en risico van koper."),
 ("h", "Artikel 5 — Lasten en beperkingen; erfdienstbaarheden"),
 ("p", "Bij de akte van levering ingeschreven ten kantore van de Dienst voor het kadaster en de openbare registers op twaalf mei negentienhonderd zesentachtig in register Hypotheken 4, deel 9811, nummer 23, is een erfdienstbaarheid van overpad gevestigd ten laste van het verkochte en ten behoeve van het perceel kadastraal bekend gemeente Groningen, sectie K, nummer 4183. Het overpad heeft een breedte van één meter en twintig centimeter langs de oostelijke perceelsgrens. Koper aanvaardt deze erfdienstbaarheid uitdrukkelijk."),
 ("p", "Verkoper verklaart dat het verkochte niet is aangewezen als beschermd monument, dat er geen aanschrijvingen van overheidswege bekend zijn en dat er geen bodemverontreiniging bekend is die een belemmering vormt voor het gebruik als woning. Op het verkochte rust een kettingbeding met betrekking tot het onderhoud van een gemeenschappelijke scheidsmuur, welk beding koper bij deze aanvaardt en zal opleggen aan iedere rechtsopvolger, op straffe van een boete van EUR 5.000,00."),
 ("h", "Artikel 6 — Garanties en ouderdomsclausule"),
 ("p", "Verkoper staat ervoor in dat het verkochte bij de feitelijke levering de feitelijke eigenschappen bezit die nodig zijn voor normaal gebruik als woonhuis. Koper is ermee bekend dat het verkochte omstreeks negentienhonderd dertig is gebouwd en dat de eisen die aan de kwaliteit kunnen worden gesteld lager liggen dan bij nieuwbouw. Verkoper staat niet in voor de afwezigheid van asbesthoudende materialen. Koper heeft een bouwkundige keuring laten verrichten door Bouwadvies Noordermeer B.V. op twintig juni tweeduizend zesentwintig."),
 ("h", "Artikel 7 — Hypotheekrecht en doorhaling"),
 ("p", "Verkoper verklaart dat op het verkochte een recht van hypotheek rust ten behoeve van de Coöperatieve Spaarbank Eemsdelta U.A., tot zekerheid van een hoofdsom van EUR 180.000,00. Uit de koopprijs wordt een bedrag van EUR 96.418,72 aan de hypotheekhouder voldaan, waarna de hypotheekhouder toestemming tot doorhaling van de inschrijving heeft verleend. Het verkochte wordt geleverd vrij van hypotheken en beslagen."),
 ("h", "Artikel 8 — Woonplaatskeuze en slotbepalingen"),
 ("p", "Voor de uitvoering van deze akte kiezen partijen woonplaats ten kantore van de bewaarder van deze akte. Partijen verklaren tijdig voor het verlijden van deze akte een ontwerp daarvan te hebben ontvangen. De zakelijke inhoud van deze akte is aan de verschenen personen opgegeven en toegelicht. Zij hebben verklaard van de inhoud kennis te hebben genomen en op volledige voorlezing daarvan geen prijs te stellen."),
 ("p", "WAARVAN AKTE, in minuut verleden te Groningen op de datum in het hoofd van deze akte vermeld. Onmiddellijk na beperkte voorlezing is deze akte door de verschenen personen en mij, notaris, ondertekend."),
 ("p", "(volgen handtekeningen)"),
 ("p", "<i>Dit document is volledig fictief en uitsluitend gegenereerd voor een benchmark. Alle namen, adressen en nummers zijn verzonnen.</i>"),
]

story, gt = [], []
for kind, c in paras:
    if kind == "tbl":
        t = Table(c, colWidths=[300, 120])
        t.setStyle(TableStyle([("FONT", (0,0), (-1,-1), "DV", 10), ("FONT", (0,0), (-1,0), "DVB", 10),
                               ("GRID", (0,0), (-1,-1), 0.5, colors.black), ("ALIGN", (1,0), (1,-1), "RIGHT")]))
        story += [Spacer(1,6), t, Spacer(1,6)]
        gt.append("\n".join(" ".join(r) for r in c))
    else:
        story.append(Paragraph(c, {"t": title, "h": h, "p": body}[kind]))
        gt.append(c.replace("<i>","").replace("</i>",""))
# padding to make it a realistic ~5 page deed: repeat a schedule (bijlage) of definitions
story.append(Paragraph("BIJLAGE 1 — Algemene bepalingen", h)); gt.append("BIJLAGE 1 — Algemene bepalingen")
for i, (k, v) in enumerate([("Onderhoud", "Verkoper zal het verkochte tot de feitelijke levering in dezelfde staat houden als bij het sluiten van de koopovereenkomst."),
    ("Bodem", "Partijen verklaren dat geen onderzoek naar de bodemgesteldheid heeft plaatsgevonden en dat koper het risico daarvan draagt, behoudens opzet of grove schuld van verkoper."),
    ("Ingebrekestelling", "Indien een van de partijen na ingebrekestelling gedurende acht dagen tekortschiet in de nakoming, is deze partij in verzuim en verbeurt zij een direct opeisbare boete van drie procent van de koopprijs."),
    ("Ontbinding", "Ontbinding van de overeenkomst geschiedt door een schriftelijke verklaring van de tot ontbinding gerechtigde partij."),
    ("Verrekening", "De over het lopende jaar verschuldigde onroerendezaakbelasting, waterschapslasten en rioolheffing worden naar tijdsevenredigheid tussen partijen verrekend."),
    ("Energielabel", "Verkoper heeft aan koper een geldig energielabel met klasse C ter hand gesteld, geregistreerd onder nummer EP-2026-77310."),
    ("Privacy", "De notaris verwerkt persoonsgegevens van partijen uitsluitend ten behoeve van het verlijden en inschrijven van deze akte en de wettelijke bewaarplicht.")] * 2, 1):
    s = f"{i}. {k}. {v}"
    story.append(Paragraph(s, body)); gt.append(s)

buf = BytesIO()
SimpleDocTemplate(buf, pagesize=A4, leftMargin=70, rightMargin=70, topMargin=70, bottomMargin=70).build(story)
pages = convert_from_bytes(buf.getvalue(), dpi=200, grayscale=True)
scans = []
for p in pages:  # simulate a office scanner: slight skew, blur, noise
    p = p.rotate(random.uniform(-0.8, 0.8), expand=False, fillcolor=255, resample=Image.BICUBIC)
    p = p.filter(ImageFilter.GaussianBlur(0.6))
    a = np.asarray(p).astype(np.int16) + np.random.normal(0, 12, (p.height, p.width)).astype(np.int16)
    scans.append(Image.fromarray(np.clip(a, 0, 255).astype(np.uint8)).convert("L"))
scans[0].save("deed_scan.pdf", save_all=True, append_images=scans[1:], resolution=200)
json.dump({"facts": facts, "text": "\n".join(gt), "pages": len(scans)}, open("ground_truth.json", "w"), ensure_ascii=False, indent=1)
print("pages:", len(scans))
