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

# Approaches spread by less than this all point the same way: a parallel merge or a
# bend, where a signal would only add delay. Above it, flows genuinely conflict.
MIN_CONFLICT_DEG = 30.0


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
    """Split incoming links into two conflicting groups, one per signal phase.

    A node needs a signal when two or more approaches arrive on meaningfully
    different axes and compete for the same downstream capacity. That includes
    two roads merging at a sharp angle, not just classic crossroads - the worst
    bottleneck in this network is a three-into-one merge.

    Returns (None, None) below three approaches, or when every approach points the
    same way: a bend or a parallel merge, where a signal would only add delay.

    Three approaches, not two, is deliberate. Signalising every two-way merge costs
    so much capacity that the network stops draining (78% of trips complete instead
    of 100%), and real networks give way at merges rather than signalising them.
    Two-approach merges that still congest are a geometry problem, not a signal one.
    """
    if len(inlinks) < 3:
        return None, None

    pairs = sorted(((_approach_axis(l), l) for l in inlinks), key=lambda t: t[0])
    axes = [a for a, _ in pairs]
    if axes[-1] - axes[0] < MIN_CONFLICT_DEG:
        return None, None

    # Split where consecutive approaches are furthest apart in angle. On a crossroads
    # this puts the opposing pairs together, which is the standard arrangement.
    _, k = max((axes[i + 1] - axes[i], i) for i in range(len(axes) - 1))
    return [l for _, l in pairs[:k + 1]], [l for _, l in pairs[k + 1:]]


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
