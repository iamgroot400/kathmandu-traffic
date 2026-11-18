#!/usr/bin/env python3
"""GEH of the baseline against JICA 2011-12 counts grown to 2026 (no simulation).

Observed 2026 = observed 2011-12 x (1 + r)^14, for the growth rates on record:
JICA/DoR 2024 Table 4.4.2 low / main-section / high (2.27, 4.52, 6.62 %/yr) and the
16 %/yr registration growth (A12). Model volumes are unchanged from geh_jica2012.csv.

    python checks/geh_grown_2026.py
"""
import csv
from pathlib import Path

ROOT = Path(__file__).parent.parent
YEARS = 14                       # counts Dec 2011-Jan 2012 -> 2026
RATES = {"none (2011-12 counts)": 0.0, "2.27%/yr (JICA 2024 low)": 0.0227,
         "4.52%/yr (JICA 2024 main)": 0.0452, "6.62%/yr (JICA 2024 high)": 0.0662,
         "16%/yr (registrations, A12)": 0.16}


def geh(m, c):
    return ((2 * (m - c) ** 2) / (m + c)) ** 0.5


assert abs(geh(100, 100)) < 1e-9 and round(geh(150, 100), 2) == 4.47

rows = list(csv.DictReader(open(ROOT / "results" / "geh_jica2012.csv", encoding="utf-8")))
out = []
print(f"{'growth to 2026':30s} factor  pass  model/observed  median GEH")
for label, r in RATES.items():
    f = (1 + r) ** YEARS
    gehs = []
    for row in rows:
        obs, mod = float(row["observed_pcu_h"]) * f, float(row["model_pcu_h"])
        g = geh(mod, obs)
        gehs.append(g)
        out.append({"growth": label, "factor": round(f, 3), "intersection": row["intersection"],
                    "observed_2026_pcu_h": round(obs), "model_pcu_h": mod, "geh": round(g, 2)})
    share = sum(float(x["model_pcu_h"]) for x in rows) / (sum(float(x["observed_pcu_h"]) for x in rows) * f)
    print(f"{label:30s} {f:5.2f}  {sum(g < 5 for g in gehs)}/{len(gehs)}   {share:6.0%}         {sorted(gehs)[len(gehs)//2]:5.1f}")

with open(ROOT / "results" / "geh_grown_2026.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(out[0]))
    w.writeheader(); w.writerows(out)
