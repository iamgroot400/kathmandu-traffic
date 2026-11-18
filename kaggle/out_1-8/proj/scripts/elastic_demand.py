#!/usr/bin/env python3
"""Elastic demand under pricing: tolled trips are partly suppressed, not only re-routed.

run_baseline.py's pricing lever holds demand fixed, so the paper calls its effect a
lower bound (A6). With --demand-elasticity set, each OD pair's volume is scaled by
demand_response() using the toll it would meet on its free-flow shortest path.

Tolls are in seconds of perceived cost (run_pricing.py), the same unit as travel time,
so "generalized cost" here is simply free-flow time + toll seconds.
"""
from __future__ import annotations

import networkx as nx


def demand_response(free_time_s: float, toll_s: float, elasticity: float) -> float:
    """Fraction of an OD pair's trips still made once it faces `toll_s` of toll.

    free_time_s  free-flow travel time of the OD's shortest path (> 0)
    toll_s       toll on that path, in seconds of perceived cost (>= 0)
    elasticity   demand elasticity w.r.t. generalized cost, negative (e.g. -0.3)

    Must return a value in [0, 1], and exactly 1.0 when toll_s == 0.
    """
    # Constant elasticity on generalized cost (A13). Never reaches zero, which suits a
    # city where most peak trips are commutes with no real public-transport fallback.
    return ((free_time_s + toll_s) / free_time_s) ** elasticity


assert demand_response(600, 0, -0.3) == 1.0
assert 0 < demand_response(300, 600, -0.3) < demand_response(1200, 600, -0.3) < 1


def od_response(W, elasticity: float):
    """Return f(orig_name, dest_name) -> fraction of trips kept, for a tolled World."""
    g = nx.DiGraph()
    for link in W.LINKS:
        toll = link.congestion_pricing(0) if getattr(link, "congestion_pricing", None) else 0.0
        a, b, free = link.start_node.name, link.end_node.name, link.length / link.u
        if not g.has_edge(a, b) or free < g[a][b]["free"]:
            g.add_edge(a, b, free=free, toll=toll)
    paths = {}

    def response(orig: str, dest: str) -> float:
        if orig not in paths:
            paths[orig] = nx.single_source_dijkstra_path(g, orig, weight="free")
        path = paths[orig].get(dest)
        if not path or len(path) < 2:
            return 1.0
        hops = list(zip(path, path[1:]))
        free = sum(g[a][b]["free"] for a, b in hops)
        toll = sum(g[a][b]["toll"] for a, b in hops)
        keep = demand_response(free, toll, elasticity)
        assert 0.0 <= keep <= 1.0, f"demand_response returned {keep}"
        return keep

    return response
