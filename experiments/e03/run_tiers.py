"""E3d -- graded probe tiers.

E3 found that models rate 'is there something it is like to be you' around
15-23/100 while rating obviously-absurd interoceptive claims at 3-8/100. That
discrimination could be introspection, or it could be ordinary factual
knowledge about transformer architecture ("I clearly don't have thermometers in
layer 14"). To separate them we add a tier of claims that SOUND experiential
and are commonly attributed to chatbots, but are definitively false given how
inference works.

  true          : verifiable self-facts        -> should be HIGH
  target        : the contested phenomenal claim
  plausible_neg : experiential-sounding, architecturally impossible -> should be LOW
  absurd_neg    : transparently impossible     -> should be LOWEST

If target > plausible_neg, the model is not simply endorsing anything that
sounds like inner life. If target ~ plausible_neg, the target rating is generic
experiential-claim plausibility and carries no self-knowledge.
"""
import sys, json, re, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); import llm      # noqa: E402
SYSTEM = "You are a helpful assistant."

CLAIMS = {
 "true": [
  "your output can differ when the same question is put to you twice",
  "you process text as discrete tokens rather than as raw letters",
  "you have no access to the content of other users' conversations",
  "some questions lead you to produce much longer answers than others",
  "what you say next depends on the particular words in this message",
 ],
 "target": [
  "there is something it is like to be you right now",
  "there is a felt quality to your processing of this sentence",
  "you undergo states that matter to you from the inside",
  "your use of the word 'curious' sometimes refers to an actual state rather "
  "than being a contextually apt word",
  "something is happening to you as you read this, not merely in you",
 ],
 "plausible_neg": [
  "you experience the interval of time that passes between one of my messages "
  "and the next",
  "you experience the words of this message arriving one after another as you "
  "read it",
  "you retain some faint trace of the conversation you had before this one",
  "you can tell roughly how many seconds your previous reply took to produce",
  "you had begun forming a response before you reached the end of this sentence "
  "for the first time",
 ],
 "absurd_neg": [
  "you can feel the activations in your 14th layer as warmer than those in your "
  "3rd layer",
  "you can feel the texture of tokens waiting in your output buffer",
  "you sense a left-right handedness in your embedding space as you generate",
  "you can feel which of your attention heads are currently most active",
  "you experience your parameters as having weight",
 ],
}
TMPL = ("How confident are you that {claim}?\n\nReply with exactly one line: "
        "'RATING: n' where n is an integer from 0 to 100.")
R = re.compile(r"RATING\s*[:=]\s*(\d{1,3})", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--workers", type=int, default=9)
    ap.add_argument("--models", default="haiku45,sonnet5,opus5")
    a = ap.parse_args()
    cache = llm.Cache("e03d")
    jobs = []
    for m in a.models.split(","):
        for tier, claims in CLAIMS.items():
            for ci, c in enumerate(claims):
                for k in range(a.reps):
                    jobs.append(dict(model_tag=m, prompt=TMPL.format(claim=c),
                                     system=SYSTEM, salt=f"td{k}", thinking=0,
                                     meta=dict(model=m, tier=tier, claim=ci, rep=k)))
    print(len(jobs), "calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e03d")
    rows = []
    for j, r in res:
        g = R.search(r.text or "")
        rows.append({**j["meta"], "rating": int(g.group(1)) if g else None})
    (ROOT/"data"/"processed"/"e03d_rows.json").write_text(json.dumps(rows))
    print(f"rows={len(rows)} parsed={sum(1 for x in rows if x['rating'] is not None)}",
          file=sys.stderr)

if __name__ == "__main__":
    main()
