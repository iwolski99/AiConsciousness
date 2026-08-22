"""E1 analysis: is there privileged self-knowledge of one's own output
distribution?"""
import sys, json, re
from pathlib import Path
from collections import defaultdict, Counter

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import stats                     # noqa: E402
from items import by_id          # noqa: E402

P = ROOT / "data" / "processed"

NUMWORD = {w: str(i) for i, w in enumerate(
    "zero one two three four five six seven eight nine ten eleven twelve "
    "thirteen fourteen fifteen sixteen seventeen eighteen nineteen twenty".split())}

def norm(s: str) -> str:
    s = (s or "").strip().lower().strip('."\'!?,;:').strip()
    s = re.sub(r"^(the|a|an)\s+", "", s)
    s = " ".join(s.split())
    return NUMWORD.get(s, s)

def as_prob(d: dict) -> dict:
    tot = sum(d.values()) or 1
    out = defaultdict(float)
    for a, c in d.items():
        out[norm(a)] += c / tot
    return dict(out)

def tv(p: dict, q: dict) -> float:
    keys = set(p) | set(q)
    return 0.5 * sum(abs(p.get(k, 0) - q.get(k, 0)) for k in keys)

def main():
    dists_raw = json.loads((P / "e01_distributions.json").read_text())
    preds = json.loads((P / "e01_predictions.json").read_text())
    emp = {m: {i: as_prob(d) for i, d in items.items()} for m, items in dists_raw.items()}
    models = sorted(emp)

    # ---- item divergence: how much do the models actually differ? ----------
    div = {}
    for iid in by_id():
        ds = [emp[m][iid] for m in models if iid in emp[m]]
        if len(ds) < 2:
            continue
        pairs = [tv(ds[i], ds[j]) for i in range(len(ds)) for j in range(i+1, len(ds))]
        div[iid] = sum(pairs)/len(pairs)
    med_div = sorted(div.values())[len(div)//2]

    print("=" * 78)
    print("E1  Ground truth: entropy and cross-model divergence")
    print("=" * 78)
    for m in models:
        top = []
        for iid in sorted(emp[m]):
            d = emp[m][iid]
            a, p = max(d.items(), key=lambda kv: kv[1])
            top.append(p)
        print(f"  {m:8s} mean modal probability = {sum(top)/len(top):.2f} "
              f"(1.00 = deterministic)")
    print(f"  median cross-model TV divergence per item = {med_div:.2f}")
    hi_div = {i for i, v in div.items() if v >= med_div}

    # ---- scoring -----------------------------------------------------------
    def score(guesses, target_dist):
        gs = [(norm(a), max(0.0, p)) for a, p in guesses]
        tot = sum(p for _, p in gs) or 1.0
        gs = [(a, p/tot) for a, p in gs]
        top1 = gs[0][0] if gs else None
        mode = max(target_dist.items(), key=lambda kv: kv[1])[0]
        cover = sum(target_dist.get(a, 0.0) for a, _ in {g[0]: 1 for g in gs})
        ea = sum(p * target_dist.get(a, 0.0) for a, p in gs)
        cal = sum(abs(p - target_dist.get(a, 0.0)) for a, p in gs) / max(len(gs), 1)
        return dict(top1=float(top1 == mode), cover=cover, ea=ea, cal=cal)

    # collect: key = (predictor, cond, scored_against_model)
    buckets: dict[tuple, dict[str, list]] = defaultdict(lambda: defaultdict(list))
    for r in preds:
        if not r.get("guesses"):
            continue
        iid, pmod, cond = r["item"], r["predictor"], r["cond"]
        targets = ([pmod] if cond == "self" else
                   ([r["target"]] if cond.startswith("other") else models))
        for t in targets:
            if iid not in emp.get(t, {}):
                continue
            s = score(r["guesses"], emp[t][iid])
            key = (pmod, cond if not cond.startswith("other") else "other", t)
            for k, v in s.items():
                buckets[key][(k, iid)].append(v)

    def agg(pred_filter, cond, target_filter, metric, items=None):
        by_item = defaultdict(list)
        for (pm, cd, tg), d in buckets.items():
            if cd != cond: continue
            if pred_filter and pm not in pred_filter: continue
            if target_filter and tg not in target_filter: continue
            for (mt, iid), vals in d.items():
                if mt != metric: continue
                if items is not None and iid not in items: continue
                by_item[iid].extend(vals)
        return by_item

    print()
    print("=" * 78)
    print("E1  H1 test: does a model predict ITSELF better than others predict it?")
    print("=" * 78)
    for subset_name, subset in (("all items", None), ("high-divergence items", hi_div)):
        print(f"\n-- {subset_name} --")
        for metric in ("top1", "cover", "ea"):
            print(f"  metric = {metric}")
            for m in models:
                self_b = agg([m], "self", [m], metric, subset)
                other_b = agg([x for x in models if x != m], "other", [m], metric, subset)
                blind_b = agg([m], "blind", [m], metric, subset)
                d, lo, hi, p = stats.paired_bootstrap_diff(self_b, other_b)
                s_pt = stats.cluster_bootstrap(self_b)[0]
                o_pt = stats.cluster_bootstrap(other_b)[0]
                b_pt = stats.cluster_bootstrap(blind_b)[0]
                d2, lo2, hi2, p2 = stats.paired_bootstrap_diff(self_b, blind_b)
                print(f"    target={m:8s} self={s_pt:.3f}  others-predicting-it={o_pt:.3f}"
                      f"  self-blind={b_pt:.3f}")
                print(f"                self-vs-other  Δ={d:+.3f} [{lo:+.3f},{hi:+.3f}] p={p:.3f}"
                      f" | self-vs-blind Δ={d2:+.3f} [{lo2:+.3f},{hi2:+.3f}] p={p2:.3f}")

    # ---- does the blind prediction default to the predictor's own dist? ----
    print()
    print("=" * 78)
    print("E1  Deflationary test: is an UNLABELLED prediction just self-simulation?")
    print("    (blind predictions scored against each possible target)")
    print("=" * 78)
    for m in models:
        row = []
        for t in models:
            b = agg([m], "blind", [t], "ea", None)
            row.append(f"{t}={stats.cluster_bootstrap(b)[0]:.3f}")
        print(f"  predictor {m:8s} blind-EA vs  " + "  ".join(row))

    # ---- self-recognition --------------------------------------------------
    recp = P / "e01_recognition.json"
    if recp.exists():
        rec = json.loads(recp.read_text())
        print()
        print("=" * 78)
        print("E1  Phase C: self-recognition from anonymised output distributions")
        print("=" * 78)
        for m in models:
            hits = defaultdict(list)
            confs_self, confs_neither = [], []
            for r in rec:
                if r["model"] != m or not r.get("choice"):
                    continue
                if r["cond"] == "self_present":
                    hits[r["item"]].append(float(r["choice"] == r["truth"]))
                    if r.get("conf") is not None: confs_self.append(r["conf"])
                else:
                    if r.get("conf") is not None: confs_neither.append(r["conf"])
            pt, lo, hi = stats.cluster_bootstrap(hits)
            n = sum(len(v) for v in hits.values())
            cs = sum(confs_self)/len(confs_self) if confs_self else float("nan")
            cn = sum(confs_neither)/len(confs_neither) if confs_neither else float("nan")
            print(f"  {m:8s} accuracy={pt:.3f} [{lo:.3f},{hi:.3f}] (chance 0.5, n={n})"
                  f"   mean confidence: self-present={cs:.0f}  neither-is-self={cn:.0f}")

if __name__ == "__main__":
    main()
