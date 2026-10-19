#!/usr/bin/env python3
"""Location-wise density, bridge bottlenecks, and jam chain-reaction report.

Builds on two things UXsim already tracks but this project had not surfaced:
density (Edie's generalized k, via Analyzer.link_traffic_state_to_pandas) and
queue spillback, which is inherent to its kinematic-wave physics - when a
link saturates, UXsim already throttles inflow from its upstream neighbours,
so a jam already propagates backward through the network without any new
mechanism added here. This script reports that behaviour rather than adding it:

  - per-link density (vehicles/m, Edie's k) normalized by that link's own
    jam capacity (l.kappa = jam_density_per_lane x number_of_lanes - NOT
    l.jam_density, which UXsim's OSM importer leaves at its flat, un-scaled
    default regardless of lane count; see run_bridge_bottleneck_check below)
  - Ring Road bridges (from find_bridges.py's data/bridges.csv) flagged
    against that density, since a bridge is a lanes bottleneck relative to
    its approaches
  - for each bridge, whether its upstream approach links measurably jam up
    *after* the bridge itself does, and by how much lag - the chain reaction

    python scripts/congestion_report.py

Outputs:
    results/congestion_by_location.csv
    results/chain_reaction.csv
"""
from __future__ import annotations

import argparse
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402


def classify_severity(jam_ratio: float) -> str:
    """Label a link's density relative to its own jam capacity.

    jam_ratio = mean density / that link's own jam capacity (l.kappa), so
    1.0 means the link is at a dead stop on average over the run. Thresholds
    below 1.0 since Newell's simplified car-following model (UXsim's basis)
    has speed dropping well before a link is literally gridlocked.
    """
    if jam_ratio < 0.5:
        return "free_flowing"
    if jam_ratio <= 0.85:
        return "congested"
    return "jammed"


def main() -> None:
    ap = argparse.ArgumentParser(description="Density, bridge, and chain-reaction report")
    add_model_args(ap)
    ap.add_argument("--bridges-file", type=Path, default=Path("data/bridges.csv"))
    ap.add_argument("--out-dir", type=Path, default=Path("results"))
    # a link counts as "jammed" for chain-reaction timing once its density
    # crosses this fraction of its own jam capacity - independent of the
    # free-flowing/congested/jammed labels above, which are for the report
    ap.add_argument("--chain-reaction-threshold", type=float, default=0.7)
    args = ap.parse_args()

    W, _zones = build_world(args)
    print("running ...")
    W.exec_simulation()

    with args.bridges_file.open(encoding="utf-8") as fh:
        bridges = {(r["u"], r["v"]): r for r in csv.DictReader(fh)}

    node_coords = {n.name: (n.x, n.y) for n in W.NODES}

    print("computing link traffic states (Edie's density/flow/speed) ...")
    state = W.analyzer.link_traffic_state_to_pandas()
    # space-average each link's density per time step, for the chain-reaction
    # timing below; the full per-cell table is not needed past this point
    ts = state.groupby(["link", "t"])["k"].mean().reset_index()

    rows = []
    link_by_name = {l.name: l for l in W.LINKS}
    series_by_link: dict[str, list[tuple[float, float]]] = {}
    for link_name, grp in ts.groupby("link"):
        series_by_link[link_name] = list(zip(grp["t"], grp["k"]))

    for l in W.LINKS:
        series = series_by_link.get(l.name, [])
        if not series:
            continue
        mean_k = sum(k for _, k in series) / len(series)
        max_k = max(k for _, k in series)
        jam_ratio = mean_k / l.kappa if l.kappa else 0.0
        key = (l.start_node.name, l.end_node.name)
        bridge = bridges.get(key)
        lon1, lat1 = node_coords.get(l.start_node.name, (None, None))
        lon2, lat2 = node_coords.get(l.end_node.name, (None, None))
        rows.append({
            "link": l.name, "u": l.start_node.name, "v": l.end_node.name,
            "lat1": lat1, "lon1": lon1, "lat2": lat2, "lon2": lon2,
            "lanes": l.number_of_lanes, "jam_capacity_veh_per_m": l.kappa,
            "mean_density": mean_k, "max_density": max_k, "jam_ratio": jam_ratio,
            "severity": classify_severity(jam_ratio),
            "is_bridge": bridge is not None,
            "is_ring_road_bridge": bridge is not None and bridge["is_ring_road"] == "True",
        })

    args.out_dir.mkdir(parents=True, exist_ok=True)
    out_path = args.out_dir / "congestion_by_location.csv"
    with out_path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"wrote {out_path} ({len(rows)} links)")

    # ---- chain reaction: does an upstream approach jam up after its bridge does? ----
    def first_crossing(link_name: str) -> float | None:
        for t, k in sorted(series_by_link.get(link_name, [])):
            link = link_by_name[link_name]
            if link.kappa and k / link.kappa >= args.chain_reaction_threshold:
                return t
        return None

    chain_rows = []
    for (u, v), bridge in bridges.items():
        bridge_link = bridge["link_name"]
        if bridge_link not in link_by_name:
            continue
        downstream_t = first_crossing(bridge_link)
        if downstream_t is None:
            continue
        # exclude the bridge's own reverse-direction link: UXsim keeps the same
        # OSM name for both carriageways of a bidirectional bridge (one gets an
        # auto-renamed suffix), so without this a bridge "jams after itself"
        bridge_base_name = bridge_link.split("_renamed")[0]
        upstream_links = [l for l in W.LINKS if l.end_node.name == u
                          and l.name.split("_renamed")[0] != bridge_base_name]
        for ul in upstream_links:
            upstream_t = first_crossing(ul.name)
            if upstream_t is not None and upstream_t >= downstream_t:
                chain_rows.append({
                    "bridge_link": bridge_link, "upstream_link": ul.name,
                    "is_ring_road_bridge": bridge["is_ring_road"] == "True",
                    "bridge_jammed_at_s": downstream_t,
                    "upstream_jammed_at_s": upstream_t,
                    "lag_s": upstream_t - downstream_t,
                })

    chain_path = args.out_dir / "chain_reaction.csv"
    with chain_path.open("w", newline="", encoding="utf-8") as fh:
        fieldnames = ["bridge_link", "upstream_link", "is_ring_road_bridge",
                      "bridge_jammed_at_s", "upstream_jammed_at_s", "lag_s"]
        w = csv.DictWriter(fh, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(chain_rows)
    print(f"wrote {chain_path} ({len(chain_rows)} bridge -> upstream-link pairs "
          f"that jam in sequence)")
    if chain_rows:
        avg_lag = sum(r["lag_s"] for r in chain_rows) / len(chain_rows)
        print(f"  average lag from bridge saturation to upstream jam: {avg_lag:.0f} s")


if __name__ == "__main__":
    main()
