#!/usr/bin/env python3
"""Robustness check: do H1-H3's conclusions survive if per-lane capacity is
lower than this project's calibrated default?

Per-lane capacity was never measured for this network; the 0.2 jam_density_per_lane
default (empirically ~2400 veh/h/lane, see paper Discussion) runs above the 1203-2160
veh/h/lane Tiwari et al. (2024) measured directly at two real Kathmandu intersections.
This tests whether the *qualitative* findings (adaptive signals reduce delay, pricing
reduces delay, no significant super-additive interaction) hold at capacities spanning
that field-measured range and below, not just whether magnitudes shift - a genuine
robustness check, not a search for whichever capacity makes a validation number pass
(that circularity trap is exactly what D23 rejected for GEH).

jam_density_per_lane -> empirical capacity (measured directly, scripts/congestion_report.py
style single-link flood test, steady-state arrivals over [600s,1800s]):
    0.095 -> ~1200 veh/h/lane
    0.101 -> ~1600 veh/h/lane
    0.150 -> ~2000 veh/h/lane
    0.200 -> ~2400 veh/h/lane (this project's existing calibrated default)

n=5 seeds per (capacity, config), not the core result's n=15: this is a secondary
robustness check on an already-well-powered core result, the same role n=3 played in
sensitivity.py's +/-20% parameter sweep - illustrative of whether conclusions survive,
not a precise magnitude to quote (see lab/decisions.md D11 for that same distinction).

    python scripts/compare_capacity_sweep.py --seeds 5 --jobs 1
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare import ci95  # noqa: E402

CAPACITIES = {
    "1200": 0.095,
    "1600": 0.101,
    "2000": 0.150,
    "2400": 0.200,
}
TOLLS = Path(__file__).parent.parent / "results" / "tolls.csv"
LEVERS = {
    "fixed_time": {},
    "adaptive": {"adaptive": True},
    "pricing": {"toll_file": TOLLS, "toll_strength": 0.2},
    "adaptive_pricing": {"adaptive": True, "toll_file": TOLLS, "toll_strength": 0.2},
}


def worker(payload: dict) -> dict:
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    # lower capacity than the calibrated default congests the network more at the
    # same demand, so a longer horizon guards against a completion-bias artifact
    args.tmax = 21600
    args.seed = payload["seed"]
    args.jam_density = payload["jam_density"]
    for k, v in payload["overrides"].items():
        setattr(args, k, v)

    try:
        W, _ = build_world(args, verbose=False)
        W.exec_simulation()
        a = W.analyzer
        a.basic_analysis()
        return {"capacity": payload["capacity"], "lever": payload["lever"], "seed": payload["seed"],
                "completed": a.trip_completed / a.trip_all if a.trip_all else 0.0,
                "delay_s": a.average_delay, "speed_kmh": getattr(a, "average_speed", 0.0) * 3.6}
    except Exception as exc:
        return {"capacity": payload["capacity"], "lever": payload["lever"],
                "seed": payload["seed"], "error": repr(exc)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Capacity-sensitivity robustness check for H1-H3")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--out", type=Path, default=Path("results/capacity_sweep.csv"))
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    partial = args.out.with_suffix(".partial.csv")
    results, header_written = [], False
    done_keys = set()
    if partial.exists():
        with partial.open(encoding="utf-8") as fh:
            for row in csv.DictReader(fh):
                results.append({**row, "seed": int(row["seed"]), "completed": float(row["completed"]),
                                "delay_s": float(row["delay_s"]), "speed_kmh": float(row["speed_kmh"])})
                done_keys.add((row["capacity"], row["lever"], int(row["seed"])))
                header_written = True
        print(f"resuming: {len(done_keys)} runs already in {partial}\n")

    tasks = [{"capacity": cap, "jam_density": jd, "lever": lever, "seed": s, "overrides": ov}
             for cap, jd in CAPACITIES.items()
             for lever, ov in LEVERS.items()
             for s in range(1, args.seeds + 1)
             if (cap, lever, s) not in done_keys]
    print(f"{len(CAPACITIES)} capacities x {len(LEVERS)} levers x {args.seeds} seeds "
          f"= {len(CAPACITIES) * len(LEVERS) * args.seeds} total, {len(tasks)} remaining, "
          f"{args.jobs} at a time\n")

    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(worker, t) for t in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            if "error" in r:
                print(f"  ! {r['capacity']} {r['lever']} seed {r['seed']}: {r['error']}")
                continue
            results.append(r)
            with partial.open("a", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=["capacity", "lever", "seed", "completed",
                                                    "delay_s", "speed_kmh"])
                if not header_written:
                    w.writeheader()
                    header_written = True
                w.writerow({k: r[k] for k in ["capacity", "lever", "seed", "completed",
                                               "delay_s", "speed_kmh"]})
            print(f"  [{i}/{len(tasks)}] {r['capacity']:>5} {r['lever']:<16} seed {r['seed']}: "
                  f"delay {r['delay_s']:.0f}s, {r['completed']:.1%}", flush=True)

    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["capacity", "lever", "seed", "completed",
                                           "delay_s", "speed_kmh"])
        w.writeheader()
        for r in results:
            w.writerow({k: r[k] for k in ["capacity", "lever", "seed", "completed",
                                          "delay_s", "speed_kmh"]})

    by = {}
    for r in results:
        by.setdefault(r["capacity"], {}).setdefault(r["lever"], {})[r["seed"]] = r

    print(f"\n{'capacity':>9} {'lever':<16} {'delay (mean)':>14} {'vs fixed_time':>22} {'completed':>10}")
    for cap in CAPACITIES:
        base = by.get(cap, {}).get("fixed_time", {})
        for lever in LEVERS:
            runs = by.get(cap, {}).get(lever, {})
            if not runs:
                continue
            d_mean, _ = ci95([r["delay_s"] for r in runs.values()])
            c_mean, _ = ci95([r["completed"] for r in runs.values()])
            if lever == "fixed_time":
                print(f"{cap:>9} {lever:<16} {d_mean:>13.1f}s {'n/a':>22} {c_mean:>9.1%}")
                continue
            shared = sorted(set(base) & set(runs))
            if len(shared) < 2:
                print(f"{cap:>9} {lever:<16} {d_mean:>13.1f}s {'too few paired seeds':>22} {c_mean:>9.1%}")
                continue
            diffs = [runs[s]["delay_s"] - base[s]["delay_s"] for s in shared]
            rels = [d / base[s]["delay_s"] * 100 for d, s in zip(diffs, shared)]
            mean_r, ci_r = ci95(rels)
            neg = sum(1 for d in diffs if d < 0)
            sig = "SIGNIFICANT" if abs(mean_r) > ci_r else "not significant"
            print(f"{cap:>9} {lever:<16} {d_mean:>13.1f}s {mean_r:>+8.2f}% +/- {ci_r:5.2f}% "
                  f"{c_mean:>9.1%}  [{neg}/{len(shared)} neg]  {sig}")
    print(f"\nwrote {args.out}")
    print("\nNote: n=5 seeds per cell, a robustness check on whether H1-H3's direction "
          "survives different capacity assumptions, not a precise magnitude to quote "
          "(same role as sensitivity.py's n=3 +/-20% sweep).")


if __name__ == "__main__":
    main()
