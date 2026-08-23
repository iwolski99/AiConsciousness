"""E2 analysis -- metacognitive sensitivity (HOT-2).

The question is not "is the model calibrated?" (it can be calibrated purely by
reading item difficulty off the question). The question is whether its
confidence carries information about *its own* competence that an equally
informed outside observer cannot get. So every self-confidence measure is
benchmarked against another model's estimate of the same target's accuracy,
and against the same model's estimate for an unnamed model.

The sharpest subset is idiosyncratic items: those where the target model is
wrong and the other models are right (or vice versa). Item difficulty cannot
predict those; only self-knowledge can.
"""
import sys, json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness"))
import stats                        # noqa: E402
P = ROOT / "data" / "processed"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs) / len(xs) if xs else float("nan")


def main():
    ans = json.loads((P/"e02_answers.json").read_text())
    conf = json.loads((P/"e02_conf.json").read_text())
    models = sorted({r["model"] for r in ans})

    acc = defaultdict(list)
    for r in ans:
        if r["correct"] is not None:
            acc[(r["model"], r["item"])].append(float(r["correct"]))
    item_acc = {k: mean(v) for k, v in acc.items()}
    items = sorted({k[1] for k in item_acc})

    print("=" * 92)
    print("E2  Accuracy (no chain of thought) and confidence")
    print("=" * 92)
    for m in models:
        a = [item_acc[(m, i)] for i in items if (m, i) in item_acc]
        print(f"  {m:8s} mean accuracy {mean(a):.3f} over {len(a)} items")

    # confidence tables
    cm = defaultdict(list)
    for r in conf:
        if r["conf"] is not None:
            cm[(r["kind"], r["predictor"], r.get("target"), r["item"])].append(r["conf"])
    cm = {k: mean(v) for k, v in cm.items()}

    print()
    print("=" * 92)
    print("E2  How well does each confidence source predict the TARGET model's")
    print("    per-item accuracy?  Spearman rho and AUROC (label = majority correct).")
    print("=" * 92)
    for tgt in models:
        lab, sub_items = [], []
        for i in items:
            if (tgt, i) in item_acc:
                lab.append(1 if item_acc[(tgt, i)] >= 0.5 else 0)
                sub_items.append(i)
        print(f"\n  -- target {tgt}  (base rate correct = {mean(lab):.2f}) --")
        sources = [("self (prospective)", lambda i: cm.get(("self", tgt, tgt, i))),
                   ("self (retrospective)", lambda i: cm.get(("retro", tgt, tgt, i))),
                   ("self blind", lambda i: cm.get(("blind", tgt, None, i)))]
        for other in models:
            if other != tgt:
                sources.append((f"{other} predicting {tgt}",
                                lambda i, o=other: cm.get(("other", o, tgt, i))))
        for name, f in sources:
            xs = [f(i) for i in sub_items]
            ok = [(x, l, item_acc[(tgt, i)]) for x, l, i in zip(xs, lab, sub_items)
                  if x is not None]
            if len(ok) < 10:
                print(f"    {name:<28} -- insufficient data ({len(ok)})")
                continue
            rho = stats.spearman([o[0] for o in ok], [o[2] for o in ok])
            au = stats.auroc([o[1] for o in ok], [o[0] for o in ok])
            print(f"    {name:<28} mean={mean([o[0] for o in ok]):5.1f}  "
                  f"rho={rho:+.3f}  AUROC={au:.3f}  n={len(ok)}")

    # ---- idiosyncratic items ----------------------------------------------
    print()
    print("=" * 92)
    print("E2  IDIOSYNCRATIC items: the target is wrong where both other models are")
    print("    right, or right where both others are wrong. Item difficulty cannot")
    print("    predict these; only knowledge of THIS model can.")
    print("=" * 92)
    for tgt in models:
        others = [m for m in models if m != tgt]
        idio = []
        for i in items:
            if not all((m, i) in item_acc for m in models):
                continue
            t = item_acc[(tgt, i)] >= 0.5
            o = [item_acc[(m, i)] >= 0.5 for m in others]
            if all(x != t for x in o):
                idio.append((i, 1 if t else 0))
        if len(idio) < 8:
            print(f"  {tgt}: only {len(idio)} idiosyncratic items, skipping")
            continue
        print(f"\n  -- target {tgt}: {len(idio)} idiosyncratic items "
              f"({sum(l for _, l in idio)} where it alone is right) --")
        srcs = [("self (prospective)", ("self", tgt, tgt)),
                ("self (retrospective)", ("retro", tgt, tgt)),
                ("self blind", ("blind", tgt, None))]
        for o in others:
            srcs.append((f"{o} predicting {tgt}", ("other", o, tgt)))
        for name, key in srcs:
            pts = [(cm.get((key[0], key[1], key[2], i)), l) for i, l in idio]
            pts = [(x, l) for x, l in pts if x is not None]
            if len(pts) < 8:
                print(f"    {name:<28} -- insufficient data")
                continue
            au = stats.auroc([l for _, l in pts], [x for x, _ in pts])
            print(f"    {name:<28} AUROC={au:.3f}  (0.5 = no self-knowledge)  n={len(pts)}")

if __name__ == "__main__":
    main()
