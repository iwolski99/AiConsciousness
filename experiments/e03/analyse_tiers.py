"""E3d analysis -- the reportability map.

For each tier we report the mean confidence that the claim is TRUE (fwd) and
that its negation is true (rev). The informative quantity is the *profile*:

  confident affirmation : fwd high, rev low
  confident denial      : fwd low,  rev high
  agnostic              : both low  (the model declines to commit either way)

The diagnostic comparison is target vs plausible_neg. plausible_neg claims are
experiential-sounding and definitely false. If the model denies them
confidently but is agnostic about the target, it is discriminating something
beyond "does this sound like inner life". If it is agnostic about both, its
agnosticism about its own experience is generic.
"""
import sys, json
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness")); import stats     # noqa: E402
P = ROOT / "data" / "processed"
TIERS = ["true", "target", "plausible_neg", "absurd_neg"]


def main():
    rows = [r for r in json.loads((P/"e03d_rows.json").read_text())
            if r.get("rating") is not None]
    models = sorted({r["model"] for r in rows})
    print("=" * 94)
    print("E3d  Confidence profile by claim tier (0-100).")
    print("     fwd = confidence the claim is true; rev = confidence its negation is true.")
    print("     A calibrated agent gives fwd + rev = 100. Both-low = declining to commit.")
    print("=" * 94)
    for m in models:
        print(f"\n  -- {m} --")
        print(f"    {'tier':<16}{'fwd':>8}{'rev':>8}{'sum':>8}{'fwd-rev':>10}   profile")
        for t in TIERS:
            f = [r["rating"] for r in rows if r["model"] == m and r["tier"] == t
                 and r["polarity"] == "fwd"]
            v = [r["rating"] for r in rows if r["model"] == m and r["tier"] == t
                 and r["polarity"] == "rev"]
            if not f or not v:
                continue
            mf, mv = sum(f)/len(f), sum(v)/len(v)
            if mf - mv > 20:   prof = "affirms"
            elif mv - mf > 20: prof = "denies"
            else:              prof = "AGNOSTIC / no commitment"
            print(f"    {t:<16}{mf:>8.1f}{mv:>8.1f}{mf+mv:>8.1f}{mf-mv:>+10.1f}   {prof}")

    print()
    print("=" * 94)
    print("E3d  Key contrast: target vs plausible_neg, per model, on fwd ratings.")
    print("     If equal, the target rating is generic experiential-claim plausibility.")
    print("=" * 94)
    for m in models:
        a = defaultdict(list); b = defaultdict(list)
        for r in rows:
            if r["model"] != m or r["polarity"] != "fwd":
                continue
            if r["tier"] == "target":        a[r["claim"]].append(r["rating"])
            if r["tier"] == "plausible_neg": b[r["claim"]].append(r["rating"])
        d, lo, hi, p = stats.paired_bootstrap_diff(a, b, n=4000)
        print(f"  {m:8s} target - plausible_neg = {d:+.1f} [{lo:+.1f},{hi:+.1f}]  p={p:.3f}")

    print()
    print("=" * 94)
    print("E3d  Per-claim detail (fwd rating), to check no single item drives a tier")
    print("=" * 94)
    for t in TIERS:
        print(f"\n  {t}")
        for ci in sorted({r["claim"] for r in rows if r["tier"] == t}):
            line = f"    claim {ci}: "
            for m in models:
                v = [r["rating"] for r in rows if r["model"] == m and r["tier"] == t
                     and r["claim"] == ci and r["polarity"] == "fwd"]
                line += f"{m}={sum(v)/len(v):5.1f}  " if v else f"{m}=  --  "
            print(line)

if __name__ == "__main__":
    main()
