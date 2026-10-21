# Part VI — The Interventions

## Chapter 17: The Fixed-Time Baseline

Every intervention in this project is measured against a single, common reference
point: **128 signalised intersections, each running a fixed, 90-second, two-phase
cycle**, with the remaining 105 intersections left as free merges (Chapter 7 explains
exactly which intersections get signalised and why). This baseline is deliberately
simple and uniform — not an attempt to recreate Kathmandu's real, heterogeneous
(and often hand-operated) signal timings exactly, but a controlled reference that
every later comparison in this manual is measured against. Because it is simple and
uniform, any improvement measured later is attributable to the *intervention* being
tested, not to an accidental head start baked into an arbitrarily generous baseline.

At this baseline, roughly 99 percent of the project's 260,000 (demand-scaled, Chapter
11) peak-hour trips complete within the simulation's horizon, mean network speed is
approximately 17.7 kilometers per hour, and the delay ratio (how much longer the
average trip takes compared to free-flow conditions) is about 0.65.

---

## Chapter 18: Adaptive Signal Control

### What "adaptive" means here, and what it does not mean

This project's adaptive signal control is a **queue-actuated heuristic** — not a
learned policy, and not reinforcement learning. It is important to be precise about
this distinction, because "adaptive traffic signals" and "AI traffic signals" are
often used loosely in public discussion to mean the same thing, and they are not: a
learned policy (for instance, a reinforcement-learning controller) would be trained
on simulated or real experience to discover a signal-switching rule from data. This
project's controller instead implements a fixed, hand-specified, interpretable rule,
directly inspired by established queue-actuated signal control practice in traffic
engineering: **switch the active phase when a competing phase's queue exceeds the
current phase's queue by more than a lost-time-adjusted threshold.**

### The mechanics

Two parameters govern this behavior:

- **Lost time per switch (3.0 seconds)**: every time the signal switches phase, a
  short period is lost to the transition itself (the amber/all-red clearance
  interval, during which no vehicles are discharging) — a real, physical cost of
  switching too eagerly.
- **Discharge rate (0.5 vehicles per second per lane)**: how quickly queued vehicles
  clear once a phase turns green, used to translate the lost-time cost into an
  equivalent queue-length threshold, so that the controller does not switch phases
  so often that the cumulative lost time from switching outweighs the benefit of
  serving the longer queue sooner.

In practice, this means the signal behaves like a patient, locally-reactive traffic
officer: it holds the current phase green as long as its own queue is being served
reasonably, and only switches once the competing approach's backup has grown enough
to justify paying the lost-time cost of a phase change.

### Why this lever is the project's practical centerpiece

Adaptive signal control has a property neither of this project's other major levers
shares: it requires **no behavior change, compliance, or enforcement from drivers at
all.** It is implemented entirely at the controller level — software and, in a real
deployment, sensors at existing intersections — and a driver experiences its benefit
without having to know it exists, pay anything, or follow any new rule. This matters a
great deal for a city with limited traffic-enforcement capacity (a theme this manual
returns to with real, cross-city evidence in Part XI), and it is the specific reason
this project's hackathon-scale deliverable centers on this lever rather than pricing,
even though pricing alone also significantly reduces simulated delay (Chapter 19).

### The result

Across the project's full, 15-seed paired comparison, adaptive signal control alone
reduces mean delay by **24.50 percent** relative to the fixed-time baseline, with all
15 seeds agreeing in direction (a unanimous result, which — as Part VII explains in
depth — is itself a much stronger form of statistical evidence than a single p-value
from one comparison would be).

---

## Chapter 19: Congestion Pricing

### The theoretical basis: marginal-cost pricing

Congestion pricing, in its classical transportation-economics form, charges a driver
not for *using* a road, but for the **externality** their trip imposes on everyone
else sharing it — the marginal increase in everyone else's travel time caused by one
more vehicle entering an already-congested link. Priced correctly, this internalizes
a cost that would otherwise be invisible to the individual driver (who experiences
only their *own* delay, not the delay they cause others), and in theory shifts just
enough demand away from the most congested links and times to bring the network
closer to a more efficient operating point.

### This project's specific pricing rule

