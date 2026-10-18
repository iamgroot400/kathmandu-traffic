# Outline — JACEM submission (10-page limit, A4, Times New Roman 11pt, 45 lines/page)

## Core claim, in two sentences

**CORRECTED 2026-10-19 (D21):** Signal retiming and congestion pricing each significantly cut peak-hour delay in a calibrated mesoscopic simulation of Kathmandu's arterial network, and combined they cut it by 65% — but a properly computed interaction test finds this combined effect is *not* statistically super-additive (the earlier claim here was based on an unreproducible number; see D21). The model's absolute calibration is honestly weak (GEH passes only 2 of 6 real intersections) and we show the relative comparisons are the part worth trusting, while two further candidate interventions (staggered scheduling, decentralized attraction) show comparably large effects with their own caveats, and two others (tidal-flow lanes, a friction-based proxy for parking enforcement) are reported as tested and rejected.

## Section list and page budget (target ≈10 pages)

1. **Abstract** (0.25 p) — C1, C2, C3 headline numbers; one line on the validation caveat (C5). Written last.
2. **Introduction** (1 p) — Kathmandu congestion context (cite M2's gap: no network-scale local model exists), the two-lever framing, what's novel (M1, with its stated limit).
3. **Related work** (0.75 p) — bilevel signal+price literature (M1), local VISSIM studies (M2), UXsim/mesoscopic justification. Short given the 10-page budget; this is not a literature-review paper.
4. **Methods** (2.5 p) — network/demand construction (233 nodes/590 links, gravity-model OD), calibration and its identifiability limit (A4, previewing C4), signal/adaptive/pricing lever implementations, paired-seed statistical design (why pairing, the documented noise sensitivity that motivates it).
5. **Results** (3 p):
   - 5.1 Core result: C1, C2, C3 (table 1, figure 1 if a bar chart adds clarity over the table alone — per dataviz judgment, likely table suffices for 3 rows)
   - 5.2 Validation: C5, C6/W1 flagged as a spot-check not a confirmed finding (table 2)
   - 5.3 Sensitivity: C4 (figure 2 — the ±20% sweep), capacity-cliff note
   - 5.4 Additional interventions (C8–C11, table 3) — staggered/decentralized as supported-with-caveats, tidal-flow/parking as tested-and-rejected, each one sentence on why
6. **Discussion and limitations** (1.5 p) — built directly from assumptions.md's untested/violated rows + the claim ledger's moderate/weak rows: demand synthesis (A1), DUE non-convergence (C7), cordon demand's negative result (C12) as a stated scope boundary, M3's confounds for C10/C11, the GEH caveat restated plainly.
7. **Conclusion** (0.25 p) — one paragraph, no new claims.
8. **References** — only `lab/literature/sources.md` entries marked verified; `[CITE]` placeholders for anything else needed.
9. **AI-use disclosure** (separate file, `paper/ai-disclosure.md`, not counted in the 10 pages unless JACEM's template requires it inline — flag for the author to check).

## What's deliberately NOT in this paper

- The hackathon pitch material (deck, writeup doc) — separate deliverable, not reused here beyond sharing the same underlying evidence.
- Full treatment of every decision-log entry (D1–D20) — the paper cites the ones that carry a claim; the rest stay in `lab/decisions.md` as the fuller record a reviewer could be pointed to if asked.
- DRL signal control — explicitly out of scope per charter.md, not mentioned beyond perhaps one clause in future work if space allows.

## Open item before drafting

Target venue & deadline (JACEM, 15 April 2027) is confirmed in charter.md. No other blocking gap — proceeding to draft needs your go-ahead on this outline, per the skill's own rule (wait for approval before writing full sections).
