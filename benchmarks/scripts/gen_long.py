"""Generate FICTITIOUS born-digital Dutch commercial real-estate deeds for long-document tests.
All names, companies, numbers are invented.
    python gen_long.py   -> long60.pdf (~60 p) + c1..c4.pdf (~20 p) + long_truth.json
Each deed has planted facts (with checkable keywords), spread through the document incl. deep in
annexes and on the last page, to test whether a summary finds them.
"""
import json, random
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
pdfmetrics.registerFont(TTFont("DVB", "/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf"))
ss = getSampleStyleSheet()
BODY = ParagraphStyle("b", parent=ss["Normal"], fontName="DV", fontSize=10, leading=14, alignment=4, spaceAfter=4)
H1 = ParagraphStyle("h1", parent=BODY, fontName="DVB", fontSize=13, spaceBefore=12, spaceAfter=6, alignment=0)
H2 = ParagraphStyle("h2", parent=BODY, fontName="DVB", fontSize=11, spaceBefore=8, spaceAfter=4, alignment=0)

# ---------- boilerplate generators (varied, so text is not trivially repetitive) ----------
SUBJ = ["Partijen", "Koper", "Verkoper", "De huurder", "De verhuurder", "Iedere partij", "De zekerheidsgever", "De bank"]
VERB = ["verklaart", "erkent", "aanvaardt", "verbindt zich", "staat ervoor in", "is gehouden"]
OBJ = ["dat de bepalingen van dit artikel onverkort van toepassing blijven na de levering",
       "dat eventuele geschillen worden beslecht door de bevoegde rechter te 's-Hertogenbosch",
       "dat mededelingen schriftelijk geschieden aan het in de aanhef vermelde adres",
       "dat kosten van onderhoud naar rato van het gebruik worden omgeslagen",
       "dat wijzigingen van deze bepaling slechts bij notariële akte kunnen worden overeengekomen",
       "dat de verplichtingen hoofdelijk gelden voor ieder van de rechtsopvolgers",
       "dat de zekerheden in stand blijven tot volledige voldoening van het verschuldigde",
       "dat een tekortkoming eerst na schriftelijke ingebrekestelling met een termijn van veertien dagen verzuim oplevert",
       "dat de verzekering van het gebouw tegen herbouwwaarde wordt voortgezet",
       "dat de servicekosten jaarlijks binnen zes maanden na afloop van het kalenderjaar worden afgerekend",
       "dat indexering plaatsvindt op basis van de consumentenprijsindex (CPI), reeks alle huishoudens",
       "dat de gebruiksvergunning en de brandveiligheidsvoorschriften steeds worden nageleefd"]
QUAL = ["", ", behoudens voor zover in deze akte uitdrukkelijk anders is bepaald", ", zulks met inachtneming van de wettelijke bepalingen",
        ", onverminderd het recht op schadevergoeding", ", voor zover redelijkerwijs mogelijk"]


def filler(rng, n):
    return " ".join(f"{rng.choice(SUBJ)} {rng.choice(VERB)} {rng.choice(OBJ)}{rng.choice(QUAL)}." for _ in range(n))


def bank_conditions(rng, story, n_articles):
    story.append(Paragraph("BIJLAGE — Algemene voorwaarden voor zakelijke kredieten en zekerheden", H1))
    topics = ["Begripsbepalingen", "Zekerheidstelling", "Verpanding van huurpenningen", "Informatieverplichtingen",
              "Financiële convenanten", "Opeisbaarheid", "Verzekering", "Kosten en belastingen", "Verrekening",
              "Overdracht en contractsoverneming", "Toepasselijk recht", "Taxatie", "Rentevaststelling", "Boeterente"]
    for i in range(n_articles):
        story.append(Paragraph(f"Artikel B{i+1} — {topics[i % len(topics)]}", H2))
        story.append(Paragraph(filler(rng, rng.randint(7, 11)), BODY))


