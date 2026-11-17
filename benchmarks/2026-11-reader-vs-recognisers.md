# Our reader against standard recognisers, November 2026

sūveryn reads every amount, number and date its checks look at with one reader of its own, in Dutch, French and
English. Tools made for this exist. This report counts how three of them read the same cases. All text is fictional.

| | |
|---|---|
| Date | 17 November 2026 |
| Cases | core's [`reading_cases.json`](https://github.com/suveryn/suveryn-core/blob/2c5bfda/packages/harness/tests/reading_cases.json): 89 written forms, each with the one thing it means |
| Script | [`scripts/reader-vs-recognisers/`](scripts/reader-vs-recognisers/) |
| Issue | suveryn-tracker#170 |

## Results

Each tool is told the case's language; a case of figures alone counts when any language reads it. Only ours is told
how the document writes decimals, as in the product. A tool is counted only on the cases it is made for.

| | All 89 | Figures (33) | Numbers in words (25) | Dates, a month, no date (23) | Not a value (8) |
|---|---|---|---|---|---|
| Ours (`values.read`) | 89 | 33 | 25 | 23 | 8 |
| Microsoft Recognizers-Text 1.8.13 (.NET) | 71 | 29 | 23 | 16 | 3 |
| dateparser 1.5.0 | | | | 11 | |
| text2num 3.1.0 | | | 22 | | 5 of the 7 in words |

What each missed:

- **Recognizers-Text** reads some forms wrongly, which is worse for a check than not reading them: "drie en twintig
  mei tweeduizend veertien" as 20 May 2014, "nummer 412B" as 412 billion, "cent" in "pour cent" as 100, "five
  thousand, five hundred and five" as 5000 and 505, and "een woning", "un immeuble" and "in acht nemen" as
  numbers. It misses a deed's opening ("Het jaar tweeduizend zesentwintig, op tweeëntwintig oktober", "L'an deux
  mille vingt-six…"), "mil neuf cent nonante-huit", "3 mio", "2,5 mld" and a figure with non-breaking spaces. Its
  Python (1.0.2a2, 2019) and JavaScript (1.3.1) releases have no Dutch; only the .NET release does.
- **dateparser** (`search_dates`, which finds dates inside a text) reads no date written in words and no deed's
  opening, and misses "12 mrt. 2021" and "1er mars 2021".
- **text2num** misses "één", "eenhonderdduizend" and "five thousand, five hundred and five", and reads "in acht
  nemen" as 8 and "pour cent" as 100. It reads no figures or dates.

## What it shows, and what it doesn't

- The cases were written with our reader, so ours reads all of them by construction. The table shows what the
  others miss on the forms deeds use, not that ours is better in general.
- Recognizers-Text comes closest. What it gets wrong are the forms a deed writes and its checks depend on: the
  deed's own date, a date in words read as another date, and articles read as numbers, which would make the
  checks report numbers that aren't there. Using it would also mean running .NET on the appliance beside the
  Python harness.
- Not tried: Duckling, a Haskell service the appliance would have to run.

**Decision:** our reader stays. Its words already come from standards (num2words and Unicode CLDR, in core's
`packages/harness/tools/number_words.py`).

## Run it again

.NET 8 and Python 3.12 or newer, in `scripts/reader-vs-recognisers/`:

```bash
dotnet build -c Release -o bin
python3 -m venv v && v/bin/pip install -r requirements.txt -e <core>/packages/playbooks -e <core>/packages/harness
v/bin/python compare.py <core>
```

`<core>` is a checkout of suveryn-core at `2c5bfda`, the cases measured here. The script prints the counts and
writes the cases each tool missed to `wrong.json`.
