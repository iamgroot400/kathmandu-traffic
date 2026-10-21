#!/usr/bin/env python3
"""Paired-seed test: calibrated baseline vs. an exponential demand projection at
a chosen horizon (years from now).

Growth rate source: the JICA/DoR 2012 survey's own 1991-2011 comparison table,
already cited in this project (paper/sections/introduction.tex, `jica2012`) -
vehicle registrations grew roughly 19.8x over that ~20-year span, an average
annual rate near 16%. This is a *registration* growth rate, not a measured
trip-generation rate, and projecting it forward assumes it continues unchanged
and that peak-hour trips scale 1:1 with the vehicle fleet - both untested
extrapolations (registered as A12, assumptions.md). The 16%/year figure itself
is the project's own already-verified source, not re-derived here. The horizon
(--years) must be decided before looking at any result, same as every other
robustness check in this project - never picked afterward to make a finding
land somewhere specific.

    python scripts/compare_future_demand.py --years 5 --seeds 15 --jobs 3
    python scripts/compare_future_demand.py --years 4.19 --label projected_2030 \\
        --seeds 15 --jobs 1   # "by end of 2030" from 2026-10-22
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare import ci95  # noqa: E402

# compare.py's own estimate (its module docstring) is "~2.6 GB", for the
# calibrated baseline. Observed directly on this run's projected_5yr seeds
# (tasklist sampling): peaked at ~3.7 GB per worker - gridlock at 2.1x demand
# keeps far more vehicle objects live simultaneously than the baseline ever
# does. Using that observed peak, not the baseline figure, since the baseline
# estimate undershot badly enough here to risk crashing the machine.
EST_MB_PER_WORKER = 4000


def ram_capped_jobs(max_ram_fraction: float) -> int:
    """How many parallel workers fit in `max_ram_fraction` of total RAM.

    Windows-only (ctypes GlobalMemoryStatusEx) to avoid adding a psutil
    dependency for one number; falls back to 1 worker (safest, not fastest)
    if total RAM can't be read, rather than guessing.
    """
    try:
        import ctypes

        class _MEMSTATUS(ctypes.Structure):
            _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                       ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                       ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                       ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                       ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]

        stat = _MEMSTATUS()
        stat.dwLength = ctypes.sizeof(_MEMSTATUS)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_mb = stat.ullTotalPhys / (1024 * 1024)
        return max(1, int(total_mb * max_ram_fraction // EST_MB_PER_WORKER))
    except Exception:
        return 1


ANNUAL_GROWTH_RATE = 0.16   # jica2012, 1991-2011 vehicle registration growth


def worker(payload: dict) -> dict:
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    # 2x the usual 14400: at ~2.1x demand the network takes substantially longer
    # to drain, and an undrained run biases delay toward short, easy trips.
    args.tmax = 21600
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
    ap = argparse.ArgumentParser(description="Baseline vs an N-year exponential demand projection")
    ap.add_argument("--years", type=float, default=5.0,
                    help="projection horizon in years (default 5, matching the "
                         "paper's own cited projection; pass a different value, "
                         "e.g. 4.19 for 'by end of 2030' from 2026-10-22, for a "
                         "different target date - never re-fit after the fact)")
    ap.add_argument("--label", type=str, default=None,
                    help="config/output-file label, default derived from --years "
                         "(e.g. 'projected_5y' or 'projected_2030')")
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--jobs", type=int, default=None,
                    help="default: as many as fit in --max-ram-fraction of total RAM")
    ap.add_argument("--max-ram-fraction", type=float, default=0.5,
                    help="cap parallel workers to this fraction of total system RAM")
    ap.add_argument("--out", type=Path, default=None)
    args = ap.parse_args()
    if args.jobs is None:
        args.jobs = ram_capped_jobs(args.max_ram_fraction)

    growth_factor = (1 + ANNUAL_GROWTH_RATE) ** args.years
    label = args.label or f"projected_{args.years:.2g}y".replace(".", "_")
    if args.out is None:
        args.out = Path(f"results/future_demand_{label}.csv")
    configs = {"baseline": {}, label: {"demand_growth": growth_factor}}

    print(f"growth: {ANNUAL_GROWTH_RATE:.0%}/yr x {args.years:.2f}yr = "
          f"{growth_factor:.4f}x peak-hour demand\n")
    print(f"jobs: {args.jobs} (capped to {args.max_ram_fraction:.0%} of total RAM, "
          f"~{EST_MB_PER_WORKER} MB/worker)\n")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    partial = args.out.with_suffix(".partial.csv")
    # resume: a prior interrupted run's rows in the partial file are kept, not
    # re-run - the worker is deterministic given (config, seed), so there is
    # nothing to gain by redoing them
    results, header_written = [], False
    done_keys = set()
    if partial.exists():
        with partial.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                results.append({**row, "seed": int(row["seed"]),
                                "completed": float(row["completed"]),
                                "delay_s": float(row["delay_s"]),
                                "speed_kmh": float(row["speed_kmh"])})
                done_keys.add((row["config"], int(row["seed"])))
                header_written = True
        print(f"resuming: {len(done_keys)} runs already in {partial}\n")

    tasks = [{"config": name, "seed": s, "overrides": ov}
              for name, ov in configs.items() for s in range(1, args.seeds + 1)
              if (name, s) not in done_keys]
    print(f"{len(tasks)} runs remaining, {args.jobs} at a time\n")
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
    for name in configs:
        runs = by_config.get(name, {})
        if not runs:
            continue
        d_mean, _ = ci95([r["delay_s"] for r in runs.values()])
        c_mean, _ = ci95([r["completed"] for r in runs.values()])
        if name == "baseline":
            print(f"{name:<14} {d_mean:>13.1f}s {'n/a':>22} {c_mean:>9.1%}")
            continue
        shared = sorted(set(base) & set(runs))
        diffs = [runs[s]["delay_s"] - base[s]["delay_s"] for s in shared]
        rels = [d / base[s]["delay_s"] * 100 for d, s in zip(diffs, shared)]
        mean_d, ci_d = ci95(diffs)
        mean_r, ci_r = ci95(rels)
        sig = "SIGNIFICANT" if abs(mean_d) > ci_d else "not significant"
        pos = sum(1 for d in diffs if d > 0)
        print(f"{name:<14} {d_mean:>13.1f}s {mean_r:>+8.2f}% +/- {ci_r:5.2f}% {c_mean:>9.1%}  "
              f"[{pos}/{len(diffs)} pos]  {sig}")
    print(f"\nwrote {args.out}")
    print("\nCaveat: assumes 16%/yr vehicle-registration growth (1991-2011, jica2012) "
          "continues unchanged and that peak-hour trips scale 1:1 with fleet size - "
          "neither is tested here. See assumptions.md A12.")


if __name__ == "__main__":
    main()
