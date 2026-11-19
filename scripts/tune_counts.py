#!/usr/bin/env python3
"""Count-tuning experiments: which lever brings modelled junction volumes to the JICA counts?

The 9 counted junctions are split once, before any tuning run, by a fixed random draw
(random.Random(20261118).sample(sorted names, 3)):
  tune (6):  Chabahil, Gausala, Kalimati, New Baneshwor, Old Baneshwor, Thapathali
  test (3):  Balaju, Kalanki, Koteshwor  -- held out: never printed while tuning
Target: GEH < 5 at all 6 tuning junctions, on the seed-mean entering volume (second hour of a
two-hour steady peak, PCU/h), with road speeds still near the JICA speed survey.

One idea per Kaggle notebook; each idea sweeps one lever and includes the unchanged baseline:
  peak         peak-hour factor K (share of daily trips in the peak hour)
  gateways     zones outside the network box enter on main roads only (valley entry roads)
  sidestreets  side-street capacity and speed (keeps traffic on the main roads)
  loading      loading junctions per zone, and trips inside one zone put on the network
  combined     levers chosen from the first four, given with --configs

    python scripts/tune_counts.py --idea peak --seeds 5 --jobs 3
    python scripts/tune_counts.py --idea peak --summary-only
    python scripts/tune_counts.py --idea combined --configs '{"k0.13_sub8": [["--k-peak","0.13","--sub","8"], []]}'
    python scripts/tune_counts.py --idea final --configs '...' --reveal-test   # only for the chosen config
"""
from __future__ import annotations

import argparse
import contextlib
import csv
import io
import json
import re
import statistics
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path[:0] = [str(ROOT / "scripts"), str(ROOT / "checks")]
NET = ROOT / "data" / "jica_net"
TUNE = ["Chabahil", "Gausala", "Kalimati", "New Baneshwor", "Old Baneshwor", "Thapathali"]
TEST = ["Balaju", "Kalanki", "Koteshwor"]
RUN = ["--data", "data/jica_net", "--minor-ways", "data/jica_net/minor_ways.txt",
       "--free-flow-kmh", "60", "--minor-free-flow-kmh", "30", "--priority-junctions",
       "--demand-scale", "1", "--pcu-factor", "1", "--demand-window", "7200", "--demand-growth", "2",
       "--measure-from", "3600"]
# name: (demand-builder args, extra run args); the first entry of each idea is the unchanged baseline
IDEAS = {
    "peak": {"base": ([], []), "k0.12": (["--k-peak", "0.12"], []), "k0.14": (["--k-peak", "0.14"], []),
             "k0.16": (["--k-peak", "0.16"], [])},
    "gateways": {"base": ([], []), "outer_main_sub4": (["--outer-main"], []),
                 "outer_main_sub2": (["--outer-main", "--sub", "2"], []),
                 "outer_main_sub1": (["--outer-main", "--sub", "1"], [])},
    "sidestreets": {"base": ([], []), "cap0.25": ([], ["--minor-capacity-ratio", "0.25"]),
                    "cap0.18": ([], ["--minor-capacity-ratio", "0.18"]),
                    "cap0.12": ([], ["--minor-capacity-ratio", "0.12"]),
                    "cap0.25_20kmh": ([], ["--minor-capacity-ratio", "0.25", "--minor-free-flow-kmh", "20"])},
    "loading": {"base": ([], []), "sub8": (["--sub", "8"], []), "intra0.5": (["--intrazonal", "0.5"], []),
                "intra1.0": (["--intrazonal", "1.0"], []), "sub8_intra0.5": (["--sub", "8", "--intrazonal", "0.5"], [])},
    # round 2: round 1 showed the busy junctions' approaches queued at 3-25x free-flow time,
    # so their limit is junction capacity, not demand
    "lanes": {"base": ([], []), "lanes2": ([], ["--min-main-lanes", "2"]), "lanes3": ([], ["--min-main-lanes", "3"]),
              "lanes2_gw1": (GW1 := ["--outer-main", "--sub", "1"], ["--min-main-lanes", "2"])},
    "saturation": {"base": ([], []), "rt0.8": ([], ["--reaction-time", "0.8"]),
                   "rt0.67": ([], ["--reaction-time", "0.67"]), "rt0.5": ([], ["--reaction-time", "0.5"])},
    "signals": {"base": ([], []), "cycle60": ([], ["--cycle", "60"]), "cycle120": ([], ["--cycle", "120"]),
                "cycle150": ([], ["--cycle", "150"])},
    "combined": {"base": ([], []), "gw1_rt0.67": (GW1, ["--reaction-time", "0.67"]),
                 "gw1_rt0.67_lanes2": (GW1, ["--reaction-time", "0.67", "--min-main-lanes", "2"]),
                 "gw1_rt0.5_lanes2": (GW1, ["--reaction-time", "0.5", "--min-main-lanes", "2"])},
}
# round 3: capacity alone gave the right volumes on roads far faster than the speed survey, demand alone
# jammed them; so each capacity setting (with round 1's entry roads) is crossed with higher peak demand
for idea, cap, ks in (("cap_rt0.8", ["--reaction-time", "0.8"], ("0.11", "0.12", "0.13")),
                      ("cap_rt0.67", ["--reaction-time", "0.67"], ("0.12", "0.13", "0.14")),
                      ("cap_lanes3", ["--min-main-lanes", "3"], ("0.11", "0.12", "0.13")),
                      ("cap_rt0.5_lanes2", ["--reaction-time", "0.5", "--min-main-lanes", "2"], ("0.12", "0.14", "0.16"))):
    IDEAS[idea] = {"base": ([], []), **{f"gw1_k{k}": (GW1 + ["--k-peak", k], cap) for k in ks}}
