#!/usr/bin/env python3
"""Re-verify the README's "node 3511456911 carries 22% of delay" claim across 15
seeds at tmax=14400 - the original figure was a single run, predating the sweep.

    python scripts/verify_bottleneck.py --seeds 15 --jobs 3
"""
from __future__ import annotations

import argparse
import csv
import statistics
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

NODE = "3511456911"


def worker(seed: int) -> dict:
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    args.tmax = 14400
    args.seed = seed

    W, _ = build_world(args, verbose=False)
    W.exec_simulation()
    df = W.analyzer.link_to_pandas()
    df["delay_veh_h"] = (df["traffic_volume"]
                         * (df["average_travel_time"] - df["free_travel_time"]) / 3600.0)
    df.loc[df["delay_veh_h"] < 0, "delay_veh_h"] = 0.0
    by_node = df.groupby("end_node")["delay_veh_h"].sum()
    total = by_node.sum()
    node_delay = by_node.get(NODE, 0.0)
    return {"seed": seed, "node_delay": node_delay, "total_delay": total,
            "share": node_delay / total if total else 0.0}


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", type=int, default=15)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--out", type=Path, default=Path("results/verify_bottleneck.csv"))
    args = ap.parse_args()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    results, header_written = [], False
    with ProcessPoolExecutor(max_workers=args.jobs) as pool:
        futures = [pool.submit(worker, s) for s in range(1, args.seeds + 1)]
        for i, fut in enumerate(as_completed(futures), 1):
            r = fut.result()
            results.append(r)
            with args.out.open("a", newline="", encoding="utf-8") as fh:
                w = csv.DictWriter(fh, fieldnames=list(r))
                if not header_written:
                    w.writeheader()
                    header_written = True
                w.writerow(r)
            print(f"  [{i}/{args.seeds}] seed {r['seed']}: node delay {r['node_delay']:.1f} veh-h, "
                  f"total {r['total_delay']:.1f} veh-h, share {r['share']:.1%}", flush=True)
    print(f"\nwrote {args.out}")

    shares = [r["share"] for r in results]
    print(f"\nnode {NODE} share of total delay, n={len(shares)}:")
    print(f"  mean {statistics.fmean(shares):.1%}, min {min(shares):.1%}, max {max(shares):.1%}, "
          f"stdev {statistics.stdev(shares):.1%}")


if __name__ == "__main__":
    main()
