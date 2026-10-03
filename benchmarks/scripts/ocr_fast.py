"""Fast OCR front-end for Docling (standalone benchmark code, not suveryn-core).

Baseline: Docling runs Tesseract itself, one page at a time, on every page
(force_full_page_ocr), ~2.4 s/page on the RTX 4090 benchmark pod.

This module instead:
  1. checks each page for an existing text layer (born-digital PDFs need no OCR),
  2. OCRs only the image pages, in parallel across CPU cores, with OCRmyPDF
     (Tesseract underneath, one process per page, 1 thread each),
  3. hands the resulting searchable PDF to Docling with do_ocr=False, so Docling
     only runs its (GPU) layout + table models and reads the text layer.

Usage:
    python ocr_fast.py input.pdf --lang nld+fra --jobs 8 [--deskew] [--rotate]
"""
from __future__ import annotations

import argparse
import os
import tempfile
import time
from dataclasses import dataclass, field
from pathlib import Path

import pypdfium2 as pdfium

MIN_TEXT_CHARS = 50  # a page with fewer extractable chars is treated as an image scan


@dataclass
class OcrReport:
    pages: int = 0
    text_pages: int = 0  # pages that already had a usable text layer
    ocr_pages: int = 0
    timings: dict = field(default_factory=dict)


def classify_pages(pdf: Path) -> list[bool]:
    """True for pages that already carry a usable text layer."""
    doc = pdfium.PdfDocument(str(pdf))
    try:
        return [len(doc[i].get_textpage().get_text_range().strip()) >= MIN_TEXT_CHARS for i in range(len(doc))]
    finally:
        doc.close()


def ocr_to_searchable_pdf(src: Path, dst: Path, lang: str, jobs: int, deskew: bool, rotate: bool) -> None:
    import ocrmypdf

    ocrmypdf.ocr(
        src, dst,
        language=lang.split("+"),
        jobs=jobs,
        skip_text=True,          # leave pages that already have text alone
        output_type="pdf",       # skip slow PDF/A conversion
        optimize=0,              # skip image recompression
        deskew=deskew,
        rotate_pages=rotate,     # orientation detection; costs time, off by default
        progress_bar=False,
        tesseract_timeout=120,
    )


def build_converter(device: str = "cuda", threads: int = 8):
    from docling.datamodel.accelerator_options import AcceleratorDevice, AcceleratorOptions
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions
    from docling.document_converter import DocumentConverter, PdfFormatOption

    opts = PdfPipelineOptions(
        do_ocr=False,  # text comes from the PDF's text layer
        do_table_structure=True,
        accelerator_options=AcceleratorOptions(
            device=AcceleratorDevice.CUDA if device == "cuda" else AcceleratorDevice.CPU, num_threads=threads),
    )
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=opts)})
    conv.initialize_pipeline(InputFormat.PDF)
    return conv


def extract(pdf: Path, converter, lang: str = "nld+fra", jobs: int | None = None,
            deskew: bool = False, rotate: bool = False, workdir: Path | None = None):
    """Return (DoclingDocument, OcrReport, searchable_pdf_path or None if it was a temp file)."""
    jobs = jobs or len(os.sched_getaffinity(0))
    rep = OcrReport()
    t = time.perf_counter()
    has_text = classify_pages(pdf)
    rep.pages, rep.text_pages = len(has_text), sum(has_text)
    rep.ocr_pages = rep.pages - rep.text_pages
    rep.timings["classify"] = time.perf_counter() - t

    # Without an explicit workdir the searchable copy is temporary and always deleted:
    # it holds the full document text, so it must not linger in /tmp.
    tmp = None if workdir else tempfile.TemporaryDirectory(prefix="ocrfast_")
    try:
        searchable = (workdir or Path(tmp.name)) / (pdf.stem + ".ocr.pdf")
        t = time.perf_counter()
        if rep.ocr_pages:
            ocr_to_searchable_pdf(pdf, searchable, lang, jobs, deskew, rotate)
        else:
            searchable = pdf  # fully born-digital: no OCR at all
        rep.timings["ocr"] = time.perf_counter() - t

        t = time.perf_counter()
        doc = converter.convert(searchable).document
        rep.timings["docling"] = time.perf_counter() - t
    finally:
        if tmp:
            tmp.cleanup()
    rep.timings["total"] = sum(rep.timings.values())
    return doc, rep, (None if tmp else searchable)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--lang", default="nld+fra")
    ap.add_argument("--jobs", type=int)
    ap.add_argument("--deskew", action="store_true")
    ap.add_argument("--rotate", action="store_true")
    ap.add_argument("--out", type=Path, help="write extracted Markdown here")
    a = ap.parse_args()
    conv = build_converter()
    doc, rep, _ = extract(a.pdf, conv, a.lang, a.jobs, a.deskew, a.rotate)
    print(f"pages={rep.pages} already_text={rep.text_pages} ocr={rep.ocr_pages} "
          + " ".join(f"{k}={v:.2f}s" for k, v in rep.timings.items()))
    if a.out:
        a.out.write_text(doc.export_to_markdown())
