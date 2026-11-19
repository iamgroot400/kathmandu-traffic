#!/usr/bin/env python3
"""Fetch OpenStreetMap pedestrian streets (highway=pedestrian; living_street is left out: in Kathmandu it also tags residential lanes beside main roads) in the
network box, once, from Overpass, as points every ~20 m along each way. Used by
run_baseline.py --pedestrian-friction to mark streets where walkers share or surround the roadway
(Basantapur, Thamel, Ason). Needs internet; the result is cached.

    python scripts/build_pedestrian_ways.py   ->  data/jica_net/osm_pedestrian_points.json  ([lat, lon] list)
"""
import json
import math
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "data" / "jica_net" / "osm_pedestrian_points.json"
BBOX = (27.635, 85.268, 27.750, 85.392)   # south, west, north, east: as scripts/build_network.py
OVERPASS = ["https://overpass-api.de/api/interpreter", "https://overpass.kumi.systems/api/interpreter"]

q = f'[out:json][timeout:180];way["highway"~"^pedestrian$"]{BBOX};out geom;'
for url in OVERPASS * 3:
    try:
        req = urllib.request.Request(url, data=urllib.parse.urlencode({"data": q}).encode(),
                                     headers={"User-Agent": "kathmandu-traffic-research"})
        with urllib.request.urlopen(req, timeout=240) as r:
            ways = json.load(r)["elements"]
        break
    except OSError as exc:
        print(f"{url}: {exc}; retrying")
        time.sleep(15)
else:
    raise SystemExit("Overpass unreachable")

pts = []
for w in ways:
    g = w.get("geometry", [])
    for a, b in zip(g, g[1:]):
        d = math.hypot(b["lat"] - a["lat"], (b["lon"] - a["lon"]) * math.cos(math.radians(a["lat"]))) * 111000
        n = max(1, int(d // 20))
        pts += [[round(a["lat"] + (b["lat"] - a["lat"]) * i / n, 7), round(a["lon"] + (b["lon"] - a["lon"]) * i / n, 7)]
                for i in range(n)]
    if g:
        pts.append([g[-1]["lat"], g[-1]["lon"]])
OUT.write_text(json.dumps(pts))
print(f"wrote {OUT}: {len(ways)} ways, {len(pts)} points")
