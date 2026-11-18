#!/usr/bin/env python3
"""Follow-up experiments from the 2026-11-10 audit (lab/qa/2026-11-10-qa.md), one
resumable queue, one worker. Designs fixed before any of these were run:

  uniform_cut     demand x 0.8863 everywhere (same total as the decentralized OD):
                  volume-matched control for H7. H7 is a redistribution effect only
                  if decentralized beats this.
  staggered_4500  demand window 4500s (25% longer, half of H6's 5400s shift).
  pricing_elastic, combined_elastic   pricing with --demand-elasticity -0.3 (A13):
                  tolled trips are partly suppressed. Read with the `trips` column.
  combined_2030   adaptive + pricing at 1.8624x demand, vs results/future_demand_
                  projected_2030.csv (no intervention at the same demand).
  cap2000_*, cap1600_*   the four levers at 2000 and 1600 veh/h/lane again, this
                  time recording time in system (below), which the first capacity
                  sweep did not, so its individual-lever result was unreadable (D27).

Every row records `tis_s`: mean time in system over ALL vehicles, finished or not
(arrival, or the horizon if still on the network, minus scheduled departure). It is
a lower bound for unfinished trips, but it is the same set of trips in every arm,
so unlike delay over completed trips it cannot be flattered by stranding vehicles.

    python scripts/compare_followups.py --seeds 15
    python scripts/compare_followups.py --only uniform_cut,staggered_4500
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

TOLLS = Path(__file__).parent.parent / "results" / "tolls.csv"
PRICING = {"toll_file": TOLLS, "toll_strength": 0.2}
LEVERS = {"fixed_time": {}, "adaptive": {"adaptive": True}, "pricing": PRICING,
          "adaptive_pricing": {"adaptive": True, **PRICING}}

# order = cheapest first, so the short answers land before the long sweep
CONFIGS = {
    "uniform_cut":    {"tmax": 14400, "demand_growth": 230432 / 260000},
    "staggered_4500": {"tmax": 14400, "demand_window": 4500},
    "pricing_elastic":  {"tmax": 14400, "demand_elasticity": -0.3, **PRICING},
    "combined_elastic": {"tmax": 14400, "demand_elasticity": -0.3, "adaptive": True, **PRICING},
    "combined_2030":  {"tmax": 21600, "demand_growth": 1.16 ** 4.19, "adaptive": True, **PRICING},
}
for cap, jam in (("2000", 0.150), ("1600", 0.101)):
    for lever, ov in LEVERS.items():
        CONFIGS[f"cap{cap}_{lever}"] = {"tmax": 21600, "jam_density": jam, **ov}

FIELDS = ["config", "seed", "completed", "delay_s", "travel_time_s", "speed_kmh", "tis_s", "trips"]


def time_in_system_s(W) -> float:
    horizon = int(W.TMAX / W.DELTAT)
    total = 0.0
    for v in W.VEHICLES.values():
        end = v.arrival_time if v.state == "end" else horizon
        total += max(0, end - v.departure_time) * W.DELTAT
    return total / len(W.VEHICLES)


def worker(payload: dict) -> dict:
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
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
                "delay_s": a.average_delay, "travel_time_s": a.average_travel_time,
                "speed_kmh": getattr(a, "average_speed", 0.0) * 3.6,
                "tis_s": time_in_system_s(W), "trips": a.trip_all}
    except Exception as exc:
        return {"config": payload["config"], "seed": payload["seed"], "error": repr(exc)}


def main() -> None:
    ap = argparse.ArgumentParser(description="Audit follow-up experiments, resumable")
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--jobs", type=int, default=1)
    ap.add_argument("--only", type=str, default=None, help="comma-separated config names")
    ap.add_argument("--out", type=Path, default=Path("results/followups.partial.csv"))
    args = ap.parse_args()

    done = set()
    if args.out.exists():
        with args.out.open(encoding="utf-8") as fh:
            done = {(r["config"], int(r["seed"])) for r in csv.DictReader(fh)}
    names = [n for n in CONFIGS if args.only is None or n in args.only.split(",")]
    tasks = [{"config": n, "seed": s, "overrides": CONFIGS[n]}
             for n in names for s in range(1, args.seeds + 1) if (n, s) not in done]
    print(f"{len(done)} done, {len(tasks)} remaining, {args.jobs} at a time\n", flush=True)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    # max_tasks_per_child=1: a fresh process per run, so a gridlock run's memory is returned
    with ProcessPoolExecutor(max_workers=args.jobs, max_tasks_per_child=1) as pool:
        futures = [pool.submit(worker, t) for t in tasks]
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            if "error" in r:
                print(f"  ! {r['config']} seed {r['seed']}: {r['error']}", flush=True)
                continue
            new = not args.out.exists()
            with args.out.open("a", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=FIELDS)
                if new:
                    w.writeheader()
                w.writerow(r)
            print(f"  [{i}/{len(tasks)}] {r['config']:<22} seed {r['seed']:>2}: delay {r['delay_s']:.0f}s, "
                  f"tis {r['tis_s']:.0f}s, {r['completed']:.1%}", flush=True)
    print("queue finished")


if __name__ == "__main__":
    main()
