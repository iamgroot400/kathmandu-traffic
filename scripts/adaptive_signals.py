#!/usr/bin/env python3
"""Queue-actuated signal control: serve whichever phase has the longest queue.

Attached to each signalised node through UXsim's `user_function`, which runs every
timestep and may rewrite `signal_phase`.

A note on naming: this is *queue-actuated* control, not true max-pressure. Proper
max-pressure subtracts the downstream queue of each turning movement, which needs
turn-movement data that a mesoscopic model does not carry - every approach here
feeds all outgoing links indiscriminately. Subtracting a term common to all phases
would not change which phase wins, so the honest description is "serve the longest
queue", and calling it max-pressure would overclaim.

This is the fair intermediate baseline for the DRL work. Comparing a neural
controller only against fixed-time cannot separate "the network learned something"
from "any adaptive control helps".
"""
from __future__ import annotations


def phase_queue(node, phase: int) -> float:
    """Vehicles queued on the approaches that receive green in `phase`."""
    total = 0.0
    for link in node.inlinks.values():
        if phase in (link.signal_group or []):
            total += link.num_vehicles_queue
    return total


# Yellow plus all-red. Every phase change forfeits this much discharge time.
LOST_TIME_S = 3.0
# Vehicles per second of green a single lane discharges, mixed motorcycle traffic.
DISCHARGE_VEH_PER_S_LANE = 0.5


def should_switch(current_queue: float, best_queue: float, best_phase: int,
                  current_phase: int, elapsed: float,
                  min_green: float, max_green: float,
                  lanes_served: float = 2.0,
                  lost_time: float = LOST_TIME_S) -> bool:
    """Decide whether to end the current green phase now.

    Called every timestep for each signalised intersection.

    current_queue : vehicles queued on approaches currently showing green
    best_queue    : vehicles queued on the best alternative phase
    best_phase    : index of that alternative
    current_phase : index of the phase running now
    elapsed       : seconds the current phase has been green

    Return True to switch to `best_phase`, False to hold.
    """
    if elapsed < min_green:
        return False                      # safety floor: never cut off a crossing
    if elapsed >= max_green:
        return best_queue > 0             # fairness ceiling: anyone waiting gets a turn

    # In between, the alternative must beat the current phase by more than switching
    # costs. A phase change forfeits `lost_time` seconds of discharge to yellow and
    # all-red, so the imbalance has to exceed the vehicles that would have cleared in
    # that time - otherwise the signal flaps and throughput falls while each individual
    # switch looks locally justified.
    forfeited = lost_time * DISCHARGE_VEH_PER_S_LANE * lanes_served
    return best_queue > current_queue + forfeited


def make_controller(min_green: float, max_green: float):
    def controller(node):
        if node.signal == [0]:
            return
        phases = list(range(len(node.signal)))
        current = node.signal_phase
        queues = {p: phase_queue(node, p) for p in phases}
        best = max((p for p in phases if p != current), key=lambda p: queues[p],
                   default=current)

        # how much discharge capacity the current phase forfeits by switching
        lanes = sum(l.number_of_lanes for l in node.inlinks.values()
                    if current in (l.signal_group or [])) or 1.0

        if should_switch(queues[current], queues[best], best, current,
                         node.signal_t, min_green, max_green, lanes_served=lanes):
            node.signal_phase = best
            node.signal_t = 0.0

    return controller


def attach(W, min_green: float = 10.0, max_green: float = 60.0) -> int:
    """Put the controller on every signalised node. Returns how many."""
    controller = make_controller(min_green, max_green)
    n = 0
    for node in W.NODES:
        if node.signal != [0]:
            node.user_function = controller
            n += 1
    return n


def self_check() -> None:
    """The rule must respect min green and must not starve a waiting approach."""
    # below min green: never switch, however bad it looks
    assert not should_switch(0.0, 99.0, 1, 0, 1.0, 10.0, 60.0), \
        "switched before min green - this would cut vehicles off mid-crossing"
    # past max green with traffic waiting elsewhere: must switch or that approach starves
    assert should_switch(99.0, 5.0, 1, 0, 61.0, 10.0, 60.0), \
        "held past max green while another approach had a queue"
    # clearly better alternative, min green satisfied: should switch
    assert should_switch(0.0, 50.0, 1, 0, 30.0, 10.0, 60.0), \
        "did not switch to a phase with a much longer queue"
    # imbalance smaller than the discharge forfeited to clearance: hold.
    # 3 s lost time x 0.5 veh/s/lane x 2 lanes = 3 vehicles must be beaten.
    assert not should_switch(10.0, 12.0, 1, 0, 30.0, 10.0, 60.0, lanes_served=2.0), \
        "switched for a 2-vehicle gain that costs 3 vehicles of lost discharge"
    assert should_switch(10.0, 14.0, 1, 0, 30.0, 10.0, 60.0, lanes_served=2.0), \
        "held despite a gain larger than the clearance cost"


if __name__ == "__main__":
    self_check()
    print("switching rule passes its checks")
