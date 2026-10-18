# Stats review: paper draft (2026-10-19)

Charter experience level: experienced — no plain-language scaffolding needed.

## Findings, ordered by how much they could change a conclusion

| Severity | Where | Issue | Fix |
|---|---|---|---|
| major | `sections/results.tex` §Additional interventions | Prose stated percentages and CIs but not the clean-seed sample sizes they rest on (7/15 and 12/15 for tidal-flow's two magnitudes, 5/15 for parking, 12/15 for staggered and decentralized) — only the table showed this. A reader relying on prose alone could overweight the 36.33%/31.13% findings without registering they're on 12 of 15 seeds, or underweight how thin the rejected parking finding's n=5 evidence base is. | **Fixed**: sample sizes now stated inline in prose for every clean-seed subset. |
| minor | `sections/methods.tex` §Statistical design | No discussion of multiple-comparisons exposure across the paper's 15 distinct paired-seed tests (plus GEH's 6 landmarks, which are a deterministic diagnostic against a fixed engineering threshold, not inferential tests, and so are correctly not counted here). At a naive $\alpha=0.05$ across 15 tests, ~0.75 false positives would be expected if all were null. | **Fixed**: added a paragraph showing the actual bar used (seed-sign-agreement) is far stricter than nominal $p<0.05$ — $0.5^{15}\approx0.0031\%$ one-tailed for a 15/15 result, corrected from an initial two-tailed miscalculation caught while drafting this review. |
| note (not a finding) | — | The calibrated baseline reproduces bit-for-bit across two independently run scripts (`compare.py`, `compare_extra.py`) for the same seeds — confirmed directly (`checks/check_reproducibility.py`). This is a positive robustness confirmation, not an issue; now cited in Methods. | Added to the paper as supporting evidence of determinism. |

## Checks completed

- **Multiple comparisons**: counted (15 paired-seed tests); addressed via the seed-agreement argument above rather than a formal correction, since the project's own falsification criteria (stated before each run, in each experiment card) already demand near-unanimous agreement, which is a stricter standard than any post-hoc correction would impose on a single CI.
- **Small-n hedging**: `n=3` (sensitivity) was already hedged in the table caption and `lab/decisions.md` D11 ("illustrative... not precise figures to quote"); `n=5` (parking's clean subset) is now hedged in prose with the correct, wide CI shown. No small-n result is presented with false precision.
- **Honest reporting**: all seeds, all configs, all four additional interventions (two rejected, two supported-with-caveats) are reported; no selective stopping or cherry-picked seed found. This is the same standard the project already held itself to before this review (e.g., D16-D20).
- **Leakage/independence**: each paired comparison uses the same 15 seeds across configurations by design (that is the point of pairing); no seed is used to tune a method and then re-used to validate it — the only parameter tuning in this project (the baseline's calibration, Section~\ref{sec:calibration}) was fit against an aggregate target (mean speed) before any of the paired-seed lever comparisons were run, not against the comparisons themselves.
- **Reproducibility/determinism**: confirmed directly (see note above), not merely assumed.
- **Simulation check with known truth** (skill's recommended, not required, step): not done. Would require building a synthetic network with a known, injected effect and confirming the paired-seed method recovers it at the stated confidence level. Flagged as a good future-work item, not performed here given the time budget — noted in the handover checklist.

## Verdict

**Supported, with caveats now stated explicitly rather than left implicit.** The paper's core result (H1, H2, and the combined lever's own effect) rests on the strongest evidence in the project — full seed agreement, properly paired, now confirmed deterministic and free of the one serious error already caught and corrected today (D21). The two supported additional interventions (staggered departures, decentralized demand) are real but each carries a named confound the paper does not resolve. The two rejected interventions are correctly reported as rejected, with their thin remaining sample sizes now visible in the prose, not just the table.
