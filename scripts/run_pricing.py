#!/usr/bin/env python3
"""Congestion pricing: toll the congested links and see what it buys.

UXsim takes a per-link `congestion_pricing(t)` function returning extra *perceived
cost in seconds*, which drivers add to travel time when choosing a route. Tolls are
therefore expressed in time, and converting to money needs a value of time:

    toll_seconds = toll_money / value_of_time_per_hour * 3600

Tolls are set in proportion to the delay each link exhibits in an untolled run, and
applied only during the peak window. That is a congestion charge of the kind cities
actually deploy, not a true Pigouvian toll - see the note on marginal cost below.

    python scripts/run_pricing.py --strengths 0 0.5 1 2

Demand here is fixed, so a toll can only make drivers *re-route*; it can never make
them travel later, travel less, or not travel. Most of the real benefit of pricing
comes from exactly those responses, so treat the result as a LOWER BOUND.
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402


def measure(W) -> dict:
    a = W.analyzer
    a.basic_analysis()
    return {
        "completed": a.trip_completed / a.trip_all if a.trip_all else 0.0,
        "travel_time_s": a.average_travel_time,
        "delay_s": a.average_delay,
        "delay_ratio": a.average_delay / a.average_travel_time if a.average_travel_time else 0,
        "speed_kmh": getattr(a, "average_speed", 0.0) * 3.6,
        "total_delay_veh_h": a.average_delay * a.trip_completed / 3600.0,
    }


def link_delays(W) -> dict:
    """Seconds of delay per vehicle on each link, from an untolled run."""
    df = W.analyzer.link_to_pandas()
    out = {}
    for _, r in df.iterrows():
        out[r["link"]] = max(0.0, r["average_travel_time"] - r["free_travel_time"])
    return out


def apply_tolls(W, delays: dict, strength: float, window: float) -> int:
    """Charge each link in proportion to the delay it showed when untolled.

    The toll is a function of time so it can switch off outside the peak - charging a
    link at 3 a.m. would distort routing for no congestion benefit.
    """
    priced = 0
    for link in W.LINKS:
        toll = strength * delays.get(link.name, 0.0)
        if toll <= 0:
            continue
        link.congestion_pricing = (lambda amount: (lambda t: amount if t <= window else 0.0))(toll)
        priced += 1
    return priced


def main() -> None:
    ap = argparse.ArgumentParser(description="Congestion pricing sweep")
    add_model_args(ap)
    ap.add_argument("--strengths", type=float, nargs="+", default=[0.0, 0.5, 1.0, 2.0],
                    help="toll as a multiple of each link's observed delay")
    ap.add_argument("--value-of-time", type=float, default=300.0,
                    help="NPR per hour, used only to report tolls in money")
    ap.add_argument("--out", type=Path, default=Path("results/pricing.csv"))
    args = ap.parse_args()

    print("untolled reference run ...")
    W0, _ = build_world(args, verbose=False)
    W0.exec_simulation()
    delays = link_delays(W0)
    ref = measure(W0)
    worst = max(delays.values()) if delays else 0.0
    print(f"  worst link delay {worst:.0f} s/veh over {len(delays)} links\n")

    rows = []
    for s in args.strengths:
        W, _ = build_world(args, verbose=False)
        priced = apply_tolls(W, delays, s, args.demand_window) if s > 0 else 0
        W.exec_simulation()
        m = measure(W)
        m["strength"] = s
        m["links_priced"] = priced
        m["max_toll_s"] = s * worst
        m["max_toll_npr"] = s * worst / 3600.0 * args.value_of_time
        m["delay_change"] = (m["delay_s"] - ref["delay_s"]) / ref["delay_s"] if ref["delay_s"] else 0
        rows.append(m)
        print(f"strength {s:>4} | {priced:>3} links priced | max toll "
              f"{m['max_toll_npr']:>6.0f} NPR | completed {m['completed']:>4.0%} | "
              f"delay {m['delay_s']:>7.0f} s ({m['delay_change']:+.1%}) | "
              f"{m['speed_kmh']:>5.1f} km/h")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)

    best = min(rows, key=lambda r: r["delay_s"])
    print(f"\nbest: strength {best['strength']} -> {best['delay_change']:+.1%} delay "
          f"at {best['completed']:.0%} completion")
    print("Read completion alongside delay: a toll severe enough to strand trips will "
          "show falling delay while making the network worse.")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
