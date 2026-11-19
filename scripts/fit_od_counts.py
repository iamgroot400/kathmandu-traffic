#!/usr/bin/env python3
"""Fit origin-destination flows to the 6 tuning junction counts (path-based multiplicative OD estimation).

Each iteration: simulate --seeds seeds with the current OD file; at each of the 6 tuning junctions
(scripts/tune_counts.py TUNE) take r = counted / modelled entering volume; route every OD pair on
the shortest path over the simulated link travel times; multiply the pair's demand by the product
of r ** alpha over the tuning junctions its path enters (clipped to [1/clip, clip]); round to whole
platoons. The 3 held-out junctions are never used or printed. This fits the counts directly, so
afterwards the 6 tuning junctions are calibration targets; only the 3 held-out junctions validate.

    python scripts/fit_od_counts.py --start "--midblock --outer-main --k-peak 0.14" \
        --run "--reaction-time 0.67" --iterations 5 --seeds 3 --jobs 3 --radius 100
Writes data/jica_net/od_matrix_odme_<i>.csv per iteration and results/odme/log.csv.
"""
from __future__ import annotations

import argparse
import csv
import shlex
import statistics
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor
from pathlib import Path

import networkx as nx

ROOT = Path(__file__).parent.parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "checks")]
from geh_jica2012 import NODES, cluster_entering, cluster_group, geh  # noqa: E402
from tune_counts import RUN, TUNE  # noqa: E402
import speed_jica2012  # noqa: E402
from build_od_jica import largest_remainder  # noqa: E402

NET = ROOT / "data" / "jica_net"
OUT = ROOT / "results" / "odme"
PCU = 0.786


def observed():
    obs = {}
    for r in csv.DictReader(open(ROOT / "data/jica2012/intersection_counts_2011.csv", encoding="utf-8")):
        if r["intersection"] in TUNE:
            obs[r["intersection"]] = (float(r["am_entering_veh_h"]) + float(r["pm_entering_veh_h"])) / 2 * PCU
    return obs


def simulate(args):
    od, zones, run_args, seed, out = args
    if out.exists():                       # resumable: a finished seed is kept
        return out
    cmd = [sys.executable, "-u", str(ROOT / "scripts" / "dump_link_volumes.py"), *RUN, "--od-file", str(od),
           "--zones-file", str(zones), *run_args, "--seed", str(seed), "--out", str(out)]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode:
        raise RuntimeError(res.stderr[-2000:])
    return out


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--start", default="", help="build_od_jica.py options for the starting OD")
    ap.add_argument("--run", default="", help="extra run options (capacity settings)")
    ap.add_argument("--iterations", type=int, default=5)
    ap.add_argument("--seeds", type=int, default=3)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--alpha", type=float, default=0.5, help="damping exponent on each junction's ratio")
    ap.add_argument("--clip", type=float, default=1.5, help="largest change per pair per iteration")
    ap.add_argument("--radius", type=float, default=0)
    ap.add_argument("--stop-after-update", action="store_true", help="write the next OD file, then stop (testing)")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    run_args = shlex.split(a.run)
    subprocess.run([sys.executable, str(ROOT / "scripts" / "build_od_jica.py"), "--data", "data/jica_net",
                    *shlex.split(a.start), "--tag", "odme_0"], cwd=ROOT, check=True)
    zones = NET / "zones_odme_0.csv"
    obs = observed()
    log = []
    for it in range(a.iterations + 1):
        od_file = NET / f"od_matrix_odme_{it}.csv"
        dumps = [OUT / f"it{it}_s{s}.csv" for s in range(1, a.seeds + 1)]
        with ProcessPoolExecutor(max_workers=a.jobs, max_tasks_per_child=1) as ex:
            list(ex.map(simulate, [(od_file, zones, run_args, s, d) for s, d in zip(range(1, a.seeds + 1), dumps)]))
        runs = [list(csv.DictReader(open(d, encoding="utf-8"))) for d in dumps]
        model = {k: statistics.fmean(cluster_entering(rows, NODES[k], a.radius) for rows in runs) for k in TUNE}
        sp = [speed_jica2012.model(str(d), str(NET / "minor_ways.txt")) for d in dumps]
        demand = {(r["origin_id"], r["dest_id"]): int(r["demand"]) for r in csv.DictReader(open(od_file, encoding="utf-8"))}
        row = {"iteration": it, "pairs": len(demand), "demand_pcu": sum(demand.values()),
               "tune_pass_of_6": sum(geh(model[k], obs[k]) < 5 for k in TUNE),
               "tune_mean_geh": round(statistics.fmean(geh(model[k], obs[k]) for k in TUNE), 2),
               "ring_kmh": round(statistics.fmean(s["ring"] for s in sp), 1),
               "inner_kmh": round(statistics.fmean(s["inner"] for s in sp), 1),
               **{k: round(model[k] / obs[k], 3) for k in TUNE}}
        log.append(row)
        print(" ".join(f"{k}={v}" for k, v in row.items()), flush=True)
        with open(OUT / "log.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(log[0]))
            w.writeheader()
            w.writerows(log)
        if it == a.iterations or row["tune_pass_of_6"] == 6:
            print(f"final OD: {od_file}  ({row['tune_pass_of_6']}/6 tuning junctions pass)")
            break
        # route every pair on the simulated travel times (mean over seeds)
        tt = {}
        for rows in runs:
            for r in rows:
                tt.setdefault((r["start"], r["end"]), []).append(float(r["tt_s"]))
        g = nx.DiGraph()
        g.add_weighted_edges_from((u, v, statistics.fmean(t)) for (u, v), t in tt.items())
        groups = {k: cluster_group(runs[0], NODES[k], a.radius) for k in TUNE}
        ratio = {k: (obs[k] / max(model[k], 1.0)) ** a.alpha for k in TUNE}
        by_origin = {}
        for (o, d), v in demand.items():
            by_origin.setdefault(o, []).append((d, v))
        new = {}
        for o, pairs in by_origin.items():
            paths = nx.single_source_dijkstra_path(g, o[1:], weight="weight")
            for d, v in pairs:
                path = paths.get(d[1:], [])
                f = 1.0
                for k, grp in groups.items():   # the path enters junction k's group from outside it
                    if any(path[i] not in grp and path[i + 1] in grp for i in range(len(path) - 1)):
                        f *= ratio[k]
                new[o, d] = v * min(a.clip, max(1 / a.clip, f))
        keys = list(new)
        units = largest_remainder(round(sum(new.values()) / 5), [new[k] for k in keys])
        with open(NET / f"od_matrix_odme_{it + 1}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.writer(fh)
            w.writerow(["origin_id", "dest_id", "demand"])
            for k, u in zip(keys, units):
                if u:
                    w.writerow([k[0], k[1], u * 5])
        print(f"wrote od_matrix_odme_{it + 1}.csv: {sum(units) * 5:,} PCU in {sum(1 for u in units if u):,} pairs", flush=True)
        if a.stop_after_update:
            break


if __name__ == "__main__":
    main()
