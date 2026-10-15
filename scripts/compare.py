#!/usr/bin/env python3
"""Compare control configurations across several seeds, paired, with confidence intervals.

UXsim's route choice carries `duo_noise`, so every seed is a different realization.
Changing the vehicle count by even one re-rolls the entire random stream - which is
how this was discovered: a 0.02% change in demand moved average delay by 2.3%.

A single run of each configuration therefore cannot separate a real effect from
realization noise. This runs every configuration on the *same* seed set and compares
per-seed differences, which cancels most of the shared randomness, then reports a
95% confidence interval and whether the difference excludes zero.

    python scripts/compare.py --seeds 5 --jobs 5

Runs are independent, UXsim is single-threaded, and one run needs ~2.6 GB - so
`--jobs` is bounded by RAM, not cores.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# Configuration name -> overrides applied to the default model args.
CONFIGS = {
    "fixed_time": {},
    "adaptive": {"adaptive": True},
}

# Two-sided 95% t critical values by degrees of freedom (n-1).
_T95 = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
        8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 14: 2.145, 19: 2.093,
        29: 2.045}


def t95(df: int) -> float:
    if df <= 0:
        return float("inf")
    for k in sorted(_T95):
        if df <= k:
            return _T95[k]
    return 1.96


def ci95(values):
    """Mean and half-width of a 95% confidence interval."""
    vals = list(values)
    if len(vals) < 2:
        return (vals[0] if vals else 0.0), float("inf")
    mean = statistics.fmean(vals)
    sem = statistics.stdev(vals) / math.sqrt(len(vals))
    return mean, t95(len(vals) - 1) * sem


def worker(payload: dict) -> dict:
    """Run one (configuration, seed). Must be module level so it can be pickled."""
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    for key, value in payload["overrides"].items():
        setattr(args, key, value)
    args.seed = payload["seed"]

    try:
        W, _ = build_world(args, verbose=False)
        W.exec_simulation()
        a = W.analyzer
        a.basic_analysis()
        return {
            "config": payload["config"],
            "seed": payload["seed"],
            "completed": a.trip_completed / a.trip_all if a.trip_all else 0.0,
            "delay_s": a.average_delay,
            "travel_time_s": a.average_travel_time,
            "speed_kmh": getattr(a, "average_speed", 0.0) * 3.6,
            "total_delay_veh_h": a.average_delay * a.trip_completed / 3600.0,
        }
    except Exception as exc:                      # one bad run must not kill the sweep
        return {"config": payload["config"], "seed": payload["seed"], "error": repr(exc)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Paired multi-seed comparison")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--jobs", type=int, default=4, help="parallel runs (~2.6 GB each)")
    ap.add_argument("--baseline", default="fixed_time")
    ap.add_argument("--out", type=Path, default=Path("results/comparison.csv"))
    args = ap.parse_args()

    seeds = list(range(1, args.seeds + 1))
    tasks = [{"config": name, "seed": s, "overrides": ov}
             for name, ov in CONFIGS.items() for s in seeds]
    print(f"{len(CONFIGS)} configs x {len(seeds)} seeds = {len(tasks)} runs, "
          f"{args.jobs} at a time\n")

    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        results = list(pool.map(worker, tasks))

    failed = [r for r in results if "error" in r]
    for r in failed:
        print(f"  ! {r['config']} seed {r['seed']}: {r['error']}")
    results = [r for r in results if "error" not in r]

    by_config = {}
    for r in results:
        by_config.setdefault(r["config"], {})[r["seed"]] = r

    print(f"{'config':<14} {'delay s (mean +/- CI)':>26} {'speed km/h':>12} "
          f"{'completed':>10} {'n':>3}")
    print("-" * 70)
    for name in CONFIGS:
        runs = by_config.get(name, {})
        if not runs:
            continue
        d_mean, d_ci = ci95([r["delay_s"] for r in runs.values()])
        s_mean, _ = ci95([r["speed_kmh"] for r in runs.values()])
        c_mean, _ = ci95([r["completed"] for r in runs.values()])
        print(f"{name:<14} {d_mean:>16.1f} +/- {d_ci:<6.1f} {s_mean:>12.2f} "
              f"{c_mean:>9.1%} {len(runs):>3}")

    base = by_config.get(args.baseline, {})
    print()
    for name in CONFIGS:
        if name == args.baseline or name not in by_config:
            continue
        shared = sorted(set(base) & set(by_config[name]))
        if len(shared) < 2:
            print(f"{name}: too few paired seeds to compare")
            continue
        diffs = [by_config[name][s]["delay_s"] - base[s]["delay_s"] for s in shared]
        rels = [d / base[s]["delay_s"] * 100 for d, s in zip(diffs, shared)]
        mean_d, ci_d = ci95(diffs)
        mean_r, ci_r = ci95(rels)
        significant = abs(mean_d) > ci_d
        verdict = "SIGNIFICANT" if significant else "NOT significant - inside the noise"
        print(f"{name} vs {args.baseline}, paired over {len(shared)} seeds:")
        print(f"  delay {mean_d:+.1f} s ({mean_r:+.2f}% +/- {ci_r:.2f}%)  -> {verdict}")
        if not significant:
            print("  The per-seed differences disagree in sign or size too much to "
                  "claim an effect. Run more seeds before quoting a number.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
