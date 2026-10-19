# Assumption register

Record every modelling choice, simplification, data filter, and hyperparameter that has no justification. Tag the code that relies on it with `# ASSUME A<n>: ...`.

**Status:** `untested` · `supported (E-ID)` · `violated (E-ID)` · `accepted (D-ID)` (accepted on purpose, with the reason logged)

Note: `# ASSUME A<n>` tags have **not** been inserted into the scripts below — project files are left untouched per standing instruction. This table is the source of truth until the human adds the tags.

| ID | Assumption | Why we make it | Where in code | Status | Headline claim it supports |
|----|------------|----------------|---------------|--------|----------------------------|
| A1 | Demand is a synthesized gravity model over junction density (proxy for activity), not survey/counted | `scripts/build_od.py` | untested | Every result — the demand matrix underlies all of them |
| A2 | Fleet mix enters as PCU-weighted demand: 70% 2W@0.25 + 20% car@1.0 + 10% bus@2.5 = 0.625 | `scripts/run_baseline.py --pcu-factor` default | untested | Absolute delay/speed magnitudes |
| A3 | Effective free-flow speed is overridden to 30 km/h on every link (vs OSM's 50 km/h tag), standing in for lane indiscipline/encroachment | `scripts/run_baseline.py --free-flow-kmh` default | accepted (D1) | Baseline matches observed Kathmandu peak speed |
| A4 | Only 30% of the citywide matrix (0.48 arterial share × 0.625 PCU) loads this network; only the *product* is identified by the speed calibration | `scripts/run_baseline.py --demand-scale`/`--pcu-factor` defaults | accepted (D3) | All absolute delay magnitudes; relative comparisons less sensitive |
| A5 | Route choice is within-day DUO (dynamic user optimum, re-routed every 600s), not day-to-day DUE — DUE does not converge on this network | `scripts/run_baseline.py` (UXsim default), `scripts/run_due.py` | accepted (D2) | All results assume a *process*, not a settled equilibrium |
| A6 | Pricing uses a toll schedule measured once from an untolled run, at 0.2× each link's observed delay, applied only during the peak window | `scripts/run_pricing.py`, `scripts/compare.py` `TOLLS`/`CONFIGS["pricing"]` | accepted (D4) | H2, H3 — pricing effect is a **lower bound** (no demand elasticity) |
| A7 | Signals are placed/split by the widest angular gap between approach axes (≥3 approaches, ≥30° spread); narrower rules under- or over-signalise | `scripts/signals.py` | accepted (D5) | Baseline realism; which nodes are "controllable" in bottleneck ranking |
| A8 | Queue-actuated adaptive control is a heuristic (hysteresis via lost-time), not true max-pressure — no turn-movement data exists in this mesoscopic model | `scripts/adaptive_signals.py` | untested | H1 — the *mechanism* claim, not just the effect size |
| A9 | Cordon (external) demand: 25% of internal trips, 30% of those pass straight through; entry points are the highest-capacity node per compass sector | `scripts/add_cordon.py --external-share`/`--through-share` | **violated (E5)** | Face-validity against named landmarks got *worse* under cordon demand (2/7→1/7), not better. Kalanki's failure traced to a map-boundary limit (the real feeder road is outside the OSM extract); Chabahil's is unexplained. Not used in H1-H3's main results (D6). |
| A10 | Jam density 0.2 veh/m/lane (~5m/vehicle) at standstill | `scripts/run_baseline.py --jam-density` default | untested | Congestion onset timing/shape |
| A12 | 5-year demand projection assumes the 1991-2011 vehicle-registration growth rate (~16%/yr, jica2012) continues unchanged for 5 more years, and that peak-hour trips scale 1:1 with fleet size | `scripts/compare_future_demand.py` (`--demand-growth` on `run_baseline.py`) | untested | Any "future demand" / "N years from now" claim |

## Open gaps (not yet an assumption with a row — nothing to test against)

- GEH validation now exists (`lab/experiments/E6.md`) but passes only 2 of 6 named intersections (33%), and a single-seed robustness check (D10) found H1 specifically fails in the opposite direction at the worst-fitting node (Koteshwor). This is now a **documented, partial** risk rather than a total absence — still the project's biggest open limitation, but it would be wrong going forward to describe it as "no validation exists."
