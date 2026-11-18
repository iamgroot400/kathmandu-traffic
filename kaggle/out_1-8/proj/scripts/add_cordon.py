#!/usr/bin/env python3
"""Add external (cordon) demand entering the study area from outside.

The gravity matrix generates trips only between zones *inside* the bounding box,
so junctions whose congestion is driven by traffic arriving from outside the area
always look empty. The hotspot check caught this: Kalanki ranked 138th of 233 and
Chabahil 131st, when both are among Kathmandu's worst in reality - Kalanki takes
everything from Thankot and the Prithvi Highway, Chabahil from the north-east.

This adds cordon zones at the network's boundary and loads them with trips in and
out of the study area, so entry-point junctions carry the traffic that actually
makes them congest.

    python scripts/add_cordon.py --external-share 0.25

Writes data/zones_cordon.csv and data/od_matrix_cordon.csv, leaving the originals
untouched. Use with:

    python scripts/run_baseline.py --zones-file data/zones_cordon.csv \\
                                   --od-file data/od_matrix_cordon.csv
"""
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path


def load_nodes(path: Path):
    with path.open(encoding="utf-8") as fh:
        return {r[0]: (float(r[2]), float(r[1])) for r in csv.reader(fh) if r}  # id -> lat, lon


def load_links(path: Path):
    with path.open(encoding="utf-8") as fh:
        return [(r[1], r[2], int(float(r[3]))) for r in csv.reader(fh) if r]  # from, to, lanes


