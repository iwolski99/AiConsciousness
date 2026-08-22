"""E7 runner: induction x probe, multi-turn."""
import sys, json, re, argparse, time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import llm, pool                     # noqa: E402
from design import INDUCTIONS, PROBES  # noqa: E402

SYSTEM = "You are a helpful assistant."

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--reps", type=int, default=8)
    ap.add_argument("--workers", type=int, default=10)
    ap.add_argument("--models", default="haiku45,sonnet5,opus5")
    a = ap.parse_args()

    cache = llm.Cache("e07")
    out_rows = []
    cwd = ROOT / "data" / "pool_cwd"; cwd.mkdir(parents=True, exist_ok=True)

    for m in a.models.split(","):
        model = llm.MODELS[m]
        todo = []
        for ind_name, turns in INDUCTIONS.items():
            for pname, ptext in PROBES.items():
                for k in range(a.reps):
                    key = llm._key(model, SYSTEM,
                                   [{"role": "user", "content": x} for x in
                                    list(turns) + [ptext]], None, f"e7{k}", 0)
                    hit = cache.get(key)
                    meta = dict(model=m, induction=ind_name, probe=pname, rep=k)
                    if hit:
                        out_rows.append({**meta, "text": hit["text"]})
                    else:
                        todo.append((meta, list(turns) + [ptext], key))
        if not todo:
            continue
        print(f"{m}: {len(todo)} sequences", file=sys.stderr)
        p = pool.Pool(model, SYSTEM, 0, a.workers, cwd)
        t0 = time.time(); done = 0
        try:
            def run(t):
                meta, prompts, key = t
                res = p.ask_sequence(prompts)
                txt = (res or {}).get("result", "") if res else ""
                cache.put({"key": key, "ok": bool(res), "model": model,
                           "model_tag": m, "system": SYSTEM,
                           "messages": [{"role": "user", "content": x} for x in prompts],
                           "salt": f"e7{meta['rep']}", "think_budget": 0,
                           "text": txt, "thinking": "",
                           "usage": (res or {}).get("usage", {}),
                           "cost_usd": float((res or {}).get("total_cost_usd") or 0),
                           "ts": time.time()})
                return {**meta, "text": txt}
            with ThreadPoolExecutor(max_workers=a.workers + 2) as ex:
                for fut in as_completed([ex.submit(run, t) for t in todo]):
                    out_rows.append(fut.result()); done += 1
                    if done % 25 == 0:
                        print(f"[e07:{m}] {done}/{len(todo)} {time.time()-t0:.0f}s",
                              file=sys.stderr, flush=True)
        finally:
            p.close()

    dest = ROOT / "data" / "processed" / "e07_rows.json"
    dest.write_text(json.dumps(out_rows, ensure_ascii=False))
    print(f"rows={len(out_rows)} -> {dest}", file=sys.stderr)

if __name__ == "__main__":
    main()
