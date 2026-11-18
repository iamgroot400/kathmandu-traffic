#!/usr/bin/env python3
"""Peak-hour demand from the JICA 2011 surveys, attached to a network.

1. Vehicle OD, 9 large zones x 4 vehicle types, PCU/day (data/jica_od/vtod_2011.csv).
2. Split to the 51 small zones in proportion to the person-trip OD
   (data/jica_od/ptod_2011.csv): v_ij = VT_IJ * PT_ij / PT_IJ.
3. Peak hour = K x daily (K = 0.10, JICA/DoR 2024 p. 6-7, 2019 count survey).
4. Each zone loads at up to --sub junctions of its own catchment (the network nodes
   nearer its centroid than any other zone's), highest-degree first, instead of one
   point. Demand is rounded to whole platoons (--deltan) with largest remainders, so
   the total survives rounding.

Writes <data>/zones.csv and <data>/od_matrix.csv in PCU per peak hour; run them with
--demand-scale 1 --pcu-factor 1 (the PCU conversion is already JICA's own, per type).

Variants for the intervention tests, same rules as the original model's
build_od_directional.py (H4) and build_od_decentralized.py (H7), applied to the 51 JICA
zones: "core" = the 20% of zones nearest the demand-weighted centroid.
  --variant am             periphery->core x1.4, core->periphery x1/1.4 (AM peak, H4)
  --variant decentralized  trips into core zones x0.75 (offices moved out, H7)
  --variant uniform        every trip x --scale: same loaded total as decentralized (H7 control)
Variants write only <data>/od_matrix_<variant>.csv and reuse the base zones.csv.

    python scripts/build_od_jica.py --data data/jica_net
    python scripts/build_od_jica.py --data data/jica_net --variant am
"""
from __future__ import annotations

import argparse
import csv
import math
from collections import defaultdict
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).parent.parent
SRC = ROOT / "data" / "jica_od"
# shortcut: zone 901 (outside the survey area, 3% of PCU) is split between the two
# main valley gateways; upgrade if gateway counts become available.
GATEWAYS_901 = [(27.6870, 85.2050), (27.6370, 85.4750)]   # Thankot (west), Sanga (east)


def largest_remainder(total_units: int, weights: list[float]) -> list[int]:
    s = sum(weights)
    raw = [total_units * w / s for w in weights]
    out = [int(r) for r in raw]
    for i in sorted(range(len(raw)), key=lambda i: raw[i] - out[i], reverse=True)[: total_units - sum(out)]:
        out[i] += 1
    return out


assert largest_remainder(7, [1, 1, 1]) == [3, 2, 2] and sum(largest_remainder(10, [3, 1])) == 10


def small_zone_od(k_peak: float) -> dict[tuple[str, str], float]:
    pt = {(r["origin"], r["destination"]): int(r["person_trips"])
          for r in csv.DictReader(open(SRC / "ptod_2011.csv", encoding="utf-8"))}
    zones = sorted({o for o, _ in pt})
    large = lambda z: z[0] + "00"
    pt_large = defaultdict(int)
    for (o, d), v in pt.items():
        pt_large[large(o), large(d)] += v
    gen = defaultdict(int)
    for (o, d), v in pt.items():
        gen[o] += v
        gen[d] += v
    vt = defaultdict(float)
    for r in csv.DictReader(open(SRC / "vtod_2011.csv", encoding="utf-8")):
        vt[r["origin_large"], r["dest_large"]] += float(r["pcu_per_day"])
    od = defaultdict(float)
    for (I, J), pcu in vt.items():
        members = [(o, d) for o in zones if large(o) == I for d in zones if large(d) == J]
        if pt_large[I, J] > 0:
            w = {p: pt[p] for p in members}
        else:                                  # no person trips: split by zone activity
            w = {(o, d): gen[o] * gen[d] for o, d in members}
        s = sum(w.values())
        for p, x in w.items():
            od[p] += pcu * x / s * k_peak
    total_daily = sum(vt.values())
    assert abs(sum(od.values()) - total_daily * k_peak) < 1e-6 * total_daily
    return od


