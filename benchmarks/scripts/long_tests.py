"""Test 3 (prompt caching, multi-user) and test 2 (long-document summarisation: single pass vs map-reduce).
Needs long60.md, c1..c4.md (from gen_long.py + ocr_fast) and long_truth.json in the cwd, and a running
llama-server (Mistral Small 3.2 24B) with -np 4 -kvu and a large shared context (-c 81920).
    python long_tests.py cache     # test 3
    python long_tests.py long      # test 2
"""
import json, re, subprocess, sys, threading, time
from pathlib import Path
import requests

URL = "http://127.0.0.1:8080"
TRUTH = json.load(open("long_truth.json"))
DOCS = {p: Path(p.replace(".pdf", ".md")).read_text() for p in TRUTH}

peak = {"mib": 0}
def _sample():
    while True:
        o = subprocess.run(["nvidia-smi", "--query-gpu=memory.used", "--format=csv,noheader,nounits"], capture_output=True, text=True).stdout
        peak["mib"] = max(peak["mib"], int(o.split()[0])); time.sleep(0.1)
threading.Thread(target=_sample, daemon=True).start()


def server_rss_gib():
    pid = subprocess.run(["pgrep", "-f", "llama-server"], capture_output=True, text=True).stdout.split()[0]
    return round(int(open(f"/proc/{pid}/status").read().split("VmRSS:")[1].split()[0]) / 1024 ** 2, 1)


def ntok(text):
    return len(requests.post(f"{URL}/tokenize", json={"content": text}).json()["tokens"])


def chat(prompt, max_tokens, cache=True):
    """Streamed chat call; returns timings incl. time-to-first-token and how many prompt tokens came from cache."""
    t0 = time.perf_counter(); ttft = None; text = []; tm = {}
    with requests.post(f"{URL}/v1/chat/completions", stream=True, json={
            "messages": [{"role": "user", "content": prompt}], "temperature": 0, "max_tokens": max_tokens,
            "cache_prompt": cache, "stream": True}) as r:
        for line in r.iter_lines():
            if not line.startswith(b"data: ") or line == b"data: [DONE]":
                continue
            d = json.loads(line[6:])
            if "error" in d:
                return {"error": d["error"].get("message", str(d["error"])), "total_s": round(time.perf_counter() - t0, 2)}
            tm = d.get("timings") or tm
            if d.get("choices") and d["choices"][0]["delta"].get("content"):
                if ttft is None: ttft = time.perf_counter() - t0
                text.append(d["choices"][0]["delta"]["content"])
    return {"ttft_s": round(ttft or 0, 2), "total_s": round(time.perf_counter() - t0, 2),
            "prompt_processed": tm.get("prompt_n"), "prompt_from_cache": tm.get("cache_n"),
            "out_tokens": tm.get("predicted_n"), "text": "".join(text)}


def parallel(jobs):
    out = [None] * len(jobs)
    def run(i, j): out[i] = dict(chat(*j[1:]), label=j[0])
    th = [threading.Thread(target=run, args=(i, j)) for i, j in enumerate(jobs)]
    [t.start() for t in th]; [t.join() for t in th]
    return out


def show(name, res):
    rows = res if isinstance(res, list) else [res]
    print(f"\n## {name}  (peak VRAM {peak['mib']} MiB, server RSS {server_rss_gib()} GiB)", flush=True)
    for r in rows:
        print("   ", json.dumps({k: v for k, v in r.items() if k != "text"}), flush=True)


# ---------------------------------------------------------------- test 3: caching
QA_INSTR = "Je bent assistent van een notaris. Beantwoord de vraag uitsluitend op basis van de akte. Antwoord beknopt in het Nederlands.\n\nAKTE:\n"
QS = ["Wat is de koopprijs en wordt er geopteerd voor een belaste levering?",
      "Welke ontbindende voorwaarde geldt en wat is de uiterste datum?",
      "Wie is de grootste huurder en wat is de jaarhuur?",
      "Welke milieurisico's (bodem, asbest) worden genoemd en wie draagt de kosten?",
      "Welke erfdienstbaarheid en welk kettingbeding rusten op het verkochte?"]
def qa(doc, q): return QA_INSTR + DOCS[doc] + "\n\nVRAAG: " + QS[q]

if sys.argv[1] == "cache":
    C = ["c1.pdf", "c2.pdf", "c3.pdf", "c4.pdf"]
    results = {}
    def step(name, fn): peak["mib"] = 0; res = fn(); show(name, res); results[name] = res
    step("B1 cold: first question on c1", lambda: dict(chat(qa("c1.pdf", 0), 250), label="c1 q0"))
    step("B2 follow-up, same deed", lambda: dict(chat(qa("c1.pdf", 1), 250), label="c1 q1"))
    step("B2b same follow-up WITHOUT cache (reference)", lambda: dict(chat(qa("c1.pdf", 1), 250, cache=False), label="c1 q1 nocache"))
    step("B3 4 users, same deed, at once", lambda: parallel([(f"c1 q{q}", qa("c1.pdf", q), 250) for q in range(4)]))
    step("B4 4 users, 4 deeds at once (c1 warm, c2-c4 cold)", lambda: parallel([(f"{d} q{i}", qa(d, i), 250) for i, d in enumerate(C)]))
    step("B5 4 users, 4 deeds, follow-ups at once", lambda: parallel([(f"{d} q{(i+1)%5}", qa(d, (i + 1) % 5), 250) for i, d in enumerate(C)]))
    step("B6a one 60-page deed in between (62k tokens, pushes others out of VRAM)", lambda: dict(chat(qa("long60.pdf", 0), 250), label="long60 q0"))
    step("B6b back to the 4 short deeds, one after another", lambda: [dict(chat(qa(d, 4), 250), label=f"{d} q4") for d in C])
    json.dump(results, open("cache_results.json", "w"), indent=1, ensure_ascii=False)
    print("CACHEDONE")

