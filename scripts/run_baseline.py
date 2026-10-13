#!/usr/bin/env python3
"""Validate the network, then run the calibrated baseline.

    python scripts/run_baseline.py

Defaults reproduce the calibrated baseline: 30% of the citywide peak-hour matrix
at an effective free-flow speed of 30 km/h. That gives ~17.7 km/h mean speed, a
delay ratio of 0.65, and 99% of trips completing. See the README for the reasoning.

UXsim warns that its OSM import can produce fragmented networks with many dead
ends. A fragmented network fails silently: trips between unconnected parts are
simply never completed, so the run still "succeeds" while measuring nothing. This
checks connectivity first and refuses to run if the network cannot carry the demand.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

import networkx as nx
from uxsim import World
from uxsim.OSMImporter import OSMImporter

sys.path.insert(0, str(Path(__file__).parent))
from signals import add_fixed_time_signals, self_check  # noqa: E402


def load_network(data: Path):
    with (data / "network_nodes.csv").open(encoding="utf-8") as fh:
        nodes = [[int(r[0]), float(r[1]), float(r[2])] for r in csv.reader(fh) if r]
    # 6th column is link length in degrees, added by osm_network_postprocessing;
    # osm_network_to_World reads it as link[5], so it must survive the CSV round-trip.
    with (data / "network_links.csv").open(encoding="utf-8") as fh:
        links = [[r[0], int(r[1]), int(r[2]), int(float(r[3])), float(r[4]), float(r[5])]
                 for r in csv.reader(fh) if r]
    return nodes, links


def connectivity(nodes, links):
    """Largest strongly connected component - the only part that can carry traffic."""
    g = nx.DiGraph()
    g.add_nodes_from(n[0] for n in nodes)
    g.add_edges_from((l[1], l[2]) for l in links)
    scc = max(nx.strongly_connected_components(g), key=len)
    dead_ends = [n for n in g.nodes if g.out_degree(n) == 0 or g.in_degree(n) == 0]
    return g, scc, dead_ends


def nearest_node(lat, lon, node_coords):
    """Closest network node to a zone centroid (flat approximation, fine at city scale)."""
    best, best_d = None, float("inf")
    for nid, (nlon, nlat) in node_coords.items():
        d = (nlat - lat) ** 2 + ((nlon - lon) * math.cos(math.radians(lat))) ** 2
        if d < best_d:
            best, best_d = nid, d
    return best, math.sqrt(best_d) * 111.32


def main() -> None:
    ap = argparse.ArgumentParser(description="Network validation + smoke-test run")
    ap.add_argument("--data", type=Path, default=Path("data"))
    # 0.3 = the arterial share of citywide demand. This network holds only
    # trunk/primary/secondary roads, so trips that stay on local streets are not
    # represented. Calibrated so mean speed matches observed Kathmandu peak.
    ap.add_argument("--demand-scale", type=float, default=0.3,
                    help="arterial share of the OD matrix (1.0 = full citywide peak hour)")
    ap.add_argument("--deltan", type=int, default=5, help="vehicles per simulated platoon")
    # Demand is injected over the peak hour, but the clock runs on so the network can
    # drain. Stopping at the end of the demand window would mark every late-departing
    # trip as incomplete and bias travel times toward short trips.
    ap.add_argument("--demand-window", type=int, default=3600, help="peak-hour length")
    # 10800 not 7200: signals slow the network enough that a 2 h horizon leaves ~20%
    # of trips unfinished, which biases every statistic toward short trips.
    ap.add_argument("--tmax", type=int, default=10800, help="simulation horizon")
    # OSM maxspeed is the legal limit (50 km/h), which no Kathmandu arterial sustains.
    # In a mesoscopic model, poor lane discipline and erratic braking are represented
    # here - as a lower effective free-flow speed - not as driver behaviour.
    ap.add_argument("--free-flow-kmh", type=float, default=30.0,
                    help="override OSM maxspeed on every link (None = use OSM)")
    ap.add_argument("--jam-density", type=float, default=0.2,
                    help="veh/m/lane at standstill (0.2 = 5 m per vehicle)")
    ap.add_argument("--no-signals", action="store_true",
                    help="leave intersections as free merges (OSM import default)")
    ap.add_argument("--cycle", type=float, default=90.0, help="signal cycle length")
    args = ap.parse_args()

    nodes, links = load_network(args.data)
    print(f"network:      {len(nodes)} nodes, {len(links)} links")

    g, scc, dead_ends = connectivity(nodes, links)
    print(f"largest SCC:  {len(scc)} nodes ({len(scc)/len(nodes):.0%} of network)")
    print(f"dead ends:    {len(dead_ends)}")
    if len(scc) < 0.5 * len(nodes):
        raise SystemExit(
            f"network is fragmented - only {len(scc)}/{len(nodes)} nodes are mutually "
            "reachable. Re-import with a larger --merge-threshold before simulating."
        )

    # zones must attach to the connected core, or their trips can never complete
    coords = {n[0]: (n[1], n[2]) for n in nodes if n[0] in scc}
    zones = {}
    far = 0
    with (args.data / "zones.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            nid, dist_km = nearest_node(float(row["lat"]), float(row["lon"]), coords)
            zones[row["zone_id"]] = nid
            if dist_km > 1.0:
                far += 1
    print(f"zones mapped: {len(zones)} -> {len(set(zones.values()))} distinct nodes")
    print(f"              {far} zones are >1 km from any connected node")

    if args.free_flow_kmh:
        for l in links:
            l[4] = args.free_flow_kmh / 3.6

    # print_mode=0 also silences analyzer output, so stats would vanish too.
    W = World(name="kathmandu-smoke", deltan=args.deltan, tmax=args.tmax,
              print_mode=1, save_mode=1, show_mode=0, random_seed=0)
    OSMImporter.osm_network_to_World(W, nodes, links,
                                     default_jam_density=args.jam_density,
                                     coef_degree_to_meter=111000)

    if not args.no_signals:
        info = add_fixed_time_signals(W, cycle_s=args.cycle)
        self_check(W)
        print(f"signals:      {info['signalised']} intersections at {args.cycle:.0f}s cycle "
              f"({info['skipped']} nodes left as free merges)")

    loaded = skipped = 0
    with (args.data / "od_matrix.csv").open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            o, d = zones.get(row["origin_id"]), zones.get(row["dest_id"])
            vol = int(int(row["demand"]) * args.demand_scale)
            if o is None or d is None or o == d or vol < args.deltan:
                skipped += vol
                continue
            W.adddemand(str(o), str(d), 0, args.demand_window, volume=vol)
            loaded += vol
    print(f"demand:       {loaded:,} trips loaded, {skipped:,} skipped "
          f"(intrazonal or below deltan={args.deltan})")

    print("running ...")
    W.exec_simulation()
    W.analyzer.print_simple_stats()

    # A baseline is only useful between the two failure modes: if most trips never
    # finish the network is gridlocked and the statistics are biased to short trips;
    # if there is almost no delay there is nothing for signals or pricing to improve.
    a = W.analyzer
    done = a.trip_completed / a.trip_all if a.trip_all else 0.0
    ratio = a.average_delay / a.average_travel_time if a.average_travel_time else 0.0
    speed_kmh = getattr(a, "average_speed", 0.0) * 3.6
    if done < 0.6:
        verdict = "GRIDLOCK - demand exceeds network capacity, stats are unusable"
    elif ratio < 0.15:
        verdict = "FREE-FLOWING - too little congestion to optimise against"
    else:
        verdict = "USABLE baseline"
    print(f"\nVERDICT: {verdict}")
    print(f"  completed {done:.0%} | delay ratio {ratio:.2f} | mean speed {speed_kmh:.1f} km/h")


if __name__ == "__main__":
    main()
