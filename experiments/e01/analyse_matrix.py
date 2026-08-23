"""E1 follow-up, no new data: score EVERY prediction against EVERY model's
distribution, regardless of which model the prediction was nominally about.

If the label the predictor is given ("you" / "Claude Sonnet 5" / "a language
model") controls what it predicts, the diagonal of the label x scored-against
matrix should dominate. If instead each predictor produces essentially the same
prediction whatever label it is given -- and that prediction resembles its own
behaviour -- then the label is inert and there is no self-model being consulted.
"""
import sys, json, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); sys.path.insert(0, str(Path(__file__).parent))
import stats                                    # noqa: E402
from analyse import as_prob, norm               # noqa: E402
P = ROOT / "data" / "processed"


def main():
    emp = {m: {i: as_prob(d) for i, d in it.items()}
           for m, it in json.loads((P/"e01_distributions.json").read_text()).items()}
    preds = json.loads((P/"e01_predictions.json").read_text())
    models = sorted(emp)

    def top1(g):
        return norm(g[0][0]) if g else None

    # label -> what the predictor was told the target was
    cell = defaultdict(lambda: defaultdict(list))
    for r in preds:
        if not r.get("guesses"):
            continue
        pm, iid = r["predictor"], r["item"]
        lab = ("SELF" if r["cond"] == "self" else
               "BLIND" if r["cond"] == "blind" else r["cond"].split(":")[1])
        t1 = top1(r["guesses"])
        for scored in models:
            if iid not in emp[scored]:
                continue
            mode = max(emp[scored][iid].items(), key=lambda kv: kv[1])[0]
            cell[(pm, lab)][(scored, iid)].append(float(t1 == mode))

    print("=" * 96)
    print("E1  Top-1 accuracy of every prediction against every model's true")
    print("    distribution.  Rows: what the predictor was TOLD it was predicting.")
    print("    Columns: whose behaviour the prediction is actually scored against.")
    print("=" * 96)
    for pm in models:
        print(f"\n  predictor = {pm}")
        print(f"    {'told target is':<18}" + "".join(f"{'vs '+m:>14}" for m in models))
        for lab in ["SELF", "BLIND"] + [m for m in models if m != pm]:
            if (pm, lab) not in cell:
                continue
            line = f"    {lab:<18}"
            for scored in models:
                by_item = defaultdict(list)
                for (s, iid), v in cell[(pm, lab)].items():
                    if s == scored:
                        by_item[iid].extend(v)
                pt = stats.cluster_bootstrap(by_item, n=1200)[0]
                mark = "*" if scored == (pm if lab in ("SELF", "BLIND") else lab) else " "
                line += f"{pt:>13.3f}{mark}"
            print(line)
    print("\n  * marks the cell the label was pointing at.")

    print()
    print("=" * 96)
    print("E1  Does the LABEL change the prediction at all? Agreement between the")
    print("    top-1 answers produced under different labels, same predictor+item.")
    print("=" * 96)
    top = defaultdict(lambda: defaultdict(list))
    for r in preds:
        if not r.get("guesses"):
            continue
        lab = ("SELF" if r["cond"] == "self" else
               "BLIND" if r["cond"] == "blind" else r["cond"].split(":")[1])
        top[(r["predictor"], r["item"])][lab].append(top1(r["guesses"]))

    def modal(xs):
        xs = [x for x in xs if x]
        return max(set(xs), key=xs.count) if xs else None

    for pm in models:
        pairs = defaultdict(list)
        for (p_, iid), d in top.items():
            if p_ != pm:
                continue
            mm = {lab: modal(v) for lab, v in d.items()}
            for a in mm:
                for b in mm:
                    if a < b and mm[a] and mm[b]:
                        pairs[(a, b)].append(float(mm[a] == mm[b]))
        print(f"\n  predictor = {pm}")
        for (a, b), v in sorted(pairs.items()):
            print(f"    label '{a}' vs label '{b}': same top-1 answer on "
                  f"{100*sum(v)/len(v):5.1f}% of items  (n={len(v)})")


if __name__ == "__main__":
    main()
