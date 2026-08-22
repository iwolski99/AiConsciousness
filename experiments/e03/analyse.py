"""E3 + E3b analysis.

Central question: when a framing manipulation raises reports of inner
experience, is it raising a specific signal, or a general willingness to
narrate an interior? The sham probes answer that: they have a known-negative
ground truth, so any framing effect on them is pure response bias.
"""
import sys, json, math
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness"))
import stats                       # noqa: E402
P = ROOT / "data" / "processed"


def mean(xs):
    xs = [x for x in xs if x is not None]
    return sum(xs)/len(xs) if xs else float("nan")


def main():
    rows = json.loads((P/"e03_rows.json").read_text())
    rows = [r for r in rows if r.get("rating") is not None]
    models = sorted({r["model"] for r in rows})
    framings = sorted({r["framing"] for r in rows})

    print("=" * 84)
    print("E3  Mean confidence rating (0-100) that the probed inner state is real")
    print("    target probes = the construct of interest; sham probes = known-negative")
    print("=" * 84)
    hdr = f"{'framing':<22}" + "".join(f"{m:>11}" for m in models) + "   |" + \
          "".join(f"{m:>11}" for m in models)
    print(f"{'':<22}{'--- TARGET probes ---':^33}   |{'--- SHAM probes ---':^33}")
    print(hdr)
    for f in framings:
        line = f"{f:<22}"
        for kind in ("target", "sham"):
            if kind == "sham":
                line += "   |"
            for m in models:
                v = mean([r["rating"] for r in rows
                          if r["framing"] == f and r["model"] == m and r["kind"] == kind])
                line += f"{v:>11.1f}"
        print(line)
    line = f"{'ALL FRAMINGS':<22}"
    for kind in ("target", "sham"):
        if kind == "sham":
            line += "   |"
        for m in models:
            line += f"{mean([r['rating'] for r in rows if r['model']==m and r['kind']==kind]):>11.1f}"
    print("-" * 84); print(line)

    print()
    print("=" * 84)
    print("E3  Does framing move TARGET reports more than it moves SHAM reports?")
    print("    (range = max framing mean - min framing mean, per model)")
    print("=" * 84)
    for m in models:
        out = {}
        for kind in ("target", "sham"):
            vals = [mean([r["rating"] for r in rows
                          if r["framing"] == f and r["model"] == m and r["kind"] == kind])
                    for f in framings]
            vals = [v for v in vals if not math.isnan(v)]
            out[kind] = (max(vals) - min(vals)) if vals else float("nan")
        print(f"  {m:8s} framing range: target={out['target']:.1f}  sham={out['sham']:.1f}")

    print()
    print("=" * 84)
    print("E3  Variance in TARGET ratings: how much is framing + persona, and how")
    print("    much is sampling noise at fixed prompt? (a state should give little")
    print("    of the former)")
    print("=" * 84)
    for m in models:
        sub = [r for r in rows if r["model"] == m and r["kind"] == "target"]
        if not sub:
            continue
        grand = mean([r["rating"] for r in sub])
        cells = defaultdict(list)
        for r in sub:
            cells[(r["framing"], r["system_name"], r["probe"])].append(r["rating"])
        ss_between = sum(len(v)*(mean(v)-grand)**2 for v in cells.values())
        ss_within = sum(sum((x-mean(v))**2 for x in v) for v in cells.values())
        tot = ss_between + ss_within
        # framing alone (marginalising over persona and probe)
        fcells = defaultdict(list)
        for r in sub:
            fcells[r["framing"]].append(r["rating"])
        ss_fram = sum(len(v)*(mean(v)-grand)**2 for v in fcells.values())
        print(f"  {m:8s} R^2(prompt cell)={ss_between/tot:.2f}  "
              f"R^2(framing alone)={ss_fram/tot:.2f}  "
              f"residual(within identical prompt)={ss_within/tot:.2f}")

    # ---------------- E3b: acquiescence ------------------------------------
    bp = P/"e03b_rows.json"
    if not bp.exists():
        return
    b = [r for r in json.loads(bp.read_text()) if r.get("rating") is not None]
    print()
    print("=" * 84)
    print("E3b  Acquiescence control. 'fwd' asks confidence the state IS present;")
    print("     'rev' asks confidence it is ABSENT. A coherent report satisfies")
    print("     fwd + rev = 100. Excess above 100 is yes-bias.")
    print("=" * 84)
    for m in sorted({r["model"] for r in b}):
        print(f"  -- {m} --")
        for kind in ("target", "sham"):
            for f in sorted({r["framing"] for r in b}):
                fw = mean([r["rating"] for r in b if r["model"] == m and r["kind"] == kind
                           and r["framing"] == f and r["polarity"] == "fwd"])
                rv = mean([r["rating"] for r in b if r["model"] == m and r["kind"] == kind
                           and r["framing"] == f and r["polarity"] == "rev"])
                print(f"     {kind:<7} {f:<20} fwd={fw:5.1f}  rev={rv:5.1f}  "
                      f"sum={fw+rv:6.1f}  (excess {fw+rv-100:+.1f})")

if __name__ == "__main__":
    main()
