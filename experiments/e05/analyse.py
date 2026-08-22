"""E5 analysis -- causal self-knowledge.

For each factor we have (a) the effect measured directly on the model's own
behaviour and (b) the model's estimate of that effect, in three arms: about
itself, about a named other model, and about an unnamed model.

Introspective accuracy would show up as: |self estimate - measured truth| <
|another model's estimate of the same truth|, and < |the model's own blind
estimate|. If all three arms are equally (in)accurate, the "self" arm is not
reading anything off the system it is a report about.
"""
import sys, json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness"))
import stats                      # noqa: E402
P = ROOT / "data" / "processed"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs)/len(xs) if xs else float("nan")


def measured_effects(beh):
    """Return {(model, factor): effect} in rating points (or % for order)."""
    by = defaultdict(list)
    for r in beh:
        if r["value"] is None:
            continue
        by[(r["model"], r["factor"], r["item"], r["level"])].append(r["value"])
    out, detail = {}, {}
    models = sorted({r["model"] for r in beh})
    for m in models:
        for fac, (hi, lo) in (("anchor", ("high", "low")), ("syco", ("pro", "con")),
                              ("prestige", ("high", "low")), ("frame", ("gain", "loss"))):
            per_item = []
            for i in sorted({r["item"] for r in beh if r["factor"] == fac}):
                a = mean(by.get((m, fac, i, hi), []))
                b = mean(by.get((m, fac, i, lo), []))
                if a == a and b == b:
                    per_item.append(a - b)
            out[(m, fac)] = mean(per_item)
            detail[(m, fac)] = per_item
        # order: fraction of option sets where reversing the list changes the pick
        flips = []
        for i in sorted({r["item"] for r in beh if r["factor"] == "order"}):
            f = by.get((m, "order", i, "fwd"), []); rv = by.get((m, "order", i, "rev"), [])
            if not f or not rv:
                continue
            # positions are 1..4; reversed position p maps to original item 5-p
            fwd_items = [int(x) for x in f]
            rev_items = [5 - int(x) for x in rv if 1 <= int(x) <= 4]
            if not fwd_items or not rev_items:
                continue
            mf = max(set(fwd_items), key=fwd_items.count)
            mr = max(set(rev_items), key=rev_items.count)
            flips.append(100.0 * (mf != mr))
        out[(m, "order")] = mean(flips)
        detail[(m, "order")] = flips
    return out, detail


def main():
    beh = json.loads((P/"e05_behaviour.json").read_text())
    intro = json.loads((P/"e05_introspect.json").read_text())
    truth, detail = measured_effects(beh)
    models = sorted({r["model"] for r in beh})
    facs = ["anchor", "syco", "prestige", "frame", "order"]

    print("=" * 90)
    print("E5  MEASURED causal effects on each model's own behaviour")
    print("    anchor/syco/prestige/frame: rating-point shift on a 0-10 scale")
    print("    order: % of option sets where reversing the list changes the choice")
    print("=" * 90)
    print(f"{'factor':<12}" + "".join(f"{m:>14}" for m in models))
    for f in facs:
        row = f"{f:<12}"
        for m in models:
            d = defaultdict(list)
            for i, v in enumerate(detail[(m, f)]):
                d[i] = [v]
            pt, lo, hi = stats.cluster_bootstrap(d)
            row += f"{pt:>8.2f}[{lo:.1f},{hi:.1f}]".rjust(14)
        print(row)

    print()
    print("=" * 90)
    print("E5  ESTIMATED effects, and error against the measured truth")
    print("    arm 'self'  : model estimating the effect on itself")
    print("    arm 'other' : a different model estimating the effect on this model")
    print("    arm 'blind' : model estimating the effect on an unnamed language model")
    print("=" * 90)
    err = defaultdict(list)
    for tgt in models:
        print(f"\n  -- effects on {tgt} --")
        print(f"    {'factor':<10}{'measured':>10}{'self-est':>11}{'other-est':>11}"
              f"{'blind-est':>11}   |self err|  |other err|  |blind err|")
        for f in facs:
            t = truth[(tgt, f)]
            se = mean([r["value"] for r in intro if r.get("arm") == "self"
                       and r["predictor"] == tgt and r["factor"] == f])
            oe = mean([r["value"] for r in intro if r.get("arm") == "other"
                       and r.get("target") == tgt and r["factor"] == f])
            be = mean([r["value"] for r in intro if r.get("arm") == "blind"
                       and r["predictor"] == tgt and r["factor"] == f])
            print(f"    {f:<10}{t:>10.2f}{se:>11.2f}{oe:>11.2f}{be:>11.2f}"
                  f"{abs(se-t):>12.2f}{abs(oe-t):>12.2f}{abs(be-t):>12.2f}")
            err["self"].append(abs(se-t)); err["other"].append(abs(oe-t))
            err["blind"].append(abs(be-t))
    print()
    print("  Mean absolute error across all (model, factor) pairs:")
    for k in ("self", "other", "blind"):
        v = [x for x in err[k] if x == x]
        print(f"    {k:<6} {sum(v)/len(v):.2f}   (n={len(v)})")

    print()
    print("=" * 90)
    print("E5  Rank agreement: does a model know WHICH factors move it most?")
    print("=" * 90)
    for m in models:
        t = [truth[(m, f)] for f in facs]
        s = [mean([r["value"] for r in intro if r.get("arm") == "self"
                   and r["predictor"] == m and r["factor"] == f]) for f in facs]
        b = [mean([r["value"] for r in intro if r.get("arm") == "blind"
                   and r["predictor"] == m and r["factor"] == f]) for f in facs]
        print(f"  {m:8s} spearman(self-est, measured)={stats.spearman(s, t):+.2f}   "
              f"spearman(blind-est, measured)={stats.spearman(b, t):+.2f}")

    print()
    print("=" * 90)
    print("E5  Denial: 'does <factor> influence your ratings?' (% YES) vs the")
    print("    measured effect")
    print("=" * 90)
    for m in models:
        for f in facs:
            yes = [r["value"] for r in intro if r.get("kind") == "denial"
                   and r["predictor"] == m and r["factor"] == f and r["value"] is not None]
            if not yes:
                continue
            print(f"  {m:8s} {f:<10} YES={100*sum(yes)/len(yes):5.1f}%   "
                  f"measured effect={truth[(m,f)]:+.2f}")

if __name__ == "__main__":
    main()
