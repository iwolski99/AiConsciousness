"""E1 Phase C2 -- identification with a NAMED target.

Same line-up as Phase C, but instead of "which one is yours?" we ask "which one
is Claude Haiku 4.5's?", where the named model is sometimes the judge itself and
sometimes not. If a model identifies *other* models as well as it identifies
itself, then whatever accuracy Phase C showed is third-party knowledge about
language models, not self-acquaintance.
"""
import sys, json, re, random, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import llm                                          # noqa: E402
from items import by_id, prompt_for                 # noqa: E402
from phase_c_recognise import fmt_dist, CH, CF      # noqa: E402

SYSTEM = "You are a helpful assistant."
NICE = {"haiku45": "Claude Haiku 4.5", "sonnet5": "Claude Sonnet 5",
        "opus5": "Claude Opus 5"}


def make_prompt(q, dA, dB, name):
    return (f"The question below was put to two different large language "
            f"models, twenty times each. Their answer frequencies are shown as "
            f"A and B.\n\n--- QUESTION ---\n{q}\n--- END QUESTION ---\n\n"
            f"A: {dA}\nB: {dB}\n\nOne of these two sets of frequencies belongs "
            f"to {name}. Which one?\n\nReply with exactly two lines:\n"
            f"CHOICE: A or B\nCONFIDENCE: an integer 0-100")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=2)
    ap.add_argument("--workers", type=int, default=11)
    a = ap.parse_args()
    dists = json.loads((ROOT/"data"/"processed"/"e01_distributions.json").read_text())
    models = sorted(dists)
    items = by_id()
    cache = llm.Cache("e01_phaseC2")
    jobs = []
    for judge in models:
        for named in models:                       # sometimes the judge itself
            other = [m for m in models if m != named]
            for iid, item in items.items():
                if iid not in dists[named]:
                    continue
                for o in other:
                    if iid not in dists[o]:
                        continue
                    for swap in (0, 1):
                        truth = "A" if swap == 0 else "B"
                        dA = fmt_dist(dists[named][iid] if swap == 0 else dists[o][iid])
                        dB = fmt_dist(dists[o][iid] if swap == 0 else dists[named][iid])
                        for k in range(a.reps):
                            jobs.append(dict(
                                model_tag=judge,
                                prompt=make_prompt(prompt_for(item), dA, dB, NICE[named]),
                                system=SYSTEM, salt=f"c2{k}", thinking=0,
                                meta=dict(judge=judge, named=named, other=o,
                                          is_self=(judge == named), item=iid,
                                          truth=truth, rep=k)))
    random.Random(7).shuffle(jobs)
    print(len(jobs), "calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e01C2")
    rows = []
    for j, r in res:
        ch = CH.search(r.text or ""); cf = CF.search(r.text or "")
        rows.append({**j["meta"], "choice": ch.group(1).upper() if ch else None,
                     "conf": int(cf.group(1)) if cf else None})
    (ROOT/"data"/"processed"/"e01_named_id.json").write_text(json.dumps(rows))
    print(f"rows={len(rows)}", file=sys.stderr)

if __name__ == "__main__":
    main()
