#!/usr/bin/env python3
"""Generate Table 3 (H4-H7, additional interventions) from results/tidal.csv,
results/tidal_half.csv, results/extra.partial.csv. Never typed numbers.

    python paper/figures/table_additional.py > paper/figures/table_additional.tex
"""
import csv
import sys
import statistics
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent / "results"
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from compare import ci95 as _ci95_tuple  # the project's own, complete t-table - never hand-copy a partial one

def ci95(vals):
    return _ci95_tuple(vals)

def paired(path, base_name, variant_name, clean_only=False):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault(r["config"], {})[int(r["seed"])] = r
    base, var = by[base_name], by[variant_name]
    seeds = sorted(set(base) & set(var))
    if clean_only:
        seeds = [s for s in seeds if float(base[s]["completed"]) >= 0.999 and float(var[s]["completed"]) >= 0.999]
    diffs = [float(var[s]["delay_s"]) - float(base[s]["delay_s"]) for s in seeds]
    rels = [d / float(base[s]["delay_s"]) * 100 for d, s in zip(diffs, seeds)]
    mean_r = statistics.fmean(rels)
    _, ci_r = ci95(rels)
    neg = sum(1 for d in diffs if d < 0)
    newly_gridlocked = sum(1 for s in set(base) & set(var)
                           if float(base[s]["completed"]) >= 0.999 and float(var[s]["completed"]) < 0.999)
    return mean_r, ci_r, neg, len(seeds), newly_gridlocked

rows_out = []
# H4: tidal-flow, two magnitudes - report clean-only (the honest number per D16/D17)
for path, label, shift in [(ROOT / "tidal.csv", "Tidal-flow, 1.0 lane-eq.", 1.0),
                            (ROOT / "tidal_half.csv", "Tidal-flow, 0.5 lane-eq.", 0.5)]:
    mean_r, ci_r, neg, n, grid = paired(path, "no_tidal", "tidal", clean_only=True)
    rows_out.append((label, mean_r, ci_r, neg, n, grid, "Rejected"))

# H5-H7 from extra.partial.csv - report clean-only per D18-D20
for variant, label, verdict in [("parking", "Parking/free-flow enforcement", "Rejected"),
                                 ("staggered", "Staggered departures", "Supported"),
                                 ("decentralized", "Decentralized core demand", "Supported*")]:
    mean_r, ci_r, neg, n, grid = paired(ROOT / "extra.partial.csv", "baseline", variant, clean_only=True)
    rows_out.append((label, mean_r, ci_r, neg, n, grid, verdict))

print(r"\begin{table}[htbp]")
print(r"\centering")
print(r"\caption{Additional interventions (H4-H7), clean-seed-only (100\% completion both configurations) paired comparison against the calibrated baseline. ``Newly gridlocked'' = seeds that reached 100\% completion without the intervention but not with it.}")
print(r"\label{tab:additional}")
print(r"\begin{tabular}{lrrrl}")
print(r"\hline")
print(r"Intervention & \% vs.\ baseline & Clean seeds neg. & Newly gridlocked & Verdict \\")
print(r"\hline")
for label, mean_r, ci_r, neg, n, grid, verdict in rows_out:
    print(f"{label} & ${mean_r:+.2f}\\%\\ \\pm {ci_r:.2f}\\%$ & {neg}/{n} & {grid} & {verdict} \\\\")
print(r"\hline")
print(r"\end{tabular}")
print(r"\end{table}")
