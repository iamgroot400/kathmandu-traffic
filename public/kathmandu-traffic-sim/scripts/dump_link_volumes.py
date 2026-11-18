#!/usr/bin/env python3
"""Run one baseline-style simulation and dump every link's first-hour volume, so
intersection matching (checks/intersection_accuracy.py) can be studied offline
without re-simulating. Same model arguments as geh_check.py.

    python scripts/dump_link_volumes.py --out results/linkvol_base.csv
    python scripts/dump_link_volumes.py --od-file data/od_matrix_am.csv --out results/linkvol_am.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser()
    add_model_args(ap)
    ap.add_argument("--out", type=Path, required=True)
    # >0: count the hour starting here (e.g. 3600 with --demand-window 7200 --demand-growth 2,
    # the second hour of a steady two-hour peak, so the network is no longer empty)
    ap.add_argument("--measure-from", type=int, default=0)
    args = ap.parse_args()
    W, _ = build_world(args, verbose=False)
    W.exec_simulation()
    W.analyzer.basic_analysis()
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["link", "start", "end", "start_lat", "start_lon", "end_lat", "end_lon", "vol_pcu_h",
                    "length_m", "tt_s"])
        t0 = args.measure_from                   # mean travel time of entries in the measured hour
        for l in W.LINKS:
            w.writerow([l.name, l.start_node.name, l.end_node.name, l.start_node.y, l.start_node.x,
                        l.end_node.y, l.end_node.x,
                        l.departure_count(args.measure_from + 3600) - l.departure_count(args.measure_from)
                        if args.measure_from else l.departure_count(args.demand_window),
                        round(l.length, 1),
                        round(sum(l.actual_travel_time(t0 + s) for s in range(0, 3600, 120)) / 30, 1)])
    a = W.analyzer
    print(f"{args.out}: speed {getattr(a, 'average_speed', 0) * 3.6:.1f} km/h, "
          f"completed {a.trip_completed / a.trip_all:.1%}")


if __name__ == "__main__":
    main()
