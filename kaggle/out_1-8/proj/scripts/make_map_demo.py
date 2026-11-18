#!/usr/bin/env python3
"""Export one paired run (fixed-time vs adaptive + pricing, same seed) as the data
for the animated map demo, and write demo/index.html from demo/template.html.

Seed 11 is the seed whose delay change (-65.7%) is closest to the 15-seed mean
(-65.3%), with both arms completing every trip: a typical run, not the best one.

    python scripts/make_map_demo.py            # two simulations, one after the other
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).parent))
from run_baseline import add_model_args, build_world  # noqa: E402
from validate_hotspots import LANDMARKS  # noqa: E402

ROOT = Path(__file__).parent.parent
TOLLS = ROOT / "results" / "tolls.csv"
SCENARIOS = {
    "fixed": {},
    "combined": {"adaptive": True, "toll_file": TOLLS, "toll_strength": 0.2},
}
BIN_S, TMAX, SEED = 240, 14400, 11


def run(overrides: dict) -> dict:
    ap = argparse.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    args.tmax, args.seed = TMAX, SEED
    for k, v in overrides.items():
        setattr(args, k, v)
    W, _ = build_world(args, verbose=False)
    W.exec_simulation()
    a = W.analyzer
    a.basic_analysis()
    a.compute_edie_state()

    nbins = TMAX // BIN_S
    speed, dist, time = [], np.zeros(nbins), np.zeros(nbins)
    for l in W.LINKS:
        step = int(BIN_S // l.edie_dt)
        assert step * l.edie_dt == BIN_S, f"BIN_S must be a multiple of the Edie step {l.edie_dt}"
        k = l.k_mat[: nbins * step].reshape(nbins, step, -1)
        q = l.q_mat[: nbins * step].reshape(nbins, step, -1)
        veh_s = k.sum(axis=(1, 2)) * l.edie_dx * l.edie_dt      # vehicle-seconds on the link
        veh_m = q.sum(axis=(1, 2)) * l.edie_dx * l.edie_dt      # vehicle-metres travelled
        ratio = np.where(veh_s > 0, veh_m / np.maximum(veh_s, 1e-9) / l.u, 1.0)
        speed.append("".join(str(int(min(9, max(0, r * 10)))) for r in ratio))   # 0 = stopped, 9 = free flow
        dist += veh_m
        time += veh_s

    horizon = TMAX / W.DELTAT
    arrivals = np.array([v.arrival_time if v.state == "end" else horizon * 2 for v in W.VEHICLES.values()])
    done = [float((arrivals <= (b + 1) * BIN_S / W.DELTAT).mean()) for b in range(nbins)]
    left = [(1 - d) * a.trip_all for d in done]
    assert all(t / BIN_S <= n + 1 for t, n in zip(time[1:], left[:-1])), "more vehicles on the road than unfinished trips"
    return {
        "speed": speed,
        "kmh": [round(float(d / t * 3.6), 1) if t > 0 else None for d, t in zip(dist, time)],
        "onroad": [round(float(t / BIN_S)) for t in time],
        "done": [round(d, 4) for d in done],
        "delay_min": round(a.average_delay / 60, 1),
        "links": [[l.start_node.x, l.start_node.y, l.end_node.x, l.end_node.y, l.number_of_lanes] for l in W.LINKS],
        "trips": int(a.trip_all),
    }


def main() -> None:
    out = {name: run(ov) for name, ov in SCENARIOS.items()}
    assert out["fixed"]["links"] == out["combined"]["links"]
    data = {"bin_s": BIN_S, "seed": SEED, "links": out["fixed"].pop("links"),
            "landmarks": [[n, lon, lat] for n, (lat, lon) in LANDMARKS.items()], **out}
    out["combined"].pop("links")
    demo = ROOT / "demo"
    (demo / "data.json").write_text(json.dumps(data, separators=(",", ":")), encoding="utf-8")
    html = (demo / "template.html").read_text(encoding="utf-8").replace("/*DATA*/null", json.dumps(data, separators=(",", ":")))
    (demo / "index.html").write_text(html, encoding="utf-8")
    for n in SCENARIOS:
        print(f"{n}: mean delay {out[n]['delay_min']} min, completed {out[n]['done'][-1]:.1%}, trips {out[n]['trips']}")
    print(f"wrote {demo / 'index.html'}")


if __name__ == "__main__":
    main()