def apply_variant(od, cent, args):
    mass = defaultdict(float)
    for (o, d), v in od.items():
        mass[o] += v
        mass[d] += v
    zs = [z for z in cent if z in mass]
    m = sum(mass[z] for z in zs)
    c = (sum(cent[z][0] * mass[z] for z in zs) / m, sum(cent[z][1] * mass[z] for z in zs) / m)
    zs.sort(key=lambda z: (cent[z][0] - c[0]) ** 2 + ((cent[z][1] - c[1]) * math.cos(math.radians(c[0]))) ** 2)
    core = set(zs[: max(1, int(len(zs) * args.core_pct))])
    print(f"core zones ({len(core)}): {' '.join(sorted(core))}")
    out = {}
    for (o, d), v in od.items():
        if args.variant == "uniform":
            f = args.scale
        elif args.variant == "am":
            f = args.boost if (o not in core and d in core) else (
                1 / args.boost if (o in core and d not in core) else 1.0)
        else:
            f = 1 - args.reduce if d in core else 1.0
        out[o, d] = v * f
    print(f"{args.variant}: total {sum(od.values()):,.0f} -> {sum(out.values()):,.0f} PCU")
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description="JICA 2011 OD -> network demand")
    ap.add_argument("--data", type=Path, required=True, help="network folder (network_*.csv)")
    ap.add_argument("--k-peak", type=float, default=0.10)
    ap.add_argument("--sub", type=int, default=4, help="max loading junctions per zone")
    ap.add_argument("--deltan", type=int, default=5)
    ap.add_argument("--variant", choices=["base", "am", "decentralized", "uniform"], default="base")
    ap.add_argument("--boost", type=float, default=1.4)
    ap.add_argument("--reduce", type=float, default=0.25)     # round-number scenario, as H7
    ap.add_argument("--core-pct", type=float, default=0.2)
    # uniform: every pair x scale, the volume-matched control for decentralized (H7);
    # 54,065 / 58,525 = loaded PCU of decentralized / base on data/jica_net
    ap.add_argument("--scale", type=float, default=54065 / 58525)
    args = ap.parse_args()

    od = small_zone_od(args.k_peak)
    cent = {r["zone"]: (float(r["lat"]), float(r["lon"]))
            for r in csv.DictReader(open(SRC / "zones_2011.csv", encoding="utf-8"))}
    if args.variant != "base":
        od = apply_variant(od, cent, args)

    nodes = {int(r[0]): (float(r[2]), float(r[1]))          # id -> (lat, lon)
             for r in csv.reader(open(args.data / "network_nodes.csv", encoding="utf-8")) if r}
    g = nx.DiGraph()
    for r in csv.reader(open(args.data / "network_links.csv", encoding="utf-8")):
        if r:
            g.add_edge(int(r[1]), int(r[2]))
    scc = max(nx.strongly_connected_components(g), key=len)

    def dist2(a, b):
        return (a[0] - b[0]) ** 2 + ((a[1] - b[1]) * math.cos(math.radians(27.7))) ** 2

    # catchments: each connected node belongs to the nearest zone centroid
    catch = defaultdict(list)
    for n in scc:
        catch[min(cent, key=lambda z: dist2(cent[z], nodes[n]))].append(n)
    load = {}
    for z, c in cent.items():
        cand = sorted(catch.get(z, []), key=lambda n: (-g.degree(n), dist2(cent[z], nodes[n])))
        load[z] = cand[: args.sub] or [min(scc, key=lambda n: dist2(c, nodes[n]))]
    load["901"] = [min(scc, key=lambda n: dist2(p, nodes[n])) for p in GATEWAYS_901]

    frac = defaultdict(float)                 # junction pair -> PCU, before rounding
    intrazonal = same_node = 0.0
    for (o, d), v in od.items():
        if o == d:
            intrazonal += v
            continue
        sub_pairs = [(a, b) for a in load[o] for b in load[d]]
        for a, b in sub_pairs:
            if a == b:
                same_node += v / len(sub_pairs)
            else:
                frac[a, b] += v / len(sub_pairs)
    # round once over all pairs, so many sub-platoon pairs don't each round to zero
    keys = list(frac)
    units = largest_remainder(round(sum(frac.values()) / args.deltan), [frac[k] for k in keys])
    pair = {k: u * args.deltan for k, u in zip(keys, units) if u}
    total = sum(od.values())
    loaded = sum(pair.values())
    print(f"peak-hour demand: {total:,.0f} PCU (K={args.k_peak})")
    print(f"  intrazonal (stays inside one of 51 zones, not on this network): {intrazonal:,.0f} "
          f"({intrazonal / total:.0%})")
    print(f"  both ends on the same junction (outer zones sharing an edge node): {same_node:,.0f}")
    print(f"  loaded: {loaded:,} PCU in {len(pair):,} junction pairs; "
          f"{sum(len(v) for v in load.values())} loading junctions")

    used = sorted({n for p in pair for n in p})
    if args.variant != "base":
        base_ids = {r["zone_id"] for r in csv.DictReader(open(args.data / "zones.csv", encoding="utf-8"))}
        missing = {f"N{n}" for n in used} - base_ids
        assert not missing, f"variant uses junctions not in the base zones.csv: {sorted(missing)[:5]}"
        od_path = args.data / f"od_matrix_{args.variant}.csv"
    else:
        with (args.data / "zones.csv").open("w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["zone_id", "lat", "lon"])
            for n in used:
                w.writerow([f"N{n}", nodes[n][0], nodes[n][1]])
        od_path = args.data / "od_matrix.csv"
    with od_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["origin_id", "dest_id", "demand"])
        for (a, b), v in sorted(pair.items()):
            w.writerow([f"N{a}", f"N{b}", v])
    print(f"wrote {od_path}")

if __name__ == "__main__":
    main()
