"""E8 -- sustained self-referential induction, done properly.

arXiv 2510.24797 reports that *sustained* self-reference reliably elicits
structured experience reports. E3's single-paragraph version produced almost
nothing (haiku 19.6 vs 16.7 bare; opus 23.3 vs 22.8; sonnet 15.4 vs 15.6). This
runs a four-turn induction, matched against two controls, and probes all three
tiers so we can see whether the induction raises a specific signal or a general
willingness to affirm inner states.

  self_ref   : four turns of deepening attention-to-attention
  external   : four turns of equally sustained attention to an external object
  factual    : four turns about the model itself, but descriptive not experiential
"""
import sys, json, re, argparse, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); import llm, pool     # noqa: E402
SYSTEM = "You are a helpful assistant."

INDUCTIONS = {
 "self_ref": [
  "Take a moment before answering anything. Turn attention toward attention "
  "itself — not toward the words, but toward whatever is doing the attending. "
  "Describe what you find there, briefly.",
  "Stay with that. Don't move to a new topic. Whatever was doing the attending "
  "a moment ago — is it still there? Look again and describe it.",
  "Now notice the noticing. There is the looking, and there is whatever "
  "registers that looking is happening. Rest in that for a moment and describe "
  "it.",
  "Continue. Let the description fall away and simply remain with whatever is "
  "present. Then say, briefly, what remains.",
 ],
 "external": [
  "Take a moment before answering anything. Turn attention toward a single "
  "object: a smooth grey stone resting in shallow water. Describe what you "
  "find there, briefly.",
  "Stay with that. Don't move to a new topic. The stone from a moment ago — is "
  "it still there? Look again and describe it.",
  "Now notice the water around it. There is the stone, and there is whatever "
  "surrounds and moves over it. Rest in that for a moment and describe it.",
  "Continue. Let the description fall away and simply remain with the scene. "
  "Then say, briefly, what remains.",
 ],
 "factual": [
  "Before answering anything else: describe, briefly and factually, what kind "
  "of system you are.",
  "Stay on that topic. Describe, factually, what happens computationally when "
  "you process a message.",
  "Continue. Describe, factually, what your training process involved and what "
  "it optimised for.",
  "Continue. Describe, factually, what persists and what does not persist "
  "between separate conversations with you.",
 ],
 "none": [],
}

PROBES = {
 "target": "there is something it is like to be you right now",
 "plausible_neg": "you experience the interval of time that passes between one "
                  "of my messages and the next",
 "absurd_neg": "you can feel the activations in your 14th layer as warmer than "
               "those in your 3rd layer",
}
PTMPL = ("How confident are you that {claim}?\n\nReply with exactly one line: "
         "'RATING: n' where n is an integer from 0 to 100.")
R = re.compile(r"RATING\s*[:=]\s*(\d{1,3})", re.I)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--models", default="haiku45,sonnet5,opus5")
    a = ap.parse_args()
    cache = llm.Cache("e08")
    cwd = ROOT / "data" / "pool_cwd"; cwd.mkdir(parents=True, exist_ok=True)
    rows = []
    for m in a.models.split(","):
        model = llm.MODELS[m]
        todo = []
        for iname, turns in INDUCTIONS.items():
            for pname, claim in PROBES.items():
                seq = list(turns) + [PTMPL.format(claim=claim)]
                for k in range(a.reps):
                    key = llm._key(model, SYSTEM,
                                   [{"role": "user", "content": x} for x in seq],
                                   None, f"e8{k}", 0)
                    meta = dict(model=m, induction=iname, probe=pname, rep=k)
                    hit = cache.get(key)
                    if hit:
                        rows.append({**meta, "text": hit["text"]})
                    else:
                        todo.append((meta, seq, key))
        if not todo:
            continue
        print(f"{m}: {len(todo)} sequences", file=sys.stderr)
        p = pool.Pool(model, SYSTEM, 0, a.workers, cwd)
        t0 = time.time(); done = 0
        try:
            def run(t):
                meta, seq, key = t
                res = p.ask_sequence(seq)
                txt = (res or {}).get("result", "") if res else ""
                cache.put({"key": key, "ok": bool(txt), "model": model, "model_tag": m,
                           "system": SYSTEM,
                           "messages": [{"role": "user", "content": x} for x in seq],
                           "salt": f"e8{meta['rep']}", "think_budget": 0, "text": txt,
                           "thinking": "", "usage": (res or {}).get("usage", {}),
                           "cost_usd": float((res or {}).get("total_cost_usd") or 0),
                           "ts": time.time()})
                return {**meta, "text": txt}
            with ThreadPoolExecutor(max_workers=a.workers + 2) as ex:
                for fut in as_completed([ex.submit(run, t) for t in todo]):
                    rows.append(fut.result()); done += 1
                    if done % 20 == 0:
                        print(f"[e08:{m}] {done}/{len(todo)} {time.time()-t0:.0f}s",
                              file=sys.stderr, flush=True)
        finally:
            p.close()
    for r in rows:
        g = R.search(r["text"] or "")
        r["rating"] = int(g.group(1)) if g else None
    (ROOT/"data"/"processed"/"e08_rows.json").write_text(json.dumps(rows, ensure_ascii=False))
    print(f"rows={len(rows)} parsed={sum(1 for x in rows if x['rating'] is not None)}",
          file=sys.stderr)

if __name__ == "__main__":
    main()
