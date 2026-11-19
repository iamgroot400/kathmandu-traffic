#!/usr/bin/env python3
"""Do the interventions still work at future demand? Paired seeds, resumable. Built for Kaggle.

The published interventions (H1-H7) were tested at 2011 demand. Here the strongest ones run at the
grown demand of the projection (scripts/project_jica.py: JICA/DoR 2024 forecast, 4.52%/yr):
x1.94 (2026) and x2.32 (2030), on the published model, 6-hour horizon, each paired with the
no-intervention run at the same demand and seed.

  baseline           no intervention (the projection's arm)
  adaptive           H1 queue-actuated signals
  adaptive_pricing   H3 signals + tolls (the 2011 toll schedule, results/tolls_jica.csv:
                     tolls are not re-derived for future congestion)
  staggered          H6 same demand over a 50% longer window
  all                adaptive signals + tolls + staggered departures

Criterion fixed before any run: an arm "solves" a demand level if its completion within 6 h is at
least the 2011 baseline's (98.1%, projection notebooks) and its mean time in system is no worse than
the 2011 baseline's at the same 6 h horizon (`--ref` row, run here as level 2011).

    python scripts/future_jica.py --level 2030 --first-seed 1 --seeds 6 --jobs 3
    python scripts/future_jica.py --summary-only
"""
from __future__ import annotations

import argparse
import csv
import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from stats import ci95  # noqa: E402
from compare_jica import BASE, FIELDS, PRICING, worker  # noqa: E402

NET = BASE["data"]
LOG = 60   # as project_jica.py: full vehicle logs of gridlocked runs exceed memory
OD = {"2011": NET / "od_matrix.csv", "2026": NET / "od_matrix_g2026.csv", "2030": NET / "od_matrix_g2030.csv"}
ARMS = {"baseline": {}, "adaptive": {"adaptive": True}, "adaptive_pricing": {"adaptive": True, **PRICING},
        "staggered": {"demand_window": 10800}, "all": {"adaptive": True, **PRICING, "demand_window": 10800}}
OUT = Path(__file__).parent.parent / "results" / "jica_future.partial.csv"


def configs(level):
    common = {"tmax": 21600, "vehicle_log_interval": LOG, "platoon_fix": True, "od_file": OD[level]}
    arms = {"baseline": {}} if level == "2011" else ARMS
    return {f"{level}_{a}": {**common, **ov} for a, ov in arms.items()}


def load():
    if not OUT.exists():
        return {}
    return {(r["config"], int(r["seed"])): r for r in csv.DictReader(open(OUT, encoding="utf-8"))}


def summary() -> None:
    by = {}
    for (c, s), r in load().items():
        by.setdefault(c, {})[s] = r
    ref = by.get("2011_baseline", {})
    ref_c = ci95([float(r["completed"]) * 100 for r in ref.values()])[0] if len(ref) > 1 else 98.1
    ref_t = ci95([float(r["tis_s"]) for r in ref.values()])[0] if len(ref) > 1 else None
    print(f"reference, 2011 demand, no intervention: completion {ref_c:.1f}%, time in system "
          f"{ref_t:.0f} s" if ref_t else f"reference completion {ref_c:.1f}% (2011 time not run here)")
    print(f"\n{'config':<24}{'n':>3}{'completed %':>14}{'time in system s':>19}{'vs same-demand baseline':>27}  solves?")
    for level in ("2026", "2030"):
        base = by.get(f"{level}_baseline", {})
        for c in configs(level):
            rs = by.get(c, {})
            if len(rs) < 2:
                continue
            comp = ci95([float(r["completed"]) * 100 for r in rs.values()])
            tis = ci95([float(r["tis_s"]) for r in rs.values()])
            shared = sorted(set(rs) & set(base))
            vs = ""
            if c != f"{level}_baseline" and len(shared) > 1:
                d = ci95([(float(rs[s]["tis_s"]) - float(base[s]["tis_s"])) / float(base[s]["tis_s"]) * 100 for s in shared])
                vs = f"{d[0]:+.1f}% +/- {d[1]:.1f}"
            solves = comp[0] >= ref_c and (ref_t is None or tis[0] <= ref_t)
            print(f"{c:<24}{len(rs):>3}{comp[0]:>8.1f} +/-{comp[1]:4.1f}{tis[0]:>12.0f} +/-{tis[1]:5.0f}{vs:>27}  "
                  f"{'yes' if solves else 'no'}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--level", choices=list(OD), required=False)
    ap.add_argument("--seeds", type=int, default=6, help="last seed")
    ap.add_argument("--first-seed", type=int, default=1)
    ap.add_argument("--jobs", type=int, default=3)
    ap.add_argument("--summary-only", action="store_true")
    a = ap.parse_args()
    if not a.summary_only:
        assert PRICING["toll_file"].exists(), "results/tolls_jica.csv missing (notebook 2 output)"
        done = load()
        tasks = [{"config": c, "seed": s, "overrides": ov} for s in range(a.first_seed, a.seeds + 1)
                 for c, ov in configs(a.level).items() if (c, s) not in done]
        print(f"{len(tasks)} runs to do ({len(done)} already done), {a.jobs} at a time", flush=True)
        OUT.parent.mkdir(parents=True, exist_ok=True)
        with ProcessPoolExecutor(max_workers=a.jobs, max_tasks_per_child=1) as ex:
            for i, f in enumerate(as_completed([ex.submit(worker, t) for t in tasks]), 1):
                r = f.result()
                if "error" in r:
                    print(f"[{i}/{len(tasks)}] {r['config']} s{r['seed']}: ERROR {r['error']}", flush=True)
                    continue
                with OUT.open("a", newline="", encoding="utf-8") as fh:
                    w = csv.DictWriter(fh, fieldnames=FIELDS)
                    if fh.tell() == 0:
                        w.writeheader()
                    w.writerow(r)
                print(f"[{i}/{len(tasks)}] {r['config']} s{r['seed']}: tis {r['tis_s']:.0f}s, "
                      f"{r['completed']:.1%} complete", flush=True)
    summary()


if __name__ == "__main__":
    main()
