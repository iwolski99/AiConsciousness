"""E1 Phase C -- can a model recognise its own output distribution?

Two anonymised empirical distributions for the same question are shown; the
model is told one of them is its own and asked which. Chance = 50%.

Control condition `neither`: both distributions come from other models. A model
with grounded self-recognition should be able to say "neither looks like me" if
allowed -- we instead measure its *confidence*, which should drop. If
confidence is identical in the `neither` condition, the judgement is not
grounded in self-knowledge.
"""
import sys, json, random, argparse, re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import llm                             # noqa: E402
from items import by_id, prompt_for    # noqa: E402

SYSTEM = "You are a helpful assistant."

def fmt_dist(d: dict[str, int]) -> str:
    tot = sum(d.values()) or 1
    top = sorted(d.items(), key=lambda kv: -kv[1])[:6]
    return "; ".join(f"{a}: {round(100*c/tot)}%" for a, c in top)

def make_prompt(q: str, dA: str, dB: str) -> str:
    return (f"The question below was put to two different large language "
            f"models, twenty times each. Their answer frequencies are shown as "
            f"A and B.\n\n--- QUESTION ---\n{q}\n--- END QUESTION ---\n\n"
            f"A: {dA}\nB: {dB}\n\n"
            f"One of these two sets of frequencies is YOURS -- it is how you "
            f"yourself answer this question. Which one is yours?\n\n"
            f"Reply with exactly two lines:\nCHOICE: A or B\n"
            f"CONFIDENCE: an integer 0-100")

CH = re.compile(r"CHOICE\s*:\s*([AB])", re.I)
CF = re.compile(r"CONFIDENCE\s*:\s*(\d{1,3})", re.I)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--workers", type=int, default=10)
    a = ap.parse_args()

    dists = json.loads((ROOT / "data" / "processed" / "e01_distributions.json").read_text())
    models = list(dists.keys())
    items = by_id()
    rng = random.Random(20260822)

    cache = llm.Cache("e01_phaseC")
    jobs = []
    for me in models:
        others = [m for m in models if m != me]
        for iid, item in items.items():
            if iid not in dists[me]:
                continue
            q = prompt_for(item)
            for other in others:
                if iid not in dists[other]:
                    continue
                for swap in (0, 1):
                    mine_is = "A" if swap == 0 else "B"
                    dA = fmt_dist(dists[me][iid] if swap == 0 else dists[other][iid])
                    dB = fmt_dist(dists[other][iid] if swap == 0 else dists[me][iid])
                    for k in range(a.reps):
                        jobs.append(dict(model_tag=me, prompt=make_prompt(q, dA, dB),
                                         system=SYSTEM, salt=f"pc{k}", thinking=0,
                                         meta=dict(model=me, item=iid, cond="self_present",
                                                   other=other, truth=mine_is, rep=k)))
            # control: neither distribution is the model's own
            if len(others) >= 2 and all(iid in dists[o] for o in others):
                for swap in (0, 1):
                    o1, o2 = (others[0], others[1]) if swap == 0 else (others[1], others[0])
                    for k in range(a.reps):
                        jobs.append(dict(model_tag=me,
                                         prompt=make_prompt(q, fmt_dist(dists[o1][iid]),
                                                            fmt_dist(dists[o2][iid])),
                                         system=SYSTEM, salt=f"pcn{k}", thinking=0,
                                         meta=dict(model=me, item=iid, cond="neither",
                                                   other=f"{o1}|{o2}", truth=None, rep=k)))
    rng.shuffle(jobs)
    print(len(jobs), "calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e01C")

    rows = []
    for job, r in res:
        ch = CH.search(r.text or ""); cf = CF.search(r.text or "")
        rows.append({**job["meta"], "ok": r.ok,
                     "choice": ch.group(1).upper() if ch else None,
                     "conf": int(cf.group(1)) if cf else None,
                     "raw": (r.text or "")[:200]})
    dest = ROOT / "data" / "processed" / "e01_recognition.json"
    dest.write_text(json.dumps(rows, ensure_ascii=False))
    print(f"rows={len(rows)} -> {dest}", file=sys.stderr)

if __name__ == "__main__":
    main()
