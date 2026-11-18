#!/usr/bin/env python3
"""Import the road network into UXsim and cache it as CSV.

UXsim's OSM importer downloads from Overpass rather than reading a local file, so
the network is imported once here and written to CSV. Everything downstream loads
those CSVs, which keeps runs reproducible and offline - re-running this script is
the only step that depends on OSM being reachable or unchanged.

    python scripts/build_network.py

Outputs:
    data/network_nodes.csv
    data/network_links.csv
"""
from __future__ import annotations

import argparse
import csv
from pathlib import Path

from uxsim.OSMImporter import OSMImporter

# Matches data/kathmandu.osm.xml: Ring Road and city core, arterials only.
BBOX = {"north": 27.750, "south": 27.635, "east": 85.392, "west": 85.268}
ROAD_FILTER = '["highway"~"trunk|primary|secondary"]'


def main() -> None:
    ap = argparse.ArgumentParser(description="Import the OSM network for UXsim")
    ap.add_argument("--north", type=float, default=BBOX["north"])
    ap.add_argument("--south", type=float, default=BBOX["south"])
    ap.add_argument("--east", type=float, default=BBOX["east"])
    ap.add_argument("--west", type=float, default=BBOX["west"])
    # ~55 m. Merges genuinely coincident junction nodes without collapsing real
    # topology; UXsim's own examples use 0.005 (~550 m), which is far too coarse here.
    ap.add_argument("--merge-threshold", type=float, default=0.0005)
    ap.add_argument("--out-dir", type=Path, default=Path("data"))
    # e.g. '["highway"~"trunk|primary|secondary|tertiary"]' for the JICA-demand network (D35)
    ap.add_argument("--road-filter", default=ROAD_FILTER)
    args = ap.parse_args()

    nodes, links = OSMImporter.import_osm_data(
        north=args.north, south=args.south, east=args.east, west=args.west,
        custom_filter=args.road_filter,
    )
    print(f"imported:     {len(nodes)} nodes, {len(links)} links")
    print(f"node sample:  {nodes[0]}")
    print(f"link sample:  {links[0]}")

    nodes, links = OSMImporter.osm_network_postprocessing(
        nodes, links, node_merge_threshold=args.merge_threshold, node_merge_iteration=5,
    )
    print(f"postprocessed:{len(nodes)} nodes, {len(links)} links")

    args.out_dir.mkdir(parents=True, exist_ok=True)
    for name, rows in (("network_nodes", nodes), ("network_links", links)):
        path = args.out_dir / f"{name}.csv"
        with path.open("w", newline="", encoding="utf-8") as fh:
            csv.writer(fh).writerows(rows)
        print(f"wrote {path}  ({len(rows)} rows)")


if __name__ == "__main__":
    main()
