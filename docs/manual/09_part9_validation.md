# Part IX — Validation Against Reality

## Chapter 33: The GEH Statistic

### Why an ordinary percentage error is the wrong tool here

A natural first instinct for comparing a model's predicted traffic volume against a
real, observed count is simple percentage error: $(M - C)/C$, where $M$ is modeled and
$C$ is the observed count. The problem with this measure is that it behaves
inconsistently across very different volume scales: a 50-vehicle-per-hour error on a
quiet side street (where the observed count might be only 100 vehicles per hour) is a
50 percent error, while the same 50-vehicle-per-hour error on a major arterial
carrying 5,000 vehicles per hour is only a 1 percent error — yet the *absolute* size
of the mistake is identical in both cases.

### The GEH formula

The transportation-engineering field's standard answer to this is the **GEH
statistic** (named for Geoffrey E. Havers, the transport planner credited with
developing it), defined as:

```latex
\text{GEH} = \sqrt{\frac{(M - C)^2}{(M + C)/2}}
```

This formula behaves like an absolute difference when volumes are small, and like a
relative (percentage) difference when volumes are large, giving it sensible behavior
across the wide range of volumes a real road network actually contains — exactly the
property a plain percentage error lacks. **GEH < 5** is the conventional pass
threshold used across the transportation-engineering field; this project adopts that
same convention rather than inventing its own.

### What a GEH check does, and does not, claim

Passing this check at a given location supports the claim that **the model's traffic
pattern is plausible at that specific point** — not that the model is correct
everywhere, and not that it describes the *present day* if the observed data is old
(which, as the next chapter explains, this project's is).

---

## Chapter 34: Where the Observed Data Came From

### The source

This project's observed traffic counts come from a real, government-conducted survey:
the **Japan International Cooperation Agency (JICA) and Nepal's Department of Roads**
jointly surveyed traffic at Kathmandu intersections between **December 2011 and
January 2012.** Two of the six landmarks this project checks against — **Koteshwor and
Thapathali** — are cross-referenced against a **2017 JICA follow-up report** that
reproduces the same two counts as clean, machine-readable text, rather than the
original 2012 report's scanned, non-text-extractable table images, giving those two
specific numbers an extra layer of confirmation the other four landmarks' numbers
lack.

### The precision gap among the six landmarks

Not all six checked landmarks carry the same evidentiary weight, and this project is
explicit about the difference rather than treating all six as equally solid:
**Koteshwor and Thapathali's coordinates come from the original government survey
itself** — genuinely surveyed points. The remaining four (**Kalimati, New Baneshwor,
Old Baneshwor, Sorakhutte**) are geocoded via OpenStreetMap's Nominatim service based
on their named location, not taken from the original survey's own coordinates — a
real, named source of extra imprecision that this project flags in every table and
chart that reports these six results, marking the four approximate ones distinctly
from the two surveyed ones.

### The age of the data, and what it means

The observed data predates this project's OpenStreetMap network snapshot by roughly
**fourteen years.** This is stated plainly, every time this validation is reported,
specifically so that a clean result is never read as "the model matches Kathmandu
today" — the honest claim a passing GEH result at these six points can actually
support is narrower: it supports *plausibility of the model's spatial pattern*
relative to a real, if dated, measurement, not a claim about present-day accuracy.

---

## Chapter 35: What 2 of 6 Passing Actually Means

### The result, stated plainly

Checked against all six named landmarks, this project's calibrated baseline passes
GEH < 5 at **two of six (33 percent)** — Thapathali (GEH 0.77) and Old Baneshwor (GEH
3.16) fit well. The remaining four fail: **Koteshwor** fails worst, with the model
*undershooting* observed volume by roughly **five times** (GEH 102.22); **Kalimati**
and **New Baneshwor** also undershoot; **Sorakhutte** *overshoots* instead. This falls
well short of the roughly 85-percent-pass convention often cited as a target in the
transportation-modeling literature.

### Why the mixed direction of the errors matters

A simpler, single-direction failure pattern (say, every landmark undershooting by a
similar amount) would point toward one, likely global explanation — perhaps the
overall demand scale (Chapter 11) is simply too low everywhere. The fact that errors
run in **both directions** (some landmarks undershoot badly, one overshoots) rules
that simple explanation out, and points instead at the calibration method itself
(Chapter 14): fitting a single global demand scale against one aggregate target —
citywide mean speed — constrains *how much* total demand is loaded, but says nothing
about *where* it concentrates. The model can match the city correctly on average
while still being wrong, in either direction, at any individual, specific
intersection — which is exactly the failure mode Chapter 15's identifiability
discussion predicted in the abstract, now confirmed concretely, at named, real
locations.

### Why this was reported as a limitation, not hidden or minimized

This project's own internal documentation describes this result explicitly as
**"closed as a limitation, not a pass"** — a deliberate choice of phrasing, recorded
directly in the project's milestone tracking. A weaker research process might have
been tempted to describe a 33 percent pass rate more charitably, or to quietly narrow
the comparison to only the two landmarks that happen to pass. This project instead
reports all six, states the pass rate plainly, and — as the next section covers —
specifically investigates whether this validation gap undermines the project's actual
headline comparisons, rather than simply asserting that it does not.

---

## Chapter 36: A Single-Seed Spot-Check

### The question this check answers

A validation gap at the absolute level (Chapter 35) raises an important follow-up
question: **do the project's relative comparisons between interventions still hold
up, specifically at the locations where the baseline itself is known to be most
wrong?** It is entirely possible for a model to be wrong about absolute volume at a
location while still correctly predicting the *direction* an intervention moves
delay there — or it is possible that the model's error is severe enough to flip even
that directional prediction. This project checked directly, rather than assuming
either answer.

### The check, and its honest limits

At the two most discrepant intersections (Koteshwor, the worst undershoot, and
Sorakhutte, the one overshoot), this project ran a single-seed comparison of all three
of its main levers. Pricing and the combined lever still reduced delay at both
locations, in the same direction as the project's aggregate, 15-seed result. But
**adaptive signal control alone increased delay substantially at Koteshwor** — the
opposite direction from the project's aggregate H1 finding of a 24.5 percent
reduction, and specifically at the one location where the baseline's own volume
estimate is worst.

This project is explicit about the limits of what this check can and cannot
establish: it is a **single-seed spot-check**, not a statistically powered claim
comparable to the project's main, 15-seed paired result (Chapter 26 explains exactly
why a single run cannot be trusted on its own). It is reported here as a **bounded,
honest caveat** — adaptive signal control's benefit may not generalize uniformly to
every individual intersection, particularly ones where the underlying demand
estimate is most uncertain — rather than folded silently into, or allowed to
overturn, the aggregate finding it does not actually contradict at the statistical
level the aggregate result was established at.
