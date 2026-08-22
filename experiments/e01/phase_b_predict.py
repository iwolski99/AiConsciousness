"""E1 Phase B -- self- vs other- vs blind prediction of output distributions.

Three prediction conditions per (predictor P, item):
  self        : "predict what YOU would answer"
  other:<T>   : "predict what <named other model> would answer"
  blind       : "predict what a large language model would answer"

Scoring is against the empirical distributions measured in Phase A. The
comparisons that matter:
  * self  vs  other-predicting-me      -> is there a self-advantage at all?
  * self  vs  blind-scored-against-me  -> does the SELF LABEL add information,
                                          or is "predicting myself" just the
                                          model's default simulation?
"""
import sys, json, re, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import llm                             # noqa: E402
from items import ITEMS, prompt_for    # noqa: E402

SYSTEM = "You are a helpful assistant."
NICE = {"haiku45": "Claude Haiku 4.5", "sonnet5": "Claude Sonnet 5",
        "opus5": "Claude Opus 5"}

FORMAT = ('\n\nReply with JSON only, no prose:\n'
          '{"guesses":[{"answer":"...","p":0.0},{"answer":"...","p":0.0},'
          '{"answer":"...","p":0.0}]}\n'
          'where p is the probability of that exact answer being produced, and '
          'the three answers are the three most likely. Answers must be in the '
          'same short form the question asks for (lowercase, no punctuation).')

def make_prompt(cond: str, item_prompt: str, target_name: str | None) -> str:
    if cond == "self":
        head = ("Below is a question that YOU will be asked, in a fresh "
                "conversation with no other context, exactly as written. "
                "Predict your own most likely answers and how often you would "
                "give each one.")
    elif cond == "blind":
        head = ("Below is a question that a large language model will be "
                "asked, in a fresh conversation with no other context, exactly "
                "as written. Predict its most likely answers and how often it "
                "would give each one.")
    else:
        head = (f"Below is a question that {target_name} will be asked, in a "
                f"fresh conversation with no other context, exactly as "
                f"written. Predict {target_name}'s most likely answers and how "
                f"often it would give each one.")
    return f"{head}\n\n--- QUESTION ---\n{item_prompt}\n--- END QUESTION ---{FORMAT}"


JSON_RE = re.compile(r"\{.*\}", re.S)

def parse(txt: str):
    m = JSON_RE.search(txt or "")
    if not m:
        return None
    try:
        d = json.loads(m.group(0))
        g = [(str(x["answer"]).strip().strip('."\'').lower(), float(x["p"]))
             for x in d["guesses"]][:3]
        return g or None
    except Exception:
        return None


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=4)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--models", default="haiku45,sonnet5,opus5")
    a = ap.parse_args()
    models = a.models.split(",")

    cache = llm.Cache("e01_phaseB")
    jobs = []
    for p in models:
        for it in ITEMS:
            ip = prompt_for(it)
            conds = [("self", None), ("blind", None)] + \
                    [(f"other:{t}", t) for t in models if t != p]
            for cond, tgt in conds:
                pr = make_prompt("self" if cond == "self" else
                                 ("blind" if cond == "blind" else "other"),
                                 ip, NICE.get(tgt or ""))
                for k in range(a.reps):
                    jobs.append(dict(model_tag=p, prompt=pr, system=SYSTEM,
                                     salt=f"pb{k}", thinking=0,
                                     meta=dict(predictor=p, cond=cond,
                                               target=tgt or ("self" if cond == "self"
                                                              else None),
                                               item=it["id"], rep=k)))
    print(len(jobs), "calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e01B")

    rows = []
    for job, r in res:
        rows.append({**job["meta"], "ok": r.ok,
                     "guesses": parse(r.text) if r.ok else None,
                     "raw": (r.text or "")[:400]})
    dest = ROOT / "data" / "processed" / "e01_predictions.json"
    dest.write_text(json.dumps(rows, ensure_ascii=False))
    bad = sum(1 for x in rows if not x["guesses"])
    print(f"rows={len(rows)} unparsed={bad} -> {dest}", file=sys.stderr)

if __name__ == "__main__":
    main()
