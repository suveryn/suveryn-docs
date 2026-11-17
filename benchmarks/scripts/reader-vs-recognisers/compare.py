# SPDX-License-Identifier: Apache-2.0
# Copyright 2026 Sūveryn Labs Ltd.
"""Our reader of amounts, numbers and dates against standard recognisers.

Reads every case of core's ``packages/harness/tests/reading_cases.json`` with core's reader (``values.read``) and with
three tools, and counts the cases each reads as the file says. Each tool is told the case's language (``LANGUAGE``,
below); a case of figures and symbols alone counts when any of the three languages reads it. Only ours is told how the
document writes decimals (a case's ``style``), as it is in the product. A tool is scored only on
the cases in its scope.

    dotnet build -c Release -o bin            # Microsoft Recognizers-Text 1.8.13, .NET 8
    python3 -m venv v && v/bin/pip install -r requirements.txt -e <core>/packages/playbooks -e <core>/packages/harness
    v/bin/python compare.py <core>      # a checkout of suveryn-core

Prints the counts, and writes the cases each tool got wrong to ``wrong.json``.
"""
import json
import re
import subprocess
import sys
from decimal import Decimal, InvalidOperation
from pathlib import Path

from dateparser.search import search_dates
from text_to_num import alpha2digit
from suveryn_harness.values import read

CORE = Path(sys.argv[1])
CASES = json.loads((CORE / "packages/harness/tests/reading_cases.json").read_text(encoding="utf-8"))["cases"]
CULTURE = {"nl": "nl-nl", "fr": "fr-fr", "en": "en-us"}

# The language each case is written in; a case not listed is figures and symbols alone (or "EUR", "ha").
LANGUAGE = {w: "nl" for w in [
    "1,2 miljoen", "3 mio", "2,5 mld", "twaalf", "één", "drieëntwintig", "eenhonderdduizend euro", "honderdduizend euro",
    "zesentwintigduizend achthonderd euro", "negentienhonderd achtennegentig", "honderd en vijf", "twee, drie of vier",
    "honderd euro", "een woning", "in acht nemen", "te Tienen", "ten laste van de koper", "gekend ten kadaster Gent",
    "nummer 412B", "12 maart 2021", "12 mrt. 2021", "twaalf maart tweeduizend eenentwintig",
    "drie en twintig mei tweeduizend veertien", "Het jaar tweeduizend zesentwintig, op tweeëntwintig oktober",
    "Het jaar negentienhonderd negen en negentig. Op negentien april.",
    "HET JAAR TWEEDUIZEND ZESENTWINTIG\n\nOP TWEEËNTWINTIG OKTOBER", "In het jaar 2026, op 3 maart",
    "tweeduizend zesentwintig stuks, op tweeëntwintig oktober geleverd", "maart 2021", "tien procent",
    "ongeveer € 450.000", "circa 450 m²", "vijfhonderd euro", "6 weken", "2 kopers"]}
LANGUAGE |= {w: "fr" for w in [
    "1,2 million", "vingt-trois", "vingt et un", "quatre-vingt-dix", "septante", "deux cent mille euros",
    "cent quatre-vingt-trois", "mil neuf cent nonante-huit", "un immeuble", "pour cent", "12 mars 2021", "1er mars 2021",
    "le premier mars 2021", "le douze mai deux mille quatorze", "L'an deux mille vingt-six, le vingt-deux octobre",
    "L'an deux mil vingt-six, le premier mars", "2,5 pour cent", "environ 10 %", "trois mois"]}
LANGUAGE |= {w: "en" for w in [
    "twenty-one", "two hundred and five", "five thousand, five hundred and five", "within ten days", "ten",
    "March 12, 2021", "12th March 2021", "127,500.00 USD", "30 days"]}
missing = [c["written"] for c in CASES if re.search(r"[a-zà-ÿ]{3,}", c["written"], re.I)
           and c["written"] not in LANGUAGE and not re.fullmatch(r"(EUR|USD)? ?[\d.,  ]+ ?(EUR|USD|ha)?", c["written"])]
assert not missing, f"cases with words but no language: {missing}"


def kind(c):
    return next((k for k in ("numbers", "number", "date", "month") if k in c), "nothing" if c.get("nothing") else "no_date")


