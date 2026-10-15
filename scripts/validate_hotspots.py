#!/usr/bin/env python3
"""Face-validity check: do the model's worst links sit where Kathmandu's are?

This is NOT validation. Validation needs observed link counts and a GEH test. What
this does is weaker but still useful: it asks whether the places the model says are
congested coincide with places widely known to be congested. Passing does not make
the model right; failing would make it clearly wrong.

    python scripts/validate_hotspots.py

Outputs results/hotspots.csv and a console summary.
"""
from __future__ import annotations

import argparse
import csv
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402

# [SURVEY] Approximate landmark positions, good to roughly a hundred metres. They are
# matched to the nearest network node, and the distance is printed so a bad match is
# visible rather than silent.
LANDMARKS = {
    "Koteshwor":  (27.6788, 85.3492),
    "Maitighar":  (27.6939, 85.3208),
    "Kalanki":    (27.6939, 85.2807),
    "Chabahil":   (27.7172, 85.3464),
    "Gwarko":     (27.6667, 85.3300),
    "Jadibuti":   (27.6781, 85.3646),
    "Thapathali": (27.6934, 85.3170),
}

# Measured earlier in this project, before calibration: raw OSM speeds (50 km/h),
# no PCU weighting, full citywide demand on an arterial-only network.
PRE_CALIBRATION = {
    "label": "uncalibrated (OSM speeds, no PCU, full demand)",
    "completed_pct": 12.0,
    "speed_kmh": 3.1 * 3.6,
    "delay_ratio": 0.679,
}


def haversine_km(lat1, lon1, lat2, lon2) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dphi, dlmb = math.radians(lat2 - lat1), math.radians(lon2 - lon1)
    a = math.sin(dphi / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dlmb / 2) ** 2
    return 2 * 6371.0 * math.asin(math.sqrt(a))


