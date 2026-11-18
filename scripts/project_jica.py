#!/usr/bin/env python3
"""Demand growth projection on the JICA baseline (D38), paired seeds, resumable. Built for Kaggle.

The baseline's demand is the 2011 JICA survey, so growth is counted from 2011 at the
JICA/DoR 2024 main-section forecast, 4.52%/yr (Table 4.4.2). Factors fixed before any run:
  x1.203  4.19 yr, the first version's factor (comparability only)
  x1.941  15 yr, 2011 -> 2026 (about today)
  x2.316  19 yr, 2011 -> end of 2030 (main projection)
Each factor is its own OD file (scripts/build_growth_od.py): the same pairs, grown in whole
UXsim platoons, so the vehicles created match the request as closely as in the baseline.
Horizon 21600 s for every arm, baseline included. Primary measure: completion and time in
system over all vehicles; completed-trip delay is biased here (D27, D33).

    python scripts/project_jica.py --first-seed 1 --seeds 8 --jobs 3
    python scripts/project_jica.py --summary-only
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from stats import ci95  # noqa: E402
from compare_jica import BASE, FIELDS, worker  # noqa: E402

LOG = 60   # vehicle log every 60 steps: full logs of 269k gridlocked vehicles exceed 30 GB (D38)
NET = BASE["data"]
CONFIGS = {"baseline": {"tmax": 21600, "vehicle_log_interval": LOG, "platoon_fix": True}}
# grown OD files from build_growth_od.py: same pairs, whole platoons (a fractional
# demand_growth would drop up to 4 vehicles per pair, 13% at x1.20)
for name, f in (("x1.20_4yr", "g4yr"), ("x1.94_2026", "g2026"), ("x2.32_2030", "g2030")):
    CONFIGS[name] = {"tmax": 21600, "vehicle_log_interval": LOG, "platoon_fix": True, "od_file": NET / f"od_matrix_{f}.csv"}
OUT = Path(__file__).parent.parent / "results" / "jica_projection.partial.csv"


def load():
    if not OUT.exists():
        return {}
    return {(r["config"], int(r["seed"])): r for r in csv.DictReader(open(OUT, encoding="utf-8"))}


def summary() -> None:
    by = {}
    for (c, s), r in load().items():
        by.setdefault(c, {})[s] = r
    base = by.get("baseline", {})
    print(f"{'config':<12}{'n':>3}{'completed':>16}{'time in system s':>20}{'vs baseline':>20}")
    for c in CONFIGS:
        rs = by.get(c, {})
        if not rs:
            continue
        comp = ci95([float(r["completed"]) * 100 for r in rs.values()])
        tis = ci95([float(r["tis_s"]) for r in rs.values()])
        shared = sorted(set(rs) & set(base))
        rel = ci95([(float(rs[s]["tis_s"]) - float(base[s]["tis_s"])) / float(base[s]["tis_s"]) * 100
                    for s in shared]) if c != "baseline" and len(shared) > 1 else None
        vs = f"{rel[0]:+.1f}% +/- {rel[1]:.1f}" if rel else "n/a"
        print(f"{c:<12}{len(rs):>3}{comp[0]:>9.1f}% +/-{comp[1]:4.1f}{tis[0]:>12.0f} +/-{tis[1]:4.0f}{vs:>20}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--seeds", type=int, default=15, help="last seed")
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    if not a.summary_only:
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
                print(f"[{i}/{len(tasks)}] {r['config']} s{r['seed']}: {r['completed']:.1%} complete, "
                      f"tis {r['tis_s']:.0f}s", flush=True)
    summary()


if __name__ == "__main__":
    main()