def dec(x):
    try:
        return Decimal(str(x).replace(",", ".")).normalize()  # Recognizers' French resolutions use a decimal comma
    except (InvalidOperation, TypeError):
        return None


def right(c, nums, dates, months):
    k = kind(c)
    if k == "number": return nums == [dec(c["number"])]
    if k == "numbers": return nums == [dec(n) for n in c["numbers"]]
    if k == "date": return dates == [tuple(c["date"])]
    if k == "month": return months == [tuple(c["month"])] and not dates
    if k == "nothing": return not nums and not dates and not months
    return not dates


def ours(text, _language, style=None):  # the document's way of writing decimals, which only ours takes
    nums, dates, months = [], [], []
    for f in read(text, style):
        {"number": nums, "date": dates, "month": months}[f.kind].append(f.value.normalize() if f.kind == "number" else tuple(f.value))
    return nums, dates, months


_helper = subprocess.Popen(["dotnet", str(Path(__file__).parent / "bin/Recognizers.dll")], stdin=subprocess.PIPE,
                           stdout=subprocess.PIPE, text=True, encoding="utf-8")


def recognizers(text, language):
    _helper.stdin.write(json.dumps({"text": text, "culture": CULTURE[language]}) + "\n"); _helper.stdin.flush()
    out = json.loads(_helper.stdout.readline())
    dates, months = [], []
    for values in out["dts"]:  # a date counts only when the text gives day, month and year (timex YYYY-MM-DD)
        values = [v for v in values if v.get("value") != "not resolved"]  # Recognizers' own "no such day"
        timex = values[0]["timex"] if values else ""
        if re.fullmatch(r"\d{4}-\d\d-\d\d", timex): y, m, d = map(int, timex.split("-")); dates.append((d, m, y))
        elif re.fullmatch(r"\d{4}-\d\d", timex): y, m = map(int, timex.split("-")); months.append((m, y))
    nums = [] if dates or months else [dec(n) for n in out["nums"] if n is not None]  # a date's parts are no amounts
    return nums, dates, months


def dateparser(text, language):  # search_dates: dates inside a text, as the reader finds them
    found = search_dates(text, languages=[language], settings={"DATE_ORDER": "DMY", "REQUIRE_PARTS": ["day", "month", "year"]}) or []
    dates = [(d.day, d.month, d.year) for _, d in found]
    months = [] if dates else [(d.month, d.year) for _, d in search_dates(text, languages=[language], settings={"REQUIRE_PARTS": ["month", "year"]}) or []]
    return [], dates, months


def text2num(text, language):  # number words to figures; the figures it writes are read back
    return [dec(f) for f in re.findall(r"\d+(?:,\d+)?", alpha2digit(text, language))], [], []


def counts(case, tool):
    languages = [LANGUAGE[case["written"]]] if case["written"] in LANGUAGE else list(CULTURE)
    style = {"style": case.get("style")} if tool is ours else {}
    return any(right(case, *tool(case["written"], language, **style)) for language in languages)


has_figure = lambda c: re.search(r"\d", c["written"])
SCOPES = {
    "all": lambda c: True,
    "figures": lambda c: kind(c) in ("number", "numbers") and has_figure(c),
    "words": lambda c: kind(c) in ("number", "numbers") and not has_figure(c),
    "dates": lambda c: kind(c) in ("date", "month", "no_date"),
    "not a value": lambda c: kind(c) == "nothing",
    "not a value, in words": lambda c: kind(c) == "nothing" and not has_figure(c),
}
TOOLS = {"ours": (ours, ["all", "figures", "words", "dates", "not a value"]),
         "Recognizers-Text 1.8.13": (recognizers, ["all", "figures", "words", "dates", "not a value"]),
         "dateparser 1.5.0": (dateparser, ["dates"]),
         "text2num 3.1.0": (text2num, ["words", "not a value, in words"])}
wrong = {}
for name, (tool, scopes) in TOOLS.items():
    for scope in scopes:
        cases = [c for c in CASES if SCOPES[scope](c)]
        missed = [c["written"] for c in cases if not counts(c, tool)]
        wrong.setdefault(name, {})[scope] = missed
        print(f"{name:24} {scope:22} {len(cases) - len(missed)}/{len(cases)}")
Path("wrong.json").write_text(json.dumps(wrong, ensure_ascii=False, indent=1), encoding="utf-8")
