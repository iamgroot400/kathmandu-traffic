#!/usr/bin/env python3
"""Build a synthetic origin-destination matrix from the OSM road map.

There is no observed trip data for this network, so demand is synthesised with a
gravity model: trips between two zones scale with how much activity each zone has
and fall off with the distance between them.

    python scripts/build_od.py --osm data/kathmandu.osm.xml --total-trips 2600000

Outputs:
    data/zones.csv      zone_id, lat, lon, junction_nodes, mass
    data/od_matrix.csv  origin_id, dest_id, demand

The result is a *hypothesis about demand*, not a measurement. Any finding that
depends on its shape has to be re-tested against surveyed counts.
"""
from __future__ import annotations

import argparse
import csv
import math
import xml.etree.ElementTree as ET
from collections import Counter, defaultdict
from pathlib import Path

EARTH_R_KM = 6371.0


# ---------------------------------------------------------------------------
# Map -> junction nodes
# ---------------------------------------------------------------------------

def load_junctions(osm_path: Path) -> list[tuple[float, float]]:
    """Coordinates of nodes where two or more roads meet.

    Junctions are used rather than every node, because most OSM nodes are just
    polyline vertices - they measure how curvy a road is drawn, not how much
    activity is there. Junction density is a far better activity proxy.
    """
    root = ET.parse(osm_path).getroot()
    coords = {n.get("id"): (float(n.get("lat")), float(n.get("lon")))
              for n in root.findall("node")}

    uses: Counter[str] = Counter()
    for way in root.findall("way"):
        if not any(t.get("k") == "highway" for t in way.findall("tag")):
            continue
        for nd in way.findall("nd"):
            uses[nd.get("ref")] += 1

    return [coords[nid] for nid, n in uses.items() if n > 1 and nid in coords]


# ---------------------------------------------------------------------------
# Junction nodes -> zones
# ---------------------------------------------------------------------------

def build_zones(points: list[tuple[float, float]], cell_km: float) -> list[dict]:
    """Group junctions into square grid cells. Empty cells are dropped."""
    lat0 = sum(p[0] for p in points) / len(points)
    km_per_deg_lat = 111.32
    km_per_deg_lon = 111.32 * math.cos(math.radians(lat0))

    buckets: dict[tuple[int, int], list[tuple[float, float]]] = defaultdict(list)
    for lat, lon in points:
        row = int(lat * km_per_deg_lat // cell_km)
        col = int(lon * km_per_deg_lon // cell_km)
        buckets[(row, col)].append((lat, lon))

    zones = []
    for i, (_key, pts) in enumerate(sorted(buckets.items())):
        zones.append({
            "zone_id": f"Z{i:03d}",
            "lat": sum(p[0] for p in pts) / len(pts),
            "lon": sum(p[1] for p in pts) / len(pts),
            "junction_nodes": len(pts),
            "mass": float(len(pts)),   # arterial access proxy
        })
    return zones


def haversine_km(a: dict, b: dict) -> float:
    p1, p2 = math.radians(a["lat"]), math.radians(b["lat"])
    dphi = p2 - p1
    dlmb = math.radians(b["lon"] - a["lon"])
    h = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * EARTH_R_KM * math.asin(math.sqrt(h))


# ---------------------------------------------------------------------------
# Gravity model
# ---------------------------------------------------------------------------

# Distance decay, trips/km. Raise it for a more local city, lower it for more
# cross-town travel. Check the intrazonal share the script prints after changing.
BETA = 0.2


def trip_weight(mass_i: float, mass_j: float, distance_km: float) -> float:
    """Unnormalised trip volume between an origin and a destination zone.

    Called for every ordered zone pair, including a zone with itself, where
    `distance_km` is the intrazonal distance (roughly half a cell width) rather
    than zero. Return a non-negative number; the caller scales the whole matrix
    to the required trip total afterwards, so only the *relative* values matter.

    Exponential deterrence: well-behaved at short distances, unlike a power law
    which would blow up on the intrazonal term.
    """
    return mass_i * mass_j * math.exp(-BETA * distance_km)


def build_matrix(zones: list[dict], cell_km: float) -> dict[tuple[str, str], float]:
    intrazonal_km = 0.5 * cell_km
    weights: dict[tuple[str, str], float] = {}
    for a in zones:
        for b in zones:
            d = intrazonal_km if a is b else haversine_km(a, b)
            w = trip_weight(a["mass"], b["mass"], d)
            if w > 0:
                weights[(a["zone_id"], b["zone_id"])] = float(w)
    return weights


def scale_to_total(weights: dict[tuple[str, str], float], total: int) -> dict[tuple[str, str], int]:
    """Scale to the trip total and round so the integers sum to it exactly.

    Naive rounding of ~5000 cells drifts by hundreds of trips, so the remainder
    is distributed by largest fractional part.
    """
    pool = sum(weights.values())
    if pool <= 0:
        raise ValueError("all trip weights are zero - check trip_weight()")

    exact = {k: v / pool * total for k, v in weights.items()}
    out = {k: int(v) for k, v in exact.items()}
    shortfall = total - sum(out.values())
    for k, _ in sorted(exact.items(), key=lambda kv: kv[1] - int(kv[1]), reverse=True)[:shortfall]:
        out[k] += 1
    return out


# ---------------------------------------------------------------------------

def main() -> None:
    ap = argparse.ArgumentParser(description="Synthesise an OD matrix from an OSM map")
    ap.add_argument("--osm", type=Path, default=Path("data/kathmandu.osm.xml"))
    ap.add_argument("--out-dir", type=Path, default=Path("data"))
    ap.add_argument("--cell-km", type=float, default=2.0, help="zone grid size")
    ap.add_argument("--total-trips", type=int, default=2_600_000)
    args = ap.parse_args()

    points = load_junctions(args.osm)
    print(f"junction nodes:     {len(points)}")

    zones = build_zones(points, args.cell_km)
    print(f"zones ({args.cell_km} km): {len(zones)}")

    weights = build_matrix(zones, args.cell_km)
    matrix = scale_to_total(weights, args.total_trips)
    nonzero = sum(1 for v in matrix.values() if v > 0)
    print(f"OD pairs:           {len(matrix)} ({nonzero} with demand)")
    print(f"total trips:        {sum(matrix.values()):,}")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    with (args.out_dir / "zones.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["zone_id", "lat", "lon", "junction_nodes", "mass"])
        w.writeheader()
        for z in zones:
            w.writerow({**z, "lat": round(z["lat"], 6), "lon": round(z["lon"], 6)})

    with (args.out_dir / "od_matrix.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["origin_id", "dest_id", "demand"])
        for (o, d), n in sorted(matrix.items()):
            if n > 0:
                w.writerow([o, d, n])

    intra = sum(n for (o, d), n in matrix.items() if o == d)
    print(f"intrazonal share:   {intra / sum(matrix.values()):.1%}")
    print(f"wrote {args.out_dir/'zones.csv'} and {args.out_dir/'od_matrix.csv'}")


if __name__ == "__main__":
    main()
