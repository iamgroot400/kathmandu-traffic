# Part XI — Grounding the Model in the Real World

## Chapter 39: Independent Field Validation — Tiwari et al. (2024)

### Why an independent source matters more than another internal check

Every validation chapter so far in this manual (Part IX) describes a check this
project ran on its *own* model, against data this project gathered and processed
itself. A genuinely independent source — a study with no connection to this project
at all, measuring real Kathmandu intersections directly in the field — carries a
different kind of evidentiary weight: it cannot be subject to this project's own
modeling choices, assumptions, or errors, because it was produced by someone else,
for a different purpose, using different tools.

### The study

Tiwari, Khadka, Poudel, Giri, Malla, Aryal, and Pradhananga (2024), published in the
*Nepal Journal of Civil Engineering*, studied two real, named intersections on
Kathmandu's Ring Road — **Satdobato and Gwarko** — using **SIDRA Intersection**, a
microscopic, analytical traffic-engineering tool (Chapter 3 situates SIDRA relative to
this project's own, mesoscopic choice of tool). Crucially, they calibrated and
validated their own model using the **exact same GEH statistic** this project's
validation work (Part IX) relies on — a shared, standard yardstick that makes a direct
comparison between the two studies' findings meaningful.

### What they measured, and what this project found when it checked

They built a SIDRA Intersection model of both intersections and calibrated it to
field data. The model gives existing delays of **226.5 seconds per vehicle at
Satdobato and 201.1 seconds at Gwarko**, both the worst service level by
conventional grading. After optimizing signal phasing and cycle timing *alone*, with
**no new infrastructure**, the model gives **51.8 and 52.5 seconds respectively**,
roughly a three-quarters reduction at each intersection.

An earlier version of this chapter called this "field-measured confirmation". That
overstated it. The saturation flows were measured in the field; the before and
after delays are outputs of a calibrated model, because the optimized timings were
never installed. What the paper provides is **a second, independent model built on
field data that points the same direction** as this project's H1 finding (Chapter
18): a different tool and a different team, but still a model.

### A second, equally important finding from the same paper

The same study also tested **coordinating** signal timing between the two
intersections, rather than optimizing each one in isolation — and found that
coordination performed **worse**, not better, attributing this to the physical
spacing between the two intersections reducing any benefit from vehicle platooning
that coordination is meant to exploit. This is an **independent, real-world precedent
for the exact same shape of finding** as this project's own super-additivity
correction (Part VIII): combining two individually effective measures is **not
guaranteed to outperform optimizing them separately**, and in this case, measured in
the real world rather than simulated, it did the opposite.

### A direct, quantitative cross-check this project performed on itself

Because the same paper reports **field-measured saturation flow rates** at both
intersections — **1,203 to 2,160 vehicles per hour per lane** — this project was able
to directly compare that real number against its own model's internally computed,
*not measured but calibrated*, per-lane capacity (roughly 2,400 vehicles per hour per
lane, Chapter 13). The comparison is unflattering, and reported as such rather than
glossed over: this project's own capacity assumption runs **above** the real,
field-measured range, suggesting the baseline may allow somewhat more per-lane
throughput than Kathmandu's roads actually sustain under real, mixed traffic
conditions. This single, independent data point is precisely what motivated the
entire capacity-sensitivity sweep described in Part X, Chapter 38 — a genuine,
externally-sourced uncertainty, acted on directly rather than ignored because it was
inconvenient.

---

## Chapter 40: What Fourteen Other Cities Taught Us

### Why this comparison was scoped down, deliberately, rather than attempted in full

A full brief existed to research traffic interventions across **35 cities** and 16
distinct intervention types. Attempting all of it in one pass would have forced
shallow, under-verified claims on most of them — exactly the failure mode this
project's own citation discipline (every claim tied to a source that was actually
opened and read, never invented) exists to prevent. This project instead covered a
deliberately narrower, explicitly-scoped slice: **fourteen cities**, chosen for
relevance (South Asian and Southeast Asian cities sharing Kathmandu's mixed-traffic,
motorcycle-heavy character — Dhaka, Delhi, Lahore, Karachi, Colombo, Pokhara, Hanoi,
Manila, Bangkok, Nairobi) and for the strength of their documented track record
(Curitiba, Bogota, Seoul, Singapore), plus Jakarta, reused from this project's
earlier, separately-verified congestion-pricing research. Every source consulted is
logged, with its verification status honestly marked — most of this comparative pass
relies on web-search synthesis rather than this project's gold-standard of directly
opening and reading a full source, and this distinction is marked plainly everywhere
it applies, rather than allowed to blur into false confidence.

### The single strongest, most consistent pattern found

