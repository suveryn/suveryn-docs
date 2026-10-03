"""Concurrent users against llama-server, using the text of your own report (from report_ocr.py).
    python load_test.py prep    # builds prompts from work/md_fast_8.md (bge-m3 retrieval), then exits
    python load_test.py run     # runs the concurrency scenarios, writes work/load_results.json
Server must run with parallel slots, e.g. -np 4 --kv-unified -c 49152.
"""
import json, os, subprocess, sys, threading, time
from pathlib import Path
import requests

URL = "http://127.0.0.1:8080/v1/chat/completions"
SUMMARY_TASK = ("Summarize this due diligence report. Give: (1) a short summary of the company and the proposed investment, "
                "(2) the key findings, as bullet points, (3) the recommendations and the final conclusion of the committee. "
                "Use only information from the text. Be factual and concise.")
QUESTIONS = ["What investment amount, valuation and conditions does the due diligence team recommend?",
             "Who are the main competitors of the company and how does it differentiate itself?",
             "What risks does the report identify regarding the management team and key people?",
             "Which exit routes does the due diligence team expect, and what value and multiple do they project?"]

if sys.argv[1] == "prep":
    import numpy as np
    from docling_core.transforms.chunker.hybrid_chunker import HybridChunker
    from docling_core.transforms.chunker.tokenizer.huggingface import HuggingFaceTokenizer
    from docling.document_converter import DocumentConverter
    from sentence_transformers import SentenceTransformer
    from transformers import AutoTokenizer
    md_path = Path("work/md_fast_8.md")
    doc = DocumentConverter().convert(md_path).document  # re-parse the Markdown into a DoclingDocument for chunking
    chunker = HybridChunker(tokenizer=HuggingFaceTokenizer(tokenizer=AutoTokenizer.from_pretrained("BAAI/bge-m3"), max_tokens=384))
    chunks = [chunker.contextualize(c) for c in chunker.chunk(dl_doc=doc)]
    emb = SentenceTransformer("BAAI/bge-m3", device="cuda")
    E = emb.encode(chunks, normalize_embeddings=True)
    qa = []
    for q in QUESTIONS:
        v = emb.encode([q], normalize_embeddings=True)[0]
        ctx = "\n\n---\n\n".join(chunks[i] for i in sorted(np.argsort(-(E @ v))[:8]))
        qa.append("Answer the question using only these excerpts from a due diligence report. Be concise.\n\n"
                  f"EXCERPTS:\n{ctx}\n\nQUESTION: {q}")
    json.dump({"summary": SUMMARY_TASK + "\n\nFULL REPORT:\n" + md_path.read_text(), "qa": qa}, open("work/prompts.json", "w"))
    print("prepared", len(chunks), "chunks")
    sys.exit()

P = json.load(open("work/prompts.json"))
peak = {"mib": 0}; stop = threading.Event()
def sample():
    while not stop.is_set():
        o = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
        peak["mib"] = max(peak["mib"], int(o.split()[0])); time.sleep(0.1)
threading.Thread(target=sample, daemon=True).start()


def call(kind, prompt, max_tokens, out):
    t0 = time.perf_counter(); ttft = None; n = 0; timings = {}
    with requests.post(URL, stream=True, json={"messages": [{"role": "user", "content": prompt}], "temperature": 0,
                                               "max_tokens": max_tokens, "cache_prompt": False, "stream": True,
                                               "timings_per_token": False}) as r:
        for line in r.iter_lines():
            if not line.startswith(b"data: ") or line == b"data: [DONE]":
                continue
            d = json.loads(line[6:])
            if d.get("timings"): timings = d["timings"]
            if d.get("choices") and d["choices"][0]["delta"].get("content"):
                n += 1
                if ttft is None: ttft = time.perf_counter() - t0
    out.append({"kind": kind, "ttft_s": round(ttft or 0, 2), "total_s": round(time.perf_counter() - t0, 2), "out_tokens": n,
                "prompt_tokens": timings.get("prompt_n"), "gen_tok_s": round(timings.get("predicted_per_second", 0), 1)})


def scenario(name, jobs):
    out = []
    th = [threading.Thread(target=call, args=(k, p, m, out)) for k, p, m in jobs]
    peak["mib"] = 0; t = time.perf_counter()
    [x.start() for x in th]; [x.join() for x in th]
    res = {"scenario": name, "wall_s": round(time.perf_counter() - t, 2), "peak_vram_mib": peak["mib"], "requests": out}
    print(json.dumps(res), flush=True); return res


S, Q = ("summary", P["summary"], 700), [("qa", q, 300) for q in P["qa"]]
results = [scenario("warmup", [Q[0]])]
results += [scenario("1 qa", Q[:1]), scenario("2 qa", Q[:2]), scenario("4 qa", Q),
            scenario("1 summary", [S]), scenario("2 summaries", [S, S]), scenario("1 summary + 3 qa", [S] + Q[:3])]

# 2 users asking questions while a new 38-page document is being OCR'd (CPU 0-7 + Docling on the GPU)
peak["mib"] = 0; t = time.perf_counter()
ocr = subprocess.Popen(f"taskset -c 0-7 python ocr_fast.py {os.environ.get('REPORT_PDF', 'work/report.pdf')} --lang eng --jobs 8",
                       shell=True, stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, text=True)
qa_during = []
while ocr.poll() is None:
    th = [threading.Thread(target=call, args=(k, p, m, qa_during)) for k, p, m in Q[:2]]
    [x.start() for x in th]; [x.join() for x in th]
ocr_line = [l for l in ocr.stdout.read().splitlines() if l.startswith("pages=")]
res = {"scenario": "2 qa during OCR of 38 pages", "wall_s": round(time.perf_counter() - t, 2), "peak_vram_mib": peak["mib"],
       "ocr": ocr_line, "requests": qa_during}
print(json.dumps(res), flush=True); results.append(res)
stop.set()
json.dump(results, open("work/load_results.json", "w"), indent=1)
print("LOADDONE")
