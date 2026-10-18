# Deadlines

Sorted by date. Always write the timezone (many CS venues use AoE, UTC-12). `verified` means the date was checked on the official page, with the link given.

| Date (TZ) | Venue / body | What | Link | Verified | Status |
|-----------|--------------|------|------|----------|--------|
| TODO | TODO | Submission | TODO | no | upcoming |

## Internal milestones
<!-- Work backwards from external deadlines: draft complete, QA pass, co-author review, etc. -->

- [x] Validate baseline/results against observed data (GEH statistic) — **done (E6), closed as a limitation, not a pass.** 2/6 landmarks pass GEH<5 (33%, vs the usual ≥85% target). Relative lever comparisons (H1-H3) are only partly robust where the baseline itself is wrong (D10: adaptive signals alone fail at Koteshwor, opposite direction from H1's aggregate). Written into README.md's "Validation against observed counts" section.
- [x] Resolve cordon demand completion question (E5) — done, scoped out (negative result, documented, not used)
- [x] Literature review — context + novelty check for the super-additivity claim (H3) — done, QA-passed. No source found measuring H1-H3's specific combined-vs-sum comparison, but full texts of the 2 closest papers remain unread, so this is "not found," not "confirmed absent."
- [x] Sensitivity analysis (±20% on demand, PCU, free-flow speed) — done (E7). Confirms A4 (demand_scale/pcu_factor -20% give identical output) and surfaces a capacity-cliff finding: +20% on any congestion-increasing knob drops completion to 74.5-83%, reproducing the project's own known survivorship bias.
- [ ] Full draft (paper-draft, writing mode = draft)
- [ ] Human review/verification pass before anything is shared or submitted
