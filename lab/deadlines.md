# Deadlines

Sorted by date. Always write the timezone (many CS venues use AoE, UTC-12). `verified` means the date was checked on the official page, with the link given.

| Date (TZ) | Venue / body | What | Link | Verified | Status |
|-----------|--------------|------|------|----------|--------|
| 2026-10-25 (TZ unconfirmed) | "buildcities" hackathon (name as given by the human; no official page checked) | Submission (repo demo, no pitch deck per the human's direction) | TODO - no official link located/checked | no - date is the human's own stated deadline, not verified against an official page | upcoming, ~6 days out as of 2026-10-19 |

## Internal milestones
<!-- Work backwards from external deadlines: draft complete, QA pass, co-author review, etc. -->

- [x] Validate baseline/results against observed data (GEH statistic) — **done (E6), closed as a limitation, not a pass.** 2/6 landmarks pass GEH<5 (33%, vs the usual ≥85% target). Relative lever comparisons (H1-H3) are only partly robust where the baseline itself is wrong (D10: adaptive signals alone fail at Koteshwor, opposite direction from H1's aggregate). Two hypotheses to improve this (cold-start warmup, lane-weighted demand) were tested 2026-10-19 and both made the fit worse, not better (D23) - reverted, GEH unchanged from these published values.
- [x] Resolve cordon demand completion question (E5) — done, scoped out (negative result, documented, not used)
- [x] Literature review — context + novelty check for the super-additivity claim (H3) — done, QA-passed. No source found measuring H1-H3's specific combined-vs-sum comparison, but full texts of the 2 closest papers remain unread, so this is "not found," not "confirmed absent."
- [x] Sensitivity analysis (±20% on demand, PCU, free-flow speed) — done (E7). Confirms A4 (demand_scale/pcu_factor -20% give identical output) and surfaces a capacity-cliff finding: +20% on any congestion-increasing knob drops completion to 74.5-83%, reproducing the project's own known survivorship bias.
- [x] Full draft (paper-draft, writing mode = draft) — done, rewritten 2026-10-19 into a two-column journal-format PDF (`paper/kathmandu_traffic_paper.pdf`) with 4 charts replacing the data tables, plus an independent field-evidence citation (Tiwari et al. 2024, Satdobato/Gwarko).
- [x] Comparative cross-city literature review (10 of the user's 35 cities, scoped explicitly) — done, `lab/literature/comparative_review.md`.
- [x] 5-year demand projection (exponential, 16%/yr registration growth) — done, network gridlocks (completion 36.8%, 97/590 links jammed) rather than just slowing down.
- [ ] Capacity-sensitivity robustness sweep (H1-H3 across 1200-2400 veh/h/lane) — in progress, paused at 25/80 runs by request, resumable (`scripts/compare_capacity_sweep.py`)
- [ ] Human review/verification pass before anything is shared or submitted — see `lab/paper/handover.md`'s 10-item checklist, still the human's own responsibility
