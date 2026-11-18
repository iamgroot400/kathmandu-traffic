#!/usr/bin/env python3
"""H1-H7 rerun on the JICA-demand baseline (D37), paired seeds, resumable. Built for Kaggle.

Baseline (D36): JICA 2011 demand, arterial + tertiary network, side streets 1 lane at
0.353 capacity and 30 km/h with give-way junctions, main roads 60 km/h, two-hour
steady peak (demand window 7200 s), horizon 14400 s. Each lever keeps its original
definition, translated to this baseline:

  H1 adaptive          queue-actuated signals
  H2 pricing           tolls 0.2 x each link's delay in an untolled baseline run
                       (results/tolls_jica.csv, run_pricing.py --save-tolls)
  H3 adaptive_pricing  both
  H4 am_tidal          AM-biased demand (od_matrix_am.csv) with tidal lanes, against
                       am_no_tidal: same demand, no lanes shifted. On this network 2 of
                       the 3 original corridors are found (one is split by a new junction)
  H5 parking           free-flow speeds x35/30 (as 30 -> 35 km/h originally): 70 / 35
  H6 staggered         same total demand over 1.5x the window (10800 s; was 3600 -> 5400)
  H7 decentralized     trips into the 10 core zones x0.75 (od_matrix_decentralized.csv),
                       against uniform_cut: every trip x the same total reduction, the
                       volume-matched control the 2026-11-10 audit required

Primary measure: tis_s, mean time in system over ALL vehicles (unfinished trips counted
to the horizon), which stranded trips cannot flatter (D27). Delay over completed trips
is recorded too, for comparison with the original paper.

    python scripts/compare_jica.py --seeds 15 --jobs 4
    python scripts/compare_jica.py --summary-only
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from stats import ci95  # noqa: E402

ROOT = Path(__file__).parent.parent
NET = ROOT / "data" / "jica_net"
BASE = {"data": NET, "minor_ways": NET / "minor_ways.txt", "free_flow_kmh": 60.0,
        "minor_free_flow_kmh": 30.0, "priority_junctions": True, "demand_scale": 1.0,
        "pcu_factor": 1.0, "demand_window": 7200, "demand_growth": 2.0, "tmax": 14400}
PRICING = {"toll_file": ROOT / "results" / "tolls_jica.csv", "toll_strength": 0.2}

CONFIGS = {
    "baseline":         {},
    "adaptive":         {"adaptive": True},
    "pricing":          {**PRICING},
    "adaptive_pricing": {"adaptive": True, **PRICING},
    "staggered":        {"demand_window": 10800},
    "parking":          {"free_flow_kmh": 70.0, "minor_free_flow_kmh": 35.0},
    "decentralized":    {"od_file": NET / "od_matrix_decentralized.csv"},
    "uniform_cut":      {"od_file": NET / "od_matrix_uniform.csv"},
    "am_no_tidal":      {"od_file": NET / "od_matrix_am.csv"},
    "am_tidal":         {"od_file": NET / "od_matrix_am.csv", "tidal_period": "am",
                         "tidal_lane_shift": 1.0},
}
# (hypothesis, config, compared against)
TESTS = [("H1", "adaptive", "baseline"), ("H2", "pricing", "baseline"),
         ("H3", "adaptive_pricing", "baseline"), ("H4", "am_tidal", "am_no_tidal"),
         ("H5", "parking", "baseline"), ("H6", "staggered", "baseline"),
         ("H7", "decentralized", "baseline"), ("H7 vs volume control", "decentralized", "uniform_cut")]
FIELDS = ["config", "seed", "completed", "delay_s", "travel_time_s", "speed_kmh", "tis_s", "trips"]
OUT = ROOT / "results" / "jica_h1h7.partial.csv"


def time_in_system_s(W) -> float:
    horizon = int(W.TMAX / W.DELTAT)
    total = 0.0
    for v in W.VEHICLES.values():
        end = v.arrival_time if v.state == "end" else horizon
        total += max(0, end - v.departure_time) * W.DELTAT
    return total / len(W.VEHICLES)


def worker(payload: dict) -> dict:
    import argparse as _ap
    from run_baseline import add_model_args, build_world

    ap = _ap.ArgumentParser()
    add_model_args(ap)
    args = ap.parse_args([])
    for k, v in {**BASE, **payload["overrides"]}.items():
        setattr(args, k, v)
    args.seed = payload["seed"]
    try:
        W, _ = build_world(args, verbose=False)
        W.exec_simulation()
        a = W.analyzer
        a.basic_analysis()
        return {"config": payload["config"], "seed": payload["seed"],
                "completed": a.trip_completed / a.trip_all if a.trip_all else 0.0,
                "delay_s": a.average_delay, "travel_time_s": a.average_travel_time,
                "speed_kmh": getattr(a, "average_speed", 0.0) * 3.6,
                "tis_s": time_in_system_s(W), "trips": a.trip_all}
    except Exception as exc:                      # one bad run must not kill the queue
        return {"config": payload["config"], "seed": payload["seed"], "error": repr(exc)}


def load():
    if not OUT.exists():
        return {}
    return {(r["config"], int(r["seed"])): r for r in csv.DictReader(open(OUT, encoding="utf-8"))}


def summary() -> None:
    rows = load()
    by = {}
    for (c, s), r in rows.items():
        by.setdefault(c, {})[s] = r
    print(f"{'config':<18}{'n':>3}{'time in system s':>18}{'delay s':>10}{'completed':>11}{'km/h':>7}")
    for c in CONFIGS:
        rs = list(by.get(c, {}).values())
        if rs:
            m = lambda k: ci95([float(r[k]) for r in rs])[0]
            print(f"{c:<18}{len(rs):>3}{m('tis_s'):>18.0f}{m('delay_s'):>10.0f}"
                  f"{m('completed'):>10.1%}{m('speed_kmh'):>7.1f}")
    print("\npaired over shared seeds, mean difference with 95% CI (negative = better)")
    for h, c, b in TESTS:
        shared = sorted(set(by.get(c, {})) & set(by.get(b, {})))
        if len(shared) < 2:
            print(f"{h:<22} {c} vs {b}: not enough paired seeds yet")
            continue
        for k, label in (("tis_s", "time in system"), ("delay_s", "delay (completed only)")):
            rel = [(float(by[c][s][k]) - float(by[b][s][k])) / float(by[b][s][k]) * 100 for s in shared]
            m, h95 = ci95(rel)
            sig = "significant" if abs(m) > h95 else "not significant"
            print(f"{h:<22} {c} vs {b}, {label:<22} {m:+6.1f}% +/- {h95:4.1f}  (n={len(shared)}, {sig})")
        dc = ci95([(float(by[c][s]["completed"]) - float(by[b][s]["completed"])) * 100 for s in shared])
        print(f"{'':<22} completion {dc[0]:+.1f} points +/- {dc[1]:.1f}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, default=15, help="last seed")
    ap.add_argument("--first-seed", type=int, default=1, help="to split the sweep across jobs")
    ap.add_argument("--jobs", type=int, default=4)
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    if not a.summary_only:
        assert PRICING["toll_file"].exists(), "make results/tolls_jica.csv first (see docstring)"
        done = load()
        tasks = [{"config": c, "seed": s, "overrides": ov} for s in range(a.first_seed, a.seeds + 1)
                 for c, ov in CONFIGS.items() if (c, s) not in done]
        print(f"{len(tasks)} runs to do ({len(done)} already done), {a.jobs} at a time", flush=True)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with ProcessPoolExecutor(max_workers=a.jobs, max_tasks_per_child=1) as ex:
            futs = [ex.submit(worker, t) for t in tasks]
            for i, f in enumerate(as_completed(futs), 1):
                r = f.result()
                if "error" in r:
                    print(f"[{i}/{len(tasks)}] {r['config']} s{r['seed']}: ERROR {r['error']}", flush=True)
                    continue
                new = not OUT.exists()
                with OUT.open("a", newline="", encoding="utf-8") as fh:
                    w = csv.DictWriter(fh, fieldnames=FIELDS)
                    if new:
                        w.writeheader()
                    w.writerow(r)
                print(f"[{i}/{len(tasks)}] {r['config']} s{r['seed']}: tis {r['tis_s']:.0f}s, "
                      f"delay {r['delay_s']:.0f}s, {r['completed']:.1%} complete", flush=True)
    summary()


if __name__ == "__main__":
    main()
