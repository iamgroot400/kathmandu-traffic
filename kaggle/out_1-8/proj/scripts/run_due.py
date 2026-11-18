#!/usr/bin/env python3
"""Solve for Dynamic User Equilibrium and compare it with the baseline.

The baseline does *not* use fixed routes. UXsim defaults to `homogeneous_DUO`:
drivers reroute within the hour on current travel times, updated every 600 s. So
"adding route guidance" is not an available improvement here - the baseline already
has it.

DUE is a different thing: day-to-day learning, where commuters repeat the trip and
switch route based on yesterday's experience until the network settles. That is a
better description of real commuters, who have learned their routes over months,
and it is the state interventions are conventionally evaluated against.

    python scripts/run_due.py --max-iter 10

Each iteration is a full simulation (~4 min here), so budget accordingly.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402

from uxsim.DTAsolvers import SolverDUE  # noqa: E402


def report(W, label: str) -> dict:
    a = W.analyzer
    a.basic_analysis()
    done = a.trip_completed / a.trip_all if a.trip_all else 0.0
    ratio = a.average_delay / a.average_travel_time if a.average_travel_time else 0.0
    row = {
        "label": label,
        "completed": done,
        "travel_time_s": a.average_travel_time,
        "delay_s": a.average_delay,
        "delay_ratio": ratio,
        "speed_kmh": getattr(a, "average_speed", 0.0) * 3.6,
    }
    print(f"{label:<22} completed {done:>5.0%} | travel {a.average_travel_time:>7.0f} s | "
          f"delay {a.average_delay:>7.0f} s | ratio {ratio:>4.2f} | "
          f"{row['speed_kmh']:>5.1f} km/h")
    return row


def main() -> None:
    ap = argparse.ArgumentParser(description="Dynamic User Equilibrium")
    add_model_args(ap)
    ap.add_argument("--max-iter", type=int, default=10, help="day-to-day iterations")
    ap.add_argument("--n-routes", type=int, default=10, help="routes enumerated per OD")
    ap.add_argument("--swap-prob", type=float, default=0.05,
                    help="chance a driver switches to a faster route each day")
    ap.add_argument("--out", type=Path, default=Path("results/due.csv"))
    args = ap.parse_args()

    print("baseline (DUO: within-day rerouting, the UXsim default)")
    W_base, _ = build_world(args, verbose=False)
    W_base.exec_simulation()
    rows = [report(W_base, "DUO baseline")]

    print(f"\nsolving DUE: {args.max_iter} iterations x ~1 simulation each ...\n")
    solver = SolverDUE(lambda: build_world(args, verbose=False)[0])
    W_due = solver.solve(max_iter=args.max_iter, n_routes_per_od=args.n_routes,
                         swap_prob=args.swap_prob, print_progress=True)

    print()
    rows.append(report(W_due, "DUE equilibrium"))

    base, due = rows[0], rows[1]
    if base["delay_s"]:
        change = (due["delay_s"] - base["delay_s"]) / base["delay_s"]
        print(f"\nDUE delay is {change:+.1%} vs the DUO baseline")
    print("Neither is 'the improvement' - DUE is the state to evaluate signals and "
          "pricing against, because it is what commuters actually settle into.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    import csv
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
