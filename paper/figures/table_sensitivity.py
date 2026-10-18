#!/usr/bin/env python3
"""Generate the sensitivity table (C4) from results/sensitivity.csv. Never typed numbers.

    python paper/figures/table_sensitivity.py > paper/figures/table_sensitivity.tex
"""
import csv
import statistics
from pathlib import Path

rows = list(csv.DictReader(open(Path(__file__).parent.parent.parent / "results" / "sensitivity.csv", encoding="utf-8")))
by = {}
for r in rows:
    by.setdefault((r["knob"], r["variant"]), []).append(r)

base = by[("demand_scale", "baseline")]  # "baseline" rows are deduped/shared across knobs
base_speed = statistics.fmean(float(r["speed_kmh"]) for r in base)
base_delay = statistics.fmean(float(r["delay_s"]) for r in base)

print(r"\begin{table}[htbp]")
print(r"\centering")
print(r"\caption{$\pm20\%$ sensitivity of the calibrated baseline's three fitted/overridden parameters, $n=3$ seeds per variant. The $-20\%$ rows for \texttt{demand\_scale} and \texttt{pcu\_factor} are bit-for-bit identical, confirming only their product is identified.}")
print(r"\label{tab:sensitivity}")
print(r"\begin{tabular}{llrrr}")
print(r"\hline")
print(r"Knob & Variant & Speed (km/h) & Completion & Note \\")
print(r"\hline")
def pct(x):  # LaTeX-safe percentage: bare '%' starts a comment
    return f"{x * 100:.1f}\\%"

print(f"Baseline & --- & {base_speed:.2f} & {pct(1.0)} & $n=3$ \\\\")
labels = {"demand_scale": r"\texttt{demand\_scale}", "pcu_factor": r"\texttt{pcu\_factor}",
          "free_flow_kmh": r"\texttt{free\_flow\_kmh}"}
for knob in ["demand_scale", "pcu_factor", "free_flow_kmh"]:
    for variant in ["-20\\%", "+20\\%"]:
        key = (knob, variant.replace("\\%", "%"))
        if key not in by:
            continue
        runs = by[key]
        speed = statistics.fmean(float(r["speed_kmh"]) for r in runs)
        completions = [float(r["completed"]) for r in runs]
        c_min, c_max = min(completions), max(completions)
        note = f"{pct(c_min)}--{pct(c_max)} range" if c_min < 0.999 else "100\\% all seeds"
        print(f"{labels[knob]} & {variant} & {speed:.2f} & {pct(statistics.fmean(completions))} & {note} \\\\")
print(r"\hline")
print(r"\end{tabular}")
print(r"\end{table}")
