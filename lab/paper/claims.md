# Claim ledger

Every claim the recorded evidence supports, graded by strength. Only **strong** and **moderate** claims may appear in the abstract (skill rule). Numbers are quoted exactly as the cited result file/decision states them — not rounded or restated.

## Strong claims (replicated, tested, CI excludes zero or directly measured)

| ID | Claim | Evidence | Depends on |
|---|---|---|---|
| C1 | Queue-actuated adaptive signal control reduces average delay by 24.50% ± 7.08% vs. fixed-time, 15/15 paired seeds negative | E2, `results/comparison.partial.csv` (config=adaptive) | A1, A2, A3, A4, A5, A7, A8, A10 |
| C2 | Marginal congestion pricing reduces average delay by 31.89% ± 5.97% vs. fixed-time, 15/15 paired seeds negative | E3, `results/comparison.partial.csv` (config=pricing) | A1-A7, A10 |
| C3 | Combining adaptive signals and pricing reduces delay by 65.30% ± 4.47% vs. fixed-time, 15/15 paired seeds negative | E4, `results/comparison.partial.csv` (config=adaptive_pricing) | A1-A10 |
| C3f | **(falsified, not a supported claim — kept here for traceability)** The combined lever's per-seed interaction term (combined_diff − adaptive_diff − pricing_diff) is −185.3 ± 275.6 seconds, t=−1.44 (df=14), CI includes zero, 9/15 seeds negative — super-additivity (H3) is not statistically supported. Corrects E4's original interpretation, which compared against an unreproducible −48.6% figure. | D21, `results/comparison.partial.csv` (recomputed) | A1-A10 |
| C4 | `demand_scale` and `pcu_factor` are not independently identified by the mean-speed calibration: a −20% change to either produces bit-for-bit identical simulation output | E7, `results/sensitivity.csv` | A2, A4 |
| C5 | The baseline's calibration target (city-wide mean speed) does not constrain spatial distribution of demand: GEH < 5 at only 2 of 6 checked intersections, with errors in both directions (3 undershoot, 1 overshoot) | E6, D8, D9 | A1-A4 |
| C6 | A single-seed check found H1's effect reverses direction (+213.9%, worse) at the one intersection (Koteshwor) where the baseline's volume is most wrong, while H2 and H3 held direction there | D10 | — (n=1, see weak claims) |
| C7 | Day-to-day user equilibrium (`SolverDUE`) does not converge on this network (route-cost gap oscillates 611.6→13.5→510.0→36.5 over 4 iterations); results use within-day DUO instead | D2 | A5 |
| C8 | A time-based tidal-flow lane-reallocation lever, tested at two magnitudes (1.0 and 0.5 lane-equivalents, 15 paired seeds each), does not reduce delay; at full magnitude it causes new non-completion in 5/15 seeds, and even after removing that side-effect (0.5 magnitude), delay among unaffected seeds is higher, not lower, than baseline | E8, D16, D17 | — |
| C9 | A free-flow-speed increase (30→35 km/h, modeling partial friction/encroachment removal) produces an apparent 28.61% delay reduction that is almost entirely a completion-bias artifact (10/15 seeds newly incomplete); among the 5 unaffected seeds the effect is −1.71% ± 13.47%, not significant | E9, D18 | A3 |
| C10 | Spreading the same total demand over a 50%-longer departure window (staggered scheduling proxy) reduces delay by 36.33% ± 6.99% among completion-matched seeds (12/15), surviving a completion-bias check | E9, D19 | A1-A4 |
| C11 | A 25% cut to core-zone trip attraction (proxy for decentralizing institutional destinations) reduces delay by 31.13% ± 4.57% among completion-matched seeds, but this intervention also cuts total demand by 11.4% | E9, D20 | A1-A4 |
| C12 | Added external (cordon) demand reduces face-validity against named landmarks (2/7 → 1/7 match), not improves it; the failure at one landmark (Kalanki) is traced to a map-boundary limit (1.25 km from the OSM extract edge) | E5, D6 | A9 |

## Moderate claims (real effect, but a stated gap limits how far it generalizes)

| ID | Claim | Evidence | Gap |
|---|---|---|---|
| M1 | **(moot as of D21 — kept for traceability, not for citing)** No prior published work was found reporting a measured super-additive interaction between signal control and congestion pricing. Since C3f found no such interaction exists in this project's own data either, this literature finding no longer supports any claim in this paper — there is nothing to be "novel" about. | `lab/literature/review.md`, QA-passed | Moot, not merely limited — do not cite in the paper |
| M2 | No prior work models Kathmandu at network/mesoscopic scale or tests congestion pricing there | `lab/literature/sources.md` (Tamang et al. 2026, Luitel et al. 2025, Bhatta 2024 — all single-intersection VISSIM or cost estimates) | Literature search, not exhaustive |
| M3 | Decentralization (C11) and staggered scheduling (C10) are each real effects, but neither isolates its mechanism cleanly: C11 is confounded with pure demand reduction; C10's magnitude reflects a large (50%) window change, not a small realistic nudge | E9 | No volume-matched control (C11); no smaller-window variant tested (C10) |

## Weak claims (flagged explicitly, not for the abstract)

| ID | Claim | Why weak |
|---|---|---|
| W1 | Adaptive signal control fails specifically at demand-miscalibrated convergence points (mechanism claim extending C6) | n=1 seed, single node; explicitly logged in D10 as "could be noise," not folded into C1 |
| W2 | The 22% figure (originally reported for node `3511456911`'s delay share) | Superseded — re-verified at mean 15.7% (range 9.3–21.9%, n=15, D15); the original was the high end of the distribution, not typical |

## Assumption dependencies (full register: `lab/assumptions.md`)

A1 (demand synthesis, untested), A2 (PCU weights, untested), A3 (friction factor, accepted D1), A4 (demand-scale/PCU split, accepted D3 — **shown unidentifiable in practice by C4**), A5 (DUO not DUE, accepted D2), A6 (toll schedule, lower bound, accepted D4), A7 (signal placement rule, accepted D5), A8 (adaptive heuristic, untested), A9 (cordon demand, **violated — E5**), A10 (jam density, untested).

## Figures/tables needed (generated from result files, not typed numbers)

1. Table: C1–C3 paired-seed results (delay, % change, CI, seeds agreeing) — from `results/comparison.partial.csv`.
2. Table: C8–C11 (H4–H7) paired-seed results with completion-bias decomposition (raw vs. clean-seed-only) — from `results/tidal.csv`, `results/tidal_half.csv`, `results/extra.partial.csv`.
3. Table/figure: GEH per intersection (C5) — from `results/hotspots.csv`-derived landmark table, `geh_check.py` output.
4. Figure: sensitivity sweep (C4) — bar chart of ±20% variants vs. baseline, completion annotated — from `results/sensitivity.csv`.
