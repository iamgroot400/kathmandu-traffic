#!/usr/bin/env python3
"""Tidal-flow lever (H4): shift capacity from the light to the heavy direction on a
few radial corridors, matching whichever AM/PM period the demand file represents.

[SURVEY] Corridor choice is picked for being radial (endpoints differ in distance
from the mass-weighted centroid) and having >=2 lanes each direction to shift from -
not from a real traffic-engineering survey of where Kathmandu would site this.
"""
from __future__ import annotations

# (far_node, near_node, lanes_each_direction) - far->near is the AM-heavy (inbound)
# direction; near->far is the PM-heavy (outbound) direction. Found via
# scripts/build_od_directional.py's core-distance method, 3 highest radial_diff
# corridors with >=2 lanes/direction.
CORRIDORS = [
    ("1832324201", "1906513584", 4),  # Rabibhawan Road
    ("360703921", "4528047840", 2),   # Mahankal Marg
    ("1835345148", "4529763640", 2),  # Janata Marg
]


def apply_tidal_lanes(W, period: str, lane_shift: float = 1.0) -> int:
    """Shift `lane_shift` lane-equivalents of capacity from light to heavy direction.

    period: "am" (far->near heavy) or "pm" (near->far heavy). Scales capacity,
    capacity_out, capacity_in in proportion to the lane change - e.g. a 4-lane link
    gaining 1 lane-equivalent gets x1.25 capacity; a 4-lane link losing one gets x0.75.
    """
    if period not in ("am", "pm"):
        raise ValueError(f"period must be 'am' or 'pm', got {period!r}")

    link_by_ends = {(l.start_node.name, l.end_node.name): l for l in W.LINKS}
    applied = 0
    for far, near, lanes in CORRIDORS:
        inbound = link_by_ends.get((far, near))   # far -> near
        outbound = link_by_ends.get((near, far))  # near -> far
        if inbound is None or outbound is None:
            continue
        heavy, light = (inbound, outbound) if period == "am" else (outbound, inbound)
        heavy_factor = (lanes + lane_shift) / lanes
        light_factor = max(0.1, (lanes - lane_shift) / lanes)  # never fully close a direction
        for link, factor in [(heavy, heavy_factor), (light, light_factor)]:
            link.capacity *= factor
            link.capacity_out *= factor
            link.capacity_in *= factor
        applied += 1
    return applied


if __name__ == "__main__":
    # self-check: a 2-lane link losing 1 lane-equivalent should roughly halve capacity,
    # not go to zero or negative.
    class _FakeLink:
        def __init__(self, cap): self.capacity = self.capacity_out = self.capacity_in = cap
    far_link, near_link = _FakeLink(100.0), _FakeLink(100.0)
    class _FakeNode:
        def __init__(self, name): self.name = name
    class _FakeW:
        LINKS = []
    # build a minimal World-like object with 2 links for the self-check
    f, n = _FakeNode("F"), _FakeNode("N")
    far_link.start_node, far_link.end_node = f, n
    near_link.start_node, near_link.end_node = n, f
    _FakeW.LINKS = [far_link, near_link]
    _orig_corridors = CORRIDORS
    CORRIDORS = [("F", "N", 2)]
    applied = apply_tidal_lanes(_FakeW(), "am", lane_shift=1.0)
    assert applied == 1
    assert abs(far_link.capacity - 150.0) < 1e-6   # (2+1)/2 = 1.5x
    assert abs(near_link.capacity - 50.0) < 1e-6    # (2-1)/2 = 0.5x
    CORRIDORS = _orig_corridors
    print("self-check passed")
