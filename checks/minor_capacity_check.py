#!/usr/bin/env python3
"""Self-check for D36: does capping a link's capacity_out after creation really cap its
discharge? Saturated two-link corridor, measured flow vs the cap.

    .venv/Scripts/python.exe checks/minor_capacity_check.py
"""
from uxsim import World


def outflow(ratio):
    W = World(name="t", deltan=5, tmax=3600, print_mode=0, save_mode=0, show_mode=0, random_seed=0)
    W.addNode("a", 0, 0); W.addNode("b", 1, 0); W.addNode("c", 2, 0); W.addNode("d", 3, 0)
    up = W.addLink("up", "a", "b", length=500, free_flow_speed=30 / 3.6, jam_density_per_lane=0.2, number_of_lanes=2)
    dn = W.addLink("dn", "b", "c", length=500, free_flow_speed=30 / 3.6, jam_density_per_lane=0.2, number_of_lanes=1)
    W.addLink("ex", "c", "d", length=500, free_flow_speed=30 / 3.6, jam_density_per_lane=0.2, number_of_lanes=2)
    if ratio:
        dn.capacity_out = ratio * dn.capacity
        dn.capacity_out_remain = dn.capacity_out * W.DELTAT
    W.adddemand("a", "d", 0, 3000, flow=2 * dn.capacity)     # far more than one lane can carry
    W.exec_simulation()
    measured = (dn.departure_count(3000) - dn.departure_count(1000)) / 2000
    return measured, dn.capacity


base, cap = outflow(None)
capped, _ = outflow(6000 / 17000)
print(f"lane capacity {cap:.3f} veh/s | uncapped outflow {base:.3f} | capped outflow {capped:.3f} "
      f"| ratio {capped / base:.2f} (target 0.35)")
assert abs(capped / base - 6000 / 17000) < 0.08, "capacity_out cap does not bind as intended"
