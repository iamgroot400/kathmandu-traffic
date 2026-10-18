#!/usr/bin/env python3
"""+/-20% sensitivity of the calibrated baseline to its 3 fitted knobs (E7).

Each parameter is perturbed alone, others held at their calibrated default, against
the fixed-time baseline only (not the H1-H3 lever comparisons - see E7.md for why).

    python scripts/sensitivity.py --seeds 3 --jobs 3
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

# name -> (arg, calibrated default, -20%, +20%)
KNOBS = {
    "demand_scale":  ("demand_scale", 0.48, 0.384, 0.576),
    "pcu_factor":    ("pcu_factor", 0.625, 0.5, 0.75),
    "free_flow_kmh": ("free_flow_kmh", 30.0, 24.0, 36.0),
}


def worker(payload: dict) -> dict:
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    args.tmax = 14400
    args.seed = payload["seed"]
    setattr(args, payload["arg"], payload["value"])

    try:
        W, _ = build_world(args, verbose=False)
        W.exec_simulation()
        a = W.analyzer
        a.basic_analysis()
        return {
            "knob": payload["knob"], "variant": payload["variant"], "seed": payload["seed"],
            "value": payload["value"],
            "completed": a.trip_completed / a.trip_all if a.trip_all else 0.0,
            "delay_s": a.average_delay,
            "speed_kmh": getattr(a, "average_speed", 0.0) * 3.6,
        }
    except Exception as exc:
        return {"knob": payload["knob"], "variant": payload["variant"], "seed": payload["seed"], "error": repr(exc)}


def main() -> None:
    ap = argparse.ArgumentParser(description="+/-20% sensitivity of the baseline's 3 fitted knobs")
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", type=Path, default=Path("results/sensitivity.csv"))
    args = ap.parse_args()

    tasks = []
    for knob, (arg, default, lo, hi) in KNOBS.items():
        for variant, value in [("-20%", lo), ("baseline", default), ("+20%", hi)]:
            for seed in range(1, args.seeds + 1):
                tasks.append({"knob": knob, "arg": arg, "variant": variant, "value": value, "seed": seed})
    # "baseline" rows repeat across all 3 knobs - dedupe to one run per seed
    seen, deduped = set(), []
    for t in tasks:
        key = (t["variant"], t["seed"]) if t["variant"] == "baseline" else (t["knob"], t["variant"], t["seed"])
        if key in seen:
            continue
        seen.add(key)
        deduped.append(t)

    print(f"{len(deduped)} runs, {args.jobs} at a time")
    # write each result as it completes - a killed/closed session loses only the
    # runs still in flight, not everything (compare.py does this too; this script
    # originally didn't, which would have lost all progress on an interruption).
    args.out.parent.mkdir(parents=True, exist_ok=True)
    partial = args.out.with_suffix(".partial.csv")
    results, header_written = [], False
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(worker, t) for t in deduped]
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            if "error" in r:
                print(f"  ! {r['knob']} {r['variant']} seed {r['seed']}: {r['error']}")
                continue
            results.append(r)
            with partial.open("a", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(r))
                if not header_written:
                    w.writeheader()
                    header_written = True
                w.writerow(r)
            print(f"  [{i}/{len(deduped)}] {r['knob']:<14} {r['variant']:<9} seed {r['seed']}: "
                  f"speed {r['speed_kmh']:.1f} km/h, delay {r['delay_s']:.0f}s, {r['completed']:.1%}", flush=True)

    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)

    base = [r for r in results if r["variant"] == "baseline"]
    base_speed = statistics.fmean(r["speed_kmh"] for r in base)
    base_delay = statistics.fmean(r["delay_s"] for r in base)
    print(f"\nbaseline: speed {base_speed:.2f} km/h, delay {base_delay:.0f}s (n={len(base)})\n")
    print(f"{'knob':<14} {'variant':<9} {'speed km/h':>11} {'% vs base':>10} {'delay s':>8} {'% vs base':>10}")
    for knob in KNOBS:
        for variant in ["-20%", "+20%"]:
            rows = [r for r in results if r["knob"] == knob and r["variant"] == variant]
            if not rows:
                continue
            s = statistics.fmean(r["speed_kmh"] for r in rows)
            d = statistics.fmean(r["delay_s"] for r in rows)
            print(f"{knob:<14} {variant:<9} {s:>11.2f} {(s/base_speed-1)*100:>9.1f}% "
                  f"{d:>8.0f} {(d/base_delay-1)*100:>9.1f}%")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
