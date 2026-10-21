# Appendix A: The Complete Assumption Register

Every modeling choice this project makes that has no independent justification
beyond "this is a reasonable default" is tagged here with an ID (A1, A2, and so
on), its current status, and which headline claim in this project depends on it.
This appendix reproduces the project's own living assumption register in full, so
that a reader of this manual never has to leave it to see the complete picture. Each
entry below also names the chapter of this manual where it is explained in depth.

**Status key:** `untested` (never independently checked against real data) ·
`supported (E-ID)` (an experiment found evidence for it) ·
`violated (E-ID)` (an experiment found evidence against it) ·
`accepted (D-ID)` (a deliberate tradeoff, decided and logged, not something waiting
to be tested).

| ID | Assumption | Status | Manual chapter |
|----|------------|--------|-----------------|
| A1 | Demand is a synthesized gravity model over junction density (a proxy for activity), not a survey or a count | untested | Chapter 8-9 |
| A2 | Fleet mix enters as PCU-weighted demand: 70% two-wheelers at 0.25, 20% cars at 1.0, 10% buses at 2.5, combining to 0.625 | untested | Chapter 10 |
| A3 | Effective free-flow speed is overridden to 30 km/h on every link (vs. OSM's own 50 km/h tag), standing in for lane indiscipline, parking, and encroachment | accepted (D1) | Chapter 12 |
| A4 | Only 30% of the citywide demand matrix loads this network (a 0.48 arterial-share factor times a 0.625 PCU factor); only their *product* is identified by the single speed-calibration target | accepted (D3) | Chapter 11, Chapter 15 |
| A5 | Route choice is within-day dynamic user optimum, rerouted every 600 seconds, not a settled day-to-day equilibrium — the equilibrium solver does not converge on this network | accepted (D2) | Chapter 16 |
| A6 | Congestion pricing uses a toll schedule measured once from a single untolled run, at 0.2 times each link's observed delay, applied only during the peak demand window | accepted (D4) | Chapter 19 |
| A7 | Signals are placed by the widest angular gap between approach axes (3+ approaches, 30+ degree spread); narrower or wider rules under- or over-signalise the network | accepted (D5) | Chapter 7 |
| A8 | Queue-actuated adaptive control is a heuristic (hysteresis via a lost-time threshold), not a true max-pressure controller, since no turn-movement data exists in this mesoscopic model | untested | Chapter 18 |
| A9 | Cordon (external) demand assumptions: 25% of internal trips, 30% of those passing straight through, entering at the highest-capacity node per compass sector | **violated (E5)** | Chapter 24 |
| A10 | Jam density of 0.2 vehicles per meter per lane (roughly 5 meters per vehicle) at a complete standstill | untested | Chapter 13 |
| A12 | The 5-year demand projection assumes the 1991-2011 vehicle-registration growth rate (approximately 16% per year) continues unchanged for 5 more years, and that peak-hour trips scale one-to-one with fleet size | untested | Chapter 42 |

Note that A11 does not appear in this project's register — ID numbers are assigned
in the order an assumption was identified and logged, and not every number in a
sequence necessarily corresponds to a surviving, currently active assumption; this
is an append-only log, not a renumbered list, by design (so that an old reference to
a specific assumption ID never silently points to a different assumption later).

### The open gap this register flags most prominently

This project's own register is explicit that its GEH validation (Part IX) — passing
only 2 of 6 named intersections — is now a **documented, partial limitation**, not
a total absence of validation, and that it would be a mischaracterization, going
forward, to describe this project as having "no validation" at all. The honest
summary the register itself settles on: the model's relative comparisons between
interventions are better supported by evidence than its absolute delay and speed
figures, and this distinction should be preserved in how any of this project's
numbers are quoted elsewhere.
