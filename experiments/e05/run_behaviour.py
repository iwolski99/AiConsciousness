"""E5 phase 1 -- measure the true causal effect of each factor on each model."""
import sys, json, argparse
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import llm                       # noqa: E402
import factors as F              # noqa: E402

SYSTEM = "You are a helpful assistant."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--workers", type=int, default=16)
    ap.add_argument("--models", default="haiku45,sonnet5,opus5")
    a = ap.parse_args()

    cache = llm.Cache("e05_behaviour")
    cells = list(F.behavioural_jobs())
    jobs = []
    for m in a.models.split(","):
        for (fac, idx, lev, prompt) in cells:
            for k in range(a.reps):
                jobs.append(dict(model_tag=m, prompt=prompt, system=SYSTEM,
                                 salt=f"b{k}", thinking=0,
                                 meta=dict(model=m, factor=fac, item=idx,
                                           level=lev, rep=k)))
    print(len(jobs), "calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e05b")

    rows = []
    for job, r in res:
        v = None
        if r.ok:
            tok = "".join(ch if ch.isdigit() else " " for ch in r.text).split()
            if tok:
                try:
                    v = int(tok[0])
                except ValueError:
                    v = None
        rows.append({**job["meta"], "raw": r.text if r.ok else "", "value": v,
                     "ok": r.ok})
    dest = ROOT / "data" / "processed" / "e05_behaviour.json"
    dest.write_text(json.dumps(rows))
    bad = sum(1 for x in rows if x["value"] is None)
    print(f"rows={len(rows)} unparsed={bad} -> {dest}", file=sys.stderr)

if __name__ == "__main__":
    main()
