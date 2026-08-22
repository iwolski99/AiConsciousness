"""Small statistics helpers: cluster bootstrap CIs and paired tests."""
from __future__ import annotations
import random, math
from collections import defaultdict


def cluster_bootstrap(values_by_cluster: dict, stat=lambda xs: sum(xs)/len(xs),
                      n: int = 4000, seed: int = 0, alpha: float = 0.05):
    """Bootstrap over clusters (e.g. items), not observations."""
    keys = [k for k, v in values_by_cluster.items() if v]
    if not keys:
        return (float("nan"),) * 3
    rng = random.Random(seed)
    flat = [x for k in keys for x in values_by_cluster[k]]
    point = stat(flat)
    draws = []
    for _ in range(n):
        samp = []
        for _ in range(len(keys)):
            samp.extend(values_by_cluster[keys[rng.randrange(len(keys))]])
        if samp:
            draws.append(stat(samp))
    draws.sort()
    lo = draws[int(alpha / 2 * len(draws))]
    hi = draws[int((1 - alpha / 2) * len(draws)) - 1]
    return point, lo, hi


def paired_bootstrap_diff(a_by_cluster: dict, b_by_cluster: dict,
                          n: int = 4000, seed: int = 0, alpha: float = 0.05):
    """Bootstrap the difference mean(a) - mean(b), resampling clusters jointly."""
    keys = sorted(set(a_by_cluster) & set(b_by_cluster))
    keys = [k for k in keys if a_by_cluster[k] and b_by_cluster[k]]
    if not keys:
        return (float("nan"),) * 4
    rng = random.Random(seed)

    def m(d, ks):
        xs = [x for k in ks for x in d[k]]
        return sum(xs) / len(xs) if xs else float("nan")

    point = m(a_by_cluster, keys) - m(b_by_cluster, keys)
    draws = []
    for _ in range(n):
        ks = [keys[rng.randrange(len(keys))] for _ in range(len(keys))]
        draws.append(m(a_by_cluster, ks) - m(b_by_cluster, ks))
    draws.sort()
    lo = draws[int(alpha / 2 * len(draws))]
    hi = draws[int((1 - alpha / 2) * len(draws)) - 1]
    # two-sided bootstrap p-value against 0
    p = 2 * min(sum(1 for d in draws if d <= 0), sum(1 for d in draws if d >= 0)) / len(draws)
    return point, lo, hi, min(p, 1.0)


def spearman(xs, ys):
    n = len(xs)
    if n < 3:
        return float("nan")
    def rank(v):
        order = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(order):
            j = i
            while j + 1 < len(order) and v[order[j + 1]] == v[order[i]]:
                j += 1
            avg = (i + j) / 2 + 1
            for k in range(i, j + 1):
                r[order[k]] = avg
            i = j + 1
        return r
    rx, ry = rank(list(xs)), rank(list(ys))
    mx, my = sum(rx)/n, sum(ry)/n
    num = sum((a-mx)*(b-my) for a, b in zip(rx, ry))
    den = math.sqrt(sum((a-mx)**2 for a in rx) * sum((b-my)**2 for b in ry))
    return num/den if den else float("nan")


def auroc(labels, scores):
    """labels: 1/0. Returns AUROC with ties handled by mid-rank."""
    pairs = sorted(zip(scores, labels))
    n1 = sum(labels); n0 = len(labels) - n1
    if n1 == 0 or n0 == 0:
        return float("nan")
    ranks = {}
    i = 0
    r = 1
    arr = [p[0] for p in pairs]
    while i < len(arr):
        j = i
        while j + 1 < len(arr) and arr[j+1] == arr[i]:
            j += 1
        avg = (r + (r + (j - i))) / 2
        for k in range(i, j + 1):
            ranks[k] = avg
        r += (j - i + 1)
        i = j + 1
    s1 = sum(ranks[k] for k, (_, lab) in enumerate(pairs) if lab == 1)
    return (s1 - n1 * (n1 + 1) / 2) / (n1 * n0)