Rather than attempt to compute a theoretically "correct" marginal-cost toll from
first principles (which would require solving a much harder optimization problem than
this project's scope allows), this project tolls each link at **0.2 times its own
observed delay in seconds**, where the delay schedule is measured once from a single
untolled baseline run, and the toll is applied only during the peak demand window.

### Why 0.2, specifically

This is not a value derived from a formula — it is a judgment call, made explicitly
and for a stated, checkable reason (recorded as **Decision D4**): this project's
baseline run showed its single worst link carrying **3,733 seconds** of observed
delay. Charging that link at full (1.0×) marginal cost would have priced it so highly
that the simulation would effectively be measuring a road *closure*, not a toll — no
driver would choose to use it at all, which is a qualitatively different (and far
less policy-realistic) scenario than a toll meant to discourage, not eliminate, use of
a congested corridor. At 0.2×, the worst link's toll is capped near 750 seconds'
worth of charge (equivalent to roughly 62 Nepali rupees, at an assumed value of time
around 300 rupees per hour) — a toll that discourages marginal use without making the
corridor practically unusable.

### Why this is a stated lower bound, not a best estimate

This project's pricing model assumes **inelastic demand**: a driver facing a toll can
reroute around it, but cannot cancel the trip entirely or shift it to a different mode
or time in response to the price itself (the toll schedule and the demand matrix are
fixed, measured once, and applied together — demand does not re-respond to its own
toll in this model). A real deployment, with real elastic demand, would plausibly
show a *larger* effect than this simulation reports, since some drivers would avoid
the toll altogether rather than simply rerouting around it. This project states this
explicitly, every time pricing's result is reported, specifically to prevent the
number from being read as a ceiling rather than a floor.

### The result, and the deployability caveat that follows it

Pricing alone reduces mean delay by **31.89 percent**, also with all 15 seeds
agreeing in direction — numerically the stronger of this project's two individual
levers. But a purely simulated result like this cannot, on its own, speak to whether
congestion pricing is actually *deployable* in a setting like Kathmandu's — a
question this manual takes up with real, cross-city evidence in Part XI, Chapter 41,
where the honest conclusion is considerably more cautious than the simulated number
alone would suggest.

---

## Chapter 20: Tidal-Flow Lanes (Rejected)

### The idea

Many corridors carry noticeably asymmetric traffic by time of day — heavier inbound
flow during the morning peak, heavier outbound flow in the evening. A **tidal-flow
lane** scheme shifts a lane's direction (or, in this project's simulated version,
shifts capacity) from the lighter-loaded direction to the heavier one during the
relevant peak, without any new construction — an appealing, low-cost lever on paper.

### What this project actually tested

Three radial corridors were selected (by distance from the demand-weighted centroid
of the network, not from a traffic survey — an explicit, named simplification), and
capacity was shifted from the lighter to the heavier direction during a demand period
specifically reweighted to carry morning directional asymmetry — reweighted because
this project's base demand matrix, being production/attraction symmetric by
construction (Chapter 8), carries no such asymmetry on its own and had to have one
added deliberately for this one test. Two magnitudes were tried: a full lane-equivalent
shift, and a gentler, half-magnitude shift.

### What went wrong, and how it was diagnosed rather than just reported as a failure

At full magnitude, the intervention caused **new non-completion in up to 5 of 15
seeds** — trips that would have finished under the baseline failed to complete at
all once this change was introduced, a serious enough side effect on its own to
reject the full-magnitude version outright. But rather than stop at "it causes
gridlock," this project tested the gentler, half-magnitude version specifically to
separate two different possible explanations: was the full-magnitude shift simply
*too aggressive* (an over-correction, fixable by dialing it back), or was the
*concept itself* flawed regardless of magnitude? Halving the shift did eliminate the
gridlock side effect, confirming it was over-aggression, not a fundamental flaw in
the concept — but delay still did not improve at either magnitude. This isolated the
real problem precisely: the three corridors were chosen by geography, never checked
for whether the direction being *lightened* actually had spare capacity to give up.
This is reported as an honest negative result precisely because it tells a future
attempt exactly what a correct version would need — **capacity-aware corridor
selection**, not simply a gentler dial on the same geographically-chosen corridors.

---

## Chapter 21: Parking and Encroachment Enforcement (Rejected)

### The proxy, and its limits

