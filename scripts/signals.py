"""Add fixed-time traffic signals to an imported UXsim network.

UXsim's OSM importer creates every node as an unsignalised free merge, so a
freshly imported network has nothing for signal control to act on. This assigns a
two-phase fixed-time plan to every real intersection.

Approaches are grouped by their *axis* (bearing modulo 180), so opposing arms share
a phase - the standard arrangement. Green time is split in proportion to the lanes
each phase serves, which makes the baseline a reasonably-timed signal rather than a
deliberately bad one. Optimising against a strawman baseline inflates the apparent
benefit of whatever you do next.
"""
from __future__ import annotations

import math

# An approach within this many degrees of the reference axis shares its phase.
AXIS_TOLERANCE_DEG = 45.0


def _approach_axis(link) -> float:
    """Direction of travel along an incoming link, folded to a 0-180 axis.

    Opposing approaches (north-bound and south-bound on the same road) differ by
    180 degrees, so folding makes them identical and groups them together.
    """
    a, b = link.start_node, link.end_node
    return math.degrees(math.atan2(b.x - a.x, b.y - a.y)) % 180.0


def _axis_gap(p: float, q: float) -> float:
    """Angular distance on a 0-180 circle."""
    d = abs(p - q) % 180.0
    return min(d, 180.0 - d)


def split_phases(inlinks: list):
    """Split incoming links into two opposing-axis groups: (major, minor).

    Returns (None, None) when every approach shares one axis - that is a mid-link
    node or a bend, not an intersection, and signalising it would only add delay.
    """
    if len(inlinks) < 3:
        return None, None

    # the widest approach defines the major axis
    reference = max(inlinks, key=lambda l: l.number_of_lanes)
    ref_axis = _approach_axis(reference)

    major, minor = [], []
    for link in inlinks:
        target = major if _axis_gap(_approach_axis(link), ref_axis) <= AXIS_TOLERANCE_DEG else minor
        target.append(link)

    if not minor:
        return None, None
    return major, minor


def add_fixed_time_signals(W, cycle_s: float = 90.0, min_green: float = 10.0) -> dict:
    """Signalise every intersection in `W`. Returns a summary dict."""
    signalised = skipped = 0
    for node in W.NODES:
        inlinks = list(node.inlinks.values())
        major, minor = split_phases(inlinks)
        if major is None:
            skipped += 1
            continue

        # green in proportion to lanes served, so the busier road gets more of the cycle
        lanes_major = sum(l.number_of_lanes for l in major)
        lanes_minor = sum(l.number_of_lanes for l in minor)
        share = lanes_major / (lanes_major + lanes_minor)
        g_major = min(cycle_s - min_green, max(min_green, cycle_s * share))
        g_minor = cycle_s - g_major

        node.override_signal(signal=[g_major, g_minor], groups=[major, minor], reset=True)
        signalised += 1

    return {"signalised": signalised, "skipped": skipped, "cycle_s": cycle_s}


def self_check(W) -> None:
    """Assert the signal plan is coherent. Cheap, and catches silent misassignment."""
    for node in W.NODES:
        if node.signal == [0]:
            continue
        assert len(node.signal) == 2, f"{node.name}: expected 2 phases, got {node.signal}"
        assert abs(node.cycle_length - sum(node.signal)) < 1e-6, f"{node.name}: bad cycle"
        groups = {g for l in node.inlinks.values() for g in (l.signal_group or [])}
        assert groups == {0, 1}, f"{node.name}: phases actually used = {groups}"
        # every approach must get green in some phase, or its traffic can never discharge
        for l in node.inlinks.values():
            assert l.signal_group, f"{l.name} into {node.name} never receives green"
