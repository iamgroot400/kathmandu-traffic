# Meta-review: end of pre-writing phase

## 1. Research overview

**Question:** can signal retiming (H1) and congestion pricing (H2), individually and combined (H3, super-additivity), reduce delay on a calibrated mesoscopic model of Kathmandu's arterial network? **Tried:** a 233-node/590-link UXsim network, gravity-model demand (A1), PCU-weighted (A2) and friction-adjusted (A3) calibration to 0.48×0.625=0.30 of citywide demand (A4), fixed-time (D5) and queue-actuated (A8) signals, delay-proportional pricing (A6, D4), a 15-seed paired sweep (E1-E4). **Supported:** H1 (−24.50%±7.08%), H2 (−31.89%±5.97%), H3 (−65.30%±4.47% vs −48.6% predicted under independence) — all 15/15 seeds, all CIs excluding zero. **Tried and failed, informatively:** cordon/external demand (E5, D6) — made face-validity worse (2/7→1/7), diagnosed as a map-boundary limit for Kalanki, unexplained for Chabahil; day-to-day equilibrium (D2) — oscillates, abandoned for within-day DUO. **Open, now closed with caveats rather than resolved:** GEH validation (E6, D7-D10) — 2/6 (33%) pass, confirming A4's calibration is unidentified in its spatial distribution, not just its arterial/PCU split; a single-seed robustness spot-check found H1 (not H2/H3) fails in the opposite direction at the worst-fit node (D10). Sensitivity analysis (E7, D11) empirically confirmed A4's unidentifiability and surfaced a capacity-cliff: +20% on any congestion-raising knob drops completion to 74-83%, reproducing a survivorship bias already fixed once in the main sweep. Literature review (QA-passed after fixing one fabricated citation) found joint signal+pricing optimization is studied but no source measuring H3's specific super-additivity claim — "not found," not "confirmed absent," since two key papers' full texts remain unread.

## 2. Recurring patterns

**Pattern A — survivorship/completion bias recurs at every scale, and is caught each time but never built in as a standing check.** Instances: (1) the original 165-signal over-signalisation trap (D5, 78% completion mistaken for an improvement); (2) the main sweep's tmax 10800→14400 fix (README, predates lab/); (3) sensitivity analysis's +20% knobs (D11, 74.5-83% completion). **Pattern, not coincidence:** three separate times, a raw delay/speed number was about to be read as a finding before someone checked completion. **Fix:** every script that reports delay/speed should print completion alongside it by default (several already do), and any result below ~95% completion should carry a standing warning in its own output, not rely on a human remembering to ask.

**Pattern B — a single aggregate calibration target is used to defend multiple downstream claims it does not actually constrain, discovered three separate times rather than once.** Instances: (1) A4/D3 — the 0.48/0.625 split was *argued* to be unidentified; (2) D9 — GEH showed this empirically, failing at 4/6 named intersections in *both* directions; (3) D11 — the −20% sensitivity runs are bit-for-bit identical, directly proving it. This is good — the project kept re-deriving the same true thing from independent angles — but it means the paper has one real finding told three times, and should say so explicitly rather than presenting D9/D11 as separate surprises.

**Pattern C — secondary findings rest on much thinner statistical ground than the primary H1-H3 result, and each one is individually caveated but never totaled up.** E6's GEH check: 6 landmarks, 4 approximately geocoded. D10's node robustness: n=1 seed. E7's sensitivity: n=3 seeds, explicitly flagged in D11 as "illustrative... not precise figures to quote." Each caveat is honest on its own card, but a reader of the whole project would reasonably ask whether *any* of the secondary findings (GEH failure pattern, Koteshwor's adaptive-signal reversal, the capacity-cliff) would survive more seeds. None has been re-run at higher n to check.

**Pattern D — documentation drifts out of sync with later findings, found in two places.** `assumptions.md`'s A9 row still says cordon demand "exposes previously invisible hotspots (Kalanki, Chabahil)" as its headline claim — D6/E5 found the *opposite* (made things worse). The same file's "Open gaps" note still says "no validation... exists anywhere in the pipeline" — E6 closed that gap (with caveats) a day before this review. Both are stale, not wrong when written, but nobody swept back through to update them once the real outcome was known.

## 3. Feedback, by role (all played by one assistant this period, but the roles are distinct and worth separating)

