#!/usr/bin/env python3
"""Does H1-H3's relative improvement still hold at the nodes GEH says the baseline
gets wrong (E6/D9)? One seed per config - a robustness spot-check, not a statistical
claim (compare.py's 15-seed paired sweep is the actual evidence for H1-H3 itself).

    python scripts/node_robustness_check.py
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402
from validate_hotspots import haversine_km  # noqa: E402
from compare import CONFIGS  # noqa: E402

# two failing nodes from E6/D9, one per error direction: Koteshwor undershoots
# (the largest GEH, 102.22), Sorakhutte overshoots (not the 2nd-worst by GEH -
# New Baneshwor is - but the only one of the four failures in the other direction).
NODES = {
    "Koteshwor": (27.6788, 85.3492),
    "Sorakhutte": (27.7188, 85.3096),
}


def node_delay(args, overrides: dict) -> dict[str, float]:
    for k, v in overrides.items():
        setattr(args, k, v)
    W, _zones = build_world(args, verbose=False)
    W.exec_simulation()
    a = W.analyzer
    a.basic_analysis()
    tt_by_link = {r["link"]: (r["average_travel_time"], r["free_travel_time"])
                  for _, r in a.link_to_pandas().iterrows()}
    node_pos, node_delay_s = {}, {}
    for l in W.LINKS:
        n = l.end_node.name
        node_pos.setdefault(n, (l.end_node.y, l.end_node.x))
        tt, free = tt_by_link.get(l.name, (0.0, 0.0))
        node_delay_s[n] = node_delay_s.get(n, 0.0) + max(0.0, tt - free)

    result = {}
    for name, (lat, lon) in NODES.items():
        best, best_km = None, 1e9
        for node, (nlat, nlon) in node_pos.items():
            d = haversine_km(lat, lon, nlat, nlon)
            if d < best_km:
                best, best_km = node, d
        result[name] = node_delay_s.get(best, 0.0)
    return result


def main() -> None:
    ap = argparse.ArgumentParser()
    add_model_args(ap)
    base_args = ap.parse_args()

    rows = {}
    for cfg_name, overrides in CONFIGS.items():
        args = argparse.Namespace(**vars(base_args))
        args.seed = base_args.seed
        rows[cfg_name] = node_delay(args, overrides)

    print(f"{'node':<12} " + " ".join(f"{c:>18}" for c in CONFIGS))
    for node in NODES:
        print(f"{node:<12} " + " ".join(f"{rows[c][node]:>18.1f}" for c in CONFIGS))

    print("\n% change vs fixed_time (same direction as the aggregate H1-H3 result = robust there):")
    base = rows["fixed_time"]
    for node in NODES:
        line = f"{node:<12} "
        for c in CONFIGS:
            if c == "fixed_time":
                continue
            pct = (rows[c][node] - base[node]) / base[node] * 100 if base[node] else 0.0
            line += f"{c}: {pct:+6.1f}%   "
        print(line)


if __name__ == "__main__":
    main()
