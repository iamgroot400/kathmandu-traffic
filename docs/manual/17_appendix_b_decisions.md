# Appendix B: The Complete Decision Log

This project keeps an **append-only** decision log: every design decision is recorded
with its date, its alternatives considered, its dissenting view (the strongest
counterargument that was not refuted), and when it should be revisited. Nothing is
ever edited or deleted from this log, even when a later decision corrects an earlier
one — D21's correction of the project's original super-additivity claim sits
alongside the original, uncorrected reasoning that preceded it, specifically so the
full history of what was believed and when stays visible. This appendix lists every
decision in order, each pointing to the manual chapter that explains it in full.

| ID | Date | Decision | Manual chapter |
|----|------|----------|-----------------|
| D1 | 2026-10-13 | Represent lane indiscipline as reduced free-flow speed, not driver behavior | Chapter 12 |
| D2 | 2026-10-15 | Use within-day DUO, not day-to-day DUE, as the route-choice process | Chapter 16 |
| D3 | 2026-10-15 | Calibrate "30% of citywide demand" against mean speed only, decomposed as 0.48 arterial share times 0.625 PCU | Chapter 11, Chapter 15 |
| D4 | 2026-10-15 | Cap congestion pricing at 0.2 times observed per-link delay, measured from a single untolled run | Chapter 19 |
| D5 | 2026-10-13 | Signalise intersections by widest angular gap between approach axes, 3+ approaches, 30+ degree spread | Chapter 7 |
| D6 | 2026-10-17 | Add cordon (external) demand at 25% of internal volume; later abandoned after it made validation worse | Chapter 24 |
| D7 | 2026-10-17 | Identify a real observed-data source for GEH validation; confirm a concrete feasibility blocker before committing effort | Chapter 34 |
| D8 | 2026-10-17 | First GEH results are mixed: Thapathali fits, Koteshwor badly undershoots | Chapter 35 |
| D9 | 2026-10-17 | GEH validation fails at intersection level (2 of 6, 33%), confirmed as systematic, not one outlier | Chapter 35 |
| D10 | 2026-10-17 | Adaptive signal control alone fails at Koteshwor (single-seed spot-check), opposite direction from the aggregate result | Chapter 36 |
| D11 | 2026-10-18 | Sensitivity analysis confirms the demand-scale/PCU identifiability problem empirically, and surfaces a capacity-cliff finding | Chapter 37 |
| D12 | 2026-10-18 | Park deep reinforcement learning for signal control explicitly out of this project's scope | Chapter 18 |
| D13 | 2026-10-18 | Re-sequence the project's target: hackathon deliverable first, academic paper second | Chapter 1 |
| D14 | 2026-10-18 | Drop pricing from the hackathon deliverable specifically, keep it for the academic paper | Chapter 41 |
| D15 | 2026-10-18 | Re-verify an earlier single-node bottleneck claim: the real mean share is 15.7%, not the 22% figure first quoted | Chapter 7 |
| D16 | 2026-10-18 | Reject the tidal-flow lever as implemented: too-aggressive a capacity shift causes new gridlock | Chapter 20 |
| D17 | 2026-10-18 | A gentler shift fixes the gridlock side effect but still does not help — the problem is corridor choice, not magnitude | Chapter 20 |
| D18 | 2026-10-18 | Reject the parking/free-flow-enforcement proxy: its apparent benefit was almost entirely a completion-bias artifact | Chapter 21 |
| D19 | 2026-10-18 | Support staggered departures: the strongest single-lever result in this project | Chapter 22 |
| D20 | 2026-10-18 | Support decentralized core demand, but flag it as confounded with pure demand reduction | Chapter 23 |
| D21 | 2026-10-19 | **Major correction:** the super-additivity claim is falsified, not supported — the project's central claim since early in its life was wrong | Part VIII |
| D22 | 2026-10-19 | Simulation realism refinement: surface density, recover Ring Road bridges, and report jam chain-reaction | Chapter 43 |
| D23 | 2026-10-19 | Two principled hypotheses to improve the GEH fit were tested; both made it worse and were rejected rather than kept | Chapter 38 |
| D24 | 2026-10-21 | Capacity-sensitivity sweep: the combined lever is robust across tested capacities, the individual levers are not | Chapter 38 |
| D25 | 2026-10-22 | Widened the OSM extract to include Thankot; Kalanki's face-validity did not improve; not adopted | Chapter 35 |
| D26 | 2026-11-10 | Capacity sweep extended to 15 seeds at 1,600 and 2,000 | Chapter 38 |
| D27 | 2026-11-10 | Final audit: the individual-lever "reversal" in D24/D26 is completion bias, not harm; Tiwari et al. results are model outputs, not field measurements | Chapters 38, 39 |

### Why this log is append-only, stated plainly

A decision log that can be silently edited loses its entire value as a historical
record: if D21's correction had simply overwritten whatever document originally
stated the super-additivity claim, with no trace of what the original, wrong
reasoning had been, a future reader would have no way to understand *how* the error
happened, only that a different number now appears in its place. Recording the
correction as a new, dated entry — alongside, not instead of, the entries that
preceded it — is what makes Part VIII's full account of this project's most
important self-correction possible to tell at all.