def main() -> None:
    ap = argparse.ArgumentParser(description="Hotspot face-validity diagnostic")
    add_model_args(ap)
    ap.add_argument("--top", type=int, default=10)
    ap.add_argument("--out", type=Path, default=Path("results/hotspots.csv"))
    args = ap.parse_args()

    W, _zones = build_world(args, verbose=False)

    # Queues must be sampled *during* the run. Reading num_vehicles_queue afterwards
    # always returns 0, because by then the network has drained.
    peak_queue = {l.name: 0.0 for l in W.LINKS}
    while W.check_simulation_ongoing():
        W.exec_simulation(duration_t=60)
        for l in W.LINKS:
            if l.num_vehicles_queue > peak_queue[l.name]:
                peak_queue[l.name] = l.num_vehicles_queue

    a = W.analyzer
    a.basic_analysis()

    # Per-link travel times come from the analyzer. `actual_travel_time(0)` would be
    # the travel time at t=0 on an empty network - always equal to free flow.
    tt_by_link = {}
    for _, r in a.link_to_pandas().iterrows():
        tt_by_link[r["link"]] = (r["average_travel_time"], r["free_travel_time"])

    hours = args.demand_window / 3600.0
    rows = []
    for link in W.LINKS:
        # Count departures within the demand window only. Counting over the whole
        # simulation (which runs on so the network can drain) and dividing by the
        # one-hour peak inflates V/C by up to 3x.
        volume = link.departure_count(args.demand_window)
        total_volume = link.departure_count(W.TMAX)
        cap_veh_h = getattr(link, "capacity", 0.0) * 3600.0
        vc = (volume / hours) / cap_veh_h if cap_veh_h > 0 else 0.0
        tt, free = tt_by_link.get(link.name, (0.0, 0.0))
        rows.append({
            "link": link.name,
            "end_node": link.end_node.name,
            "end_lat": link.end_node.y,
            "end_lon": link.end_node.x,
            "volume_peak_hour": volume,
            "volume_total": total_volume,
            "capacity_veh_h": round(cap_veh_h, 1),
            "vc_ratio": round(vc, 3),
            "delay_s": round(max(0.0, tt - free), 1),
            "queue_veh": round(peak_queue.get(link.name, 0.0), 1),
        })

    by_vc = sorted(rows, key=lambda r: r["vc_ratio"], reverse=True)
    by_delay = sorted(rows, key=lambda r: r["delay_s"], reverse=True)

    print(f"\n{'='*74}\nTOP {args.top} LINKS BY VOLUME / CAPACITY\n{'='*74}")
    print(f"{'#':>3} {'link':<28} {'V/C':>6} {'vol':>7} {'delay s':>8} {'queue':>6}")
    for i, r in enumerate(by_vc[:args.top], 1):
        print(f"{i:>3} {r['link'][:28]:<28} {r['vc_ratio']:>6.2f} "
              f"{r['volume_peak_hour']:>7.0f} {r['delay_s']:>8.1f} {r['queue_veh']:>6.1f}")

    # which nodes are hotspots, so landmarks can be checked against them
    hot_nodes = {r["end_node"] for r in by_vc[:args.top]} | {r["end_node"] for r in by_delay[:args.top]}
    node_pos = {}
    for r in rows:
        node_pos.setdefault(r["end_node"], (r["end_lat"], r["end_lon"]))

    print(f"\n{'='*74}\nFACE VALIDITY vs KNOWN KATHMANDU BOTTLENECKS\n{'='*74}")
    print(f"{'landmark':<12} {'nearest node':>13} {'dist km':>8} {'V/C':>6} {'delay s':>8}  hotspot?")
    hits = 0
    for name, (lat, lon) in LANDMARKS.items():
        best, best_km = None, 1e9
        for node, (nlat, nlon) in node_pos.items():
            d = haversine_km(lat, lon, nlat, nlon)
            if d < best_km:
                best, best_km = node, d
        at_node = [r for r in rows if r["end_node"] == best]
        vc = max((r["vc_ratio"] for r in at_node), default=0.0)
        dly = max((r["delay_s"] for r in at_node), default=0.0)
        is_hot = best in hot_nodes
        hits += is_hot
        flag = "YES" if is_hot else "no"
        warn = "  <- poor match" if best_km > 0.5 else ""
        print(f"{name:<12} {best:>13} {best_km:>8.2f} {vc:>6.2f} {dly:>8.1f}  {flag}{warn}")

    print(f"\n{hits}/{len(LANDMARKS)} known bottlenecks appear in the model's top-{args.top} lists.")

    print(f"\n{'='*74}\nPRE- vs POST-CALIBRATION\n{'='*74}")
    post_speed = getattr(a, "average_speed", 0.0) * 3.6
    post_done = a.trip_completed / a.trip_all * 100 if a.trip_all else 0.0
    post_ratio = a.average_delay / a.average_travel_time if a.average_travel_time else 0.0
    veh_h = a.average_delay * a.trip_completed / 3600.0
    print(f"{'metric':<22} {'pre-calibration':>18} {'calibrated':>14}")
    print(f"{'trips completed':<22} {PRE_CALIBRATION['completed_pct']:>17.0f}% {post_done:>13.0f}%")
    print(f"{'mean speed (km/h)':<22} {PRE_CALIBRATION['speed_kmh']:>18.1f} {post_speed:>14.1f}")
    print(f"{'delay ratio':<22} {PRE_CALIBRATION['delay_ratio']:>18.2f} {post_ratio:>14.2f}")
    print(f"{'total delay (veh-h)':<22} {'n/a (gridlocked)':>18} {veh_h:>14,.0f}")
    print(f"\npre-calibration: {PRE_CALIBRATION['label']}")
    print("Completion is the key column: an uncalibrated run that strands 88% of trips "
          "cannot be compared on delay at all.")

    args.out.parent.mkdir(parents=True, exist_ok=True)
    with args.out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(by_vc)
    print(f"\nwrote {args.out}")


if __name__ == "__main__":
    main()
