#!/usr/bin/env python3
"""Generate Table 2 (GEH validation) from results/geh.csv. Never typed numbers.

    python paper/figures/table_geh.py > paper/figures/table_geh.tex
"""
import csv
from pathlib import Path

rows = list(csv.DictReader(open(Path(__file__).parent.parent.parent / "results" / "geh.csv", encoding="utf-8")))
n_pass = sum(1 for r in rows if r["pass"] == "True")

print(r"\begin{table}[htbp]")
print(r"\centering")
print(r"\caption{GEH validation against observed peak-hour volumes (PCU/h) at six named Kathmandu intersections. "
      r"Observed data: JICA/Department of Roads survey, Dec.\ 2011--Jan.\ 2012 \cite{jica2012}, "
      r"Koteshwor and Thapathali cross-referenced against a 2017 machine-readable reproduction \cite{jica2017}; "
      r"the remaining four landmarks' coordinates are approximate (OpenStreetMap-geocoded, not surveyed).}")
print(r"\label{tab:geh}")
print(r"\begin{tabular}{lrrrl}")
print(r"\hline")
print(r"Landmark & Model (PCU/h) & Observed (PCU/h) & GEH & Verdict \\")
print(r"\hline")
for r in rows:
    approx = "$^{*}$" if r["approx_coords"] == "True" else ""
    verdict = "Pass" if r["pass"] == "True" else "Fail"
    print(f"{r['landmark']}{approx} & {float(r['model_pcu_h']):.0f} & {float(r['observed_pcu_h']):.0f} & "
          f"{float(r['geh']):.2f} & {verdict} \\\\")
print(r"\hline")
print(r"\end{tabular}")
print(f"\\\\[2pt] {{\\footnotesize $^{{*}}$ approximate coordinates. {n_pass}/{len(rows)} pass GEH$<5$.}}")
print(r"\end{table}")
