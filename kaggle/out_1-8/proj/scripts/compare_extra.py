#!/usr/bin/env python3
"""Paired-seed test of H5-H7: parking enforcement, staggered departures,
decentralized core demand - each alone vs the calibrated fixed-time baseline.

    python scripts/compare_extra.py --seeds 15 --jobs 3
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare import ci95  # noqa: E402

CONFIGS = {
    "baseline":      {},
    "parking":       {"free_flow_kmh": 35.0},
    "staggered":     {"demand_window": 5400},
    "decentralized": {"od_file": Path("data/od_matrix_decentralized.csv")},
}


def worker(payload: dict) -> dict:
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    args.tmax = 14400
    args.seed = payload["seed"]
    for k, v in payload["overrides"].items():
        setattr(args, k, v)

    try:
        W, _ = build_world(args, verbose=False)
        W.exec_simulation()
        a = W.analyzer
        a.basic_analysis()
        return {"config": payload["config"], "seed": payload["seed"],
                "completed": a.trip_completed / a.trip_all if a.trip_all else 0.0,
                "delay_s": a.average_delay, "speed_kmh": getattr(a, "average_speed", 0.0) * 3.6}
    except Exception as exc:
        return {"config": payload["config"], "seed": payload["seed"], "error": repr(exc)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Paired test of H5-H7 vs the calibrated baseline")
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", type=Path, default=Path("results/extra.csv"))
    args = ap.parse_args()

    tasks = [{"config": name, "seed": s, "overrides": ov}
              for name, ov in CONFIGS.items() for s in range(1, args.seeds + 1)]
    print(f"{len(CONFIGS)} configs x {args.seeds} seeds = {len(tasks)} runs, {args.jobs} at a time\n")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    partial = args.out.with_suffix(".partial.csv")
    results, header_written = [], False
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(worker, t) for t in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            if "error" in r:
                print(f"  ! {r['config']} seed {r['seed']}: {r['error']}")
                continue
            results.append(r)
            with partial.open("a", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(r))
                if not header_written:
                    w.writeheader()
                    header_written = True
                w.writerow(r)
            print(f"  [{i}/{len(tasks)}] {r['config']:<14} seed {r['seed']:>2}: "
                  f"delay {r['delay_s']:.0f}s, {r['completed']:.1%}", flush=True)

    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)

    by_config = {}
    for r in results:
        by_config.setdefault(r["config"], {})[r["seed"]] = r
    base = by_config.get("baseline", {})
    print(f"\n{'config':<14} {'delay (mean)':>14} {'vs baseline':>22} {'completed':>10}")
    for name in CONFIGS:
        runs = by_config.get(name, {})
        if not runs:
            continue
        d_mean, _ = ci95([r["delay_s"] for r in runs.values()])
        c_mean, _ = ci95([r["completed"] for r in runs.values()])
        if name == "baseline":
            print(f"{name:<14} {d_mean:>13.1f}s {'—':>22} {c_mean:>9.1%}")
            continue
        shared = sorted(set(base) & set(runs))
        diffs = [runs[s]["delay_s"] - base[s]["delay_s"] for s in shared]
        rels = [d / base[s]["delay_s"] * 100 for d, s in zip(diffs, shared)]
        mean_d, ci_d = ci95(diffs)
        mean_r, ci_r = ci95(rels)
        sig = "SIGNIFICANT" if abs(mean_d) > ci_d else "not significant"
        neg = sum(1 for d in diffs if d < 0)
        print(f"{name:<14} {d_mean:>13.1f}s {mean_r:>+8.2f}% +/- {ci_r:5.2f}% {c_mean:>9.1%}  "
              f"[{neg}/{len(diffs)} neg]  {sig}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
