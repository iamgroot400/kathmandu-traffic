#!/usr/bin/env python3
"""Fetch the OSM tags that set road width and direction (highway, lanes, oneway, junction) for every
way in data/jica_net/network_links.csv, once, from Overpass. Needs internet; the result is cached.

UXsim's OSM importer reads the `lanes` tag as lanes per direction, but on a two-way road OSM's
`lanes` counts both directions, so the importer doubled every tagged two-way road
(run_baseline.py --osm-way-tags corrects it from this file).

    python scripts/build_way_tags.py   ->  data/jica_net/osm_way_tags.csv
"""
import csv
import json
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "jica_net" / "osm_way_tags.csv"
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]
KEYS = ["highway", "lanes", "lanes:forward", "lanes:backward", "oneway", "junction"]

ids = sorted({r[0].rsplit("-", 1)[-1] for r in csv.reader(open(ROOT / "data/jica_net/network_links.csv", encoding="utf-8"))})
tags = {}
for i in range(0, len(ids), 400):
    q = f"[out:json][timeout:120];way(id:{','.join(ids[i:i + 400])});out tags;"
    for url in OVERPASS * 2:
        try:
            req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                                         headers={"User-Agent": "kathmandu-traffic-research"})
            with urllib.request.urlopen(req, timeout=180) as r:
                for e in json.load(r)["elements"]:
                    tags[str(e["id"])] = e.get("tags", {})
            break
        except OSError as exc:
            print(f"{url}: {exc}; retrying")
            time.sleep(10)
    else:
        raise SystemExit("Overpass unreachable")
with open(OUT, "w", newline="", encoding="utf-8") as fh:
    w = csv.writer(fh)
    w.writerow(["way"] + KEYS)
    for i in ids:
        w.writerow([i] + [tags.get(i, {}).get(k, "") for k in KEYS])
print(f"wrote {OUT}: {len(ids)} ways, {len(tags)} found in OSM today")
