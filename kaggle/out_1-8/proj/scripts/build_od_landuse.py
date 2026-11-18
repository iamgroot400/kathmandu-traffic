#!/usr/bin/env python3
"""Alternative demand hypothesis: trips are attracted to activity, not to junctions.

The base OD (build_od.py) uses junction count as both origin and destination mass.
This variant keeps junction count as the origin mass and replaces the destination
mass with the number of OSM activity points (amenity / shop / office) nearest each
zone. Same zones, same gravity function, same trip total, so no recalibration is
needed and nothing is tuned against the validation counts (D23's rule). Whether it
validates better is decided only by geh_check.py / validate_hotspots.py afterwards.

    python scripts/build_od_landuse.py          # writes data/od_matrix_landuse.csv
"""
from __future__ import annotations

import argparse
import csv
import json
import urllib.parse
import urllib.request
from collections import Counter
from pathlib import Path

from build_od import build_matrix, haversine_km, scale_to_total, trip_weight  # noqa: F401
from build_network import BBOX

OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]


def fetch_pois(cache: Path) -> list[tuple[float, float]]:
    if cache.exists():
        return [tuple(p) for p in json.loads(cache.read_text(encoding="utf-8"))]
    box = f'({BBOX["south"]},{BBOX["west"]},{BBOX["north"]},{BBOX["east"]})'
    q = f'[out:json][timeout:180];(nwr["amenity"]{box};nwr["shop"]{box};nwr["office"]{box};);out center;'
    for attempt, url in enumerate(OVERPASS * 2):     # public servers 502 under load; try the mirror
        req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                                     headers={"User-Agent": "kathmandu-traffic-research"})
        try:
            with urllib.request.urlopen(req, timeout=240) as r:
                els = json.load(r)["elements"]
            break
        except OSError as exc:
            print(f"overpass attempt {attempt + 1} failed: {exc}")
    else:
        raise SystemExit("could not reach Overpass")
    pts = []
    for e in els:
        c = e if "lat" in e else e.get("center")
        if c:
            pts.append((c["lat"], c["lon"]))
    cache.write_text(json.dumps(pts), encoding="utf-8")
    return pts


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--data", type=Path, default=Path("data"))
    ap.add_argument("--cell-km", type=float, default=1.0)
    ap.add_argument("--total-trips", type=int, default=260_000)
    args = ap.parse_args()

    with (args.data / "zones.csv").open(encoding="utf-8") as fh:
        zones = [{"zone_id": r["zone_id"], "lat": float(r["lat"]), "lon": float(r["lon"]),
                  "mass": float(r["mass"])} for r in csv.DictReader(fh)]
    pois = fetch_pois(args.data / "kathmandu_pois.json")
    counts = Counter()
    for lat, lon in pois:
        p = {"lat": lat, "lon": lon}
        z = min(zones, key=lambda z: haversine_km(z, p))
        if haversine_km(z, p) <= args.cell_km:      # ignore activity far from any modeled zone
            counts[z["zone_id"]] += 1
    print(f"POIs: {len(pois)}, assigned: {sum(counts.values())}, "
          f"zones with activity: {len(counts)}/{len(zones)}")

    weights = {}
    for a in zones:
        for b in zones:
            d = 0.5 * args.cell_km if a is b else haversine_km(a, b)
            w = trip_weight(a["mass"], counts[b["zone_id"]], d)
            if w > 0:
                weights[(a["zone_id"], b["zone_id"])] = w
    matrix = scale_to_total(weights, args.total_trips)
    assert sum(matrix.values()) == args.total_trips

    out = args.data / "od_matrix_landuse.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["origin_id", "dest_id", "demand"])
        for (o, d), n in sorted(matrix.items()):
            w.writerow([o, d, n])
    top = ", ".join(f"{z}:{c}" for z, c in counts.most_common(5))
    print(f"wrote {out}  ({sum(matrix.values()):,} trips); busiest destination zones: {top}")


if __name__ == "__main__":
    main()