This project does not have a way to simulate parking enforcement directly — there is
no individual parked vehicle to remove from a specific curb in a mesoscopic model.
Instead, this intervention is represented as a **network-wide increase in free-flow
speed, from 30 to 35 kilometers per hour**, standing in for the aggregate effect that
clearing roadside parking and encroachment would plausibly have on how fast arterial
traffic can move (recall Chapter 12's explanation of why free-flow speed is this
model's only lever for representing such frictions at all).

### The apparent result, and the artifact hiding inside it

At first glance, this intervention appeared to produce a substantial **28 percent**
reduction in delay. But this project's standing discipline against completion bias
(explained in full in Chapter 28) required checking completion rate before trusting
that number — and the check found that **10 of 15 seeds became newly incomplete**
under this intervention, meaning the apparent improvement was almost entirely an
artifact of excluding the slowest-finishing trips from the average, not a genuine
speed benefit. Among the five seeds that stayed fully complete in both the baseline
and the intervention — the only seeds where a fair, apples-to-apples comparison is
even possible — the real effect is small and **not statistically significant.**

This is one of the clearest illustrations, anywhere in this project, of why
completion rate must be checked alongside delay on every single comparison, not just
the ones that look suspicious in hindsight: this result looked like a strong success
story until the check was actually run.

---

## Chapter 22: Staggered Departures (Supported)

### The idea

Rather than changing infrastructure or control policy at all, this intervention
changes *when* the same total demand arrives: instead of loading all 260,000 trips
into a 3,600-second (one-hour) peak window, the same trips are spread across a
5,400-second (90-minute) window — a coarse proxy for coordinated schedule shifts
across institutions (staggered school and office start times, for instance), a policy
lever several real cities have attempted in some form.

### The result

This intervention reduced delay by **36.33 percent**, the **largest single-lever
effect measured anywhere in this project**, surviving the completion-bias check
cleanly (only 1 of 15 seeds was affected at all, a sharp contrast with the previous
chapter's parking result). The honest caveat: a 50-percent-longer departure window is
a substantial real-world coordination request, requiring genuine buy-in from many
separate institutions (schools, employers, government offices) simultaneously, and
this project's result should not be read as implying that a smaller, more modest
schedule shift would produce a proportionally smaller benefit — that scaling
relationship was never tested, and nothing in this project's evidence supports
assuming it is linear.

---

## Chapter 23: Decentralized Attraction (Supported, Confounded)

### The idea

This intervention models a 25 percent cut to trip *attraction* (how many trips end,
not start, in a cell) specifically at the city's "core" zones — a proxy for
relocating institutional destinations (government offices, for instance) out of the
dense city center, reducing the pull that draws so many trips toward one concentrated
area.

### The result, and the confound this project did not resolve

Delay fell by **31.13 percent**, also surviving the completion-bias check (12 of 15
seeds stayed clean). But this intervention has a structural problem that this
project's own methodology flags rather than hides: cutting attraction at the core
zones does not *only* redistribute where trips end — it necessarily also **reduces
total demand by 11.4 percent**, since some of those trips to the core simply cease to
exist in the reweighted matrix rather than being redirected elsewhere. No
volume-matched control (a separate run applying the same 11.4 percent demand cut
*uniformly*, rather than concentrated at the core, to isolate the pure
volume-reduction effect from the genuine redistribution effect) was run within this
project's time budget. This result is therefore reported honestly as
**supported-but-confounded** — real, robust, and statistically significant, but not
yet proven to be a "decentralization" effect specifically, as opposed to simply a
"less total demand" effect in disguise. This is flagged explicitly as the clearest
next step for anyone extending this work (Part XIV).

---

## Chapter 24: Cordon Demand (Abandoned)

### Why it was tried

A standing concern about this project's network scope (Chapter 5: only arterial
roads inside a bounded OpenStreetMap extract are modeled at all) is that real trips
originating or ending *outside* that boundary are simply invisible to the model. This
intervention attempted to add such **external, boundary-crossing demand** back in,
specifically to test whether doing so would expose congestion hotspots driven by
genuinely external trips that the project's core demand matrix misses.

### What happened instead

Rather than improving the model's face-validity against named, real landmarks, adding
this cordon demand **reduced** it — face-validity dropped from matching 2 of 7 named
landmarks before the change to only 1 of 7 after. This project diagnosed, rather than
simply discarded, this failure: one specific case (the Kalanki landmark) was traced
directly to a **map-boundary limit** — the landmark sits only 1.25 kilometers from the
edge of this project's OpenStreetMap extract, meaning the real road that actually
feeds traffic to it lies entirely outside the modeled network, so no amount of
cordon-demand tuning inside the existing boundary could fix it; the problem is a
scope limitation, not a demand-parameter error. A second failure (at a different named
landmark, Chabahil) could not be explained and remains an open question.

Because this intervention made results worse by a measurable, honest check rather
than better, it is **not used anywhere** in this project's reported results — a
negative finding, logged and preserved for future reference (Decision D6), rather
than quietly discarded as if the attempt had never been made.
