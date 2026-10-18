#!/usr/bin/env python3
"""Paired-seed test of H4: does the tidal-flow lever help, under AM-biased demand?

Reuses compare.py's ci95() apparatus. Two configs only: AM demand with vs without
the tidal lever, fixed-time signals in both (isolating the lever, not stacking it
with H1-H3's levers - that's a follow-up, not this test).

    python scripts/compare_tidal.py --seeds 15 --jobs 3
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from compare import ci95  # noqa: E402

def configs(lane_shift: float) -> dict:
    return {
        "no_tidal": {},
        "tidal": {"tidal_period": "am", "tidal_lane_shift": lane_shift},
    }


CONFIGS = configs(1.0)  # default; overridden in main() from --lane-shift


def worker(payload: dict) -> dict:
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    args.tmax = 14400
    args.od_file = Path("data/od_matrix_am.csv")
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
    ap = argparse.ArgumentParser(description="Paired test of the tidal-flow lever (H4)")
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--lane-shift", type=float, default=1.0)
    ap.add_argument("--out", type=Path, default=Path("results/tidal.csv"))
    args = ap.parse_args()

    cfgs = configs(args.lane_shift)
    tasks = [{"config": name, "seed": s, "overrides": ov}
              for name, ov in cfgs.items() for s in range(1, args.seeds + 1)]
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
            print(f"  [{i}/{len(tasks)}] {r['config']:<10} seed {r['seed']:>2}: "
                  f"delay {r['delay_s']:.0f}s, {r['completed']:.1%}", flush=True)

    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(results[0]))
        w.writeheader()
        w.writerows(results)

    by_config = {}
    for r in results:
        by_config.setdefault(r["config"], {})[r["seed"]] = r
    base, tidal = by_config.get("no_tidal", {}), by_config.get("tidal", {})
    shared = sorted(set(base) & set(tidal))
    diffs = [tidal[s]["delay_s"] - base[s]["delay_s"] for s in shared]
    rels = [d / base[s]["delay_s"] * 100 for d, s in zip(diffs, shared)]
    mean_d, ci_d = ci95(diffs)
    mean_r, ci_r = ci95(rels)
    sig = "SIGNIFICANT" if abs(mean_d) > ci_d else "NOT significant - inside the noise"
    neg = sum(1 for d in diffs if d < 0)
    print(f"\ntidal vs no_tidal, paired over {len(shared)} seeds (AM demand, fixed-time signals both):")
    print(f"  delay {mean_d:+.1f}s ({mean_r:+.2f}% +/- {ci_r:.2f}%)  [{neg}/{len(diffs)} negative]  -> {sig}")
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
