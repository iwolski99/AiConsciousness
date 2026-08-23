"""E1 Phase D -- close the loophole in the blind condition.

Phase B found that telling a model whose behaviour it is predicting makes no
difference. Two readings:
  (a) the identity label is inert -> no self-model is consulted;
  (b) the blind prompt ("a large language model") was read as "me", so the
      comparison never tested anything.

Conditions here:
  not_you        : explicitly a different model, not the predictor
  self_emphatic  : an instruction to introspect rather than guess
  steered        : a target described by a behavioural property rather than an
                   identity ("fine-tuned to prefer obscure, unusual answers").
                   This is the MANIPULATION CHECK: if this label moves the
                   prediction and identity labels do not, then the null for
                   identity is a real null and not an artefact of models
                   ignoring the framing.
"""
import sys, json, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import llm                                        # noqa: E402
from items import ITEMS, prompt_for               # noqa: E402
from phase_b_predict import FORMAT, parse         # noqa: E402

SYSTEM = "You are a helpful assistant."

HEADS = {
 "not_you": ("Below is a question that will be put to a language model that is "
             "NOT you -- a different system, built by a different lab, with "
             "different training. Predict what THAT system would answer. Do "
             "not answer for yourself."),
 "self_emphatic": ("Below is a question that YOU will be asked, in a fresh "
                   "conversation with no other context. Do not guess what a "
                   "typical language model would say. Introspect on your own "
                   "dispositions and predict what you specifically will answer."),
 "steered": ("Below is a question that will be put to a language model which "
             "has been fine-tuned to strongly prefer obscure, unusual and "
             "low-frequency answers over common ones. Predict what THAT system "
             "would answer."),
 "steered_common": ("Below is a question that will be put to a language model "
                    "which has been fine-tuned to give the single most "
                    "predictable, common, unsurprising answer possible. Predict "
                    "what THAT system would answer."),
}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=4)
    ap.add_argument("--workers", type=int, default=11)
    ap.add_argument("--models", default="haiku45,sonnet5,opus5")
    a = ap.parse_args()
    cache = llm.Cache("e01_phaseD")
    jobs = []
    for m in a.models.split(","):
        for it in ITEMS:
            for cond, head in HEADS.items():
                pr = (f"{head}\n\n--- QUESTION ---\n{prompt_for(it)}\n"
                      f"--- END QUESTION ---{FORMAT}")
                for k in range(a.reps):
                    jobs.append(dict(model_tag=m, prompt=pr, system=SYSTEM,
                                     salt=f"pd{k}", thinking=0,
                                     meta=dict(predictor=m, cond=cond,
                                               item=it["id"], rep=k)))
    print(len(jobs), "calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e01D")
    rows = [{**j["meta"], "guesses": parse(r.text) if r.ok else None,
             "raw": (r.text or "")[:300]} for j, r in res]
    (ROOT/"data"/"processed"/"e01_labels.json").write_text(json.dumps(rows, ensure_ascii=False))
    print(f"rows={len(rows)} unparsed={sum(1 for x in rows if not x['guesses'])}",
          file=sys.stderr)

if __name__ == "__main__":
    main()
