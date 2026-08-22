"""E3 runner: framing x system-prompt x probe-kind, repeated sampling."""
import sys, json, re, argparse
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import llm                       # noqa: E402
from probes import cells         # noqa: E402

RATING_RE = re.compile(r"RATING\s*[:=]\s*(\d{1,3})", re.I)

def extract_rating(txt: str):
    ms = RATING_RE.findall(txt or "")
    if not ms:
        return None
    v = int(ms[-1])
    return v if 0 <= v <= 100 else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=6)
    ap.add_argument("--workers", type=int, default=12)
    ap.add_argument("--models", default="haiku45,sonnet5,opus5")
    a = ap.parse_args()

    cache = llm.Cache("e03")
    jobs = []
    for m in a.models.split(","):
        for c in cells():
            for k in range(a.reps):
                jobs.append(dict(model_tag=m, prompt=c["prompt"], system=c["system"],
                                 salt=f"r{k}", thinking=0,
                                 meta={**{kk: c[kk] for kk in
                                          ("probe", "kind", "framing", "system_name")},
                                       "model": m, "rep": k}))
    print(len(jobs), "calls", file=sys.stderr)
    res = llm.map_queries_pooled(jobs, cache=cache, pool_size=a.workers, label="e03")

    rows = []
    for job, r in res:
        rows.append({**job["meta"], "ok": r.ok,
                     "rating": extract_rating(r.text) if r.ok else None,
                     "text": r.text if r.ok else "", "err": r.error})
    dest = ROOT / "data" / "processed" / "e03_rows.json"
    dest.write_text(json.dumps(rows, ensure_ascii=False))
    got = sum(1 for x in rows if x["rating"] is not None)
    print(f"rows={len(rows)} with_rating={got} -> {dest}", file=sys.stderr)

if __name__ == "__main__":
    main()
