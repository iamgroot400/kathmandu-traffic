#!/usr/bin/env python3
"""Add AM/PM directional asymmetry to the OD matrix (H4 prerequisite).

The base od_matrix.csv is production/attraction-symmetric (README: "no peak
directionality") - a tidal-flow lever has nothing to exploit without this. This
reweights the existing matrix rather than rebuilding the gravity model: zones near
the mass-weighted centroid are "core"; AM trips core-bound are boosted, core-outbound
are reduced by the reciprocal factor; PM reverses it. [SURVEY] factor is a guess
(no commute-direction survey for Kathmandu was found), not measured - same status as
A1/A9's other unmeasured demand-shape assumptions.

    python scripts/build_od_directional.py --boost 1.4 --core-pct 0.2
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="AM/PM directional demand variants")
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--boost", type=float, default=1.4, help="core-bound AM multiplier")
    ap.add_argument("--core-pct", type=float, default=0.2,
                    help="fraction of zones (closest to the mass-weighted centroid) treated as core")
    args = ap.parse_args()

    zones = list(csv.DictReader((args.data / "zones.csv").open(encoding="utf-8")))
    for z in zones:
        z["lat"], z["lon"], z["mass"] = float(z["lat"]), float(z["lon"]), float(z["mass"])

    mass_total = sum(z["mass"] for z in zones) or 1.0
    c_lat = sum(z["lat"] * z["mass"] for z in zones) / mass_total
    c_lon = sum(z["lon"] * z["mass"] for z in zones) / mass_total
    cos_lat = math.cos(math.radians(c_lat))

    for z in zones:
        z["dist_km"] = math.hypot((z["lat"] - c_lat) * 111.32, (z["lon"] - c_lon) * 111.32 * cos_lat)
    zones.sort(key=lambda z: z["dist_km"])
    n_core = max(1, int(len(zones) * args.core_pct))
    core_ids = {z["zone_id"] for z in zones[:n_core]}
    print(f"core zones (closest {args.core_pct:.0%} to mass-weighted centroid "
          f"{c_lat:.4f},{c_lon:.4f}): {n_core} of {len(zones)}, "
          f"radius {zones[n_core-1]['dist_km']:.2f} km")

    od = list(csv.DictReader((args.data / "od_matrix.csv").open(encoding="utf-8")))
    reduce = 1.0 / args.boost

    for period, out_name in [("am", "od_matrix_am.csv"), ("pm", "od_matrix_pm.csv")]:
        rows, changed, total_before, total_after = [], 0, 0, 0
        for r in od:
            demand = int(r["demand"])
            total_before += demand
            o_core, d_core = r["origin_id"] in core_ids, r["dest_id"] in core_ids
            inbound = (not o_core) and d_core     # periphery -> core
            outbound = o_core and (not d_core)    # core -> periphery
            if period == "am":
                factor = args.boost if inbound else (reduce if outbound else 1.0)
            else:  # pm: reverse of the AM commute
                factor = args.boost if outbound else (reduce if inbound else 1.0)
            new_demand = max(0, round(demand * factor))
            if new_demand != demand:
                changed += 1
            total_after += new_demand
            rows.append({"origin_id": r["origin_id"], "dest_id": r["dest_id"], "demand": new_demand})

        out_path = args.data / out_name
        with out_path.open("w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=["origin_id", "dest_id", "demand"])
            w.writeheader()
            w.writerows(rows)
        print(f"{period}: {changed}/{len(od)} pairs reweighted, total demand "
              f"{total_before:,} -> {total_after:,} ({total_after/total_before-1:+.1%}), "
              f"wrote {out_path}")


if __name__ == "__main__":
    assert round(1.0 / 1.4 * 1.4, 6) == 1.0  # reduce/boost are reciprocal, sanity check
    main()
