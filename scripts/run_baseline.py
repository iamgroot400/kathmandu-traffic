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
from adaptive_signals import attach as attach_adaptive  # noqa: E402


def load_network(data: Path):
    with (data / "network_nodes.csv").open(encoding="utf-8") as fh:
        nodes = [[int(r[0]), float(r[1]), float(r[2])] for r in csv.reader(fh) if r]
    # 6th column is link length in degrees, added by osm_network_postprocessing;
    # osm_network_to_World reads it as link[5], so it must survive the CSV round-trip.
    with (data / "network_links.csv").open(encoding="utf-8") as fh:
        links = [[r[0], int(r[1]), int(r[2]), int(float(r[3])), float(r[4]), float(r[5])]
                 for r in csv.reader(fh) if r]
    return nodes, links


def halve_twoway_lanes(links, tags_file: Path, way) -> int:
    """UXsim's importer reads OSM `lanes` as lanes per direction; on a two-way road it counts both
    directions, so each direction gets ceil(lanes / 2). One-way roads and untagged roads are unchanged."""
    tags = {r["way"]: r for r in csv.DictReader(tags_file.open(encoding="utf-8"))}
    n = 0
    for l in links:
        t = tags.get(way(l))
        if not t or not t["lanes"].split(";")[0].strip().isdigit():
            continue
        if t["oneway"] in ("yes", "1", "-1", "true") or t["junction"] in ("roundabout", "circular"):
            continue
        l[3] = max(1, math.ceil(int(t["lanes"].split(";")[0]) / 2))
        n += 1
    return n


def untagged_lanes(links, tags_file: Path, way, spec: str, minor) -> int:
    """Main links whose OSM way has no `lanes` tag get the lanes per direction given for their class in
    `spec`, e.g. "trunk=2,primary=2,secondary=1" (the median of the tagged main links of each class),
    instead of UXsim's generic defaults (trunk 3, primary 2, secondary 2)."""
    per_class = {k: int(v) for k, v in (kv.split("=") for kv in spec.split(","))}
    tags = {r["way"]: r for r in csv.DictReader(tags_file.open(encoding="utf-8"))}
    n = 0
    for l in links:
        t = tags.get(way(l))
        if way(l) in minor or not t or t["lanes"].strip() or t["highway"] not in per_class:
            continue
        l[3] = per_class[t["highway"]]
        n += 1
    return n


