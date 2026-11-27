"""Headline results in units a reader can picture: vehicle-hours and minutes per vehicle saved per morning peak.

    python checks/vehicle_hours.py      (reads results/clean/jica_h1h7.csv, writes results/clean/vehicle_hours.csv)

Same runs and same pairing as the paper: each configuration against its control on the same 15 seeds.
Vehicle-hours in the network = vehicles x mean time in system (unfinished trips counted up to the 4-hour horizon).
These are model numbers for the 2011 demand, not measured savings on today's roads.
"""
import math
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

ROOT = Path(__file__).parent.parent
h = pd.read_csv(ROOT / "results/clean/jica_h1h7.csv")
h["veh_h"] = h.trips * h.tis_s / 3600

TESTS = [("H1 adaptive signals", "adaptive", "baseline"), ("H2 congestion pricing", "pricing", "baseline"),
         ("H3 adaptive + pricing", "adaptive_pricing", "baseline"), ("H6 staggered departures", "staggered", "baseline")]


def ci(x):
    x = np.asarray(x, float)
    return x.mean(), stats.t.ppf(0.975, len(x) - 1) * x.std(ddof=1) / math.sqrt(len(x))


w = {k: h.pivot(index="seed", columns="config", values=k) for k in ("veh_h", "tis_s", "trips")}
base_vh, base_vh_h = ci(w["veh_h"].baseline)
print(f"baseline: {int(w['trips'].baseline.iloc[0]):,} vehicles, {base_vh:,.0f} +/- {base_vh_h:,.0f} vehicle-hours "
      f"in the network per morning peak, {ci(w['tis_s'].baseline)[0] / 60:.1f} min per vehicle")
rows = []
for name, c, b in TESTS:
    assert (w["trips"][c] == w["trips"][b]).all(), f"{c} and {b} must load the same vehicles"   # else not comparable
    saved_vh, saved_vh_h = ci(w["veh_h"][b] - w["veh_h"][c])
    saved_min, saved_min_h = ci((w["tis_s"][b] - w["tis_s"][c]) / 60)
    rows.append({"test": name, "vehicle_hours_saved": round(saved_vh), "vehicle_hours_ci": round(saved_vh_h),
                 "minutes_saved_per_vehicle": round(saved_min, 1), "minutes_ci": round(saved_min_h, 1),
                 "seeds": len(w["veh_h"])})
    print(f"{name:<26} {saved_vh:>8,.0f} +/- {saved_vh_h:,.0f} vehicle-hours   "
          f"{saved_min:5.1f} +/- {saved_min_h:.1f} min per vehicle")
pd.DataFrame(rows).to_csv(ROOT / "results/clean/vehicle_hours.csv", index=False)
