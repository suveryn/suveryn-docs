# Sūveryn Hardware Benchmark, October 2026

This report covers what to rent for development and what to put in a notary office. We measured the full pipeline (OCR, chunking, retrieval and a local LLM) on one RTX 4090, with two models. The test documents were synthetic Dutch deeds of 4 to 60 pages, plus three real documents: two Belgian notarial deeds (one born-digital, one scanned) and a 38-page scanned report.

| | |
|---|---|
| GPU | RTX 4090, 24 GB |
| LLMs | Mistral Small 3.2 24B and Qwen3.8-27B (Q4_K_M) |
| LLM server | llama.cpp |
| OCR | Tesseract 5.3.4, Docling, OCRmyPDF |
| Documents | synthetic deeds, 2 real deeds, 1 real report |

Contents:

1. [Recommended hardware](#recommended-hardware)
2. [Server configuration](#server-configuration)
3. [Document extraction](#document-extraction)
4. [Model choice and speed](#model-choice-and-speed)
5. [Several users at once](#several-users-at-once)
6. [Prompt caching](#prompt-caching)
7. [Long documents (60 pages)](#long-documents-60-pages)
8. [Mistral or Qwen](#mistral-or-qwen)
9. [Two real deeds](#two-real-deeds)
10. [Sizing rules of thumb](#sizing-rules-of-thumb)
11. [What we did not test](#what-we-did-not-test)
12. [Test setup](#test-setup)

## Recommended hardware

Volume does not drive the hardware. Even 50 deeds a day is under half an hour of GPU work. What matters is GPU memory for long documents, and how many people ask the model something at the same moment.

**Recommended model: Qwen3.8-27B.** On the real deeds it made fewer legal errors than Mistral Small 3.2 24B. Mistral is 20–40% faster. Both fit the specs below.

### Development pod

| | |
|---|---|
| GPU | RTX 4090, 24 GB (tested) |
| CPU | 8 vCPU or more |
| RAM | 32 GB; 64 GB to test prompt caching |
| Disk | **60 GB or more.** A 30 GB container disk was 95% full. |
| Image | Ubuntu 24.04, CUDA 12.8 or newer |
| Access | Expose TCP port 22. The basic SSH proxy cannot copy files. |

Rent a 48 GB card if you work on long documents or load testing.

### On-prem: Standard (up to 10 people)

| | |
|---|---|
| GPU | 24 GB (RTX 4090 class; a workstation card for 24/7 use) |
| CPU | 8 cores. 16 cores only gave 1.3× faster OCR. |
| RAM | 64 GB, of which 32 GB is prompt cache |
| Disk | 2 TB NVMe |
| Handles | Documents up to about 60 pages in one pass. 4 people asking questions at once. |

This depends on the software choices in the next section: summaries queued at upload, document text placed first in prompts, and a large RAM cache.

### On-prem: Heavy

| | |
|---|---|
| GPU | 48 GB |
| CPU | 16 cores |
| RAM | 128 GB |
| Disk | 2–4 TB NVMe |
| When | A lot of corporate work or commercial real estate (documents over 60 pages), or several live summaries at the same moment |

This is an estimate. We did not test 48 GB cards.

## Server configuration

We used this llama-server command for the multi-user and long-document tests:

```bash
llama-server -m Mistral-Small-3.2-24B-Instruct-2506-Q4_K_M.gguf \
  -ngl 99 -fa on -ctk q8_0 -ctv q8_0 \
  -np 4 -kvu -c 81920 \
  -cram 32768
```

- `-np 4 -kvu`: 4 parallel requests share one context pool, so one request can use the whole pool.
- `-c 81920`: an 80k-token pool. With Mistral it takes 21.0 GB of GPU memory at idle, which is too much next to OCR on a 24 GB card. For the Standard appliance, use `-c 65536`. We measured 19.6 GB at idle with Mistral and 18.3 GB with Qwen.
- `-ctk/-ctv q8_0`: stores the context cache at 8 bits, which halves its memory use.
- `-cram 32768`: a 32 GB prompt cache in system RAM. The default of 8 GB was too small.
- For Qwen3.8-27B, add `--jinja --chat-template-kwargs '{"enable_thinking":false}'`.

Application rules that follow from the tests:

- Generate document summaries once, at upload, in a queue that runs one at a time.
- Put the document text first and the question last in every prompt, so cached text can be reused.
- Send follow-up questions about the same document to the same server slot.
- Skip OCR on pages that already have a text layer, and OCR the rest in parallel (`ocr_fast.py`).
- Never leave intermediate files in `/tmp`. A searchable copy is the full confidential document.

## Document extraction

In the old setup, Docling calls Tesseract itself, one page at a time. In `ocr_fast`, OCRmyPDF runs one Tesseract process per CPU core, and Docling then reads the resulting text layer. CPU cores were pinned with `taskset`.

| Document | Old setup, 8 cores | ocr_fast, 8 cores | ocr_fast, 16 cores |
|---|---:|---:|---:|
| Synthetic deed, 4 pages, 200 dpi scan | 11.7 s | 2.8 s | 2.7 s |
| Synthetic deed, 40 pages, 200 dpi scan | 116.8 s | 14.0 s | 10.6 s |
| Real report, 38 pages, 300 dpi scan with tables | 90.2 s | 24.7 s | 19.8 s |
| Born-digital deed, 60 pages (no OCR needed) | — | 5.0 s | — |

- **Scans:** 0.35–0.65 s per page with ocr_fast on 8 cores. **Born-digital PDFs:** about 0.08 s per page. Deeds the notary drafts in-house mostly fall in the second group.
- **Accuracy:** on the synthetic deed, the word error rate went from 0.5% to 1.5%. Key facts found were the same (8 of 10). On the real report, all 16 checked figures were present, and ocr_fast picked up about 3× more table text.
- **Known issue:** ocr_fast dropped the final line of one document. It is probably being classified as a page footer. Check this on real deeds.
- Cadastral references were garbled in both setups (“sectie K,” became “K‚” or “K,,”). Validate identifiers after OCR.

## Model choice and speed

| Model | GPU memory (weights) | Prompt reading | Answer writing | Verdict |
|---|---:|---:|---:|---|
| Mistral 7B Instruct v0.3, Q5_K_M | 5 GB | 8,500–10,700 tok/s | 103–148 tok/s | **Rejected:** made up facts and missed the parties |
| Mistral Small 3.2 24B, Q4_K_M | 14.3 GB | 2,500–3,900 tok/s | 49–59 tok/s | **Use:** correct on every deed question; says when something is missing |
| Qwen3.8-27B, UD-Q4_K_M (thinking off) | 16.5 GB | 2,100–2,500 tok/s | 49 tok/s | **Recommended:** more complete summaries and fewer legal errors; made up a computed figure once |
| Mistral Small 4, 119B | does not fit | — | — | Too large for 24–48 GB |

Prompt reading slows as the prompt gets longer: about 3,800 tok/s at 2k tokens and about 2,500 tok/s at 62k tokens for Mistral. Answer writing slows the same way.

**End to end, real 38-page scanned report (Mistral):** about 110 s with the old OCR. With ocr_fast it comes to about 49 s: 24.7 s of OCR plus a 24.5 s whole-document summary.

## Several users at once

These requests used the real report on Mistral Small 3.2 24B, with a 48k shared context. Questions sent about 2.3k tokens of retrieved text; summaries sent the whole report (30k tokens).

| Scenario | First word | Full answer | |
|---|---:|---:|---|
| 1 question | 0.6 s | 4.0 s | Fine |
| 4 questions at once | 1.4–2.9 s | 5.5–7.8 s | Fine |
| 1 whole-document summary | 10.2 s | 24.5 s | Fine |
| 1 summary + 3 questions | up to 12.9 s | questions about 20 s | Slow |
| 2 summaries at once | — | failed | Out of context |
| 2 people asking questions during OCR of a new document | 1.4–3.5 s | 4.9–7.9 s | Fine |

While a summary is running, everyone else's questions are 4–5× slower. That is why summaries should run at upload, in a queue.

## Prompt caching

We asked questions with a whole 20-page deed in the prompt (about 20k tokens), document text first. These results are for Mistral Small 3.2 24B.

| Scenario | First word | Full answer | Tokens reused from cache |
|---|---:|---:|---:|
| First question on a deed | 5.9 s | 7.1 s | 0 |
| Follow-up question, same deed | 0.09 s | 1.1 s | 20,071 of 20,091 |
| 4 people, same deed, at once | 0.1–28 s | 29–34 s | only 1 of 4 |
| 4 people, 4 deeds, follow-ups at once | 3.9 s | 5.8–10.8 s | 4 of 4 |
| Back to 4 deeds after a 60-page deed, 8 GB RAM cache | 6.8–9.0 s | 8.7–10.8 s | 0 of 4 |
| Same, 32 GB RAM cache | 1.3–9.0 s | 2.4–10.0 s | 3 of 4 |

- The cache makes a follow-up question about 6× faster.
- The cache belongs to one server slot. Several people asking about the same deed at the same moment each reprocess it.
- Each cached 20-page deed takes about 1.6 GB of system RAM. A 32 GB cache holds roughly 15–20 of them.

## Long documents (60 pages)

The test document was a synthetic commercial-property deed: 60 pages, 62k tokens, with 17 test facts. Some facts were hidden in the annexes and one was on the last page. These results are for Mistral Small 3.2 24B.

| Method | Time | Facts found (keyword check) | Read by hand |
|---|---:|---:|---|
| Whole document in one prompt | 47.3 s | 17 / 17 | Complete on the contract terms. Vague on the tenant in arrears: no name or amount. |
| Section by section, then combined (sections run one at a time) | 58.2 s | 15 / 17 | Exact on tenants. Misses the cadastral number and the last-page correction. Pads with boilerplate and ends with a misleading line. |
| Section by section, then combined (sections run in parallel) | 66.6 s | 15 / 17 | Same gaps. Running sections in parallel does not help, because prompt reading already uses the whole GPU. |

Peak GPU memory was 21.0–21.4 GB with an 80k context, with no OCR models loaded. Up to about 60 pages, use the whole document in one prompt. Splitting into sections is only needed beyond the context pool, and it is worse. Neither method is safe without citing each fact back to its page.

## Mistral or Qwen

We ran the same synthetic tests, on the same server settings (80k context, 4 slots, 32 GB RAM cache, q8 context cache), with Mistral Small 3.2 24B and Qwen3.8-27B. Qwen's thinking mode was switched off.

| | Mistral Small 3.2 24B | Qwen3.8-27B |
|---|---:|---:|
| Weights (Q4_K_M) | 14.3 GB | 16.5 GB |
| GPU memory at idle, 64k / 80k context | 19.6 / 21.0 GB | **18.3 / 18.9 GB** |
| Tokens for the same Dutch text (20-page deed) | 20,091 | **18,318** (9–17% fewer) |
| Prompt reading / answer writing | **about 3,700 / 59 tok/s** | about 2,300 / 49 tok/s |
| 4-page deed, end to end (retrieval) | **14.5–15.2 s** | 17.3–17.9 s |
| 4-page deed, whole deed in prompt | 4.4 s, correct | 5.4 s, correct |
| Follow-up question, cached | **1.1 s** | 1.9 s (re-reads the last ~500 tokens) |
| 60-page deed, one prompt | **47 s**, 17/17 facts | 58 s, 17/17 facts |
| 60-page deed, section by section | 58–67 s, 15/17 | 76–77 s, 16/17 (missed the soil contamination) |
| Short deeds still cached after one 60-page deed | 3 of 4 | **4 of 4** |

Reading the 60-page summaries by hand:

- **Mistral** is terse. It was vague on the most important risk: it did not name the tenant in arrears or the amount.
- **Qwen** is complete and well structured. It named the tenant in arrears, the amount, the suspension of payments, and the seller-paid soil clean-up with its deadline.
- But Qwen also added a **total annual rent it calculated itself, and got it wrong** (€8,479,000; the table adds up to €8,174,000). One of its three “early lease end” examples does not exist in the deed.
- Both models answered “not in the excerpts” rather than guessing when retrieval missed the information.

### Same comparison on the three real documents

The documents were the 38-page scanned report and the two real deeds. Both models got identical extracted text and the same questions, on the Standard configuration (64k context). Every specific claim was checked by hand against the source.

| | Mistral Small 3.2 24B | Qwen3.8-27B |
|---|---:|---:|
| Summary, 38-page report (29k tokens) | **29.3 s** | 34.9 s |
| Summary, 8-page deed | **24.3 s** | 34.9 s (hit the 1,500-token limit) |
| Summary, 5-page deed | **15.9 s** | 21.7 s |
| First question / cached follow-up, first word | **2.1–17.5 s / 0.04–0.13 s** | 3.1–19.4 s / 0.35–0.48 s |
| Verified facts in the summaries (keyword check) | 22 / 30 | **25 / 30** |

- **Qwen got the legal nuances right that Mistral missed.** It gave the mortgage's fourth rank, with the earlier registrations listed. It read the interest surcharge correctly. It named the notary who keeps the minutes correctly. It also covered the report's risks and exit route more completely.
- **Mistral's errors:** it left out the fourth rank, attributed the deed register to the wrong notary, read the surcharge as an alternative rate, mislabelled cost codes, and said “no amounts” while listing amounts.
- **Qwen's errors:** it mislabelled one cost code. Its long deed summary was cut off at the token limit.
- **Both models misspelled the notary's name** in the scanned deed, in different ways, although the OCR text had it right. Names must be checked against the extracted text by the application, not trusted from the model.
- No invented figures appeared in either model's output on these three documents. Qwen's made-up rent total happened on the synthetic 60-page deed.

**Conclusion.** Hardware sizing is the same for both models: either fits a 24 GB card, and Qwen leaves more room. On real documents, Qwen produced fewer substantive legal errors. Mistral is 20–40% faster and its cached follow-ups start almost instantly. For a notary, accuracy matters more than a few seconds, so Qwen3.8-27B is the better default. It still needs these application rules: give it a larger output budget, check names against the source text, allow no computed figures, and cite the source for every number.

## Two real deeds

Two real Belgian notarial deeds in Dutch, used with the owner's permission and deleted after the run. The setup was the Standard configuration (64k context, 32 GB RAM cache, 8 cores) with Mistral Small 3.2 24B. Each deed got a summary plus 5 standard questions, with the whole deed in the prompt.

| | Credit-opening / mortgage deed (2015) | Share survivorship agreement (2022) |
|---|---:|---:|
| Pages, type | 8, born-digital | 5, scanned (no text layer) |
| Tokens | 7,485 (about 935 per page) | 3,102 (about 620 per page) |
| Extraction, old setup | 25.3 s (OCR'd pages that already had text) | 13.8 s |
| Extraction, ocr_fast | **0.38 s** | **5.2 s** |
| Summary (first word / complete) | 2.2 s / 22.8 s | 1.4 s / 15.7 s |
| First question (first word / full answer) | 2.6 s / 4.9 s | 1.1 s / 2.1 s |
| Follow-up questions, cached | 0.06–0.08 s / 1.7–5.4 s | 0.05–0.07 s / 0.5–4.4 s |
| Peak GPU memory | 22.1 GB | 21.8 GB |

The peak GPU memory is an upper bound: the test loaded both OCR pipelines next to the server. Production loads only one.

- **OCR on the real scan:** the old setup and ocr_fast agree on 99.6% of words. ocr_fast read “§” correctly where the old setup read “8”. Names, share counts and dates were OCR'd correctly.
- **Correct:** deed type, parties, dates, amounts, cadastral parcel, share counts, and the main clauses in both deeds.
- **Model errors (Mistral):** it misspelled the notary's name twice, even though the OCR text had it right; it attributed the deed register to the wrong notary; it left the mortgage's fourth rank out of the summary (one answer did mention it); it read a 0.50% per year surcharge as an alternative interest rate; and it mislabelled the RR and ROG cost codes.
- **Configuration:** two answers were cut off at the 300-token limit. Use about 600 for questions.
- **Privacy:** summaries repeat national register numbers. Treat model output, logs and the prompt cache as personal data.

## Sizing rules of thumb

| Quantity | Value | Source |
|---|---:|---|
| Tokens per page, real deeds | 620–935 | two real Belgian deeds |
| Tokens per page, scanned | about 800 | synthetic deed, real report |
| Tokens per page, born-digital and dense | about 1,000 | synthetic 20- and 60-page deeds (an upper bound) |
| Context memory per token (Mistral 24B, q8) | about 90 KB | 48k pool: 18.1 GB, 80k pool: 21.0 GB |
| OCR and embedding models on the GPU | about 2.2 GB | peak during OCR |
| RAM per cached 20-page deed | about 1.6 GB | server memory growth |
| Longest document in one pass on 24 GB | about 60 pages | 64k context; tight with OCR loaded |

The page-length distribution we were given (not independently verified) says about 93% of notarial deeds are 30 pages or fewer, and about 7% are 31 to more than 100 pages. On a 24 GB card, nearly everything fits in one pass. Only the longest corporate and commercial-property deeds need a 48 GB card or splitting into sections.

## What we did not test

All of these numbers come from one RTX 4090 on RunPod, from mostly synthetic documents, and from at most 4 simultaneous requests. Treat the on-prem specs as a starting point and repeat the tests on the target machine.

- More than two real deeds. We still need real scans with stamps, signatures, handwriting and rotated pages, and Dutch (NL) as well as Belgian deeds.
- GPUs other than the RTX 4090. 48 GB and 32 GB cards are estimates.
- More than 4 simultaneous users, and 64k context with OCR models loaded on a 24 GB card.
- Accuracy checks beyond keyword matching and manual reading. Answers need citations to the source page.
- The pod's CPU was a 128-core server. Pinning to 8 cores approximates an office CPU, but clock speed and memory bandwidth differ.
- The page-length distribution comes from a summary without a primary source. Validate it with a sample of 50–100 real deeds.

## Test setup

| | |
|---|---|
| Hardware | RunPod RTX 4090 24 GB, driver 595.91, CUDA 12.8, Ubuntu 24.04, Python 3.12 |
| LLM server | llama.cpp build b92761a, CUDA, compute arch 89, flash attention |
| Models | `unsloth/Mistral-Small-3.2-24B-Instruct-2506-GGUF` Q4_K_M, `bartowski/Mistral-7B-Instruct-v0.3-GGUF` Q5_K_M, `unsloth/Qwen3.8-27B-GGUF` UD-Q4_K_M (run with `--jinja --chat-template-kwargs '{"enable_thinking":false}'`), `BAAI/bge-m3` |
| Extraction | Docling (layout and tables on CUDA, torch 2.14.1+cu130), Tesseract 5.3.4 with nld/fra/eng, OCRmyPDF 17.13 |
| Scripts | [`scripts/`](scripts/) |
| Data | Synthetic Dutch deeds (fictional names and numbers), plus one real scanned report and two real deeds, all used with the owner's permission and deleted from the pod after each run. The real documents are not published. |

These are standalone measurements, not part of suveryn-core.