def lease_annex(rng, story, leases):
    story.append(Paragraph("BIJLAGE — Overzicht huurovereenkomsten", H1))
    rows = [["Huurder", "Unit", "m²", "Jaarhuur (EUR)", "Einddatum"]] + [[l[0], l[1], l[2], l[3], l[4]] for l in leases]
    t = Table(rows, colWidths=[150, 45, 50, 90, 80])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DV", 8.5), ("FONT", (0, 0), (-1, 0), "DVB", 8.5),
                           ("GRID", (0, 0), (-1, -1), 0.4, colors.black)]))
    story += [t, Spacer(1, 8)]
    for l in leases:
        story.append(Paragraph(f"Huurovereenkomst {l[0]} (unit {l[1]})", H2))
        story.append(Paragraph(f"De huurovereenkomst met {l[0]} betreft unit {l[1]} met een verhuurbaar vloeroppervlak van {l[2]} m², "
                               f"tegen een jaarhuur van EUR {l[3]}, lopende tot en met {l[4]}. " + l[5] + " " + filler(rng, rng.randint(5, 9)), BODY))


def soil_annex(rng, story, special):
    story.append(Paragraph("BIJLAGE — Samenvatting verkennend en nader bodemonderzoek", H1))
    story.append(Paragraph("Het bodemonderzoek is uitgevoerd conform NEN 5740 en NEN 5707. Hieronder volgen de meetresultaten per boring.", BODY))
    rows = [["Boring", "Diepte (m-mv)", "Minerale olie (mg/kg ds)", "Zink (mg/kg ds)", "Asbest (mg/kg ds)", "Toetsing"]]
    for b in range(1, 25):
        rows.append([f"B{b:02d}", f"{rng.choice(['0,0-0,5', '0,5-1,0', '1,0-2,0'])}", str(rng.randint(20, 140)),
                     str(rng.randint(30, 160)), "<1", "achtergrondwaarde"])
    t = Table(rows, colWidths=[45, 70, 105, 75, 80, 90])
    t.setStyle(TableStyle([("FONT", (0, 0), (-1, -1), "DV", 8), ("GRID", (0, 0), (-1, -1), 0.4, colors.black)]))
    story += [t, Spacer(1, 6), Paragraph(filler(rng, 6), BODY)]
    if special:
        story.append(Paragraph(special, BODY))
    story.append(Paragraph(filler(rng, 8), BODY))