def pedestrian_friction(nodes, links, pois_file: Path, ped_file: Path, exempt, a_kmh: float = 15,
                        b_kmh: float = 30, b_top: float = 0.10) -> tuple[int, int]:
    """Walkers, street trade and stopping vehicles slow traffic in busy areas. Trunk roads (`exempt`: wide, with
    footpaths) are left out. Tier A (a_kmh): links within 50 m of an OSM pedestrian street (the pedestrianised
    core: Basantapur, Thamel, Ason). Tier B (b_kmh): the top b_top of the remaining links by OSM shops /
    amenities / offices within 100 m along the whole link, per km. Speeds only ever go down."""
    import json
    pos = {n[0]: (n[2], n[1]) for n in nodes}                    # node rows are [id, lon, lat]
    cell = 0.001                                                 # ~110 m grid for the neighbour search

    def grid_of(points):
        g = {}
        for i, (la, lo) in enumerate(points):
            g.setdefault((int(la / cell), int(lo / cell)), []).append((i, la, lo))
        return g

    pois = grid_of(json.loads(pois_file.read_text(encoding="utf-8")))
    peds = grid_of(json.loads(ped_file.read_text(encoding="utf-8")))

    def near(g, l, radius, step=50):
        (ya, xa), (yb, xb) = pos[l[1]], pos[l[2]]
        k = math.cos(math.radians(ya))
        length = math.hypot(yb - ya, (xb - xa) * k) * 111000
        m = max(1, int(length // step))
        found = set()
        for j in range(m + 1):
            pa, po = ya + (yb - ya) * j / m, xa + (xb - xa) * j / m
            for di in (-1, 0, 1):
                for dj in (-1, 0, 1):
                    for i, la, lo in g.get((int(pa / cell) + di, int(po / cell) + dj), ()):
                        if math.hypot(la - pa, (lo - po) * k) * 111000 <= radius:
                            found.add(i)
        return length, found

    cand = [l for l in links if not exempt(l)]
    tier_a = [l for l in cand if near(peds, l, 50)[1]]
    rest = [l for l in cand if l not in tier_a]
    dens = []
    for l in rest:
        length, found = near(pois, l, 100)
        dens.append(len(found) / max(length, 100) * 1000)       # per km; links under 100 m count as 100 m
    cut_b = sorted(dens)[int(len(dens) * (1 - b_top))] if dens else float("inf")
    for l in tier_a:
        l[4] = min(l[4], a_kmh / 3.6)
    nb = 0
    for l, d in zip(rest, dens):
        if d >= max(cut_b, 1):
            l[4], nb = min(l[4], b_kmh / 3.6), nb + 1
    return len(tier_a), nb


def roadside_friction(nodes, links, pois_file: Path, share: float, kmh: float, skip) -> int:
    """Main links whose midpoint has the most shops / amenities / offices within 100 m (top `share`
    of main links) get free-flow speed `kmh`: stopping buses, pedestrians and street trade."""
    import json
    pois = json.loads(pois_file.read_text(encoding="utf-8"))   # [lat, lon]
    cell = 0.001                                                 # ~110 m grid for the neighbour search
    grid = {}
    for la, lo in pois:
        grid.setdefault((int(la / cell), int(lo / cell)), []).append((la, lo))
    pos = {n[0]: (n[2], n[1]) for n in nodes}                    # node rows are [id, lon, lat]

    def count(la, lo):
        k = math.cos(math.radians(la))
        return sum(1 for di in (-1, 0, 1) for dj in (-1, 0, 1)
                   for p in grid.get((int(la / cell) + di, int(lo / cell) + dj), ())
                   if math.hypot(p[0] - la, (p[1] - lo) * k) * 111000 <= 100)

    main = [l for l in links if not skip(l)]
    dens = [count((pos[l[1]][0] + pos[l[2]][0]) / 2, (pos[l[1]][1] + pos[l[2]][1]) / 2) for l in main]
    cut = sorted(dens)[int(len(dens) * (1 - share))]
    n = 0
    for l, d in zip(main, dens):
        if d >= max(cut, 1):
            l[4] = min(l[4], kmh / 3.6)
            n += 1
    return n


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


def add_model_args(ap: argparse.ArgumentParser) -> None:
    """Model parameters, shared by every script that builds this network."""
    ap.add_argument("--data", type=Path, default=Path("data"))
    # Overridable so an alternative demand (e.g. with cordon trips) can be run
    # without overwriting the files a sweep in progress is still reading.
    ap.add_argument("--od-file", type=Path, default=None, help="default: <data>/od_matrix.csv")
    ap.add_argument("--zones-file", type=Path, default=None, help="default: <data>/zones.csv")
    # Effective load = demand-scale x pcu-factor, and only that product is identified
    # by the calibration (mean speed). It is decomposed into two defensible parts:
    #   0.48  arterial share - this network holds only trunk/primary/secondary roads,
    #         so trips that stay on local streets are not represented
    #   0.625 PCU factor - Kathmandu's fleet converted to passenger-car equivalents
    # 0.48 x 0.625 = 0.30, the value originally fitted with PCU implicitly 1.0.
    ap.add_argument("--demand-scale", type=float, default=0.48,
                    help="arterial share of the OD matrix (1.0 = full citywide peak hour)")
    # 70% two-wheelers @0.25 + 20% cars @1.0 + 10% buses @2.5 = 0.625 PCU per vehicle.
    # UXsim is single-class, so the mix enters as weighted demand, not vehicle types.
    ap.add_argument("--pcu-factor", type=float, default=0.625,
                    help="passenger-car equivalents per vehicle (1.0 = all cars)")
    # Default 1.0 (no change) to leave every already-published run untouched.
    # Separate from demand_scale/pcu_factor, which are the calibrated split of a
    # single identified "effective load" (A4) - this is an independent multiplier
    # for projecting that same load forward in time.
    ap.add_argument("--demand-growth", type=float, default=1.0,
                    help="multiplier on top of demand-scale x pcu-factor, e.g. "
                         "for a future-year demand projection")
    ap.add_argument("--deltan", type=int, default=5, help="vehicles per simulated platoon")
    # Demand is injected over the peak hour, but the clock runs on so the network can
    # drain. Stopping at the end of the demand window would mark every late-departing
    # trip as incomplete and bias travel times toward short trips.
    ap.add_argument("--demand-window", type=int, default=3600, help="peak-hour length")
    # Default 0 to leave every already-published run's timing untouched. A nonzero
    # warmup delays demand's start so the network isn't literally empty when the
    # "peak hour" being measured begins - real roads already carry pre-peak traffic
    # at that moment, ours starts cold. Tried at 3600s for geh_check.py (D23): it
    # did not improve the GEH fit (made it worse network-wide, see decisions.md),
    # so geh_check.py does not use it either - kept here only as an opt-in building
    # block for whoever revisits that finding.
    ap.add_argument("--warmup", type=int, default=0,
                    help="seconds of empty-network run-up before demand starts")
    # 10800 not 7200: signals slow the network enough that a 2 h horizon leaves ~20%
    # of trips unfinished, which biases every statistic toward short trips.
    ap.add_argument("--tmax", type=int, default=10800, help="simulation horizon")
    # OSM maxspeed is the legal limit (50 km/h), which no Kathmandu arterial sustains.
    # In a mesoscopic model, poor lane discipline and erratic braking are represented
    # here - as a lower effective free-flow speed - not as driver behaviour.
    ap.add_argument("--free-flow-kmh", type=float, default=30.0,
                    help="override OSM maxspeed on every link (None = use OSM)")
    # Narrow side streets (D36): OSM ways listed in this file are built as 1-lane links whose
    # discharge is capped at --minor-capacity-ratio of a normal lane. JICA (2012, Table 8.2.4)
    # gives a narrow 2-lane road 6,000 PCU/day against 17,000 for a 2-lane road: 0.353.
    # Default off, so every published run is unchanged.
    ap.add_argument("--minor-ways", type=Path, default=None,
                    help="file of OSM way ids to treat as narrow side streets")
    ap.add_argument("--minor-capacity-ratio", type=float, default=6000 / 17000)
    # JICA 2012 Table 8.2.4b free speed: asphalt good 60, fair 45, bad 30 km/h (D36)
    ap.add_argument("--priority-junctions", action="store_true",
                    help="side-street-only crossings give way instead of being signalised (D36)")
    ap.add_argument("--yield-priority", type=float, default=0.2,
                    help="merge priority of side streets at give-way junctions (assumed, D36)")
    ap.add_argument("--minor-free-flow-kmh", type=float, default=None,
                    help="side-street free-flow speed (default: same as --free-flow-kmh)")
    ap.add_argument("--jam-density", type=float, default=0.2,
                    help="veh/m/lane at standstill (0.2 = 5 m per vehicle)")
    ap.add_argument("--no-signals", action="store_true",
                    help="leave intersections as free merges (OSM import default)")
    ap.add_argument("--cycle", type=float, default=90.0, help="signal cycle length")
    # count-tuning (scripts/tune_counts.py); defaults leave the model unchanged
    ap.add_argument("--reaction-time", type=float, default=1.0,
                    help="UXsim reaction time (s); per-lane capacity is at most 1/reaction-time")
    ap.add_argument("--min-main-lanes", type=int, default=0,
                    help="raise main-road links to at least this many lanes per direction")
    ap.add_argument("--osm-way-tags", type=Path, default=None,
                    help="data/jica_net/osm_way_tags.csv: give two-way roads half their OSM lanes tag per direction")
    ap.add_argument("--untagged-lanes", default="",
                    help='with --osm-way-tags: lanes per direction for untagged main roads by class, '
                         'e.g. "trunk=2,primary=2,secondary=1"')
    ap.add_argument("--pedestrian-friction", type=Path, default=None,
                    help="with --osm-way-tags; data/jica_net/osm_pedestrian_points.json: non-trunk links near a "
                         "pedestrian street 15 km/h; top 10%% of the rest by roadside shops 30 km/h")
    ap.add_argument("--friction-kmh", type=float, default=0,
                    help="free-flow speed on the main links with the most roadside shops / amenities")
    ap.add_argument("--friction-share", type=float, default=0.10,
                    help="share of main links (by roadside POI count within 100 m) that get --friction-kmh")
    ap.add_argument("--pois", type=Path, default=Path("data/kathmandu_pois.json"))
    ap.add_argument("--adaptive", action="store_true",
                    help="queue-actuated control instead of fixed-time")
    ap.add_argument("--min-green", type=float, default=10.0)
    ap.add_argument("--max-green", type=float, default=60.0)
    # UXsim's route choice carries duo_noise, so each seed is a different realization.
    # Comparing two configurations on one seed each cannot separate effect from noise.
    ap.add_argument("--seed", type=int, default=0, help="random seed for this run")
    ap.add_argument("--platoon-fix", action=argparse.BooleanOptionalAction, default=True,
                    help="pass each pair's volume +0.5 so UXsim's float accumulation does not drop its "
                         "last platoon (D38: 2.5-6%% of vehicles lost otherwise, varying by demand file)")
    ap.add_argument("--vehicle-log-interval", type=int, default=1,
                    help="UXsim per-vehicle log every N steps; >1 saves memory in gridlock (D38). "
                         "Trip times are unaffected; average speed becomes sampled")
    ap.add_argument("--toll-file", type=Path, default=None,
                    help="per-link delay schedule to price from (results/tolls.csv)")
    ap.add_argument("--toll-strength", type=float, default=0.0,
                    help="toll as a multiple of each link's observed delay")
    ap.add_argument("--demand-elasticity", type=float, default=0.0,
                    help="with pricing: elasticity of each OD's volume to the toll on "
                         "its path (negative, e.g. -0.3); 0 keeps demand fixed (A6)")
    ap.add_argument("--tidal-period", choices=["am", "pm"], default=None,
                    help="apply the tidal-flow lever (H4) for this period; pair with "
                         "--od-file data/od_matrix_<period>.csv")
    ap.add_argument("--tidal-lane-shift", type=float, default=1.0,
                    help="lane-equivalents shifted from light to heavy direction")


def build_world(args, verbose: bool = True):
    """Validate the network, build the World, signalise it and load demand.

    Returns (World, {zone_id: node_id}). `verbose=False` silences it for solvers
    that rebuild the World once per iteration.
    """
    def say(msg):
        if verbose:
            print(msg)

    nodes, links = load_network(args.data)
    say(f"network:      {len(nodes)} nodes, {len(links)} links")

    g, scc, dead_ends = connectivity(nodes, links)
    say(f"largest SCC:  {len(scc)} nodes ({len(scc)/len(nodes):.0%} of network)")
    say(f"dead ends:    {len(dead_ends)}")
    if len(scc) < 0.5 * len(nodes):
        raise SystemExit(
            f"network is fragmented - only {len(scc)}/{len(nodes)} nodes are mutually "
            "reachable. Re-import with a larger --merge-threshold before simulating."
        )

    # zones must attach to the connected core, or their trips can never complete
    coords = {n[0]: (n[1], n[2]) for n in nodes if n[0] in scc}
    zones = {}
    far = 0
    zones_file = args.zones_file or (args.data / "zones.csv")
    od_file = args.od_file or (args.data / "od_matrix.csv")
    with zones_file.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            nid, dist_km = nearest_node(float(row["lat"]), float(row["lon"]), coords)
            zones[row["zone_id"]] = nid
            if dist_km > 1.0:
                far += 1
    say(f"zones mapped: {len(zones)} -> {len(set(zones.values()))} distinct nodes")
    say(f"              {far} zones are >1 km from any connected node")

    if args.free_flow_kmh:
        for l in links:
            l[4] = args.free_flow_kmh / 3.6

    # print_mode=0 also silences analyzer output, so stats would vanish too.
    W = World(name="kathmandu", deltan=args.deltan, tmax=args.tmax,
              print_mode=1 if verbose else 0, save_mode=1, show_mode=0,
              random_seed=args.seed, reaction_time=args.reaction_time,
              vehicle_logging_timestep_interval=args.vehicle_log_interval)
    minor = set()
    if args.minor_ways:
        minor = set(args.minor_ways.read_text(encoding="utf-8").split())
    way = lambda l: str(l[0]).rsplit("-", 1)[-1]
    if args.osm_way_tags:
        say(f"two-way lanes: {halve_twoway_lanes(links, args.osm_way_tags, way)} links set to half their OSM lanes tag")
    if args.friction_kmh:
        n = roadside_friction(nodes, links, args.pois, args.friction_share, args.friction_kmh,
                              lambda l: way(l) in minor)
        say(f"roadside friction: {n} main links at {args.friction_kmh:.0f} km/h")
    if args.untagged_lanes:
        n = untagged_lanes(links, args.osm_way_tags, way, args.untagged_lanes, minor)
        say(f"untagged lanes: {n} main links set to their class's tagged median ({args.untagged_lanes})")
    if args.pedestrian_friction:
        trunk = {r["way"] for r in csv.DictReader(args.osm_way_tags.open(encoding="utf-8"))
                 if r["highway"] in ("trunk", "motorway")}
        na, nb = pedestrian_friction(nodes, links, args.pois, args.pedestrian_friction, lambda l: way(l) in trunk)
        say(f"pedestrian friction: {na} links at 15 km/h, {nb} at 30 km/h")
    if args.min_main_lanes:   # main roads whose OSM lane count is missing or low
        for l in links:
            if way(l) not in minor:
                l[3] = max(l[3], args.min_main_lanes)
    OSMImporter.osm_network_to_World(W, nodes, [l for l in links if way(l) not in minor],
                                     default_jam_density=args.jam_density,
                                     coef_degree_to_meter=111000)
    n_minor = 0
    minor_links = set()
    for l in links:
        if way(l) in minor:
            link = W.addLink(str(l[0]), str(l[1]), str(l[2]), length=l[5] * 111000,
                             free_flow_speed=(min(args.minor_free_flow_kmh / 3.6, l[4]) if args.minor_free_flow_kmh
                                              and args.pedestrian_friction else args.minor_free_flow_kmh / 3.6
                                              if args.minor_free_flow_kmh else l[4]), jam_density_per_lane=args.jam_density,
                             number_of_lanes=1, auto_rename=True)
            link.capacity_out = args.minor_capacity_ratio * link.capacity
            link.capacity_out_remain = link.capacity_out * W.DELTAT
            minor_links.add(link)
            n_minor += 1
    if minor:
        say(f"side streets: {n_minor} links at 1 lane, discharge {args.minor_capacity_ratio:.3f} x lane capacity")

    if args.tidal_period:
        from tidal_lanes import apply_tidal_lanes
        n = apply_tidal_lanes(W, args.tidal_period, lane_shift=args.tidal_lane_shift)
        say(f"tidal lanes:  {n} corridors shifted {args.tidal_lane_shift:.1f} "
            f"lane-equivalents for {args.tidal_period}")

    if not args.no_signals:
        info = add_fixed_time_signals(W, cycle_s=args.cycle,
                                      priority_minor=minor_links if args.priority_junctions else None,
                                      yield_priority=args.yield_priority)
        self_check(W)
        say(f"signals:      {info['signalised']} intersections at {args.cycle:.0f}s cycle "
            f"({info['skipped']} nodes left as free merges, {info.get('priority', 0)} side-street give-way junctions)")
        if args.adaptive:
            n = attach_adaptive(W, min_green=args.min_green, max_green=args.max_green)
            say(f"control:      queue-actuated on {n} intersections "
                f"(min green {args.min_green:.0f}s, max {args.max_green:.0f}s)")

    if args.toll_file and args.toll_strength > 0:
        from run_pricing import apply_tolls, load_toll_schedule
        priced = apply_tolls(W, load_toll_schedule(args.toll_file),
                             args.toll_strength, args.demand_window)
        say(f"pricing:      {priced} links tolled at {args.toll_strength}x "
            f"observed delay, peak window only")

    kept = None
    if args.demand_elasticity and args.toll_file and args.toll_strength > 0:
        from elastic_demand import od_response
        kept = od_response(W, args.demand_elasticity)

    loaded = skipped = 0
    with od_file.open(encoding="utf-8") as fh:
        for row in csv.DictReader(fh):
            o, d = zones.get(row["origin_id"]), zones.get(row["dest_id"])
            vol = int(int(row["demand"]) * args.demand_scale * args.pcu_factor
                     * args.demand_growth)
            if kept and o is not None and d is not None and o != d:
                vol = int(vol * kept(str(o), str(d)))
            if o is None or d is None or o == d or vol < args.deltan:
                skipped += vol
                continue
            W.adddemand(str(o), str(d), args.warmup, args.warmup + args.demand_window,
                       volume=vol + (0.5 if args.platoon_fix else 0))
            loaded += vol
    say(f"demand:       {loaded:,} trips loaded, {skipped:,} skipped "
          f"(intrazonal or below deltan={args.deltan})")

    return W, zones


def main() -> None:
    ap = argparse.ArgumentParser(description="Network validation + calibrated baseline run")
    add_model_args(ap)
    args = ap.parse_args()

    W, _zones = build_world(args)
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
