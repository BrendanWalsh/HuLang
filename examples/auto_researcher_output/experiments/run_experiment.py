#!/usr/bin/env python3
"""Deterministic bounded comparison of single-tier and two-tier spatial hashes."""
import argparse
import hashlib
import json
import math
import os
import platform
import random
import statistics
import sys
import time
from collections import defaultdict
from pathlib import Path


GRID = (0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 6.0, 8.0, 12.0, 16.0)
DOMAIN = (100.0, 100.0, 100.0)
SEEDS = (11, 23, 37)
N = 320


def percentile(values, q):
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    pos = (len(ordered) - 1) * q
    lo, hi = math.floor(pos), math.ceil(pos)
    if lo == hi:
        return ordered[lo]
    return ordered[lo] + (ordered[hi] - ordered[lo]) * (pos - lo)


def aabb_overlap(a, b):
    return (abs(a[0] - b[0]) * 2 <= a[3] + b[3] and
            abs(a[1] - b[1]) * 2 <= a[4] + b[4] and
            abs(a[2] - b[2]) * 2 <= a[5] + b[5])


def cells_for(obj, cell):
    x, y, z, sx, sy, sz = obj
    # Half-open cell indexing plus an inclusive maximum is the declared boundary rule.
    return ((math.floor((x - sx / 2) / cell), math.floor((y - sy / 2) / cell),
             math.floor((z - sz / 2) / cell)),
            (math.floor((x + sx / 2) / cell), math.floor((y + sy / 2) / cell),
             math.floor((z + sz / 2) / cell)))


def hash_candidates(objects, cell, only=None, query_objects=None):
    buckets = defaultdict(list)
    selected = range(len(objects)) if only is None else only
    for i in selected:
        lo, hi = cells_for(objects[i], cell)
        for x in range(lo[0], hi[0] + 1):
            for y in range(lo[1], hi[1] + 1):
                for z in range(lo[2], hi[2] + 1):
                    buckets[(x, y, z)].append(i)
    pairs = set()
    queries = range(len(objects)) if query_objects is None else query_objects
    for i in queries:
        lo, hi = cells_for(objects[i], cell)
        for x in range(lo[0], hi[0] + 1):
            for y in range(lo[1], hi[1] + 1):
                for z in range(lo[2], hi[2] + 1):
                    for j in buckets.get((x, y, z), ()):
                        if i != j:
                            pairs.add((min(i, j), max(i, j)))
    return pairs, sum(len(v) for v in buckets.values())


def two_tier_candidates(objects):
    diameters = [max(o[3:]) for o in objects]
    small, large = percentile(diameters, 0.5), percentile(diameters, 0.9)
    small_ids = [i for i, d in enumerate(diameters) if d <= small]
    large_ids = [i for i, d in enumerate(diameters) if d > small]
    # Small-small uses the median tier; large-large uses the 90th-percentile tier.
    # Cross-tier pairs query large objects against the small-object hash.
    ss, work_ss = hash_candidates(objects, small, only=small_ids)
    ll, work_ll = hash_candidates(objects, large, only=large_ids)
    cross, work_cross = hash_candidates(objects, small, only=small_ids,
                                        query_objects=large_ids)
    return ss | ll | cross, {
        "median_cell": small, "p90_cell": large, "small_objects": len(small_ids),
        "large_objects": len(large_ids), "cell_visits": work_ss + work_ll + work_cross,
    }


def make_scene(kind, spatial, seed):
    rng = random.Random(seed)
    objects = []
    for _ in range(N):
        if kind == "mono":
            d = 2.0
        elif kind == "loglow":
            d = min(5.0, max(1.0, rng.lognormvariate(math.log(2.0), 0.18)))
        elif kind == "bimodal":
            d = 1.5 if rng.random() < 0.75 else 9.0
        elif kind == "pareto":
            d = min(14.0, 1.2 * (1.0 - rng.random()) ** (-1.0 / 1.6))
        else:
            raise ValueError("unknown distribution: " + kind)
        if spatial == "clustered":
            cx, cy, cz = (rng.gauss(50.0, 13.0) for _ in range(3))
            cx, cy, cz = (min(99.0, max(1.0, v)) for v in (cx, cy, cz))
        else:
            cx, cy, cz = (rng.uniform(1.0, 99.0) for _ in range(3))
        objects.append((cx, cy, cz, d, d, d))
    return objects


