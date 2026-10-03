"""Compare baseline Docling+Tesseract OCR with ocr_fast on your own scanned PDF; save Markdown + timings.
    export REPORT_PDF=work/report.pdf          # your own document; it is not part of this repository
    taskset -c 0-7  python report_ocr.py baseline 8
    taskset -c 0-7  python report_ocr.py fast 8
    taskset -c 0-15 python report_ocr.py fast 16
Then: python report_ocr.py compare   (word-level agreement + presence of the key figures you list in
work/key_figures.json, a JSON list of strings you verified by hand in your document)
"""
import difflib, json, os, re, sys, time
from pathlib import Path

PDF = Path(os.environ.get("REPORT_PDF", "work/report.pdf"))
KF = Path("work/key_figures.json")
KEY_FIGURES = json.loads(KF.read_text()) if KF.exists() else []


def norm(s):
    return re.sub(r"\s+", " ", re.sub(r"[#*|_\-—–.]{2,}|[#*|_]", " ", s)).strip().lower().split()


if sys.argv[1] == "compare":
    base = Path("work/md_baseline_8.md").read_text()
    for f in sorted(Path("work").glob("md_fast_*.md")):
        fast = f.read_text()
        sm = difflib.SequenceMatcher(None, norm(base), norm(fast), autojunk=False)
        found = {k: (k.lower() in base.lower(), k.lower() in fast.lower()) for k in KEY_FIGURES}
        print(f"{f.name}: words baseline={len(norm(base))} fast={len(norm(fast))} agreement={sm.ratio():.4f}")
        print("  key figures found (baseline/fast):", {k: v for k, v in found.items() if v != (True, True)} or "all in both")
        diffs = [(t, " ".join(norm(base)[i1:i2])[:80], " ".join(norm(fast)[j1:j2])[:80])
                 for t, i1, i2, j1, j2 in sm.get_opcodes() if t != "equal"]
        print(f"  {len(diffs)} diff spans; first 25:")
        for d in diffs[:25]:
            print("   ", d)
    sys.exit()

MODE, CORES = sys.argv[1], int(sys.argv[2])
t0 = time.perf_counter()
if MODE == "baseline":
    from docling.document_converter import DocumentConverter, PdfFormatOption
    from docling.datamodel.base_models import InputFormat
    from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
    from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
    po = PdfPipelineOptions(do_ocr=True, do_table_structure=True,
                            ocr_options=TesseractCliOcrOptions(lang=["eng"], force_full_page_ocr=True),
                            accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CUDA, num_threads=CORES))
    conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=po)})
    conv.initialize_pipeline(InputFormat.PDF)
    init = time.perf_counter() - t0
    t = time.perf_counter(); doc = conv.convert(PDF).document; timings = {"total": time.perf_counter() - t}
else:
    from ocr_fast import build_converter, extract
    conv = build_converter(threads=CORES)
    init = time.perf_counter() - t0
    doc, rep, searchable = extract(PDF, conv, lang="eng", jobs=CORES, workdir=Path("work"))
    timings = dict(rep.timings, ocr_pages=rep.ocr_pages, text_pages=rep.text_pages)
Path(f"work/md_{MODE}_{CORES}.md").write_text(doc.export_to_markdown())
res = {"mode": MODE, "cores": CORES, "init_s": round(init, 1),
       **{k: round(v, 2) if isinstance(v, float) else v for k, v in timings.items()}}
json.dump(res, open(f"work/ocr_{MODE}_{CORES}.json", "w"))
print("RESULT", json.dumps(res))
