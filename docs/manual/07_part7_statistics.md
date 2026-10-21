# Part VII — Statistical Methodology

## Chapter 25: Why One Simulation Run Proves Nothing

### The discovery that shaped this entire project

Early in this project, a seemingly trivial test revealed something that changed how
every subsequent comparison was designed: changing the simulation's total demand by
just **0.02 percent** — a change small enough that no one would expect it to matter —
moved a single simulation run's average delay by **2.3 percent.** That is a signal-
to-noise ratio bad enough to make a single run worthless for comparing interventions:
if a change this small in demand alone can move the output by more than two percent,
then an intervention whose real effect is, say, five percent could easily be
measured anywhere from two to eight percent on a single unlucky or lucky run, with no
way to tell which number is closer to the truth.

### Where the noise comes from

This noise is not a bug — it is an intrinsic feature of any traffic simulator with
realistic, reactive route-choice behavior (Part V). UXsim's route-choice process
carries its own internal stochastic noise (`duo_noise`, in the simulator's own
terminology), meaning that even running the *exact same* configuration twice, with
two different random seeds, produces two genuinely different, independently valid
realizations of how traffic could have unfolded. A single run is a single sample from
a distribution of possible outcomes, not the one "true" answer.

### The consequence for this project's design

Given this, no comparison in this project ever draws a conclusion from a single run of
anything. Every comparison between two configurations — a fixed-time baseline against
an intervention, or one capacity assumption against another — is run across **the same
set of random seeds in both configurations**, and the comparison is made seed-by-seed,
paired, rather than by comparing the two configurations' unpaired overall averages.
Chapter 26 explains precisely how that pairing works and why it matters.

---

## Chapter 26: Paired Seeds and Confidence Intervals

### Why pairing, not just averaging more runs

It might seem like the fix for noisy single runs is simply "run many more of them and
average" — and that is close to correct, but *how* those many runs are compared
matters as much as how many there are. If configuration A is run on seeds 1 through
15, and configuration B is run on a *different* set of seeds, 16 through 30, then any
difference between their average outcomes is contaminated by whatever seed-to-seed
variation exists in the underlying noise, on top of whatever real difference the
intervention produces. **Pairing** — running both configuration A and configuration B
on the *identical* seed 1, then the identical seed 2, and so on — means that seed 1's
particular realization of route-choice noise affects both configurations the same
way, and so it mostly **cancels out** when the *difference* between A and B on that
seed is computed. What remains, after this cancellation, is a much cleaner estimate
of the intervention's actual effect.

### Computing the confidence interval

For each paired seed $s$, this project computes the difference
$d_s = \text{delay}_B(s) - \text{delay}_A(s)$ (or, more often, the equivalent
percentage change). Across all 15 paired differences, the project computes:

```latex
\bar{d} = \frac{1}{n}\sum_{s=1}^{n} d_s
\qquad\qquad
\text{SEM} = \frac{\text{stdev}(d_s)}{\sqrt{n}}
```

and reports a **95 percent confidence interval** as $\bar{d} \pm t_{0.975,\,n-1}
\cdot \text{SEM}$, using the Student's $t$-distribution's critical value for $n-1$
degrees of freedom (14, for this project's standard 15-seed design), rather than the
normal distribution's critical value, because the normal approximation is less
accurate at this comparatively small sample size. This computation is implemented
once, in a single shared function (`ci95()`, inside `scripts/compare.py`), and
**every other script in this project that reports a confidence interval imports and
reuses that exact function**, rather than re-implementing the same statistics
independently in each script. This single-source-of-truth discipline exists for a
concrete, specific reason explained in Part VIII: an earlier version of one of this
project's own supporting scripts hand-copied only a *partial* table of
$t$-distribution critical values (missing several degrees-of-freedom entries), which
produced subtly wrong, too-narrow confidence intervals for comparisons that happened
to fall outside the copied table's range. Importing one shared, complete
implementation everywhere is the fix, and it is a general lesson worth stating
explicitly: hand-copying a piece of a well-defined mathematical object, instead of
computing or importing it in full, is exactly the kind of error that is invisible
until it silently corrupts a specific downstream result.

### Why 15 seeds, specifically

Fifteen is not a number derived from a formal power calculation — it is a practical
choice, balanced against this project's computational budget (each individual
simulation run takes meaningful wall-clock time and several gigabytes of memory,
Part XIII covers this in detail) and the goal of having enough seeds that a
**unanimous or near-unanimous direction of agreement** across all of them becomes a
meaningful, strict statistical standard in its own right — which is exactly the
subject of the next chapter.

