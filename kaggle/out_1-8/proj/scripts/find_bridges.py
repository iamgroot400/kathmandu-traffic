#!/usr/bin/env python3
"""Flag which links in the simulated network are physical bridges.

UXsim's OSM importer (OSMImporter.import_osm_data) only keeps [name, from, to,
lanes, maxspeed] from each OSM way - it drops every other tag, including
`bridge`. This script re-reads the raw OSM extract directly (the same file
build_network.py's custom_filter was matched against) to recover that tag,
then locates each bridge way in the already-built, already-merged network.

Exact node-id matching does not work here: build_network.py's node-merge step
(55 m threshold, 5 iterations) collapses short links, and about half of this
area's bridge ways span under 55 m (checked directly against the raw extract),
so many bridges have had both endpoints merged into one surviving node and no
longer exist as a distinct link at all - the bridge is now zero-length,
internal to an intersection. This is reported explicitly below rather than
silently matching nothing.

For each bridge way, both endpoints are snapped to their nearest surviving
simulated node (nearest_node from run_baseline.py); if the two snapped
endpoints differ and a live link connects them, that link is the bridge.

    python scripts/find_bridges.py

Output: data/bridges.csv (link name, u, v, lanes, is_ring_road)
"""
from __future__ import annotations

import argparse
import csv
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import nearest_node  # noqa: E402

RING_ROAD_MARKERS = ("ring road", "ringroad", "चक्रपथ")
# nearest_node's snap distance for a genuinely absorbed bridge is small (it
# collapsed into an intersection a few metres away); beyond this, treat the
# raw extract's coordinates as not corresponding to anything in our merged
# network rather than force a match.
SNAP_TOLERANCE_KM = 0.15


def ring_road_way(name: str | None) -> bool:
    if not name:
        return False
    low = name.lower()
    return any(m in low for m in RING_ROAD_MARKERS)


def bridge_ways(osm_xml: Path):
    """(first_node_coords, last_node_coords, is_ring_road, name) per bridge way."""
    root = ET.parse(osm_xml).getroot()
    node_coords = {}
    for n in root.findall("node"):
        node_coords[int(n.get("id"))] = (float(n.get("lon")), float(n.get("lat")))

    out = []
    for way in root.findall("way"):
        tags = {t.get("k"): t.get("v") for t in way.findall("tag")}
        if tags.get("bridge") != "yes" or tags.get("highway") not in (
            "trunk", "primary", "secondary",
        ):
            continue
        refs = [int(nd.get("ref")) for nd in way.findall("nd")]
        if refs[0] not in node_coords or refs[-1] not in node_coords:
            continue
        name = tags.get("name") or tags.get("alt_name") or ""
        is_rr = ring_road_way(tags.get("name")) or ring_road_way(tags.get("alt_name"))
        out.append((node_coords[refs[0]], node_coords[refs[-1]], is_rr, name))
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="Identify bridge links, flag Ring Road ones")
    ap.add_argument("--osm-xml", type=Path, default=Path("data/kathmandu.osm.xml"))
    ap.add_argument("--nodes", type=Path, default=Path("data/network_nodes.csv"))
    ap.add_argument("--links", type=Path, default=Path("data/network_links.csv"))
    ap.add_argument("--out", type=Path, default=Path("data/bridges.csv"))
    args = ap.parse_args()

    with args.nodes.open(encoding="utf-8") as fh:
        node_coords = {int(r[0]): (float(r[1]), float(r[2])) for r in csv.reader(fh) if r}
    with args.links.open(encoding="utf-8") as fh:
        link_rows = [r for r in csv.reader(fh) if r]
    live_links = {(int(u), int(v)): (name, lanes) for name, u, v, lanes, *_ in link_rows
                  for u, v in [(u, v)]}
    # also index the reverse direction, since a bridge can be traversed either way
    live_lookup = {}
    for name, u, v, lanes, *_ in link_rows:
        u, v = int(u), int(v)
        live_lookup[(u, v)] = (name, lanes)

    matched, absorbed, unresolved = [], 0, 0
    for (lon1, lat1), (lon2, lat2), is_rr, way_name in bridge_ways(args.osm_xml):
        n1, d1 = nearest_node(lat1, lon1, node_coords)
        n2, d2 = nearest_node(lat2, lon2, node_coords)
        if d1 > SNAP_TOLERANCE_KM or d2 > SNAP_TOLERANCE_KM:
            unresolved += 1
            continue
        if n1 == n2:
            absorbed += 1
            continue
        hit = live_lookup.get((n1, n2)) or live_lookup.get((n2, n1))
        if hit:
            matched.append([hit[0], n1, n2, hit[1], is_rr, way_name])
        else:
            unresolved += 1

    # several raw OSM way fragments (e.g. a bridge split by a tag change
    # partway across) can resolve to the same already-merged simulated link
    by_link: dict[tuple, list] = {}
    for name, u, v, lanes, is_rr, way_name in matched:
        key = (name, u, v)
        row = by_link.setdefault(key, [name, u, v, lanes, False, way_name])
        row[4] = row[4] or is_rr
    matched = list(by_link.values())

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["link_name", "u", "v", "lanes", "is_ring_road", "osm_way_name"])
        w.writerows(matched)

    total = len(matched) + absorbed + unresolved
    ring_road = sum(1 for m in matched if m[4])
    print(f"{total} bridge ways found in the raw OSM extract (trunk/primary/secondary)")
    print(f"  {len(matched)} resolved to a distinct simulated link ({ring_road} on the Ring Road)")
    print(f"  {absorbed} fully absorbed into a single intersection node by the node-merge step")
    print(f"  {unresolved} could not be snapped within {SNAP_TOLERANCE_KM*1000:.0f} m")
    print(f"wrote {args.out}")


if __name__ == "__main__":
    main()