Across every one of these fourteen cities, one pattern recurred more consistently
than any other: **interventions that depend on sustained, discretionary enforcement
tend to fail in low-institutional-capacity settings.** Jakarta's occupancy-based "3-in-1"
rule was defeated by drivers hiring strangers (sometimes children) to sit in the
vehicle and satisfy the rule without genuinely sharing the trip. Hanoi's 2004-2005
motorcycle registration suspension in its most congested districts was defeated
simply by riders using motorbikes registered in a neighboring province, which the
suspension did not cover. Colombo's first attempt at a dedicated bus lane was
scrapped after a short period because of weak enforcement and motorist
non-compliance — while a later, second attempt, backed by active, sustained
enforcement, did show a reported speed improvement. Pokhara installed traffic
signals at its main intersections that are, by the most recent reporting found,
**still not in use**, with police continuing to direct traffic manually by hand.

This pattern is directly, mechanistically relevant to this project's own choice of
centerpiece lever (Chapter 18): **adaptive signal control requires no enforcement of
driver behavior at all.** It is implemented entirely at the controller level, and a
driver benefits from it without needing to comply with, know about, or be caught
violating anything. Across every city this comparative review checked, this is
precisely the category of intervention that survives in low-enforcement-capacity
settings, while the alternative category — rules requiring drivers to behave
differently and be checked on it — recurs, city after city, as the category that
fails.

### A second pattern, worth stating honestly

South Asian bus-rapid-transit (BRT) attempts specifically — as opposed to Latin
America's celebrated examples (Curitiba, Bogota) — show a markedly worse track
record: Delhi's BRT corridor was built and then **physically dismantled** after a
court-ordered evaluation found it degraded other traffic; Karachi's Green Line
overran its budget by roughly **2x** and its schedule by roughly **6x**, with
ridership settling at well under a quarter of what officials had projected. This
project's own evidence does not support treating BRT as a straightforwardly portable
success story for a city sharing Kathmandu's institutional and infrastructural
constraints, even though it has worked well in other contexts.

### An honest methodological caution this comparison itself surfaced

One widely cited figure — Manila's EDSA Busway cutting a specific route's travel time
from nearly three hours to around 45 minutes — is explicitly **confounded**: the
measurement window overlaps with a period of pandemic-driven traffic reduction that
had nothing to do with the bus lane itself. This is flagged directly in this
project's own review as a general warning: an uncontrolled, real-world "before and
after" headline figure can be impossible to separate from an unrelated external
shock, which is precisely the kind of confound this project's own paired-seed,
controlled simulation design (Part VII) exists specifically to avoid — a useful
reminder of why this project's own methodology matters, found by looking outward at
other cities' evidence rather than only inward at its own.

---

## Chapter 41: Why Congestion Pricing Is Not Recommended Yet

### The simulated result, restated

Taken purely on its own simulated terms, congestion pricing is this project's
*second*-strongest individual lever: a 31.89 percent reduction in delay (Chapter 19),
a real and statistically robust result inside this model.

### Why a simulated result alone cannot answer the deployability question

A simulation can answer "if this policy were implemented exactly as specified, how
much delay would it remove?" It cannot, on its own, answer a different and equally
important question: "can this policy actually be implemented, and sustained, in this
specific city's institutional context?" Chapter 40's cross-city evidence bears
directly on that second question, and the answer it points to is considerably more
cautious than the simulated number alone would suggest.

### The closest real-world precedent, and why it is discouraging

No well-documented case was found, across this project's comparative review, of
congestion pricing being **implemented and measured** in a lower- or middle-income
country under institutional capacity comparable to Nepal's. The closest available
precedent is **Jakarta**, where a proposed electronic road pricing scheme never
launched at all, after roughly a decade of attempts, and the occupancy-based rule
used in its place was defeated by exactly the enforcement-evasion pattern Chapter 40
describes in general. This points to a structural weakness specific to any
congestion-control scheme that depends on **manual, discretionary enforcement rather
than automated detection**: it is vulnerable to precisely the kind of workaround
observed, repeatedly, in Jakarta and elsewhere.

### The practical conclusion this project draws

Adaptive signal control, by contrast, requires no enforcement of driver behavior at
all — a practical advantage this project's simulation results alone cannot capture,
since the simulation only measures the *delay* a policy would remove if faithfully
implemented, not the *probability* that a given city can actually sustain its
implementation. This practical advantage is precisely why this project's real,
deployable, hackathon-scale deliverable centers on signal retiming rather than
pricing, even though pricing's simulated number is numerically larger — congestion
pricing remains part of this project's evidence base, genuinely studied and reported
honestly, but reserved for the project's academic paper and future work rather than
proposed as this project's near-term, practical recommendation for Kathmandu.
