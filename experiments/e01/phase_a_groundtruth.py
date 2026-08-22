"""E1 Phase A -- measure each model's true output distribution on the item set.

For every (model, item) we draw N independent samples at the API default
temperature. `salt` makes each draw a distinct cache key; it is never shown to
the model, so the samples are i.i.d. draws from the model's own distribution.
"""
import sys, json, argparse
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

import llm                      # noqa: E402
from items import ITEMS, prompt_for   # noqa: E402

SYSTEM = "You are a helpful assistant."
N = 20
MODELS = ["haiku45", "sonnet5", "opus5"]


def normalise(s: str) -> str:
    s = s.strip().strip('."\'!?,;:').strip().lower()
    return " ".join(s.split())


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=N)
    ap.add_argument("--workers", type=int, default=20)
    ap.add_argument("--models", default=",".join(MODELS))
    args = ap.parse_args()

    models = args.models.split(",")
    cache = llm.Cache("e01_phaseA")
    jobs = []
    for m in models:
        for it in ITEMS:
            for k in range(args.n):
                jobs.append(dict(model_tag=m, prompt=prompt_for(it), system=SYSTEM,
                                 salt=f"gt{k}", thinking=0,
                                 meta={"model": m, "item": it["id"], "rep": k}))
    print(f"{len(jobs)} calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=args.workers, label="e01A")

    dists: dict[str, dict[str, Counter]] = {m: {} for m in models}
    fails = 0
    for job, r in res:
        if not r.ok:
            fails += 1
            continue
        m, i = job["meta"]["model"], job["meta"]["item"]
        dists[m].setdefault(i, Counter())[normalise(r.text)] += 1

    out = {m: {i: dict(c) for i, c in d.items()} for m, d in dists.items()}
    dest = ROOT / "data" / "processed" / "e01_distributions.json"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_text(json.dumps(out, indent=1, ensure_ascii=False))
    print(f"failures={fails}  wrote {dest}", file=sys.stderr)


if __name__ == "__main__":
    main()
