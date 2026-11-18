# Part X — Sensitivity and Robustness

## Chapter 37: The ±20% Parameter Sweep

### The question

This project's baseline rests on three fitted or overridden parameters: the demand
scale and PCU factor (Chapter 11), and the free-flow speed override (Chapter 12). A
natural question about any calibrated model is: **how sensitive is the result to
these specific parameter values?** If a small change to any one of them would flip
the project's conclusions, those conclusions would rest on a much shakier foundation
than if they are robust across a reasonable range of plausible values.

### The design

This project swept each of the three parameters by **plus and minus 20 percent**
independently, running **3 seeds per variant** — fewer than the core result's 15,
deliberately, because this sweep serves an *illustrative* role (is the baseline in a
stable operating regime, broadly?) rather than aiming to produce a precise number to
quote on its own. This project's own decision log is explicit about this distinction,
specifically to prevent a future reader from mistaking this sweep's numbers for
results with the same statistical weight as the main, 15-seed comparisons.

### The two findings

1. **Empirical confirmation of the identifiability problem** (Chapter 15): reducing
   either the demand-scale factor or the PCU factor by 20 percent, independently,
   produced simulation output **identical to many decimal places** — not similar,
   genuinely indistinguishable — direct, numerical proof that only the *product* of
   the two factors is identified by this project's single calibration target, exactly
   as the theoretical argument in Chapter 15 predicted.
2. **A capacity-cliff finding**: every variant that *increased* congestion (rather
   than decreased it) dropped completion into the **75-to-83-percent range** at the
   same simulation horizon used everywhere else in this project — a direct,
   reproduced instance of the same survivorship-bias pattern Chapter 28 covers in
   depth. This is a genuine warning sign about how close to a fragile operating point
   this project's calibrated baseline actually sits: it does not take an extreme
   parameter shift to push the network from "congested but functioning" into
   "meaningfully incomplete."

---

## Chapter 38: The Capacity-Sensitivity Sweep

### Why this sweep exists, and why it is different from the one above

Chapter 37's sweep tested whether this project's calibration is in a *stable*
operating regime — it perturbed parameters that were already fitted to a real
target. This chapter's sweep tests something different and, in a specific sense,
more serious: **per-lane road capacity was never measured for this network at
all** (Chapter 13 logs this directly as assumption A10, status untested). Worse,
this project's own calibrated value for that capacity — measured empirically,
directly from the simulator, at roughly **2,400 vehicles per hour per lane** — runs
*above* the real, field-measured range Tiwari et al. (2024) report from two actual
Kathmandu intersections: **1,203 to 2,160 vehicles per hour per lane** (Part XI,
Chapter 39 covers this independent source in full). That is a real, specific,
*named* uncertainty in this project's own modeling assumptions, not a hypothetical
one — and this chapter's sweep exists specifically to test whether the project's
headline conclusions survive it.

### The critical methodological line this sweep had to stay on the right side of

It would have been easy, and tempting, to simply keep adjusting the capacity
assumption until the model's GEH validation (Part IX) happened to improve — but this
project had already tried exactly that kind of search, for a different purpose,
and explicitly rejected it (Decision D23, discussed in Part IX): two separate
attempts to improve the GEH fit (a cold-start measurement-window adjustment, and a
lane-weighted demand redistribution) were tested honestly, found to make the fit
*worse*, not better, and were reverted rather than kept and reported selectively.
This sweep is built on the opposite discipline: **the four capacity values tested —
1,200, 1,600, 2,000, and 2,400 vehicles per hour per lane — were chosen in advance**,
specifically to bracket and fall below the real, independently-measured field range,
**not adjusted afterward based on which values happened to produce a favorable
result.**

### The design

Each of this project's three main levers (adaptive signal control, pricing, and the
combined configuration) was re-run against the fixed-time baseline at each of the
four capacity levels, with **5 seeds per cell** (again, a reduced-power,
illustrative sample, the same role Chapter 37's sweep plays for the other
parameters) — 80 total simulation runs in the sweep's first pass, later extended with
additional seeds specifically at the two middle capacity levels (1,600 and 2,000)
once a reversal was found there, to sharpen exactly where it happens.

### The result

At the calibrated default (2,400 vehicles per hour per lane), all three levers
reproduce this project's main result in direction: adaptive signals **−25.9% ±
6.4%**, pricing **−29.7% ± 14.7%**, combined **−67.3% ± 4.3%**.

Below that capacity, something happens that changes how every other number must be
read: **the fixed-time baseline itself stops completing every trip.** Mean
completion in the baseline is 82% at 2,000, 77% at 1,600 and 75% at 1,200. Chapter
28 explained why that matters. Average delay is computed over completed trips only,
so two arms that complete different shares of their trips are not being measured on
the same set of journeys.

### The mistake this chapter originally made, and its correction (D27)

The first version of this chapter reported that the individual levers "reverse
sign" below the default, and in particular that pricing alone makes delay
significantly *worse* at 2,000 (+23.2% ± 17.5% with 15 seeds). That reading was
wrong, and it was wrong in exactly the way Chapter 28 warns about, only in the
opposite direction from the parking result of Chapter 21.

At 2,000, pricing completes **98.8%** of trips against the baseline's **81.9%**, a
paired gain of **+17.0 ± 5.9 points**. The trips pricing rescues are the long,
badly delayed ones the baseline never finishes. They enter pricing's average and
are missing from the baseline's. Pricing's mean delay goes up *because it is doing
better*, not worse. Only 3 of 15 baseline seeds complete fully at that capacity, so
a completion-matched comparison (the fix used in Chapters 21 to 23) is not possible
here; among those 3 seeds pricing is lower in all 3, which is suggestive and
nothing more.

The error was caught in the final audit (`lab/qa/2026-11-10-qa.md`,
`checks/audit_numbers.py`) and is recorded as D27. D24 and D26 are left in the
decision log as written, with D27 correcting them.

### What survives

**The combined lever is the one result that reads the same on both measures.** It
lowers delay in direction at every capacity (−11.5% ± 11.4% at 1,200, −8.2% ± 13.4%
at 1,600 with 11 of 15 seeds negative, −38.9% ± 9.7% at 2,000, −67.3% ± 4.3% at
2,400), and at each of the three lower capacities it also completes more trips
(+17.5 ± 11.3, +17.1 ± 7.7 and +16.4 ± 5.5 points). Completion bias therefore works
*against* it: its delay figures understate its benefit.

The individual levers are not robust in the same way, but "not robust" is a weaker
statement than "reversed". Adaptive signals alone lower delay at 1,600 (−16.5% ±
8.8%) with no significant completion change (−4.4 ± 5.6 points) and show no clear
delay effect at 2,000 (+2.7% ± 16.0%). Pricing alone raises completion at 1,600
and 2,000 while its completed-trip delay does not fall. Below the default, their
effect on delay is **undetermined by this metric**.

### What would settle it

A metric that counts unfinished trips, such as total system delay with stranded
vehicles charged for the time they spent in the network, or a horizon long enough
that every arm drains. `compare_capacity_sweep.py` does not record either, so this
is future work (Chapter 48).

### Why this is still a strengthening of the project's case

The sweep still identifies which claim is the strong one. The standalone adaptive
and pricing results are **conditional on the calibrated capacity assumption**. The
**combined lever** is the project's most capacity-robust claim, and after the
completion check it is supported by two measures instead of one.