# round 4: zones loaded trips at their highest-degree nodes, i.e. at the big junctions themselves
# (1,860 PCU/h at each Baneshwor node); such trips bypass the junction's approaches and its count
MB = ["--midblock", "--outer-main"]
IDEAS["midblock"] = {"base": ([], []),
                     "mb_rt0.67_k0.14": (MB + ["--k-peak", "0.14"], ["--reaction-time", "0.67"]),
                     "mb_rt0.67_k0.12": (MB + ["--k-peak", "0.12"], ["--reaction-time", "0.67"]),
                     "mb_lanes3_k0.13": (MB + ["--k-peak", "0.13"], ["--min-main-lanes", "3"]),
                     "mb_rt0.5_lanes2_k0.14": (MB + ["--k-peak", "0.14"], ["--reaction-time", "0.5", "--min-main-lanes", "2"])}
# round 5: two network rules applied city-wide, fixed before any run. (1) UXsim read OSM `lanes` as
# per direction, doubling every tagged two-way road (the Ring Road at Chabahil/Gausala) while the
# one-way Baneshwor/Thapathali roads were right; (2) main links with the most roadside shops slow to 30 km/h
LANES = ["--osm-way-tags", "data/jica_net/osm_way_tags.csv"]
FRIC = LANES + ["--friction-kmh", "30", "--friction-share", "0.10"]
for idea, net in (("osmlanes", LANES), ("osmlanes_friction", FRIC)):
    IDEAS[idea] = {"base": ([], []), "net": ([], net),
                   "net_mb_k0.13": (MB + ["--k-peak", "0.13"], net),
                   "net_mb_rt0.67_k0.14": (MB + ["--k-peak", "0.14"], net + ["--reaction-time", "0.67"]),
                   "net_mb_rt0.5_k0.14": (MB + ["--k-peak", "0.14"], net + ["--reaction-time", "0.5"])}


def geh(m, o):
    return (2 * (m - o) ** 2 / (m + o)) ** 0.5


def run(idea: str, name: str, od_args: list, run_args: list, seed: int) -> str:
    out_dir = ROOT / "results" / f"tune_{idea}"
    out = out_dir / f"{name}_s{seed}.csv"
    if out.exists():
        return f"{out.name}: already done"
    files = []
    if od_args:
        tag = f"{idea}_{name}"
        files = ["--od-file", f"data/jica_net/od_matrix_{tag}.csv", "--zones-file", f"data/jica_net/zones_{tag}.csv"]
    tmp = out.with_suffix(".tmp")
    cmd = [sys.executable, "-u", str(ROOT / "scripts" / "dump_link_volumes.py"), *RUN, *files, *run_args,
           "--seed", str(seed), "--out", str(tmp)]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode:
        return f"{out.name}: FAILED\n{res.stderr[-2000:]}"
    out.with_suffix(".log").write_text(res.stdout, encoding="utf-8")
    tmp.replace(out)
    return f"{out.name}: {res.stdout.strip().splitlines()[-1]}"


