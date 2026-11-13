# A round on real documents, November 2026

The [answer checks report](2026-11-answer-checks.md) measures the checks on fictional cases written for the
purpose. This report puts the whole product to real documents: reading them, answering questions about them, and
checking each answer against the passages it cites. It was run to see what a user would notice, and it changed
what was fixed.

The documents are real contracts and deeds, used with their owner's permission on a rented GPU machine and deleted
afterwards. This report holds counts only: no document, party or sentence is named here or anywhere in the
repositories.

| | |
|---|---|
| Date | 11 November 2026; a second round on a 24 GB card on 12 November; a third on 13 November |
| Code | [suveryn-core](https://github.com/suveryn/suveryn-core), the answers test of `scripts/gpu-round.sh` |
| Model | Qwen3.8-27B (Q4_K_M), llama.cpp b12111; Mistral Small 3.2 24B for comparison |
| GPU | 11 November: one card with 32 GB, once more with 8 GB of it held back. 12 November: an RTX 4090, 24 GB. 13 November: an RTX 5090, 32 GB |
| Documents | 11 documents: ten PDFs of 3 to 98 pages (299 pages in all, 145 of them scans) and one Word file |
| Questions | 106, in 23 sets, mostly in Dutch, on Dutch, French and English documents |

What the results led to is in core's design note,
[How an answer is checked](https://github.com/suveryn/suveryn-core/blob/main/docs/design/answer-checks.md).

## In short

- 83 of 106 answers passed every check; 88 after two fixes this round led to. No answer missed a fact it was
  expected to give.
- The same round twice gives the same result: 83 and 83, with 104 of 106 verdicts the same. A difference of one or
  two answers between rounds is noise.
- What the checks report is mostly one thing: a name that is in the documents, but not in the passage the answer
  cites for it.
- The model reading each answer a second time, which did well on fictional cases, flagged more than half of the
  real answers, most of them wrongly. It is not in the product.
- Marking a source sentence by its meaning, for a Dutch answer on a French or English source, found the right
  sentence in every case read. It is on.
- The product fits a 24 GB card: run on one the next day, it used 24.0 of 24.5 GB, with no memory error.
- Mistral Small fits the card only with its working memory halved, and then four people asking at once all get
  an error. It stays a second model for a larger card.
- One more sentence in the prompt about citing was tried twice and dropped: it costs clean answers.

## Reading the documents

| Document | Pages | Scanned pages | Seconds |
|---|---|---|---|
| 1 | 98 | 66 | 34 |
| 2 | 58 | 0 | 17 |
| 3 | 46 | 0 | 19 |
| 4 | 38 | 38 | 33 |
| 5 | 22 | 22 | 10 |
| 6 | 11 | 11 | 6 |
| 7 | 10 | 0 | 1 |
| 8 | 8 | 0 | 1 |
| 9 | 5 | 5 | 6 |
| 10 | 3 | 3 | 5 |

A page of digital text takes 0.1 to 0.4 seconds, a scanned page 0.4 to 1.6. Every document was read without an
error; the Word file, which has no pages to count, took under a second. For 44 of the 106 questions the documents were longer than the model reads at once, and the answer was
made from the passages that match the question best.

## The answers

An answer passes when it cites its sources, gives the expected fact where one was set, holds no figure that is in
no passage, has every sum made by the server and not by the model, and every cited passage holds what its
sentence says.

| | Before the fixes | After |
|---|---|---|
| Answers that pass | 83 of 106 | 88 of 106 |
| Answers with something not in its cited passage | 19 | 16 |
| Sums made by the server | 5 of 8 | 7 of 8 |
| Answers with a figure in no passage | 1 | 1 |
| Seconds per answer (average, longest) | 13.6, 38 | 13.8, 40 |

The two fixes: a deed's date written with the year first is now read, and a part of a whole is now computed when
either way of reading its figures gives the same result. An earlier round the same day led to a third: a contract's
defined terms ("the Company", "the Shares") were taken for names, which made 85 of 137 reports in that round.

## What the checks report

Before the fixes, the checks reported 60 items in 19 answers.

| | Items |
|---|---|
| A name | 52 |
| A number or a date | 8 |

Of the 52 names:

| | Names |
|---|---|
| In another passage the model was given | 49 |
| In the passage next to the cited one | 6 |
| Spelled differently in the document | 8 |
| Nowhere in the documents | 3 |

A name can be in more than one row. So the model had the name and cited the wrong passage for it. Accepting the passage next door would settle 6 of
52; the way forward is in how the model is asked to cite, not in a looser check. One document accounts for 26 of
the 60 items, and 15 of the 23 sets of questions have none.

## The model reading the answer a second time

The same model and question as in the [answer checks report](2026-11-answer-checks.md#how-the-model-was-asked),
on the real answers: 861 cited sentences.

| | |
|---|---|
| Sentences the model says are not carried by their passage | 166 of 861 |
| Answers with such a sentence | 58 of 106 (the rules: 20) |
| Sentences the rules report that the model reports too | 22 of 36 |
| Time | 1.4 s per sentence, about 11 s per answer |

Twelve of the model's reports were read by hand: about three were real mistakes that no rule sees (a figure from
a table given the wrong meaning), two were unclear, and seven were wrong: a remark on wording, or the model
misreading a table or a form. On fictional cases it flagged one correct answer in 52; here it flags more than
half of all answers. As it stands it would cost more trust than it earns.

## Marking a sentence by its meaning

When a person opens a source, the sentence the answer rests on is marked. That is found by shared words and
figures, which fails when the answer is in another language than its source, or rewords it.

| | Markers |
|---|---|
| All markers in the 106 answers | 1 158 |
| A sentence marked by its words | 882 |
| No sentence by words | 254 |
| Of those, a sentence marked by meaning | 130 |

Marking by meaning uses the search's own model, and marks a sentence only when it is close enough, clearly closer
than the next, and holds the claim's figures. Sixteen of the 130 were read by hand: all sixteen were the right
sentence, each a Dutch answer on an English or French source. The source panel says such a sentence was found by
meaning and asks the reader to check it. It checks nothing itself; a wrong mark costs the reader a line.

## Two models

| | Qwen3.8-27B | Mistral Small 3.2 24B |
|---|---|---|
| Answers that pass | 83 of 106 | 76 of 106 |
| Items the checks report | 60 | 216 |
| Answers that cite nothing | 0 | 2 |
| Answers in another language than the question | 0 | 1 |
| Sums made by the server | 5 of 8 | 4 of 8 |
| Seconds per answer | 13.6 | 10.7 |
| GPU memory at its highest | 23.4 GB | 24.8 GB |

Qwen stays the default.

## A 24 GB card, first with memory held back

With 8 GB of the card held back, leaving 24.6 GB, the round ran to the end and gave the same 106 answers word for
word. The product used 23.4 GB at its highest: it fits, with about 1 GB to spare and no room for anything else on
the card.

The round on a real 24 GB card followed the next day, below.

## The next day, on a 24 GB card

On 12 November the same documents and questions were run on an RTX 4090 (24 564 MiB), with core as it stood that
day: the fixes above merged, marking by meaning on. The machine had 31 GB of system memory.

| | Qwen3.8-27B | Mistral Small 3.2, as listed | Mistral, working memory halved |
|---|---|---|---|
| Answers that pass | 88 of 106 | 85 of 106 | 85 of 106 |
| Items the checks report | 63 | 108 | 118 |
| Sums made by the server | 7 of 8 | 6 of 8 | 6 of 8 |
| Seconds per answer | 11.6 | 8.8 | 8.7 |
| GPU memory at its highest | 24.0 GB | 24.1 GB | 22.4 GB |
| The reader out of GPU memory | never | 63 times | never |
| The longest document read in | 56 s | 163 s | 61 s |

- **Qwen fits a real 24 GB card**, with about half a gigabyte to spare. Nothing ran out of memory.
- **Mistral as listed does not fit it**: the model leaves the document reader too little, the reader runs out of
  GPU memory, recovers, and reads up to four times slower. With the model's working memory halved (`-c 32768`)
  it fits, reads at normal speed, and answers as before. What half the working memory costs with several people
  at once was not measured.
- **Mistral did much better than the day before** (76 of 106, 216 items), on newer code. Why was not examined.
- Running Mistral with its own chat template changed nothing: the same results, answer for answer.

**One more sentence in the prompt.** Most of what the checks report comes from answers that list many parties or
amounts and cite the same one or two passages for all of them. A sentence asking to cite, for each item of a list
or a table, the passage that names that item was tried on both models:

| | Qwen | Qwen, with the sentence | Mistral | Mistral, with the sentence |
|---|---|---|---|---|
| Items the checks report | 63 | 45 | 118 | 99 |
| The answer with the most items | 25 | 10 | 42 | 21 |
| Answers that pass | 88 | 86 | 85 | 83 |

It thins out the worst answers. On this day the number of answers that pass moved by two, the noise between
identical rounds; the round of 13 November, below, showed that it costs clean answers. It is not in the product.

**System memory.** The model server is started with a 32 GB prompt cache in system memory, which the hardware
benchmark specifies for an office machine with 64 GB. On this machine, with 31 GB, the system stopped the server
in the middle of every round until the cache was set to 8 GB. A machine must have well more memory than the
cache it is given.

## A third round, 13 November

The same documents and questions once more, on core as it stood on 13 November (after about ten more merges), on an
RTX 5090 with 32 GB and 117 GB of system memory, so with the model server's settings as an office machine has
them. The card is larger than the minimum: this round is about the answers, not about what fits.

**Every playbook, start to finish.** Deed intake (two runs), company formation (two runs) and the care mandate,
on fictional documents through the gateway: five of five passed, every check held, nothing invented.

**The answers.**

| | Qwen | Qwen, with the sentence | Mistral, working memory halved | Mistral, halved, with the sentence |
|---|---|---|---|---|
| Answers that pass | 93 of 106 | 86 | 86 | 84 |
| Answers with something reported | 12 | 19 | 17 | 19 |
| Items the checks report | 73 | 62 | 120 | 112 |
| The answer with the most items | 25 | 19 | 42 | 21 |
| Sums made by the server | 7 of 8 | 7 of 8 | 6 of 8 | 6 of 8 |
| Seconds per answer | 7.4 | 7.7 | 5.8 | 5.7 |

- **Qwen passes 93 of 106**, up from 83 two days earlier and 88 the day before on the same questions. The code and
  the card both changed between the rounds, so which change did it is not known.
- **The sentence about citing is dropped.** It makes the worst answer less bad and spreads reports over answers
  that were clean: seven fewer answers pass with Qwen, two fewer with Mistral. With the day before, three of four
  comparisons lose more than the noise.
- What the checks report is now concentrated: with Qwen, two answers carry 50 of the 73 items.

**Several people at the same moment, on long documents.** Each person asks a question about one of the four
longest documents, so every question fills the reading budget. Mistral only; the round for Qwen was not finished.

| People asking at once | Mistral, working memory halved (`-c 32768`) | Mistral, as listed (`-c 65536`) |
|---|---|---|
| 1 | 2 of 2 answered | 2 of 2 |
| 2 | 4 of 4 | 4 of 4 |
| 4 | 0 of 8: "context size has been exceeded" | 8 of 8, the slowest in 54 s |
| 8 | 0 of 16 | 8 of 16; the others the same error |

- **Halving Mistral's working memory is not a setting for the product.** It makes the model fit a 24 GB card, and
  then four people at once, which is what an office machine is specified for, all get an error. As listed, Mistral
  serves four at once and does not fit a 24 GB card. So on the minimum card Mistral is not offered.
- With eight people at once on long documents, half the questions fail with an error where they should wait
  their turn. Whether Qwen does the same was not measured.

## What this does not show

- These are mostly company contracts, with a few notarial deeds, from one owner. A round on notarial deeds in
  French and Dutch is still to come.
- Ten documents and 106 questions are few, and the questions were written knowing the documents.
- Whether each reported item is a real problem for a reader was not judged one by one, only where the item is.
- The second reading and the marking by meaning rest on samples of 12 and 16 read by one person: enough to choose
  a direction, too few to quote as a rate.
- One person at a time. Several people at once are measured in the
  [hardware benchmark](2026-10-hardware-benchmark.md).
- The rounds on the 106 questions were one person at a time. Several people at once on long documents was
  measured for Mistral only, twice per number of people.
- The round on the 24 GB card ran on a machine with less system memory than an office's.

## Run it again

```bash
OWN_QUESTIONS=/path/to/your/documents bash scripts/gpu-round.sh   # on a GPU machine: the answers that pass
```

Your documents go in a folder with a file of questions beside each (the answers test in
`packages/rag/tests/test_answers_e2e.py` says how). The other counts here (where a reported name is, the second
reading, the marking by meaning) were made with a script written for this round, which is not in the repository.
