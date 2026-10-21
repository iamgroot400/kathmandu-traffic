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
6.4%**, pricing **−29.7% ± 14.7%**, combined **−67.3% ± 4.3%** — all statistically
significant at this reduced sample size, and consistent in direction with the
project's full, 15-seed main result.

**Below that capacity, the two individual levers degrade — and can reverse sign
entirely.** At 2,000 vehicles per hour per lane, pricing alone comes out at **+38.2%
± 16.5%** — a statistically significant result, but in the *wrong* direction: pricing
alone makes delay *worse*, not better, under this lower (and, per Tiwari et al.'s
real measurements, arguably more realistic) capacity assumption. Adaptive signal
control alone, at the same capacity, comes out at **+9.6% ± 11.1%** — no longer a
significant improvement at all. **The combined lever is the only one that stays
directionally beneficial at every single capacity level tested** — negative
(beneficial) at all four levels, statistically significant at three of the four,
including the lowest (1,200) and highest (2,400) levels, with the 1,600 level's wide
confidence interval (given the reduced seed count) the main reason it falls just
short of significance there.

### Why this is a strengthening of the project's case, not a weakening of it

This finding could easily be mistaken for bad news — "two of our three headline levers
aren't robust" — but the correct reading is more specific and, if anything, more
useful: it identifies **exactly which of this project's claims is the strong one.**
The standalone adaptive-signal and pricing results should now be read as
**conditional on this project's calibrated capacity assumption holding** — a real,
named caveat that this project's paper states explicitly, rather than continuing to
present those two findings with the same unconditional confidence as before this
sweep was run. The **combined lever**, by contrast, emerges as this project's **most
capacity-robust claim** — the one finding that survives a real, substantial range of
uncertainty in an assumption this project never had the ability to measure directly
against the city. This is a textbook example of what a genuine robustness check is
supposed to do: not simply confirm what was already believed, but **sharpen exactly
which part of a conclusion deserves confidence, and which part does not.**