def score(idea: str, configs: dict, reveal_test: bool, radius: float = 0) -> None:
    import geh_jica2012
    import speed_jica2012
    out_dir = ROOT / "results" / f"tune_{idea}"
    sfx = f"_r{radius:g}" if radius else ""   # cluster measure writes its own files
    rows, junc = [], []
    for name in configs:
        vols, per_seed = {}, []
        for f in sorted(out_dir.glob(f"{name}_s*.csv")):
            if not re.fullmatch(rf"{re.escape(name)}_s\d+\.csv", f.name):
                continue
            g_rel = f"tune_{idea}/_geh{sfx}_{f.stem}.csv"
            with contextlib.redirect_stdout(io.StringIO()):
                geh_jica2012.main(f.relative_to(ROOT / "results").as_posix(), g_rel, 0.786, radius)
            g = {r["intersection"]: r for r in csv.DictReader(open(ROOT / "results" / g_rel, encoding="utf-8"))}
            for k, r in g.items():
                vols.setdefault(k, []).append(float(r["model_pcu_h"]))
            obs = {k: float(r["observed_pcu_h"]) for k, r in g.items()}
            sp = speed_jica2012.model(str(f), str(NET / "minor_ways.txt"))
            done = re.search(r"completed ([\d.]+)%", f.with_suffix(".log").read_text(encoding="utf-8"))
            per_seed.append({"ring": sp["ring"], "inner": sp["inner"], "completed": float(done.group(1)),
                             "tune_pass": sum(float(g[k]["geh"]) < 5 for k in TUNE)})
        if not per_seed:
            continue
        mean = {k: statistics.fmean(v) for k, v in vols.items()}
        shown = TUNE + (TEST if reveal_test else [])
        for k in shown:
            junc.append({"config": name, "junction": k, "set": "tune" if k in TUNE else "test",
                         "observed_pcu_h": round(obs[k]), "model_pcu_h": round(mean[k]),
                         "ratio": round(mean[k] / obs[k], 3), "geh": round(geh(mean[k], obs[k]), 2)})
        row = {"config": name, "seeds": len(per_seed),
               "tune_pass_of_6": sum(geh(mean[k], obs[k]) < 5 for k in TUNE),
               "tune_pass_per_seed": round(statistics.fmean(s["tune_pass"] for s in per_seed), 2),
               "tune_share": round(sum(mean[k] for k in TUNE) / sum(obs[k] for k in TUNE), 3),
               "tune_mean_geh": round(statistics.fmean(geh(mean[k], obs[k]) for k in TUNE), 2),
               "ring_kmh": round(statistics.fmean(s["ring"] for s in per_seed), 1),
               "inner_kmh": round(statistics.fmean(s["inner"] for s in per_seed), 1),
               "completed_pct": round(statistics.fmean(s["completed"] for s in per_seed), 1)}
        if reveal_test:
            row["test_pass_of_3"] = sum(geh(mean[k], obs[k]) < 5 for k in TEST)
        rows.append(row)
    for path, data in ((out_dir.parent / f"tune_{idea}{sfx}_summary.csv", rows),
                       (out_dir.parent / f"tune_{idea}{sfx}_junctions.csv", junc)):
        with open(path, "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(data[0]))
            w.writeheader()
            w.writerows(data)
    print("survey: Ring Road 24.0 km/h, inner main roads 15.3 km/h; target: GEH < 5 at all 6 tuning junctions\n")
    print(f"{'config':<22}" + "".join(f"{k:>20}" for k in rows[0] if k != "config"))
    for r in rows:
        print(f"{r['config']:<22}" + "".join(f"{v:>20}" for k, v in r.items() if k != "config"))
    print()
    for k in TUNE + (TEST if reveal_test else []):
        cells = " ".join(f"{j['ratio']:>5.2f}/{j['geh']:>5.1f}" for j in junc if j["junction"] == k)
        print(f"{k:<15} {'tune' if k in TUNE else 'TEST'}  model/count, GEH per config: {cells}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--idea", required=True)
    ap.add_argument("--configs", help="JSON {name: [demand-builder args, run args]}; default: the idea's set")
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--summary-only", action="store_true")
    ap.add_argument("--reveal-test", action="store_true", help="also score the 3 held-out junctions")
    ap.add_argument("--radius", type=float, default=0,
                    help="count each junction as traffic entering all nodes within this many metres (0: one node)")
    a = ap.parse_args()
    configs = json.loads(a.configs) if a.configs else IDEAS[a.idea]
    assert not set(TUNE) & set(TEST) and len(TUNE + TEST) == 9
    (ROOT / "results" / f"tune_{a.idea}").mkdir(parents=True, exist_ok=True)
    if not a.summary_only:
        for name, (od_args, _) in configs.items():
            if od_args and not (NET / f"od_matrix_{a.idea}_{name}.csv").exists():
                subprocess.run([sys.executable, str(ROOT / "scripts" / "build_od_jica.py"), "--data", "data/jica_net",
                                *od_args, "--tag", f"{a.idea}_{name}"], cwd=ROOT, check=True)
        tasks = [(a.idea, n, od, ra, s) for s in range(1, a.seeds + 1) for n, (od, ra) in configs.items()]
        print(f"{len(tasks)} runs, {a.jobs} at a time", flush=True)
        with ProcessPoolExecutor(max_workers=a.jobs, max_tasks_per_child=1) as ex:
            for i, fut in enumerate(as_completed([ex.submit(run, *t) for t in tasks]), 1):
                print(f"[{i}/{len(tasks)}] {fut.result()}", flush=True)
    score(a.idea, configs, a.reveal_test, a.radius)


if __name__ == "__main__":
    main()
