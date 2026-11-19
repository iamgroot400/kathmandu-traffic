#!/usr/bin/env python3
"""GEH against the JICA 2011-12 intersection counts (data/jica2012/
intersection_counts_2011.csv, transcribed from the turning-movement diagrams in the survey
report's appendix), using a saved link-volume dump. No simulation.

Observed = mean of the AM and PM peak-hour entering volume (veh/h) x the PCU factor.
Model = entering volume at the intersection's OSM node in the measured hour.
Nodes were fixed by road name and location before any volume was compared.

    python checks/geh_jica2012.py <dump under results/> <output name> [pcu factor]
"""
import csv
import math
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
PCU_FACTOR = 0.786   # average PCU per vehicle in JICA's 2011 vehicle OD table

# entering volume is summed at these OSM nodes (one per counted intersection)
NODES = {"Gausala": "4879891022", "Chabahil": "3084565718", "Balaju": "31303568",
         "Koteshwor": "6275508137", "Kalanki": "10921097915", "Kalimati": "360831200",
         "Thapathali": "977642662", "Old Baneshwor": "1882601483", "New Baneshwor": "313735983"}


def geh(model: float, observed: float) -> float:
    if model + observed <= 0:
        return 0.0
    return math.sqrt((model - observed) ** 2 / ((model + observed) / 2))


def cluster_group(rows, node, radius_m):
    """`node` plus every node within radius_m of it: OSM often draws one large junction as several nodes."""
    pos = {}
    for r in rows:
        pos[r["start"]] = (float(r["start_lat"]), float(r["start_lon"]))
        pos[r["end"]] = (float(r["end_lat"]), float(r["end_lon"]))
    p = pos[node]
    dist = lambda q: math.hypot(q[0] - p[0], (q[1] - p[1]) * math.cos(math.radians(p[0]))) * 111000  # noqa: E731
    return {n for n, q in pos.items() if dist(q) <= radius_m} | {node}


def cluster_entering(rows, node, radius_m):
    """Volume entering the node's group from outside it; radius 0 gives the single node's entering volume."""
    group = cluster_group(rows, node, radius_m)
    return sum(float(r["vol_pcu_h"]) for r in rows if r["end"] in group and r["start"] not in group)


def main(dump="linkvol_base.csv", out_name="geh_jica2012.csv", pcu=PCU_FACTOR, radius_m=0):
    """Model vs observed peak-hour entering volume at the nine counted intersections."""
    pcu, radius_m = float(pcu), float(radius_m)
    rows = list(csv.DictReader(open(ROOT / "results" / dump, encoding="utf-8")))
    entering = {}
    for r in rows:
        entering[r["end"]] = entering.get(r["end"], 0.0) + float(r["vol_pcu_h"])
    if radius_m:
        entering = {n: cluster_entering(rows, n, radius_m) for n in NODES.values()}

    obs_rows = [r for r in csv.DictReader(open(ROOT / "data/jica2012/intersection_counts_2011.csv", encoding="utf-8"))
                if r["am_entering_veh_h"]]
    print(f"{'intersection':<14}{'obs veh/h':>10}{'obs pcu':>9}{'model':>8}{'GEH':>7}  node")
    passes = 0
    out = []
    for r in obs_rows:
        name = r["intersection"]
        veh = (float(r["am_entering_veh_h"]) + float(r["pm_entering_veh_h"])) / 2
        o = veh * pcu
        n = NODES[name]
        m = entering.get(n, 0.0)
        g = geh(m, o)
        passes += g < 5
        print(f"{name:<14}{veh:>10.0f}{o:>9.0f}{m:>8.0f}{g:>7.1f}  {n}")
        out.append({"intersection": name, "observed_veh_h": round(veh), "observed_pcu_h": round(o),
                    "model_pcu_h": round(m), "geh": round(g, 2), "pass": g < 5, "node": n})
    print(f"\nGEH < 5: {passes}/{len(obs_rows)}   model/observed total: "
          f"{sum(x['model_pcu_h'] for x in out) / sum(x['observed_pcu_h'] for x in out):.0%}")
    with open(ROOT / "results" / out_name, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
