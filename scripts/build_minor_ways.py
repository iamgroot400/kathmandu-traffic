#!/usr/bin/env python3
"""List the side streets: OSM ways in the arterial + tertiary network that are not in the
main-road network. run_baseline.py builds these as one-lane, reduced-capacity links.

    python scripts/build_minor_ways.py   # writes data/jica_net/minor_ways.txt
"""
import csv
from pathlib import Path

DATA = Path(__file__).parent.parent / "data"
way = lambda link_id: link_id.rsplit("-", 1)[-1]   # link ids are "<name>-<osm way id>"

main_roads = {way(r[0]) for r in csv.reader(open(DATA / "network_links.csv", encoding="utf-8"))}
full = {way(r[0]) for r in csv.reader(open(DATA / "jica_net" / "network_links.csv", encoding="utf-8"))}
minor = sorted(full - main_roads)
(DATA / "jica_net" / "minor_ways.txt").write_text("\n".join(minor) + "\n", encoding="utf-8")
print(f"{len(minor)} side-street ways of {len(full)}")