- **grad-student (ran E1-E4, the core result):** Nothing to fix — predictions were written before running, falsification criteria were explicit, and the result is the most solid piece of the project. Keep doing it exactly this way for any future hypothesis.
- **lab-engineer (built add_cordon.py, geh_check.py, node_robustness_check.py, sensitivity.py):** `sensitivity.py` was shipped without incremental result-saving (would have lost all 21 runs on an interruption — caught only because the human asked about closing the session mid-run, not by design). Before writing another multi-run sweep script, copy `compare.py`'s incremental-write pattern as the default, not an afterthought.
- **QA (ran once, on the literature review):** Caught a real fabricated DOI — good process working as intended. **Not yet run on anything else** — the GEH/sensitivity findings (E6, E7, D8-D11) and the README edits have had zero QA pass. Given Pattern D (stale docs) and the README correction that happened mid-session (D10's note: "initially mis-stated this result... before re-reading the actual output"), a QA pass on `README.md` + `assumptions.md` + `E6.md`/`E7.md` is overdue, not optional.
- **Whoever updates `assumptions.md` going forward:** sweep A9's status/headline-claim column to match E5's actual (negative) outcome; add the GEH caveat to the "Open gaps" note instead of leaving it saying validation doesn't exist.

## 4. Stalled and dead ends

- **DRL signal control:** mentioned at length earlier in the project's history (CUDA/torch verified working) but is not in the current charter's Scope section at all — not listed as "in," not listed as "out (on purpose)." It was silently dropped when `lab/` was set up, with no decision logged either way. **Recommendation: park explicitly** — add it to charter's "Out" list with a one-line reason (time budget, not a negative result), so a future reader doesn't wonder why it vanished.
- **Day-to-day DUE (D2):** correctly killed, well-documented, no action needed.
- **Cordon demand (D6/E5):** correctly parked as a negative result. The one loose thread — the flat near-zero-speed tail at t=10,800-14,400s — was never diagnosed as artifact vs. genuine gridlock. Low priority given the whole lever is parked, but worth one line in the paper's limitations rather than silently dropping it.
- **`lab/plan.md` was never created** (research-plan skill not run) — not blocking, since the charter and deadlines.md have carried that function informally, but `next`/`pi` skills expect it to exist; worth a 10-minute pass before heavy writing starts if those roles get used.

## 5. Suggested updates (diff for the human to approve — not applied)

**`charter.md`:**
```diff
 ## Scope
 - **In:** ...
-- **Out (on purpose):** New road capacity. Day-to-day equilibrium (DUE)...
+- **Out (on purpose):** New road capacity. Day-to-day equilibrium (DUE)...
+  Deep reinforcement learning for signal control — explored early (CUDA/torch
+  verified working), dropped for time budget, not a negative result; revisit if
+  there's a second research cycle.

 ## Target venue & deadline
-TODO(human): pick a venue...
+[STILL OPEN — this is now the only unresolved item blocking paper-draft's
+formatting/length decisions. Everything else in the pre-writing checklist is
+closed as of 2026-10-18.]
```

**`assumptions.md`:**
```diff
 | A9 | Cordon (external) demand... | ... | untested | Today's run (lab/experiments/E5)
-     | exposes previously invisible hotspots (Kalanki, Chabahil)
+ | A9 | Cordon (external) demand... | ... | **violated (E5)** | Face-validity got
+     *worse* (2/7->1/7), not better; Kalanki's failure traced to a map-boundary
+     limit, Chabahil's left unexplained. Not used in H1-H3's main results (D6).

 ## Open gaps
-No validation against observed/surveyed link counts or speeds (GEH statistic)
-exists anywhere in the pipeline. This is the biggest unaddressed risk...
+GEH validation now exists (E6) but passes only 2/6 (33%) named intersections,
+and a single-seed robustness check (D10) found H1 specifically fails in the
+opposite direction at the worst-fit node. This is now a *documented, partial*
+risk rather than a total absence - still the project's biggest limitation,
+but mischaracterizing it as "doesn't exist" would be wrong going forward.
```

**Recommended immediate next step:** run `qa-check` once more, scoped to `README.md`, `assumptions.md`, `E6.md`, `E7.md` (per the lab-engineer/QA feedback above) before anything moves to `paper-draft` — closing that gap is cheaper now than after a draft already cites these numbers.