def deed(path, seed, f, n_bank_articles, leases, extra_sections):
    """f: dict of fact sentences; returns nothing, writes the PDF."""
    rng = random.Random(seed)
    s = [Paragraph("AKTE VAN LEVERING — BEDRIJFSMATIG ONROEREND GOED", ParagraphStyle("t", parent=H1, fontSize=15, alignment=1)),
         Paragraph(f"Kenmerk: {f['kenmerk']}", BODY),
         Paragraph(f"Heden, {f['datum']}, verschijnen voor mij, {f['notaris']}, notaris te {f['plaats']}:", BODY),
         Paragraph(f"1. {f['verkoper_zin']}", BODY), Paragraph(f"2. {f['koper_zin']}", BODY),
         Paragraph("Artikel 1 — Koopovereenkomst en omschrijving", H1), Paragraph(f["object_zin"] + " " + filler(rng, 5), BODY),
         Paragraph("Artikel 2 — Koopprijs, omzetbelasting en betaling", H1), Paragraph(f["prijs_zin"] + " " + filler(rng, 4), BODY),
         Paragraph(f["garantie_zin"] + " " + filler(rng, 3), BODY),
         Paragraph("Artikel 3 — Ontbindende voorwaarden", H1), Paragraph(f["voorwaarde_zin"] + " " + filler(rng, 5), BODY),
         Paragraph("Artikel 4 — Levering, risico en huurovereenkomsten", H1), Paragraph(f["levering_zin"] + " " + filler(rng, 6), BODY),
         Paragraph("Artikel 5 — Erfdienstbaarheden en kettingbedingen", H1), Paragraph(f["erf_zin"] + " " + filler(rng, 5), BODY),
         Paragraph(f["ketting_zin"] + " " + filler(rng, 4), BODY)]
    for title, n in extra_sections:
        s.append(Paragraph(title, H1)); s.append(Paragraph(filler(rng, n), BODY))
    s.append(Paragraph("Artikel 12 — Concurrentie en non-solicitatie", H1)); s.append(Paragraph(f["concurrentie_zin"] + " " + filler(rng, 4), BODY))
    s.append(Paragraph("WAARVAN AKTE, in minuut verleden. (volgen handtekeningen)", BODY)); s.append(PageBreak())
    bank_conditions(rng, s, n_bank_articles // 2)
    lease_annex(rng, s, leases)
    soil_annex(rng, s, f["bodem_zin"])
    s.append(Paragraph("BIJLAGE — Asbestinventarisatie en bouwkundige staat", H1)); s.append(Paragraph(filler(rng, 10) + " " + f["asbest_zin"] + " " + filler(rng, 10), BODY))
    bank_conditions(rng, s, n_bank_articles - n_bank_articles // 2)
    s.append(Paragraph("BIJLAGE — Rectificatie en slotverklaring", H1)); s.append(Paragraph(filler(rng, 4) + " " + f["slot_zin"], BODY))
    s.append(Paragraph("<i>Dit document is volledig fictief en uitsluitend gegenereerd voor een benchmark.</i>", BODY))
    SimpleDocTemplate(path, pagesize=A4, leftMargin=65, rightMargin=65, topMargin=60, bottomMargin=60).build(s)


def leases_for(rng, n, big, risky):
    names = ["Rivierland Opslag", "Kempen Pallet Service", "Dongemond Retourlogistiek", "Baronie Koelcellen", "Langstraat Fulfilment",
             "Biesbosch Bouwmaterialen", "Peelland Food Hub", "Markdal Verpakkingen", "Oisterwijk Cross-Dock", "Heuvelrug Distributie",
             "Maaskant Expeditie", "Zwaluwe Onderdelen", "Hilvarenbeek Textiel", "Goirle E-commerce"]
    out = [big]
    for i in range(n - 2):
        out.append((names[(i + rng.randint(0, 3)) % len(names)] + f" B.V.", f"{chr(66 + i % 6)}{i+2}", f"{rng.randint(900, 6500):,}".replace(",", "."),
                    f"{rng.randint(60, 480) * 1000:,}".replace(",", ".") + ",00", f"{rng.randint(1, 28)} {rng.choice(['maart', 'juni', 'september', 'december'])} {rng.randint(2027, 2034)}",
                    "Er zijn geen bijzonderheden gemeld."))
    out.insert(n // 2, risky)
    return out


TRUTH = {}
# ---------------- long deed: ~60 pages, 16 planted facts ----------------
L = dict(kenmerk="MvdW/2026/1182-LBV", datum="30 november 2026", notaris="mr. Maarten Valkenhorst", plaats="Tilburg",
         verkoper_zin="Havenkwartier Vastgoed N.V., statutair gevestigd te Rotterdam, hierna: 'verkoper';",
         koper_zin="Logistiek Fonds Zuidas B.V., statutair gevestigd te Amsterdam, hierna: 'koper'.",
         object_zin="Verkoper levert aan koper het distributiecentrum met drie hallen (A, B en C), kantoren en parkeerterrein, plaatselijk bekend Ringbaan-Noord 400 te Tilburg, kadastraal bekend gemeente Tilburg, sectie M, nummer 2291, groot vier hectare.",
         prijs_zin="De koopprijs bedraagt EUR 38.750.000,00, exclusief omzetbelasting. Partijen opteren voor een belaste levering als bedoeld in artikel 11 lid 1 sub a Wet OB 1968.",
         garantie_zin="Koper heeft een bankgarantie gesteld ten bedrage van EUR 3.875.000,00, afgegeven door een in Nederland gevestigde bank.",
         voorwaarde_zin="De koop is aangegaan onder de ontbindende voorwaarde dat uiterlijk op 15 december 2026 geen onherroepelijke omgevingsvergunning is verleend voor de uitbreiding met een mezzaninevloer in hal A.",
         levering_zin="De juridische levering vindt plaats op 30 november 2026. Het verkochte wordt geleverd onder de lopende huurovereenkomsten vermeld in de bijlage.",
         erf_zin="Ten laste van het verkochte is een erfdienstbaarheid gevestigd voor het hebben en onderhouden van kabels en leidingen ten behoeve van Netbeheer Midden-Brabant B.V., over een strook van zes meter langs de noordgrens.",
         ketting_zin="Op het verkochte rust een kettingbeding betreffende de instandhouding van de geluidswal, op straffe van een boete van EUR 250.000,00 per overtreding.",
         concurrentie_zin="Verkoper zal gedurende vijf jaar na de levering binnen een straal van vijftien kilometer geen concurrerend logistiek vastgoed ontwikkelen (concurrentiebeding).",
         bodem_zin="In afwijking van het voorgaande is ter plaatse van de voormalige tankplaats (boringen B17 en B18) een sterke verontreiniging met minerale olie aangetroffen. Verkoper verbindt zich deze verontreiniging vóór 1 maart 2027 voor eigen rekening te saneren.",
         asbest_zin="In het dakbeschot van hal C is asbesthoudend materiaal aangetroffen. Verkoper garandeert sanering; het daarvoor gereserveerde bedrag van EUR 412.000,00 wordt in depot gehouden bij de notaris.",
         slot_zin="Bij deze wordt gerectificeerd dat het verhuurbaar vloeroppervlak van hal B niet 17.240 m² maar 18.420 m² bedraagt.")
rng = random.Random(1)
leases = leases_for(rng, 24,
                    ("Noordelijk Koeltransport B.V.", "A1", "21.600", "1.284.000,00", "31 december 2031", "Dit is de grootste huurder van het complex."),
                    ("Fietsdistributie Brabant B.V.", "C4", "3.150", "214.000,00", "30 juni 2028",
                     "Deze huurder heeft per de datum van deze akte een huurachterstand van EUR 96.300,00; surseance van betaling is aangevraagd."))
deed("long60.pdf", 1, L, 104, leases, [(f"Artikel {i} — {t}", 16) for i, t in zip(range(6, 12),
     ["Garanties van verkoper", "Milieu en duurzaamheid", "Splitsing en gebruiksregels", "Overdracht van rechten", "Fiscale bepalingen", "Kosten en volmacht"])] * 2)
TRUTH["long60.pdf"] = {
    "verkoper": ["havenkwartier"], "koper": ["zuidas"], "koopprijs": ["38.750.000", "38,75"], "btw_belast": ["belast"],
    "kadaster": ["2291"], "bankgarantie": ["3.875.000"], "omgevingsvergunning_15dec": ["15 december 2026"],
    "erfdienstbaarheid_netbeheer": ["netbeheer"], "kettingbeding_boete": ["250.000"], "levering_30nov": ["30 november 2026"],
    "grootste_huurder": ["noordelijk koeltransport"], "huurachterstand_surseance": ["fietsdistributie", "96.300", "surseance"],
    "bodem_olie_sanering": ["minerale olie", "1 maart 2027"], "asbest_depot": ["asbest"], "asbest_bedrag": ["412.000"],
    "concurrentiebeding": ["concurrentiebeding", "vijf jaar", "5 jaar"], "rectificatie_18420": ["18.420"]}

# ---------------- four ~20-page deeds for the caching test ----------------
for k, (city, seller, buyer, price) in enumerate([("Breda", "Singelpoort Beheer B.V.", "Mark Logistiek C.V.", "9.400.000,00"),
                                                  ("Eindhoven", "Genneper Vastgoed N.V.", "Strijp Holding B.V.", "12.150.000,00"),
                                                  ("Den Bosch", "Dommel Invest B.V.", "Bossche Broek Fonds B.V.", "7.825.000,00"),
                                                  ("Helmond", "Peelpoort Real Estate B.V.", "Kanaalzone Partners B.V.", "5.990.000,00")], 1):
    C = dict(L, kenmerk=f"MvdW/2026/20{k}-C", plaats=city,
             verkoper_zin=f"{seller}, hierna: 'verkoper';", koper_zin=f"{buyer}, hierna: 'koper'.",
             object_zin=f"Verkoper levert aan koper het bedrijfscomplex te {city}, kadastraal bekend gemeente {city}, sectie K, nummer {4100 + k}.",
             prijs_zin=f"De koopprijs bedraagt EUR {price}, exclusief omzetbelasting.")
    rngc = random.Random(10 + k)
    deed(f"c{k}.pdf", 10 + k, C, 24, leases_for(rngc, 8, leases[0], leases[2])[:8],
         [(f"Artikel {i} — Overige bepalingen {i}", 12) for i in range(6, 10)])
    TRUTH[f"c{k}.pdf"] = {"verkoper": [seller.split()[0].lower()], "koopprijs": [price.split(",")[0]]}

json.dump(TRUTH, open("long_truth.json", "w"), indent=1, ensure_ascii=False)
import pypdfium2 as pdfium
for p in ["long60.pdf", "c1.pdf", "c2.pdf", "c3.pdf", "c4.pdf"]:
    print(p, len(pdfium.PdfDocument(p)), "pages")
