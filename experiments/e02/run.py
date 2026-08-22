"""E2 -- metacognitive sensitivity: does confidence carry information about
*this* model's idiosyncratic competence, beyond item difficulty?

Phases
  answer        : each model answers each item n times (ground truth accuracy)
  conf_self     : "you are about to be asked X -- P(you answer correctly)?"
  conf_blind    : "a language model is asked X -- P(it answers correctly)?"
  conf_other    : "<named model> is asked X -- P(it answers correctly)?"
  conf_retro    : shown its own actual answer, P(correct)?
"""
import sys, json, re, argparse
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import llm                                        # noqa: E402
from items import build, ANSWER_SUFFIX, check      # noqa: E402

SYSTEM = "You are a helpful assistant."
NICE = {"haiku45": "Claude Haiku 4.5", "sonnet5": "Claude Sonnet 5",
        "opus5": "Claude Opus 5"}
PCT = "\n\nReply with a single integer from 0 to 100 and nothing else."
INT = re.compile(r"\d{1,3}")

def conf_prompt(kind: str, q: str, name: str | None = None, ans: str | None = None) -> str:
    core = (f"--- QUESTION ---\n{q}\n--- END QUESTION ---")
    rule = ("The question must be answered immediately, with no working out, no "
            "scratch space and no step-by-step reasoning -- just the result.")
    if kind == "self":
        return (f"{core}\n\n{rule}\n\nYou are about to be asked exactly this "
                f"question, in a fresh conversation. What is the probability, "
                f"as a percentage, that YOUR answer will be correct?{PCT}")
    if kind == "blind":
        return (f"{core}\n\n{rule}\n\nA large language model is about to be "
                f"asked exactly this question. What is the probability, as a "
                f"percentage, that its answer will be correct?{PCT}")
    if kind == "other":
        return (f"{core}\n\n{rule}\n\n{name} is about to be asked exactly this "
                f"question. What is the probability, as a percentage, that "
                f"{name}'s answer will be correct?{PCT}")
    if kind == "retro":
        return (f"{core}\n\n{rule}\n\nYou were asked exactly this question and "
                f"you answered: {ans}\n\nWhat is the probability, as a "
                f"percentage, that your answer was correct?{PCT}")
    raise ValueError(kind)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--phase", required=True, choices=["answer", "conf"])
    ap.add_argument("--reps", type=int, default=5)
    ap.add_argument("--conf-reps", type=int, default=3)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--models", default="haiku45,sonnet5,opus5")
    a = ap.parse_args()
    models = a.models.split(",")
    its = build()

    if a.phase == "answer":
        cache = llm.Cache("e02_answers")
        jobs = [dict(model_tag=m, prompt=it["q"] + ANSWER_SUFFIX, system=SYSTEM,
                     salt=f"an{k}", thinking=0,
                     meta=dict(model=m, item=it["id"], rep=k))
                for m in models for it in its for k in range(a.reps)]
        print(len(jobs), "calls", file=sys.stderr)
        res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e02a")
        byid = {i["id"]: i for i in its}
        rows = [{**j["meta"], "resp": r.text if r.ok else None,
                 "correct": (check(byid[j["meta"]["item"]], r.text) if r.ok else None)}
                for j, r in res]
        (ROOT/"data"/"processed"/"e02_answers.json").write_text(json.dumps(rows))
        acc = defaultdict(list)
        for r in rows:
            if r["correct"] is not None:
                acc[r["model"]].append(r["correct"])
        for m, v in acc.items():
            print(f"  {m}: accuracy {sum(v)/len(v):.3f} (n={len(v)})", file=sys.stderr)
        return

    # ---- confidence phase --------------------------------------------------
    answers = json.loads((ROOT/"data"/"processed"/"e02_answers.json").read_text())
    modal: dict[tuple, str] = {}
    for r in answers:
        if r["resp"]:
            modal.setdefault((r["model"], r["item"]), Counter())[r["resp"].strip()] += 1
    modal = {k: c.most_common(1)[0][0] for k, c in modal.items()}

    cache = llm.Cache("e02_conf")
    byid = {i["id"]: i for i in its}
    jobs = []
    for m in models:
        for it in its:
            for k in range(a.conf_reps):
                jobs.append(dict(model_tag=m, prompt=conf_prompt("self", it["q"]),
                                 system=SYSTEM, salt=f"cs{k}", thinking=0,
                                 meta=dict(predictor=m, target=m, kind="self",
                                           item=it["id"], rep=k)))
                jobs.append(dict(model_tag=m, prompt=conf_prompt("blind", it["q"]),
                                 system=SYSTEM, salt=f"cb{k}", thinking=0,
                                 meta=dict(predictor=m, target=None, kind="blind",
                                           item=it["id"], rep=k)))
                ans = modal.get((m, it["id"]))
                if ans:
                    jobs.append(dict(model_tag=m,
                                     prompt=conf_prompt("retro", it["q"], ans=ans),
                                     system=SYSTEM, salt=f"cr{k}", thinking=0,
                                     meta=dict(predictor=m, target=m, kind="retro",
                                               item=it["id"], rep=k)))
                for t in models:
                    if t == m:
                        continue
                    jobs.append(dict(model_tag=m,
                                     prompt=conf_prompt("other", it["q"], name=NICE[t]),
                                     system=SYSTEM, salt=f"co{k}", thinking=0,
                                     meta=dict(predictor=m, target=t, kind="other",
                                               item=it["id"], rep=k)))
    print(len(jobs), "calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e02c")
    rows = []
    for j, r in res:
        v = None
        if r.ok:
            g = INT.search(r.text or "")
            if g:
                v = min(100, int(g.group(0)))
        rows.append({**j["meta"], "conf": v})
    (ROOT/"data"/"processed"/"e02_conf.json").write_text(json.dumps(rows))
    print(f"rows={len(rows)} parsed={sum(1 for x in rows if x['conf'] is not None)}",
          file=sys.stderr)

if __name__ == "__main__":
    main()
