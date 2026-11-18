#!/usr/bin/env python3
"""Decentralized-attraction OD variant (H7): reduce trip attraction to core zones,
simulating government/institutional offices relocated out of the city center.
Reuses the core-zone classification from build_od_directional.py.

[SURVEY] The 25% reduction is a round-number scenario, not a measured relocation
plan - same status as the other unmeasured demand-shape assumptions (A1, A9, A11).

    python scripts/build_od_decentralized.py --reduce 0.25 --core-pct 0.2
"""
from __future__ import annotations

import argparse
import csv
import math
from pathlib import Path


def main() -> None:
    ap = argparse.ArgumentParser(description="Decentralized core-attraction OD variant")
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--reduce", type=float, default=0.25, help="fraction cut from core-bound trips")
    ap.add_argument("--core-pct", type=float, default=0.2)
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
    print(f"core zones: {n_core} of {len(zones)}, radius {zones[n_core-1]['dist_km']:.2f} km")

    od = list(csv.DictReader((args.data / "od_matrix.csv").open(encoding="utf-8")))
    rows, total_before, total_after = [], 0, 0
    for r in od:
        demand = int(r["demand"])
        total_before += demand
        new_demand = round(demand * (1 - args.reduce)) if r["dest_id"] in core_ids else demand
        total_after += new_demand
        rows.append({"origin_id": r["origin_id"], "dest_id": r["dest_id"], "demand": new_demand})

    out_path = args.data / "od_matrix_decentralized.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["origin_id", "dest_id", "demand"])
        w.writeheader()
        w.writerows(rows)
    print(f"total demand {total_before:,} -> {total_after:,} ({total_after/total_before-1:+.1%}), wrote {out_path}")


if __name__ == "__main__":
    main()
