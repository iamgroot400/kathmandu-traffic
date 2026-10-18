#!/usr/bin/env python3
"""Generate Table 1 (core result, H1-H3) as a LaTeX table from results/comparison.partial.csv.
Never typed numbers - this script is the only source of Table 1's numeric content.

    python paper/figures/table_core.py > paper/figures/table_core.tex
"""
import csv
import sys
import statistics
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent / "scripts"))
from compare import ci95  # the project's own, complete t-table

rows = list(csv.DictReader(open(Path(__file__).parent.parent.parent / "results" / "comparison.partial.csv", encoding="utf-8")))
by = {}
for r in rows:
    by.setdefault(r["config"], {})[int(r["seed"])] = r

labels = {"fixed_time": "Fixed-time (baseline)", "adaptive": "Adaptive signals",
          "pricing": "Congestion pricing", "adaptive_pricing": "Adaptive + pricing"}
base = by["fixed_time"]

print(r"\begin{table}[htbp]")
print(r"\centering")
print(r"\caption{Paired-seed delay comparison, $n=15$ seeds, $t_{max}=14400$s. \% change and 95\% CI are paired differences against fixed-time on identical seeds.}")
print(r"\label{tab:core}")
print(r"\begin{tabular}{lrrr}")
print(r"\hline")
print(r"Configuration & Mean delay (s) & \% vs.\ baseline & Seeds negative \\")
print(r"\hline")
for cfg in ["fixed_time", "adaptive", "pricing", "adaptive_pricing"]:
    runs = by[cfg]
    d_mean, _ = ci95([float(r["delay_s"]) for r in runs.values()])
    if cfg == "fixed_time":
        print(f"{labels[cfg]} & {d_mean:.1f} & --- & --- \\\\")
        continue
    shared = sorted(set(base) & set(runs))
    diffs = [float(runs[s]["delay_s"]) - float(base[s]["delay_s"]) for s in shared]
    rels = [d / float(base[s]["delay_s"]) * 100 for d, s in zip(diffs, shared)]
    _, ci_r = ci95(rels)
    mean_r = statistics.fmean(rels)
    neg = sum(1 for d in diffs if d < 0)
    print(f"{labels[cfg]} & {d_mean:.1f} & ${mean_r:+.2f}\\%\\ \\pm {ci_r:.2f}\\%$ & {neg}/{len(shared)} \\\\")
print(r"\hline")
print(r"\end{tabular}")
print(r"\end{table}")
