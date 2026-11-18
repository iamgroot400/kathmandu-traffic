#!/usr/bin/env python3
"""Rank intersections by the delay they cause, to pick DRL signal-control targets.

Delay is measured per link, then attributed to the link's **downstream** node - the
intersection it feeds into - because that is where the queue forms and what a signal
can act on. Delay caused by a link's own length or speed limit is not a signal
problem and is excluded by subtracting free-flow travel time.

    python scripts/find_bottlenecks.py --top 20

Outputs data/bottlenecks.csv, ranked by vehicle-hours of delay.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Rank intersections by delay caused")
    add_model_args(ap)
    ap.add_argument("--top", type=int, default=20, help="how many to print")
    ap.add_argument("--out", type=Path, default=Path("data/bottlenecks.csv"))
    args = ap.parse_args()

    W, _zones = build_world(args)
    print("running ...")
    W.exec_simulation()

    df = W.analyzer.link_to_pandas()
    # vehicle-hours of delay on each approach, above what free flow would have cost
    df["delay_veh_h"] = (df["traffic_volume"]
                         * (df["average_travel_time"] - df["free_travel_time"]) / 3600.0)
    df.loc[df["delay_veh_h"] < 0, "delay_veh_h"] = 0.0

    signalised = {n.name for n in W.NODES if n.signal != [0]}
    by_node = df.groupby("end_node").agg(
        delay_veh_h=("delay_veh_h", "sum"),
        approaches=("link", "count"),
        volume=("traffic_volume", "sum"),
        worst_delay_ratio=("delay_ratio", "max"),
    ).reset_index()
    by_node["signalised"] = by_node["end_node"].isin(signalised)
    by_node = by_node.sort_values("delay_veh_h", ascending=False).reset_index(drop=True)
    by_node["share_of_total"] = by_node["delay_veh_h"] / by_node["delay_veh_h"].sum()
    by_node["cumulative_share"] = by_node["share_of_total"].cumsum()

    args.out.parent.mkdir(parents=True, exist_ok=True)
    by_node.to_csv(args.out, index=False)

    total = by_node["delay_veh_h"].sum()
    print(f"\ntotal delay: {total:,.0f} vehicle-hours across {len(by_node)} nodes\n")
    print(f"{'#':>3} {'node':>12} {'sig':>4} {'delay veh-h':>12} {'share':>7} "
          f"{'cum':>7} {'appr':>5} {'volume':>9}")
    for i, r in by_node.head(args.top).iterrows():
        print(f"{i+1:>3} {r['end_node']:>12} {'yes' if r['signalised'] else ' no':>4} "
              f"{r['delay_veh_h']:>12,.0f} {r['share_of_total']:>6.1%} "
              f"{r['cumulative_share']:>6.1%} {r['approaches']:>5} {r['volume']:>9,.0f}")

    # How concentrated is the problem? Signal control only pays off if a small number
    # of intersections carry most of the delay.
    top20 = by_node.head(20)
    sig_top = top20["signalised"].sum()
    print(f"\ntop 20 carry {top20['share_of_total'].sum():.1%} of all delay "
          f"({sig_top}/20 are signalised and therefore controllable)")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