def scene_hash(objects):
    return hashlib.sha256(json.dumps(objects, separators=(",", ":")).encode()).hexdigest()


def row(condition, spatial, seed, objects, method, cell=None, permuted=False):
    start = time.perf_counter()
    if method == "two_tier":
        pairs, details = two_tier_candidates(objects)
        label = "median90"
    else:
        pairs, work = hash_candidates(objects, cell)
        details = {"cell_visits": work}
        label = "single:" + str(cell)
    true_pairs = sum(aabb_overlap(objects[i], objects[j]) for i, j in pairs)
    all_true = sum(aabb_overlap(objects[i], objects[j])
                   for i in range(len(objects)) for j in range(i + 1, len(objects)))
    elapsed = time.perf_counter() - start
    return {
        "status": "ok", "condition": condition, "spatial": spatial, "seed": seed,
        "n": len(objects), "domain": DOMAIN, "scene_hash": scene_hash(objects),
        "method": label, "candidate_pairs": len(pairs), "unique_pairs": len(pairs),
        "true_overlaps_among_candidates": true_pairs, "all_true_overlaps": all_true,
        "false_positives": len(pairs) - true_pairs,
        "candidate_true_ratio": (len(pairs) / true_pairs if true_pairs else None),
        "permuted": permuted, "details": details,
        "elapsed_seconds": elapsed,
    }


def run(out):
    out.mkdir(parents=True, exist_ok=False)
    results = out / "results.jsonl"
    failures = out / "failures.jsonl"
    conditions = ("mono", "loglow", "bimodal", "pareto")
    rows = []
    failures.write_text("", encoding="utf-8")
    for condition in conditions:
        for spatial in ("uniform", "clustered"):
            for seed in SEEDS:
                try:
                    objects = make_scene(condition, spatial, seed)
                    for cell in GRID:
                        rows.append(row(condition, spatial, seed, objects, "single", cell))
                    rows.append(row(condition, spatial, seed, objects, "two_tier"))
                    if condition == "bimodal" and spatial == "clustered" and seed == SEEDS[0]:
                        perm = list(range(N))
                        random.Random(991).shuffle(perm)
                        inverse = [0] * N
                        for new, old in enumerate(perm):
                            inverse[old] = new
                        shuffled = [objects[i] for i in perm]
                        rows.append(row(condition, spatial, seed, shuffled, "two_tier",
                                        permuted=True))
                except Exception as exc:
                    failures.open("a", encoding="utf-8").write(
                        json.dumps({"status": "failed", "condition": condition,
                                    "spatial": spatial, "seed": seed,
                                    "error_type": type(exc).__name__,
                                    "error": str(exc)}) + "\n")
    with results.open("w", encoding="utf-8") as handle:
        for item in rows:
            handle.write(json.dumps(item, sort_keys=True) + "\n")
    metadata = {
        "status": "ok", "python": sys.version, "platform": platform.platform(),
        "implementation": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "command": " ".join(sys.argv), "seed_set": SEEDS, "n": N,
        "domain": DOMAIN, "grid": GRID, "percentile": "linear, p*(n-1)",
        "boundary_rule": "inclusive max AABB cell; floor coordinates",
        "assignment_policy": "d<=median small tier; others large tier; cross-tier query in small hash",
        "rows": len(rows), "failure_rows": sum(1 for _ in failures.open()),
    }
    (out / "metadata.json").write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n",
                                         encoding="utf-8")
    for path in (results, failures, out / "metadata.json"):
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        with (out / "SHA256SUMS").open("a", encoding="utf-8") as handle:
            handle.write(f"{digest}  {path.name}\n")


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", required=True)
    args = parser.parse_args()
    run(Path(args.out))


if __name__ == "__main__":
    main()