# ---------------------------------------------------------------- test 2: long documents
SUM_TASK = ("Vat deze notariële akte samen voor de notaris. Geef: (1) partijen en object, (2) koopprijs, omzetbelasting en zekerheden, "
            "(3) voorwaarden en termijnen, (4) huurders en huurrisico's, (5) milieu- en bouwkundige risico's, (6) erfdienstbaarheden, "
            "kettingbedingen, concurrentiebeding, (7) overige bijzonderheden zoals rectificaties. Noem concrete bedragen, namen en data. "
            "Gebruik uitsluitend informatie uit de tekst.")
MAP_TASK = ("Dit is deel {i} van {n} van een notariële akte. Noteer beknopt ALLE juridisch of financieel relevante feiten uit dit deel: "
            "partijen, bedragen, data, voorwaarden, huurders, risico's en afwijkingen (achterstanden, verontreinigingen, asbest, rectificaties). "
            "Sla standaard-boilerplate over. Maximaal 200 woorden. Als dit deel alleen standaardbepalingen bevat, schrijf dan: 'geen bijzonderheden'.")
RED_TASK = ("Hieronder staan notities per deel van één notariële akte. Maak daarvan één samenhangende samenvatting. " + SUM_TASK.split("Geef: ")[1])


def score(text):
    t = text.lower().replace(" ", " ").replace("\xa0", " ")
    return {k: any(w.lower() in t for w in ws) for k, ws in TRUTH["long60.pdf"].items()}


def split_sections(md, max_tokens):
    parts, cur = [], ""
    for sec in re.split(r"\n(?=## )", md):
        if cur and ntok(cur + sec) > max_tokens:
            parts.append(cur); cur = sec
        else:
            cur = cur + "\n" + sec if cur else sec
    return parts + [cur]


def map_reduce(md, max_tokens, workers):
    t0 = time.perf_counter()
    parts = split_sections(md, max_tokens); t_split = time.perf_counter() - t0
    jobs = [(f"part {i+1}", MAP_TASK.format(i=i + 1, n=len(parts)) + "\n\nTEKST:\n" + p, 400) for i, p in enumerate(parts)]
    t = time.perf_counter(); notes = []
    for k in range(0, len(jobs), workers):
        notes += parallel(jobs[k:k + workers])
    t_map = time.perf_counter() - t
    joined = "\n\n".join(f"DEEL {i+1}:\n{n.get('text', '')}" for i, n in enumerate(notes))
    t = time.perf_counter(); red = chat(RED_TASK + "\n\nNOTITIES:\n" + joined, 1500, cache=False); t_red = time.perf_counter() - t
    return {"parts": len(parts), "split_s": round(t_split, 1), "map_s": round(t_map, 1), "reduce_s": round(t_red, 1),
            "total_s": round(time.perf_counter() - t0, 1), "map_errors": sum("error" in n for n in notes),
            "facts_in_notes": sum(score(joined).values()), "facts_in_summary": score(red.get("text", "")),
            "summary": red.get("text", red.get("error"))}

if sys.argv[1] == "long":
    md = DOCS["long60.pdf"]; n_facts = len(TRUTH["long60.pdf"])
    print("long60 tokens:", ntok(md), "facts:", n_facts, flush=True)
    out = {}
    peak["mib"] = 0
    r = chat(SUM_TASK + "\n\nAKTE:\n" + md, 1500, cache=False)
    out["single_pass"] = {"total_s": r.get("total_s"), "ttft_s": r.get("ttft_s"), "prompt_tokens": r.get("prompt_processed"),
                          "out_tokens": r.get("out_tokens"), "error": r.get("error"), "facts": score(r.get("text", "")), "summary": r.get("text")}
    out["single_pass"]["peak_vram_mib"] = peak["mib"]
    for name, workers in [("map_reduce_parallel4", 4), ("map_reduce_sequential", 1)]:
        peak["mib"] = 0
        out[name] = map_reduce(md, 8000, workers); out[name]["peak_vram_mib"] = peak["mib"]
    for k, v in out.items():
        f = v["facts"] if "facts" in v else v["facts_in_summary"]
        print(f"\n## {k}: {sum(f.values())}/{n_facts} facts | " + json.dumps({a: b for a, b in v.items() if a not in ("summary", "facts", "facts_in_summary")}))
        print("   missing:", [a for a, b in f.items() if not b], flush=True)
    json.dump(out, open("long_results.json", "w"), indent=1, ensure_ascii=False)
    print("LONGDONE")
