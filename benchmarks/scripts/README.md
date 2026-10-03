# Benchmark scripts

These are the scripts behind the [October 2026 hardware benchmark](../2026-10-hardware-benchmark.md). They are standalone measurement code, not part of suveryn-core.

## Requirements

- Ubuntu 24.04 with an NVIDIA GPU and CUDA 12.8 or newer
- Python 3.12, plus:
  ```bash
  pip install docling ocrmypdf sentence-transformers reportlab pdf2image pypdfium2 requests huggingface_hub
  ```
- Tesseract with Dutch, French and English data, plus Ghostscript and poppler:
  ```bash
  apt install tesseract-ocr tesseract-ocr-nld tesseract-ocr-fra ghostscript poppler-utils
  ```
- llama.cpp `llama-server`, built with CUDA. The command used for the multi-user tests:
  ```bash
  llama-server -m <model>.gguf -ngl 99 -fa on -ctk q8_0 -ctv q8_0 -np 4 -kvu -c 65536 -cram 32768 --port 8080
  ```
  For Qwen3.8-27B, add `--jinja --chat-template-kwargs '{"enable_thinking":false}'`.

## Scripts

| Script | What it does |
|---|---|
| `gen_doc.py` | Generates a fictional 4-page Dutch deed as an image-only scan, with ground truth for OCR scoring. |
| `gen_long.py` | Generates fictional born-digital deeds: one 60-page deed with 17 planted facts, and four 20-page deeds. |
| `ocr_fast.py` | Parallel OCR front-end. It skips pages that already have text, OCRs the rest with OCRmyPDF, then runs Docling with `do_ocr=False`. |
| `bench.py` | Full pipeline on the 4-page deed: extraction, chunking, retrieval and one answer from the model. |
| `bench_ocr.py` | Compares baseline Docling OCR with `ocr_fast` on synthetic deeds. |
| `report_ocr.py` | Compares the same two setups on **your own** scanned PDF (`REPORT_PDF`). |
| `load_test.py` | Measures several users at once, using text from `report_ocr.py`. |
| `long_tests.py` | `cache`: the prompt-caching scenarios. `long`: 60-page summary, one prompt versus section by section. |

All test documents generated here are fictional. `report_ocr.py` and `load_test.py` work on a document you provide yourself, in `work/`. Keep real documents out of this repository.
