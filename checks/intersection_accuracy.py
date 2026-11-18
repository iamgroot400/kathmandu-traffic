#!/usr/bin/env python3
"""GEH at the six observed intersections under different matching rules and demand
variants, from link-volume dumps (scripts/dump_link_volumes.py). No simulation here.

Matching rules (fixed in lab/experiments/E11.md before any of this was run):
  nearest   the single model node closest to the landmark (what geh_check.py does)
  cluster   every node within R of the landmark is one intersection; its entering
            volume is the flow on links that start outside the cluster and end inside
            it. R = 100 m is the pre-specified value (about twice the 55 m node-merge
            threshold); 150 m is printed as a sensitivity only.

    python checks/intersection_accuracy.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from geh_check import OBSERVED, geh  # noqa: E402
from validate_hotspots import haversine_km  # noqa: E402


def load(name):
    p = ROOT / "results" / name
    if not p.exists():
        return None
    rows = list(csv.DictReader(open(p, encoding="utf-8")))
    for r in rows:
        r["vol"] = float(r["vol_pcu_h"])
    return rows


def average(a, b):
    vb = {r["link"]: r["vol"] for r in b}
    return [{**r, "vol": (r["vol"] + vb.get(r["link"], 0.0)) / 2} for r in a]


def entering(rows, lat, lon, radius_km):
    nodes = {}
    for r in rows:
        nodes[r["start"]] = (float(r["start_lat"]), float(r["start_lon"]))
        nodes[r["end"]] = (float(r["end_lat"]), float(r["end_lon"]))
    dist = {n: haversine_km(lat, lon, la, lo) for n, (la, lo) in nodes.items()}
    if radius_km is None:
        inside = {min(dist, key=dist.get)}
    else:
        inside = {n for n, d in dist.items() if d <= radius_km} or {min(dist, key=dist.get)}
    return sum(r["vol"] for r in rows if r["end"] in inside and r["start"] not in inside), len(inside)


def table(label, rows):
    print(f"\n{label}")
    print(f"  {'landmark':<14}{'observed':>9} | {'nearest':>8} {'GEH':>6} | {'100 m':>8} {'GEH':>6} {'nodes':>5} | {'150 m':>8} {'GEH':>6}")
    passes = [0, 0, 0]
    for name, obs in OBSERVED.items():
        o = obs["volume_pcu_h"]
        cells = []
        for i, r in enumerate((None, 0.10, 0.15)):
            v, n = entering(rows, obs["lat"], obs["lon"], r)
            g = geh(v, o)
            passes[i] += g < 5
            cells.append((v, g, n))
        print(f"  {name:<14}{o:>9.0f} | {cells[0][0]:>8.0f} {cells[0][1]:>6.1f} | {cells[1][0]:>8.0f} {cells[1][1]:>6.1f} "
              f"{cells[1][2]:>5} | {cells[2][0]:>8.0f} {cells[2][1]:>6.1f}")
    print(f"  GEH < 5:  nearest {passes[0]}/6   100 m {passes[1]}/6   150 m {passes[2]}/6")


base, am, pm, cordon = (load(f"linkvol_{n}.csv") for n in ("base", "am", "pm", "cordon"))
if base:
    table("Baseline demand (symmetric gravity model)", base)
if am and pm:
    table("Directional demand, AM and PM runs averaged (the JICA figures are AM/PM averages)", average(am, pm))
if cordon:
    table("With external (cordon) demand, shares as guessed in add_cordon.py", cordon)
