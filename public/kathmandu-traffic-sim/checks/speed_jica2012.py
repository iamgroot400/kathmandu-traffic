#!/usr/bin/env python3
"""Model link speeds against the JICA 2012 travel speed survey (weekday, Table 6.2.10,
vol. 2 p. 6-30; transcribed in data/jica2012/route_speeds_2011.csv). The calibration
target for road speeds; the intersection counts stay validation-only.

Model speed for a road class = total length / total travel time over its links (the
harmonic mean a probe car would see), travel times from a link dump with tt_s.
Classes: Ring Road (links named Ring Road, route 1); all other roads inside the Ring
Road, against the city-side routes 2, 5, 6, 7, 9 (approximate: those routes also run
outside the Ring Road, where they are faster).

    .venv/Scripts/python.exe checks/speed_jica2012.py results/linkvol_jica_net_minor_h2.csv [morning|evening]
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
RING_BOX = (27.665, 27.745, 85.282, 85.360)    # lat/lon box just inside the Ring Road


def observed(period):
    rows = list(csv.DictReader(open(ROOT / "data/jica2012/route_speeds_2011.csv", encoding="utf-8")))
    mean = lambda rs: sum(float(r[f"{period}_kmh"]) for r in rs) / len(rs)
    return (mean([r for r in rows if r["route"] == "1"]),
            mean([r for r in rows if r["route"] in {"2", "5", "6", "7", "9"}]))


def model(dump, minor_file=None):
    minor = set(Path(minor_file).read_text().split()) if minor_file else set()
    acc = {"ring": [0.0, 0.0], "inner": [0.0, 0.0], "minor": [0.0, 0.0]}
    for r in csv.DictReader(open(dump, encoding="utf-8")):
        L, tt = float(r["length_m"]), float(r["tt_s"])
        lat = (float(r["start_lat"]) + float(r["end_lat"])) / 2
        lon = (float(r["start_lon"]) + float(r["end_lon"])) / 2
        inside = RING_BOX[0] < lat < RING_BOX[1] and RING_BOX[2] < lon < RING_BOX[3]
        if "Ring" in r["link"]:
            k = "ring"
        elif r["link"].rsplit("-", 1)[-1] in minor:
            k = "minor"
        elif inside:
            k = "inner"
        else:
            continue
        acc[k][0] += L
        acc[k][1] += tt
    return {k: (L / tt * 3.6 if tt else float("nan")) for k, (L, tt) in acc.items()}


def main(dump, period="morning", minor_file="data/jica_net/minor_ways.txt"):
    ring_o, inner_o = observed(period)
    m = model(dump, minor_file if Path(minor_file).exists() else None)
    print(f"weekday {period}      observed   model")
    print(f"Ring Road            {ring_o:6.1f}   {m['ring']:6.1f} km/h")
    print(f"inner main roads     {inner_o:6.1f}   {m['inner']:6.1f} km/h  (observed: routes 2,5,6,7,9, approx.)")
    print(f"side streets           n/a    {m['minor']:6.1f} km/h")


if __name__ == "__main__":
    main(*sys.argv[1:])