def find_cordon_nodes(nodes: dict, links: list, margin_km: float, top_n: int):
    """The highest-capacity boundary node in each compass sector.

    netconvert leaves no dangling stubs, so there is no explicit 'edge of network'
    marker. Instead: take nodes within `margin_km` of the bounding box and rank by
    the lane capacity meeting there - a highway crossing the boundary has more lanes
    than a lane does.

    Selection is per compass sector rather than globally top-N. Boundary nodes tend
    to tie on lane count, so a global ranking breaks ties arbitrarily and returns a
    spatially clustered set - the first attempt put all eight entry points in the
    north and west, leaving the south and east as blind as before.
    """
    lats = [p[0] for p in nodes.values()]
    lons = [p[1] for p in nodes.values()]
    lat_lo, lat_hi, lon_lo, lon_hi = min(lats), max(lats), min(lons), max(lons)
    dlat = margin_km / 111.32
    dlon = margin_km / (111.32 * math.cos(math.radians(sum(lats) / len(lats))))

    lanes_at = defaultdict(int)
    for a, b, lanes in links:
        lanes_at[a] += lanes
        lanes_at[b] += lanes

    mid_lat = (lat_lo + lat_hi) / 2.0
    mid_lon = (lon_lo + lon_hi) / 2.0
    cos_lat = math.cos(math.radians(mid_lat))

    # best candidate per sector, so entry points ring the study area
    best_in_sector: dict[int, tuple] = {}
    for nid, (lat, lon) in nodes.items():
        near = (lat - lat_lo < dlat or lat_hi - lat < dlat
                or lon - lon_lo < dlon or lon_hi - lon < dlon)
        if not near:
            continue
        bearing = math.degrees(math.atan2((lon - mid_lon) * cos_lat, lat - mid_lat)) % 360
        sector = int(bearing // (360 / top_n))
        # tie-break on distance from centre: the outermost node is the true entry
        dist = math.hypot((lat - mid_lat), (lon - mid_lon) * cos_lat)
        key = (lanes_at[nid], dist)
        if sector not in best_in_sector or key > best_in_sector[sector][0]:
            best_in_sector[sector] = (key, (lanes_at[nid], nid, lat, lon))

    found = [v[1] for v in best_in_sector.values()]
    if len(found) < top_n:
        print(f"  note: only {len(found)} of {top_n} sectors have a boundary node")
    return found


def main() -> None:
    ap = argparse.ArgumentParser(description="Add cordon (external) demand")
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--margin-km", type=float, default=1.5,
                    help="how close to the bounding box counts as a boundary node")
    ap.add_argument("--cordons", type=int, default=8, help="number of entry points")
    # [SURVEY] External trips as a share of internal demand. Kathmandu valley takes
    # substantial highway traffic from Thankot, Bhaktapur and the north-east, but the
    # real figure needs a cordon count at the valley entries.
    ap.add_argument("--external-share", type=float, default=0.25)
    ap.add_argument("--through-share", type=float, default=0.30,
                    help="of external trips, the share passing straight through")
    args = ap.parse_args()

    nodes = load_nodes(args.data / "network_nodes.csv")
    links = load_links(args.data / "network_links.csv")
    cordons = find_cordon_nodes(nodes, links, args.margin_km, args.cordons)
    if len(cordons) < 2:
        raise SystemExit("found fewer than 2 boundary nodes - widen --margin-km")

    zones = list(csv.DictReader((args.data / "zones.csv").open(encoding="utf-8")))
    od = list(csv.DictReader((args.data / "od_matrix.csv").open(encoding="utf-8")))
    internal_total = sum(int(r["demand"]) for r in od)
    external_total = internal_total * args.external_share

    print(f"internal demand: {internal_total:,} trips")
    print(f"cordon zones:    {len(cordons)} entry points")
    for i, (lanes, nid, lat, lon) in enumerate(cordons):
        print(f"  C{i:03d}  node {nid:>12}  {lanes:>3} lanes  ({lat:.4f}, {lon:.4f})")

    # Each entry point's share of external traffic is proportional to its road capacity.
    lane_total = sum(c[0] for c in cordons) or 1
    cordon_zones = []
    for i, (lanes, nid, lat, lon) in enumerate(cordons):
        cordon_zones.append({"zone_id": f"C{i:03d}", "lat": round(lat, 6),
                             "lon": round(lon, 6), "junction_nodes": 1,
                             "mass": round(lanes / lane_total, 5)})

    # Internal zones attract external trips in proportion to their mass.
    zone_mass = {z["zone_id"]: float(z["mass"]) for z in zones}
    mass_total = sum(zone_mass.values()) or 1.0

    new_rows = []
    through = external_total * args.through_share
    inbound = (external_total - through) / 2.0      # split evenly in and out

    for cz in cordon_zones:
        share = cz["mass"]
        for zid, m in zone_mass.items():
            v_in = inbound * share * m / mass_total
            v_out = inbound * share * m / mass_total
            if v_in >= 1:
                new_rows.append({"origin_id": cz["zone_id"], "dest_id": zid,
                                 "demand": int(v_in)})
            if v_out >= 1:
                new_rows.append({"origin_id": zid, "dest_id": cz["zone_id"],
                                 "demand": int(v_out)})
        # through traffic: entry point to every other entry point
        others = [c for c in cordon_zones if c["zone_id"] != cz["zone_id"]]
        other_mass = sum(c["mass"] for c in others) or 1.0
        for oc in others:
            v = through * share * oc["mass"] / other_mass
            if v >= 1:
                new_rows.append({"origin_id": cz["zone_id"], "dest_id": oc["zone_id"],
                                 "demand": int(v)})

    out_zones = args.data / "zones_cordon.csv"
    with out_zones.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(zones[0]))
        w.writeheader()
        w.writerows(zones)
        for cz in cordon_zones:
            w.writerow(cz)

    out_od = args.data / "od_matrix_cordon.csv"
    with out_od.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=["origin_id", "dest_id", "demand"])
        w.writeheader()
        w.writerows(od)
        w.writerows(new_rows)

    added = sum(r["demand"] for r in new_rows)
    print(f"\nadded {added:,} external trips ({added/internal_total:.1%} of internal) "
          f"over {len(new_rows)} OD pairs")
    print(f"wrote {out_zones}")
    print(f"wrote {out_od}")
    print("\nOriginals untouched. Run with --zones-file/--od-file to use these.")


if __name__ == "__main__":
    main()
