"""Compare baseline Docling+Tesseract OCR with ocr_fast (parallel OCRmyPDF + Docling do_ocr=False).

Run inside /workspace/bench (needs deed_scan.pdf + ground_truth.json from gen_doc.py):
    taskset -c 0-7  python bench_ocr.py baseline 8
    taskset -c 0-7  python bench_ocr.py fast 8
    taskset -c 0-15 python bench_ocr.py fast 16
"""
import json, re, sys, time
from pathlib import Path

import pypdfium2 as pdfium

MODE, CORES = sys.argv[1], int(sys.argv[2])
LANG = "nld"


def make_test_docs():
    """deed40.pdf: deed scan tiled 10x (40 image pages). mixed40.pdf: 4 born-digital + 36 scanned pages."""
    if not Path("deed40.pdf").exists():
        src, out = pdfium.PdfDocument("deed_scan.pdf"), pdfium.PdfDocument.new()
        for _ in range(10):
            out.import_pages(src)
        out.save("deed40.pdf")
    if not Path("mixed40.pdf").exists():
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.pdfbase import pdfmetrics
        from reportlab.pdfbase.ttfonts import TTFont
        pdfmetrics.registerFont(TTFont("DV", "/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf"))
        st = getSampleStyleSheet()["Normal"]; st.fontName = "DV"
        gt = json.load(open("ground_truth.json"))["text"]
        SimpleDocTemplate("digital.pdf", pagesize=A4).build([Paragraph(p, st) for p in gt.split("\n") if p.strip()])
        dig, scan, out = pdfium.PdfDocument("digital.pdf"), pdfium.PdfDocument("deed40.pdf"), pdfium.PdfDocument.new()
        out.import_pages(dig, list(range(min(4, len(dig)))))
        out.import_pages(scan, list(range(36)))
        out.save("mixed40.pdf")


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[#*|_\-]+", " ", s)).strip().lower().split()


def wer(ref, hyp):
    prev = list(range(len(hyp) + 1))
    for i, x in enumerate(ref, 1):
        cur = [i]
        for j, y in enumerate(hyp, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (x != y)))
        prev = cur
    return prev[-1] / len(ref)


make_test_docs()
gt = json.load(open("ground_truth.json"))
res = {"mode": MODE, "cores": CORES}

if MODE == "baseline":
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
    from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
    po = PdfPipelineOptions(do_ocr=True, do_table_structure=True,
                            ocr_options=TesseractCliOcrOptions(lang=[LANG], force_full_page_ocr=True),
                            accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CUDA, num_threads=CORES))
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=po)})
    conv.initialize_pipeline(InputFormat.PDF)
    def run(pdf):
        t = time.perf_counter(); doc = conv.convert(pdf).document
        return doc, {"total": time.perf_counter() - t}
else:
    from ocr_fast import build_converter, extract
    conv = build_converter(threads=CORES)
    def run(pdf):
        doc, rep, _ = extract(Path(pdf), conv, lang=LANG, jobs=CORES)
        return doc, dict(rep.timings, ocr_pages=rep.ocr_pages, text_pages=rep.text_pages)

run("deed_scan.pdf")  # warm-up (CUDA kernels, model caches)
for name in ["deed_scan.pdf", "deed40.pdf"] + (["mixed40.pdf"] if MODE == "fast" else []):
    doc, t = run(name)
    t = {k: round(v, 2) if isinstance(v, float) else v for k, v in t.items()}
    res[name] = t
    if name == "deed_scan.pdf":
        res["wer_vs_ground_truth"] = round(wer(norm(gt["text"]), norm(doc.export_to_markdown())), 4)
        res["facts_exact"] = sum(v.lower() in " ".join(norm(doc.export_to_markdown())) for v in gt["facts"].values())
    print(name, t, flush=True)

json.dump(res, open(f"ocr_{MODE}_{CORES}.json", "w"), indent=1)
print("RESULT", json.dumps(res))
