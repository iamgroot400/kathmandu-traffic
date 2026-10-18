# Research charter

_Last updated: 2026-10-17. Only the human changes this file. Agents propose edits as a diff, and every accepted change is logged in decisions.md._

**Research mode:** discovery
<!-- synthesis = review and synthesize existing literature, invent nothing new.
     discovery = novel hypotheses, POC code, experiments.
     Change only by logging a decision in decisions.md. -->

**Experience level:** experienced

**Writing mode:** draft

## Working title

Signal Retiming and Congestion Pricing on Kathmandu's Arterial Network: A Mesoscopic Simulation Study of Independent and Combined Effects
<!-- TODO(human): confirm or rewrite -->

## Core question

Can queue-actuated signal control and marginal congestion pricing, individually and combined, significantly reduce vehicle delay on a calibrated mesoscopic model of Kathmandu's arterial network relative to a fixed-time baseline — and is their combined effect super-additive?

## Hypotheses

- **H1:** Queue-actuated adaptive signal control reduces total vehicle delay relative to fixed-time signals, under identical demand and routing behavior.
  - Falsified if: the paired-seed 95% CI of (adaptive − fixed_time) includes zero.

- **H2:** Marginal congestion pricing (toll proportional to each link's observed delay, applied only during the peak window) reduces total vehicle delay relative to the fixed-time baseline.
  - Falsified if: the paired-seed 95% CI of (pricing − fixed_time) includes zero.

- **H3 — FALSIFIED 2026-10-19 (D21), by its own stated criterion below.** Combining adaptive signals and pricing reduces delay by more than the sum of their individual effects (super-additivity) — pricing relieves saturation enough that adaptive control regains room to act.
  - Falsified if: (adaptive_pricing − fixed_time) is not significantly more negative than the sum of (adaptive − fixed_time) and (pricing − fixed_time), i.e. the interaction term's CI includes zero.
  - **Result: the interaction term is −185.3 ± 275.6 seconds (t=−1.44, df=14), CI includes zero, 9/15 seeds negative. Not significant.** The combined lever's own effect (−65.30% ± 4.47% vs. fixed-time, 15/15 negative) remains strong and is unaffected — only the claim that it exceeds independent/additive effects is wrong. A stale, unreproducible "−48.6% independence prediction" figure in the original E4.md was used instead of this calculation; see D21.

- **H4 (added 2026-10-18, the hackathon's build target):** A time-based tidal-flow lever — shifting lane capacity from the light to the heavy direction on radial corridors, matched to a demand period with real AM/PM directional asymmetry (built via `build_od_directional.py`, since the base OD matrix has none) — reduces total vehicle delay relative to fixed-time with no lever, under the same directionally-asymmetric demand.
  - Falsified if: the paired-seed 95% CI of (tidal − no-tidal), both under AM-biased demand, includes zero. A single-seed check already found a −2.3% difference — the *same magnitude* as this project's documented seed-noise sensitivity, so this prediction exists specifically because one seed cannot distinguish a real effect from noise here.

- **H5 (added 2026-10-18):** Partial removal of roadside friction (parking/encroachment) — modeled as raising the effective free-flow speed override from 30 km/h to 35 km/h — reduces total vehicle delay relative to the calibrated baseline, with no change to signals or demand.
  - Falsified if: the paired-seed 95% CI of (parking − baseline) includes zero.

- **H6 (added 2026-10-18):** Staggering departure times (modeled as spreading the same total demand over a 5400s window instead of 3600s) reduces total vehicle delay relative to the calibrated baseline.
  - Falsified if: the paired-seed 95% CI of (staggered − baseline) includes zero.

- **H7 (added 2026-10-18):** Decentralizing core-zone trip attraction (government/institutional offices relocated out of the city center, modeled as a 25% cut to core-bound trips via `build_od_decentralized.py`) reduces total vehicle delay relative to the calibrated baseline.
  - Falsified if: the paired-seed 95% CI of (decentralized − baseline) includes zero. Note this changes total demand (-11.4%), so any delay reduction must be read partly as a demand-volume effect, not purely a routing/distribution effect.

## Scope

- **In:** Ring Road + city-core arterial network (trunk/primary/secondary, 233 nodes / 590 links). Signal retiming and congestion pricing as the only two intervention levers. Within-day dynamic user equilibrium (DUO) route choice. Paired-seed statistical comparison against a calibrated fixed-time baseline.
- **Out (on purpose):** New road capacity. Day-to-day equilibrium (DUE) — attempted, does not converge on this network (see A-register). Demand elasticity to tolls (pricing reroutes but does not suppress trips — a stated lower bound). Microscopic driver behavior (lane discipline, car-following) — represented only as an aggregate speed reduction. Residential/tertiary roads (not in the imported network). Deep reinforcement learning for signal control — explored early (CUDA/torch verified working), dropped for time budget, not a negative result; revisit if there's a second research cycle.

## What success looks like

A table of paired-seed delay reductions (adaptive, pricing, adaptive+pricing vs. fixed-time) with 95% CIs excluding zero — achieved (Table 1) — validated against at least one external check (GEH statistic against surveyed or literature-reported link counts/speeds) so the result is defensible as more than a self-consistent simulation — partially achieved (2/6 intersections pass). **Revised 2026-10-19:** a statistically supported super-additive interaction term is not achieved and H3 is falsified by its own criterion (D21) — the combined lever's strong standalone effect is the headline result instead.

## Target venue & deadline

**Two targets, sequenced (corrected 2026-10-18 — the original pick below assumed this
was purely an academic project, which was wrong):**

1. **Immediate/primary: "buildcities" 6-month Kathmandu traffic challenge** (Nepali-Builders
   Hub). Phases: Ideation -> Research -> Development -> Testing/Pilot -> Deployment ->
   Final Demo & Impact Presentation. Judged on: Originality, Feasibility, Implementation
   Details, Number & Quality of Proof Points, Estimated Traffic Reduction. Explicitly
   rates a working prototype/pilot higher than "just really good ideas." **Deadline
   confirmed 2026-10-18: this week's submission is due 2026-10-25 (7 days out)** —
   both a written submission and a live presentation to a 3-judge panel. This is a
   near-term checkpoint inside the 6-month program, not the final deployment deadline.
2. **Later/secondary: academic publication** of the same findings, once the hackathon
   phase is done. Journal of Advanced College of Engineering and Management (JACEM,
   nepjol.info/index.php/JACEM) remains a reasonable pick for this — peer-reviewed,
   already publishes closely related Kathmandu-congestion work (Luitel et al. 2025),
   fixed annual deadline **15 April** (next window 15 April 2027), plenty of runway
   after the hackathon concludes.

All work until further notice is prioritized for (1). (2) does not block or compete
with it — the same evidence base (E1-E7) serves both, just packaged differently.

**What this means for scope (logged as D13):** this project's simulation work
(H1-H3, E1-E7) is the "Research" phase's proof points — the paired-seed delay
reductions are exactly the "Estimated Traffic Reduction" evidence the judges ask for.
A metro system or major public-transport buildout cannot be prototyped/piloted by a
hackathon team in 6 months — those score badly on Feasibility/Implementation Details
for *this* competition specifically, regardless of their real-world merit.

**Revised 2026-10-18 (D14): pricing dropped from the hackathon build/pitch, kept for
the paper.** H2/H3's pricing results (E3/E4) are real, already-run evidence and stay
in the project for the academic paper (target 2 above) — they are not discarded.
But checking comparable-country evidence found no well-documented case of congestion
*pricing* working in a low/middle-income country; the closest real attempt (Jakarta's
electronic road pricing) never launched, and the quantity-restriction scheme used in
its place (3-in-1 occupancy rule) was defeated by hired "jockeys" faking passenger
counts — a direct example of a human-enforced rule failing under weak enforcement
capacity. **The hackathon deliverable is now signal optimization only, plus the
pending time-based one-way/tidal-flow idea** — both are pure software/geometry
changes needing no payment collection or behavioral compliance from the public, so
neither has pricing's gameable-enforcement problem. Public transport and metro remain
out of scope per the reasoning above.

## Key references

See `lab/literature/` for the full review, claim table and source list (2026-10-17). Headline findings:
- Joint signal+pricing optimization is a studied design (Smith & Xiang & Yarrow 1997; Mao et al. 2013; Smith et al. 2022) — the two-lever choice itself is not novel.
- **No located source reports measuring a combined effect against the sum of each lever alone** — this is the specific gap H3 would fill, though only abstracts were read for the bilevel papers (Mao 2013, Smith & Xiang & Yarrow 1997, Clegg et al. 2001); the full texts of Smith et al. 2022 and Clegg et al. 2001 are the highest-priority unread sources before claiming this gap firmly.
- No Kathmandu study models the city at mesoscopic/network scale or tests pricing — all located Kathmandu work (Tamang et al. 2026; Luitel et al. 2025; Bhatta 2024) is single-intersection VISSIM microsimulation or a cost estimate with no lever. This project's Kathmandu-specific novelty is better supported than its general novelty claim.
- UXsim citations: Seo, T. (2025) *JOSS* 10(106):7617 (software) and Seo, T. (2023) arXiv:2309.17114 (method/technical overview).
