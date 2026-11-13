# Benchmarks

| Date | Benchmark | Summary |
|---|---|---|
| October 2026 | [Hardware benchmark](2026-10-hardware-benchmark.md) | OCR, local LLM (Mistral Small 3.2 24B and Qwen3.8-27B), several users at once, prompt caching and long documents on an RTX 4090, with recommended dev-pod and on-prem specs. |
| November 2026 | [Answer checks](2026-11-answer-checks.md) | How many planted mistakes the checks catch and how many correct answers they flag: fixed rules against the model reading the answer a second time, and number words typed by hand against the standard's. |
| November 2026 | [A round on real documents](2026-11-real-documents.md) | Ten real contracts and deeds, 106 questions: how many answers pass the checks, what the checks report, the model's second reading and marking by meaning on real answers, two models, reading time, a second round on a 24 GB card and a third with every playbook and several people at once. Counts only. |

The [scripts](scripts/) used for the hardware benchmark are standalone and not part of [suveryn-core](https://github.com/suveryn/suveryn-core); the answer checks and the round on real documents are measured by core's own tests.