---

## Chapter 27: Multiple Comparisons

### The problem

This project makes **15 distinct paired-seed comparisons** in total across its full
body of work (the core result's three levers, the additional interventions, the
sensitivity sweep, and more), and running many separate statistical tests raises a
classic concern: at a conventional significance threshold of $p < 0.05$, roughly one
in twenty tests would be expected to show a "significant" result purely by chance,
even if every single one of the underlying effects were actually zero. Applying a
formal multiple-comparisons correction (lowering the significance threshold for each
individual test, to compensate for running many of them) is the standard textbook fix.

### This project's alternative: a much stricter, non-parametric bar

Rather than apply a formal correction to the confidence-interval-based tests directly,
this project relies on a different, and in this specific case *stricter*, standard:
**every supported finding in this project has at least 12 of its (up to 15) paired
seeds agreeing in the direction that was predicted before the run was made** —
several of them unanimously, 15 out of 15. Because each test's direction was
committed to in advance (an experiment card is written, with its prediction, *before*
the run — Chapter 29 explains why this matters even more directly in the context of
this project's one serious self-correction), the probability of all 15 seeds agreeing
in sign purely by chance, if the true underlying effect were genuinely zero, is:

```latex
P(\text{15/15 agree by chance}) = 0.5^{15} \approx 0.0031\%
```

and for the two findings resting on a reduced, 12-clean-seed sample (after the
completion-bias check removes contaminated seeds, Chapter 28):

```latex
P(\text{12/12 agree by chance}) = 0.5^{12} \approx 0.0244\%
```

Both of these are far stricter than a nominal $p < 0.05$ threshold applied to even a
single, uncorrected comparison — let alone one of fifteen. This project's own
statistics-review pass (conducted by a dedicated adversarial-review process, not
self-assessed) explicitly checked this reasoning for a subtle but important error:
an initial draft of the above calculation mistakenly treated the test as two-tailed
(as if "all seeds disagree" were an equally meaningful outcome to flag), which was
caught and corrected to the proper one-tailed form, since the direction was
*predicted* in advance, not merely observed after the fact. This correction is itself
a small, concrete example of the review discipline Part VIII describes in full.

---

## Chapter 28: Completion Bias — The Project's Recurring Trap

### What completion bias is

A traffic simulation does not force every simulated trip to finish within its
horizon. If a link or intersection becomes severely enough congested, some vehicles
may still be queued, mid-trip, when the simulation's clock runs out — these trips are
**incomplete**, and by convention, an incomplete trip's delay is excluded from the
average delay statistic entirely (there is no well-defined "delay" for a trip that
never arrived). This creates a trap: an intervention that makes the network *worse*
overall can still show a *lower* average delay, if its effect is severe enough that
the very worst, longest-delayed trips simply never finish and get dropped from the
average — leaving only the easier, shorter trips to be averaged, producing a number
that looks like an improvement while describing something closer to the opposite.

### Where this project encountered it, each time catching it before trusting a result

This is not a single, one-off problem that was fixed once — it is a recurring pattern
this project's methodology specifically guards against on **every** comparison, and it
has shown up, concretely, more than once:

- **Signal-placement threshold testing** (Chapter 7): a looser signalisation rule
  appeared to produce lower total delay, until completion rate was checked and found
  to have dropped to 78 percent — 22 percent of trips were silently excluded from
  that lower-looking average.
- **The parking/encroachment-enforcement intervention** (Chapter 21): an apparent 28
  percent delay reduction turned out to be almost entirely this artifact, with 10 of
  15 seeds becoming newly incomplete.
- **The sensitivity sweep's capacity-cliff finding** (Part X, Chapter 37): every
  parameter variant that increased congestion dropped completion into the 75-83
  percent range, a general, structural warning sign about how close to a fragile
  operating point this project's calibrated baseline actually sits.

### The standing rule this project follows as a result

Because of this recurring pattern, **no result in this project is ever reported, or
trusted internally, without checking completion rate alongside delay** — and where an
intervention causes any seeds to become newly incomplete relative to the baseline,
this project reports results on the **"clean seeds" subset only**: the seeds where
both the baseline and the intervention achieved full (or matching) completion, which
is the only subset where a fair, apples-to-apples delay comparison is actually
possible. This project's own tables and figures explicitly report how many seeds
were excluded this way and why, rather than silently narrowing the sample size
without comment.
