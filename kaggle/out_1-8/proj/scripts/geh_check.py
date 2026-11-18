#!/usr/bin/env python3
"""GEH validation against observed counts (E6) - currently 2 landmarks only.

Observed peak-hour volumes come from the 2017 JICA "Urban Transport Improvement for
Kathmandu Valley" report (Tables 8.2.5/8.2.6), sourced from a Dec 2011-Jan 2012 survey.
A clean GEH here supports "the baseline's pattern is plausible", not "matches 2026
Kathmandu" - see lab/experiments/E6.md. Add more landmarks here as they're transcribed.

    python scripts/geh_check.py
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402
from validate_hotspots import haversine_km  # noqa: E402

# (lat, lon), observed peak-hour volume, its unit, and source table.
# Thapathali's 7,395 veh/h is a raw vehicle count (AM/PM average); converted to PCU
# with this project's own fleet-mix factor (0.625, see assumptions.md A2) since the
# model's own volumes are PCU-weighted - an approximation, not a measured PCU split.
PCU_FACTOR = 0.625
OBSERVED = {
    "Koteshwor":     {"lat": 27.6788, "lon": 85.3492, "volume_pcu_h": 9996, "source": "Table 8.2.6 (already pcu/h)"},
    "Thapathali":    {"lat": 27.6939, "lon": 85.3208, "volume_pcu_h": 7395 * PCU_FACTOR, "source": "Table 8.2.5 (7,395 veh/h avg, PCU-converted)"},
    # Coordinates below are from OSM Nominatim (chowk-area geocoding, not a surveyed
    # point like the two above) - less precise, flagged in the printed output.
    "Kalimati":      {"lat": 27.6996, "lon": 85.2996, "volume_pcu_h": 4897, "source": "Table 8.2.6 (already pcu/h)", "approx_coords": True},
    "New Baneshwor": {"lat": 27.6890, "lon": 85.3355, "volume_pcu_h": 9123 * PCU_FACTOR, "source": "Table 8.2.5 (9,123 veh/h avg, PCU-converted)", "approx_coords": True},
    "Old Baneshwor": {"lat": 27.6907, "lon": 85.3360, "volume_pcu_h": 3910 * PCU_FACTOR, "source": "Table 8.2.5 (3,910 veh/h avg, PCU-converted)", "approx_coords": True},
    "Sorakhutte":    {"lat": 27.7188, "lon": 85.3096, "volume_pcu_h": 4395 * PCU_FACTOR, "source": "Table 8.2.5 (4,395 veh/h avg, PCU-converted)", "approx_coords": True},
}


def geh(model: float, observed: float) -> float:
    if model + observed <= 0:
        return 0.0
    return math.sqrt((model - observed) ** 2 / ((model + observed) / 2))


def main() -> None:
    ap = argparse.ArgumentParser(description="GEH check against observed landmark counts")
    add_model_args(ap)
    ap.add_argument("--out", type=Path, default=Path("results/geh.csv"))
    args = ap.parse_args()

    W, _zones = build_world(args, verbose=False)
    W.exec_simulation()

    # sum volume over every approach link ending at the matched node - an
    # intersection's "entering traffic volume" in the JICA tables is a sum across
    # approaches, not a single link.
    node_pos, node_volume = {}, {}
    for l in W.LINKS:
        n = l.end_node.name
        node_pos.setdefault(n, (l.end_node.y, l.end_node.x))
        node_volume[n] = node_volume.get(n, 0.0) + l.departure_count(args.demand_window)

    print(f"{'landmark':<14} {'node':>13} {'dist km':>8} {'model pcu/h':>12} {'observed':>10} {'GEH':>6}  verdict")
    rows = []
    for name, obs in OBSERVED.items():
        best, best_km = None, 1e9
        for node, (lat, lon) in node_pos.items():
            d = haversine_km(obs["lat"], obs["lon"], lat, lon)
            if d < best_km:
                best, best_km = node, d
        model_vol = node_volume.get(best, 0.0)
        g = geh(model_vol, obs["volume_pcu_h"])
        pass_fit = g < 5
        verdict = "GEH<5 (good fit)" if pass_fit else "GEH>=5 (poor fit)"
        flag = " *approx coords*" if obs.get("approx_coords") else ""
        print(f"{name:<14} {best:>13} {best_km:>8.2f} {model_vol:>12.0f} "
              f"{obs['volume_pcu_h']:>10.0f} {g:>6.2f}  {verdict}{flag}")
        rows.append({"landmark": name, "node": best, "dist_km": round(best_km, 3),
                     "model_pcu_h": round(model_vol, 1), "observed_pcu_h": round(obs["volume_pcu_h"], 1),
                     "geh": round(g, 2), "pass": pass_fit, "approx_coords": obs.get("approx_coords", False)})

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print(f"\nwrote {args.out}")
    print("\nCaveat: observed data is from a Dec 2011-Jan 2012 survey (~14 years old) - "
          "see lab/experiments/E6.md. This checks plausibility of pattern, not a 2026 match.")


if __name__ == "__main__":
    assert round(geh(100, 100), 6) == 0.0  # identical volumes -> GEH 0
    assert geh(110, 100) > 0  # any mismatch -> positive GEH
    main()
