#!/usr/bin/env python3
"""Seed sweep for the JICA-demand model, built to run on Kaggle.

Main configuration: JICA 2011 demand, arterial + tertiary network, side streets at 1 lane,
0.353 capacity, 30 km/h, give-way junctions, main roads 60 km/h, second (warmed-up) hour.
Also runs the yield-priority sensitivity (assumed 0.2; 0.1 and 0.4 tested).

Resumable: each finished run is a file in results/jica_sweep/, skipped on restart.

    python scripts/sweep_jica_seeds.py --jobs 4                 # all runs, then summary
    python scripts/sweep_jica_seeds.py --summary-only           # just the summary

Writes results/jica_sweep_summary.csv (one row per run) and prints mean +/- 95% CI.
"""
from __future__ import annotations

import argparse
import csv
import math
import re
import statistics
import subprocess
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from stats import ci95  # noqa: E402
OUT = ROOT / "results" / "jica_sweep"
BASE = ["--data", "data/jica_net", "--minor-ways", "data/jica_net/minor_ways.txt",
        "--free-flow-kmh", "60", "--minor-free-flow-kmh", "30", "--priority-junctions",
        "--demand-scale", "1", "--pcu-factor", "1",
        "--demand-window", "7200", "--demand-growth", "2", "--measure-from", "3600"]
CONFIGS = {"main_y0.2": (0.2, 15), "yield_0.1": (0.1, 5), "yield_0.4": (0.4, 5)}  # yield, seeds


def run(config: str, yield_p: float, seed: int) -> str:
    out = OUT / f"{config}_s{seed}.csv"
    if out.exists():
        return f"{out.name}: already done"
    tmp = out.with_suffix(".tmp")
    cmd = [sys.executable, "-u", str(ROOT / "scripts" / "dump_link_volumes.py"), *BASE,
           "--yield-priority", str(yield_p), "--seed", str(seed), "--out", str(tmp)]
    res = subprocess.run(cmd, cwd=ROOT, capture_output=True, text=True)
    if res.returncode:
        return f"{out.name}: FAILED\n{res.stderr[-2000:]}"
    (OUT / f"{config}_s{seed}.log").write_text(res.stdout, encoding="utf-8")
    tmp.replace(out)                              # only complete runs get the final name
    return f"{out.name}: {res.stdout.strip().splitlines()[-1]}"


def summary() -> None:
    sys.path.insert(0, str(ROOT / "checks"))
    import geh_jica2012
    import speed_jica2012
    import contextlib
    import io

    rows = []
    for f in sorted(OUT.glob("*_s*.csv")):
        if f.name.startswith("_"):
            continue                              # this function's own GEH files
        config, seed = re.match(r"(.+)_s(\d+)\.csv", f.name).groups()
        rel = f.relative_to(ROOT / "results").as_posix()
        with contextlib.redirect_stdout(io.StringIO()):
            geh_jica2012.main(rel, f"jica_sweep/_geh_{f.stem}.csv", 0.786)
        g = list(csv.DictReader(open(OUT / f"_geh_{f.stem}.csv", encoding="utf-8")))
        o = [float(r["observed_pcu_h"]) for r in g]
        m = [float(r["model_pcu_h"]) for r in g]
        mo, mm = statistics.mean(o), statistics.mean(m)
        corr = (sum((a - mo) * (b - mm) for a, b in zip(o, m))
                / math.sqrt(sum((a - mo) ** 2 for a in o) * sum((b - mm) ** 2 for b in m)))
        sp = speed_jica2012.model(str(f), str(ROOT / "data/jica_net/minor_ways.txt"))
        log = (OUT / f"{f.stem}.log").read_text(encoding="utf-8")
        mean_kmh, done = re.search(r"speed ([\d.]+) km/h, completed ([\d.]+)%", log).groups()
        rows.append({"config": config, "seed": int(seed), "mean_kmh": float(mean_kmh),
                     "completed_pct": float(done), "ring_kmh": round(sp["ring"], 2),
                     "inner_kmh": round(sp["inner"], 2), "share": round(sum(m) / sum(o), 4),
                     "corr": round(corr, 4),
                     "within_1_5": sum(abs(math.log(b / a)) < math.log(1.5) for a, b in zip(o, m)),
                     "geh_pass": sum(r["pass"] == "True" for r in g)})
    if not rows:
        print("no finished runs yet")
        return
    with open(ROOT / "results" / "jica_sweep_summary.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    print("observed (JICA 2012 survey): Ring Road 24.0 km/h, inner main roads 15.3 km/h\n")
    for config in CONFIGS:
        rs = [r for r in rows if r["config"] == config]
        if not rs:
            continue
        print(f"{config}  (n={len(rs)})")
        for k in ("ring_kmh", "inner_kmh", "completed_pct", "share", "corr", "within_1_5", "geh_pass"):
            m, h = ci95([r[k] for r in rs])
            print(f"  {k:<14}{m:8.3f} +/- {h:.3f}")
    print("\nwrote results/jica_sweep_summary.csv")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--jobs", type=int, default=4, help="parallel runs; keep at RAM / 5 GB")
    ap.add_argument("--summary-only", action="store_true")
    args = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if not args.summary_only:
        tasks = [(c, y, s) for c, (y, n) in CONFIGS.items() for s in range(1, n + 1)]
        print(f"{len(tasks)} runs, {args.jobs} at a time", flush=True)
        with ProcessPoolExecutor(max_workers=args.jobs) as ex:
            for i, fut in enumerate(as_completed([ex.submit(run, *t) for t in tasks]), 1):
                print(f"[{i}/{len(tasks)}] {fut.result()}", flush=True)
    summary()


if __name__ == "__main__":
    main()
