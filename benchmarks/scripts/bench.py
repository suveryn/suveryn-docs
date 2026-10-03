# End-to-end pipeline benchmark: Docling+Tesseract -> HybridChunker -> bge-m3 retrieval -> llama-server
# usage: python bench.py <pdf> <runs> <label>
import json, sys, time, threading, subprocess, re, difflib, os
import numpy as np, requests

PDF, RUNS, LABEL = sys.argv[1], int(sys.argv[2]), sys.argv[3]
OCR_DEVICE = os.environ.get("DOCLING_DEVICE", "cuda")
QUESTION = ("Wie zijn de verkoper en de koper, wat is de koopprijs en de waarborgsom, "
            "tot wanneer loopt het financieringsvoorbehoud, en welke erfdienstbaarheid rust op het verkochte?")
gt = json.load(open("ground_truth.json"))

# ---- VRAM sampler (whole GPU, includes llama-server + this process) ----
peak = {"mib": 0}; stop = threading.Event()
def sample():
    while not stop.is_set():
        out = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"],
                             capture_output=True, text=True).stdout.strip()
        if out: peak["mib"] = max(peak["mib"], int(out.splitlines()[0]))
        time.sleep(0.1)
threading.Thread(target=sample, daemon=True).start()

T = {}
def tick(): return time.perf_counter()

# ---- one-time init (cold start costs) ----
t0 = tick()
from docling.document_converter import DocumentConverter, PdfFormatOption
from docling.datamodel.base_models import InputFormat
from docling.datamodel.pipeline_options import PdfPipelineOptions, TesseractCliOcrOptions
try:
    from docling.datamodel.accelerator_options import AcceleratorOptions, AcceleratorDevice
except ImportError:
    from docling.datamodel.pipeline_options import AcceleratorOptions, AcceleratorDevice
po = PdfPipelineOptions(do_ocr=True, do_table_structure=True,
                        ocr_options=TesseractCliOcrOptions(lang=["nld"], force_full_page_ocr=True),
                        accelerator_options=AcceleratorOptions(device=AcceleratorDevice.CUDA if OCR_DEVICE == "cuda" else AcceleratorDevice.CPU,
                                                               num_threads=int(os.environ.get("NT", "8"))))
conv = DocumentConverter(format_options={InputFormat.PDF: PdfFormatOption(pipeline_options=po)})
conv.initialize_pipeline(InputFormat.PDF)
from docling.chunking import HybridChunker
try:
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
    from transformers import AutoTokenizer
    chunker = HybridChunker(tokenizer=HuggingFaceTokenizer(tokenizer=AutoTokenizer.from_pretrained("BAAI/bge-m3"), max_tokens=384))
except ImportError:
    chunker = HybridChunker(tokenizer="BAAI/bge-m3", max_tokens=384)
from sentence_transformers import SentenceTransformer
emb = SentenceTransformer("BAAI/bge-m3", device="cuda")
emb.encode(["warmup"])
T["init_cold"] = tick() - t0

def norm(s): return re.sub(r"\s+", " ", re.sub(r"[#*|_\-]+", " ", s)).strip().lower()
def lev(a, b):  # word-level edit distance
    prev = list(range(len(b) + 1))
    for i, x in enumerate(a, 1):
        cur = [i]
        for j, y in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j-1] + 1, prev[j-1] + (x != y)))
        prev = cur
    return prev[-1]

results = []
for run in range(RUNS):
    r = {}
    t_all = tick()
    t = tick(); doc = conv.convert(PDF).document; r["extraction"] = tick() - t
    t = tick(); chunks = [chunker.contextualize(c) for c in chunker.chunk(dl_doc=doc)]; r["chunking"] = tick() - t
    t = tick()
    E = emb.encode(chunks, normalize_embeddings=True, batch_size=16)
    q = emb.encode([QUESTION], normalize_embeddings=True)[0]
    top = np.argsort(-(E @ q))[:5]
    ctx = "\n\n---\n\n".join(chunks[i] for i in sorted(top))
    r["retrieval"] = tick() - t
    t = tick()
    resp = requests.post("http://127.0.0.1:8080/v1/chat/completions", json={
        "messages": [{"role": "user", "content":
            "Je bent assistent van een notaris. Beantwoord de vraag uitsluitend op basis van de onderstaande fragmenten "
            "uit een akte. Antwoord in het Nederlands, beknopt en feitelijk.\n\nFRAGMENTEN:\n" + ctx + "\n\nVRAAG: " + QUESTION}],
        "temperature": 0, "max_tokens": 400, "cache_prompt": False}).json()
    r["inference"] = tick() - t
    r["total"] = tick() - t_all
    u = resp.get("usage", {}); tm = resp.get("timings", {})
    r.update(n_chunks=len(chunks), prompt_tokens=u.get("prompt_tokens"), completion_tokens=u.get("completion_tokens"),
             prefill_tok_s=tm.get("prompt_per_second"), gen_tok_s=tm.get("predicted_per_second"))
    results.append(r)
    print(f"[{LABEL}] run {run}: " + " ".join(f"{k}={v:.2f}" if isinstance(v, float) else f"{k}={v}" for k, v in r.items()), flush=True)

stop.set(); time.sleep(0.2)
md = doc.export_to_markdown()
a, b = norm(gt["text"]).split(), norm(md).split()
sm = difflib.SequenceMatcher(None, b, a, autojunk=False)
missing = [" ".join(a[j1:j2]) + "  →  " + " ".join(b[i1:i2]) for tag, i1, i2, j1, j2 in sm.get_opcodes() if tag != "equal"]
facts_ok = {k: (v.lower() in norm(md)) for k, v in gt["facts"].items()}
out = {"label": LABEL, "init_cold_s": T["init_cold"], "runs": results, "peak_vram_mib": peak["mib"],
       "ocr_word_error_rate": lev(a, b) / len(a), "gt_words": len(a), "ocr_words": len(b),
       "facts_exact": facts_ok, "ocr_diffs": missing[:60], "answer": resp["choices"][0]["message"]["content"],
       "retrieved_chunk_idx": [int(i) for i in top]}
json.dump(out, open(f"result_{LABEL}.json", "w"), ensure_ascii=False, indent=1)
open(f"extracted_{LABEL}.md", "w").write(md)
print(json.dumps({k: out[k] for k in ["init_cold_s", "peak_vram_mib", "ocr_word_error_rate", "facts_exact"]}, ensure_ascii=False))
print("ANSWER:", out["answer"])
