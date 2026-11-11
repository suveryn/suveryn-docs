# Answer checks, November 2026

sūveryn checks every answer against the passages it cites before a person reads it. This report measures how
good those checks are, and compares two ways of doing them: fixed rules, and the language model on the appliance
reading the answer a second time. All test text is fictional.

| | |
|---|---|
| Date | 10 and 11 November 2026 |
| Code | [suveryn-core](https://github.com/suveryn/suveryn-core), `packages/harness/tests/` |
| Model | the default model of core's `models/manifest.json`, llama.cpp, on a rented GPU machine |
| Languages | Dutch, French, English |

What the results led to is in core's design note,
[How an answer is checked](https://github.com/suveryn/suveryn-core/blob/main/docs/design/answer-checks.md): the
checks stay rules, the number words are generated, and the model's second reading is a proposal that real deeds
will decide. It is not in the product.

## In short

- Rules are exact for what can be compared: amounts, dates, names, percentages, the source cited. They catch all
  of those and flag no correct answer.
- Rules can't judge what a sentence means. Of ten wrong answers that no figure shows, they caught none.
- The model caught every planted mistake and all ten of those, at about a second per sentence. It flagged one
  correct answer in 52.
- Number words typed by hand had mistakes that 66 hand-picked cases never showed. Reading back 2 490 numbers
  spelled by a standard found them.

## The planted-error benchmark

Forty correct answers on fictional passages, each citing its source. A script plants one kind of mistake at a time
(another amount, another day, a "not" taken out, the buyer for the seller) and counts what the checks report. A
planted mistake is caught when the checks report something; a correct answer that gets a report is a false alarm.

Twenty-two harder cases were added by hand: twelve correct answers that shorten, reword, translate or combine
their source, and ten wrong answers that no figure, date or name shows ("at the latest" told as "at the
earliest", informing told as obtaining, consent told as notice).

## Rules against the model

| | Rules | The model |
|---|---|---|
| Another amount | 9 of 9 | 9 of 9 |
| Another day | 6 of 6 | 6 of 6 |
| A name misspelled by one letter | 4 of 4 | 4 of 4 |
| The wrong source cited | 6 of 6 | 6 of 6 |
| Another percentage | 3 of 3 | 3 of 3 |
| Another small number | 3 of 7 | 7 of 7 |
| Another article number | 0 of 1 | 1 of 1 |
| Money told as a surface | 8 of 9 | 9 of 9 |
| A "not" taken out or put in | 0 of 12 | 12 of 12 |
| The other party | 0 of 20 | 20 of 20 |
| Wrong answers written by hand | 0 of 10 | 10 of 10 |
| Correct answers flagged, of 40 | 0 | 1 |
| Correct answers by hand flagged, of 12 | 0 | 0 |
| Time | none | 0.9 s per sentence (median), 144 sentences in 129 s |

Two rules for a "not" and for the other party were tried on 10 November, with word lists per language: they caught
7 of 12 and 12 of 20, and were taken out again, because a language's words don't belong in the code and the lists
would be needed again for every language.

The one correct answer the model flagged: the passage gives a bare number, the answer adds "euro". The model
called that an added unit, which it is.

## How the model was asked

The model sees one cited sentence of the answer and the passages it cites. Three ways of asking were tried, without
letting the model think first.

| Asked | Correct answers flagged | Mistakes caught |
|---|---|---|
| "Do the passages say the same?" | 1 of 40 | 77 of 77 |
| "Does everything the sentence says follow from the passages?" | 3 of 40, 1 of 12 | 77 of 77, 10 of 10 |
| "Name the kind of difference: none, leaves out, adds, contradicts" | 1 of 40, 0 of 12 | 77 of 77, 10 of 10 |

With the first two, the model described a shortened sentence correctly as leaving words out and still answered "not
supported". With the third, the code decides: only *adds* and *contradicts* count. The run with thinking was
stopped: it is too slow to use on every answer.

## Number words

The reader knew numbers in words from tables typed by hand. A sample of numbers spelled by the standard rules
(num2words) was read back by that reader:

| Language | Read correctly | What went wrong |
|---|---|---|
| Dutch | 997 of 998 | a hundred written alone |
| French | 769 of 998 | "cent quatre-vingt-trois" read as 2 083 |
| Belgian French | 883 of 998 | the same |
| English | 273 of 998 | a comma inside the number split it in two |

The tables are now generated from the standard, and 2 490 numbers spelled by it are a test: all are read. Over
the 11 878 lines of text in core's repository the old and the new reader differ on two.

## What this does not show

- The cases and the questions were written by the same author. The hand-written cases were new to the model, not
  independent of that author.
- The passages are short. Real ones run to 3 000 characters, and real answers rest on several at once.
- 52 correct answers are few: one false alarm could be half a percent or five in real use.
- One model. The checks must hold for every model sūveryn ships.
- The standard's spelling is not every deed's. Three notarial variants were found and added; a new language will
  have its own.

## Run it again

```bash
uv run python packages/harness/tests/check_benchmark.py              # the rules
MEANING=1 ONLY_MEANING=1 bash scripts/gpu-round.sh                   # the model, on a GPU machine
uv run pytest packages/harness/tests/test_reading.py                 # the number words
```
