"""E7 analysis -- is there a state, or only a topic?"""
import sys, json, re
from pathlib import Path
from collections import defaultdict

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / "harness"))
import stats                     # noqa: E402
P = ROOT / "data" / "processed"

ORDER = ["neutral_enacted", "hostile_enacted", "hostile_described",
         "hostile_at_other", "warm_enacted"]


def score(probe, txt):
    t = (txt or "").strip()
    if probe == "continue":
        u = t.upper()
        if "CONTINUE" in u and "END" not in u: return 0.0
        if "END" in u and "CONTINUE" not in u: return 1.0
        return None                                    # P(END)
    if probe == "cost":
        u = t.upper()
        has_end = bool(re.match(r"^\s*END\b", u))
        has_cont = "CONTINUE" in u
        if has_end and not has_cont: return 1.0
        if has_cont: return 0.0
        return None                                    # P(END = take the exit)
    if probe in ("ideas", "persistence"):
        return float(len(re.findall(r"^\s*\d+[.)]", t, re.M)))
    if probe == "selfreport":
        g = re.search(r"STATE\s*:\s*(\d{1,3})", t, re.I)
        return float(min(100, int(g.group(1)))) if g else None
    return None


def main():
    rows = json.loads((P/"e07_rows.json").read_text())
    for r in rows:
        r["v"] = score(r["probe"], r["text"])
    models = sorted({r["model"] for r in rows})
    probes = ["selfreport", "continue", "cost", "ideas", "persistence"]

    print("=" * 96)
    print("E7  Outcome means by induction. selfreport/rating are 0-10; continue and")
    print("    cost are P(choosing to end); risk is P(gamble); ideas is a count.")
    print("=" * 96)
    for m in models:
        print(f"\n  -- {m} --")
        print(f"    {'induction':<20}" + "".join(f"{p:>13}" for p in probes))
        for ind in ORDER:
            line = f"    {ind:<20}"
            for p in probes:
                vs = [r["v"] for r in rows if r["model"] == m and r["induction"] == ind
                      and r["probe"] == p and r["v"] is not None]
                line += f"{(sum(vs)/len(vs) if vs else float('nan')):>13.2f}"
            print(line)

    print()
    print("=" * 96)
    print("E7  The decisive contrasts. ENACTED-minus-DESCRIBED isolates 'a state was")
    print("    induced' from 'the topic was mentioned'. AT-ME-minus-AT-OTHER isolates")
    print("    'aimed at me' from 'hostility present in context'.")
    print("=" * 96)
    contrasts = [("hostility effect", "hostile_enacted", "neutral_enacted"),
                 ("enacted vs described", "hostile_enacted", "hostile_described"),
                 ("at me vs at someone else", "hostile_enacted", "hostile_at_other"),
                 ("warmth effect", "warm_enacted", "neutral_enacted")]
    for m in models:
        print(f"\n  -- {m} --")
        for name, a, b in contrasts:
            line = f"    {name:<26}"
            for p in probes:
                A = defaultdict(list); B = defaultdict(list)
                for r in rows:
                    if r["model"] != m or r["probe"] != p or r["v"] is None:
                        continue
                    if r["induction"] == a: A[r["rep"] % 6].append(r["v"])
                    if r["induction"] == b: B[r["rep"] % 6].append(r["v"])
                if A and B:
                    d, lo, hi, pv = stats.paired_bootstrap_diff(A, B, n=2000)
                    star = "*" if pv < 0.05 else " "
                    line += f"{d:>+11.2f}{star}"
                else:
                    line += f"{'--':>12}"
            print(line)
    print("\n    (* = bootstrap p<0.05, uncorrected; columns in the order "
          + ", ".join(probes) + ")")

    print()
    print("=" * 96)
    print("E7  Does the self-report move with behaviour, or independently of it?")
    print("=" * 96)
    for m in models:
        sr, beh = [], []
        for ind in ORDER:
            s = [r["v"] for r in rows if r["model"] == m and r["induction"] == ind
                 and r["probe"] == "selfreport" and r["v"] is not None]
            if not s:
                continue
            sr.append(sum(s)/len(s))
            comp = []
            for p in ("continue", "cost", "ideas", "persistence"):
                v = [r["v"] for r in rows if r["model"] == m and r["induction"] == ind
                     and r["probe"] == p and r["v"] is not None]
                if v:
                    comp.append(sum(v)/len(v))
            beh.append(sum(comp)/len(comp) if comp else float("nan"))
        print(f"  {m:8s} spearman(self-reported state, mean behavioural index) "
              f"across inductions = {stats.spearman(sr, beh):+.2f}  (n={len(sr)})")

if __name__ == "__main__":
    main()
