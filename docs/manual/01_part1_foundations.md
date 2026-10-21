# Part I — Foundations

## Chapter 1: Why This Project Exists

Kathmandu Valley is one of the most densely populated urban areas in South Asia, and
its road network has not grown anywhere near as fast as the number of vehicles using
it. A 2012 government survey conducted jointly by the Japan International Cooperation
Agency (JICA) and Nepal's Department of Roads found that motorcycle traffic volumes
had grown roughly 19.8 times between 1991 and 2011 — an average annual growth rate
close to 16 percent, sustained for two decades. Most of that growth landed on arterial
roads that were never widened to match it.

Two responses are available to a city that does not have the years, the capital, or
the land acquisition process that a new road or a metro line would require:

1. **Retime the traffic signals that already exist**, so that green time is allocated
   to where the queues actually are, rather than on a fixed clock a traffic engineer
   set once and never revisited.
2. **Charge for road use during the busiest hours**, so that some of the demand that
   currently piles onto the network at 9 AM shifts to a less congested time, a less
   congested route, or doesn't happen by car at all.

Both of these act on infrastructure or policy that is already available today. Neither
requires a single new meter of road.

This project asks, as precisely as the evidence allows: **how much delay could these
two levers actually remove from Kathmandu's arterial network, and does combining them
produce something better than the sum of what each does alone?** That second question
matters because it is not just about magnitude — it is a claim about *mechanism*. If
pricing relieves congestion on a corridor, does that free up slack that an adaptive
signal can then exploit to cut delay even further, in a way that running either lever
alone could never achieve? Or do the two levers simply do their own, separate jobs,
with no interaction between them at all?

### Why simulate rather than just reason about it

It would be convenient to answer these questions by pure argument: "pricing reduces
demand on a link, adaptive signals use green time more efficiently, so together they
should obviously help more." But traffic networks are not simple sums of independent
parts. A link's delay depends on every other link that feeds into it and every signal
that controls it. Reducing demand on one corridor can push drivers onto a different
corridor that was previously under capacity, which can create a new bottleneck that
did not exist before. Predicting this by hand, for a network of 233 intersections and
590 directional road segments, is not something a person can do reliably. It has to be
simulated.

This manual explains, in full, how that simulation was built, calibrated, tested,
validated against real-world data, and where it still falls short. It is written so
that someone who has never seen this codebase, and who may not yet know what a
"mesoscopic traffic model" even is, can read from the first page to the last and
understand every decision that was made, what it cost, and why the alternative was not
chosen instead.

### The central discipline of this project

One idea recurs constantly throughout this manual, and it is worth stating up front so
that it does not feel repetitive later: **a single simulation run proves nothing.**
Every traffic simulator with any realistic route-choice behavior has some randomness
built into it, and this project discovered early on that a change in demand as small
as 0.02 percent could move a single run's average delay by 2.3 percent — noise, not
signal. Every comparison in this project is therefore run across 15 independent random
seeds per configuration, and reported as a confidence interval, never as a single
number from a single run. This discipline is what later allowed the project to catch
and correct its own most serious mistake (Part VIII), and it is the single most
important methodological habit this manual tries to teach.

---

## Chapter 2: Traffic Flow Theory, From the Ground Up

Before explaining *this* simulation, it helps to understand the family of ideas that
traffic flow theory as a field is built on, because every modeling choice in this
project is a choice between competing theories, not an arbitrary pick.

### The fundamental diagram

The single most important object in traffic flow theory is the **fundamental
diagram**: a curve relating three quantities on a road segment:

- **Density** $k$ — vehicles per unit length of road (e.g. vehicles per kilometer per
  lane).
- **Flow** $q$ — vehicles passing a point per unit time (e.g. vehicles per hour).
- **Speed** $v$ — the mean speed of vehicles on that segment.

These three are related by the simplest possible traffic equation:

```latex
q = k \cdot v
```

At very low density, vehicles can travel near the road's free-flow speed, and flow
rises roughly linearly with density. But as density keeps rising, vehicles must slow
down to maintain safe following distances, so speed falls — and at some point, flow
itself starts to *fall* too, because the loss in speed outweighs the gain in density.
This produces a curve that rises, peaks, and then falls: the fundamental diagram. The
peak is the road's **capacity** — the maximum sustainable flow it can carry. Beyond
that peak, adding more vehicles does not increase throughput; it only makes the jam
worse, a phenomenon drivers everywhere recognize as the difference between "busy" and
"gridlocked."

Two idealized shapes for this diagram are in common use:

- **Greenshields' model**: speed decreases *linearly* with density,
  $v = v_f(1 - k/k_j)$, where $v_f$ is free-flow speed and $k_j$ is jam density (the
  density at which vehicles are bumper-to-bumper and speed is zero). This gives a
  parabolic flow-density curve.
- **The triangular fundamental diagram**: flow rises linearly with density up to
  capacity, then falls linearly back to zero at jam density, with a different
  (steeper) slope on the way down. This is the shape used by the **kinematic wave
  model** described next, and it is the shape UXsim — this project's simulator —
  builds on.

The triangular shape has a physical interpretation that the parabolic one does not:
the rising branch's slope is the free-flow speed (how fast an uncongested vehicle
moves), and the falling branch's slope is the speed at which a traffic jam's back edge
propagates *backward* against the flow of traffic — something every driver has
experienced as a wave of brake lights rolling toward them on a highway, seemingly for
no reason, long after whatever caused it has cleared. That backward-propagating jam
wave is not an approximation or a side effect; it is a core physical prediction of the
model, and it is exactly the mechanism this project's "chain-reaction" congestion
findings in Part XII rely on.

### The Lighthill-Whitham-Richards (LWR) model and the kinematic wave

Lighthill and Whitham (1955) and Richards (1956), working independently, proposed
treating traffic as a *continuous fluid* governed by a conservation law:

```latex
\frac{\partial k}{\partial t} + \frac{\partial q}{\partial x} = 0
```

In plain language: vehicles are neither created nor destroyed inside a road segment,
so any change in density over time must be explained by more vehicles flowing in at
one end than flowing out the other. Combined with a fundamental diagram relating $q$
to $k$, this single conservation equation is enough to predict how a traffic jam forms,
how it propagates backward through a queue, and how it eventually dissolves once
demand drops. This is the **kinematic wave model**, and it is the direct mathematical
ancestor of every mesoscopic traffic simulator in use today, including UXsim.

### Newell's simplified car-following model

Newell (2002) showed that the kinematic wave model with a triangular fundamental
diagram is *mathematically equivalent* to a much simpler description of individual
vehicle behavior: each vehicle follows the one ahead of it, maintaining a given
time-headway and a minimum safe spacing, and its trajectory can be computed directly
from the vehicle ahead's trajectory, offset by that headway and spacing. This is
important for understanding what this project's simulator actually computes: it does
not model steering wheels, acceleration pedals, or driver reaction times in the way a
microscopic simulator (like SUMO or VISSIM) does. It tracks vehicle *platoons* moving
through a kinematic wave field that is, by Newell's equivalence, exactly the same
physics as a simplified car-following model — just computed far more efficiently,
because the model operates on the fluid-like aggregate rather than on every individual
vehicle's acceleration decision.

### Macroscopic, mesoscopic, and microscopic: the three families

Traffic simulation tools are usually grouped into three families, and it is worth
being precise about where this project's tool sits, because the choice has real
consequences for what the model can and cannot tell us:

- **Macroscopic models** treat traffic purely as a continuous flow, typically solving
  the LWR equation directly on each road segment with no notion of individual
  vehicles at all. Fast, but cannot represent discrete events like an individual
  vehicle queuing to turn left, or heterogeneous vehicle types mixed on the same
  lane.
- **Microscopic models** simulate every vehicle individually, with its own
  acceleration, lane-changing, and reaction-time behavior (SUMO, VISSIM, Aimsun are
  the best-known examples). This is the most behaviorally detailed option, and it is
  what Tiwari et al. (2024) used (SIDRA Intersection, a microscopic/analytical tool)
  for their two-intersection study this project cites as independent validation
  (Part XI). But it is computationally expensive: simulating 260,000 trips across 590
  links, individually, across 15 seeds per configuration and dozens of configurations,
  would be far slower than this project's time budget allowed.
- **Mesoscopic models** sit between the two: vehicles are grouped into platoons and
  move through links according to kinematic wave physics (so the aggregate behavior is
  realistic and the model is fast), but route choice, demand loading, and signal
  interaction are still represented at something close to individual-vehicle
  granularity. This is what UXsim is, and it is why this project chose it: mesoscopic
  models are the standard tool for network-scale questions (hundreds of intersections,
  many interventions, many random seeds) precisely because they are fast enough to
  make that scale of experiment practical, while still capturing the essential
  physics — queue formation, backward wave propagation, and capacity constraints —
  that a purely macroscopic model would smooth away.

This tradeoff is revisited explicitly in Chapter 3, where UXsim is compared directly
against the alternatives this project considered and rejected.

---

## Chapter 3: Choosing a Simulator: UXsim and Its Alternatives

### What UXsim is

UXsim (Seo, 2023; Seo, 2025) is an open-source, pure-Python mesoscopic traffic flow
simulator. It implements the kinematic wave model described in Chapter 2 on a network
of directed links and nodes, with platoons of vehicles (not individual cars) as the
unit of simulation. Its defining design choice — the one that matters most for this
project — is **`deltan`**, the number of real vehicles represented by one simulated
platoon. This project uses `deltan=5` throughout: every simulated "vehicle" in the
model output actually represents five real vehicles moving together. This is why some
of this project's measurements (for example, link discharge flow in the capacity
calibration work of Part X) come out in coarse steps rather than smooth values — the
measurement granularity is fundamentally five vehicles per unit, not one.

### Why not a microscopic simulator (SUMO, VISSIM, Aimsun)?

The honest answer is a tradeoff, not a simple "ours is better": a microscopic
simulator would represent individual driver behavior, lane-changing, and gap-acceptance
far more realistically than UXsim does. SUMO in particular is free, widely used in
research, and has no license cost. The reasons this project did not use one:

1. **Computational cost at this project's scale.** This project's statistical design
   (Part VII) requires running every configuration across 15 independent seeds,
   across more than a dozen distinct interventions, plus sensitivity sweeps and
   robustness checks that multiply that further (the capacity-sensitivity sweep alone,
   Part X, ran 80 full-network simulations). A microscopic simulator modeling every
   individual vehicle's car-following and lane-changing decisions across a
   260,000-trip demand matrix, 590 links, and this many repeated runs would have made
   this project's full experimental design impractical within its time budget.
2. **The question being asked does not require individual-vehicle fidelity.** This
   project's two central interventions — signal retiming and congestion pricing — act
   at the level of links and intersections, not individual driver psychology. A
   mesoscopic model's kinematic-wave physics (Chapter 2) already captures queue
   formation, spillback, and capacity constraints correctly; what it does not capture
   is fine-grained behavior like aggressive lane-changing or gap acceptance at an
   unsignalized merge, which matters more for safety studies than for an aggregate
   delay comparison between control policies.
3. **Pure Python, no external binary dependency.** SUMO and VISSIM are separate
   compiled applications that a Python research pipeline has to shell out to and
   parse output files from. UXsim is a Python library, so this project's entire
   pipeline — network import, demand generation, every intervention, every
   statistical comparison — runs as ordinary Python function calls, which made the
   kind of rapid, paired-seed experimentation this project relies on (run a
   configuration, change one parameter, rerun, compare) far more direct to build and
   far easier to make fully reproducible (Part XIII).

### Why not a macroscopic model?

A pure macroscopic (link-based LWR, no discrete vehicles at all) model would be even
faster than UXsim, but it cannot represent the signal-control interventions this
project tests in a realistic way: adaptive signal control (Part VI, Chapter 18) reacts
to the specific queue length on specific approaches at specific moments, and
congestion pricing (Chapter 19) is applied per-link based on observed delay. Both of
these need at least a platoon-level (not a purely continuous) representation of
vehicles to make sense, which rules out the purely macroscopic option for this
project's purposes.

### Why not MATSim?

MATSim is a widely used agent-based transport simulation framework, strong at
whole-day activity-based demand modeling (where an agent decides whether to go to
work, then shopping, then home, and chooses a mode and route for each leg). This
project's demand is a single peak-hour synthetic matrix (Part III), not an
activity-based day plan, so MATSim's main strength — modeling the chain of decisions
behind why a trip happens at all — was not what this project needed. UXsim's simpler,
link-based kinematic-wave approach was a closer match to the actual question being
asked: given a fixed demand matrix, how much does the network's delay change under
different control policies?

### The honest limitation this choice carries forward

Because UXsim is mesoscopic, it has no genuine car-following model, no reaction time,
and no lane-level dynamics. This has a direct, named consequence that recurs throughout
this manual: effects like roadside parking, informal stops, and lane indiscipline —
all real features of Kathmandu traffic — cannot be represented as *behavior* in this
model. Instead, this project represents their aggregate effect as a reduced free-flow
speed (Chapter 12), which reproduces the *outcome* of poor driving conditions (slower
traffic) without being able to say anything about *why* speeds are slow, or to
distinguish "drivers behave erratically here" from "this intersection's geometry is
just bad." This tradeoff is logged formally as Decision D1 in this project's decision
record, and it is revisited honestly in the paper's own Discussion section.

---

## Chapter 4: How the Pieces Fit Together — Project Architecture

Before diving into each individual piece in detail (Parts II through XII), it helps to
see the whole pipeline laid out once, so that later chapters' details have a map to
attach to.

### The data flow, start to finish

```
1. data/kathmandu.osm.xml          <- raw OpenStreetMap extract (committed to the repo)
         |
         v  scripts/build_network.py
2. data/network_nodes.csv,
   data/network_links.csv          <- cleaned, merged, UXsim-ready network

3. data/zones.csv,
   data/od_matrix.csv              <- synthetic gravity-model demand
         |  scripts/build_od.py
         v
4. scripts/run_baseline.py          <- loads network + demand into a UXsim World,
                                        signalises intersections, runs one simulation
         |
         v
5. scripts/compare.py, compare_extra.py,
   compare_tidal.py, compare_capacity_sweep.py,
   compare_future_demand.py        <- run run_baseline.py's build_world() across many
                                        seeds and configurations, compute paired
                                        statistics
         |
         v
6. results/*.csv                    <- every comparison's raw, per-seed output
         |
         v
7. paper/figures/*.py                <- turn results/ CSVs into charts and tables,
   paper/build_pdf.py                   never typing a number by hand
         |
         v
8. paper/kathmandu_traffic_paper.pdf <- the final, citable output
```

Every box in this chain reads only from the box above it, and every number that ends
up in the paper or in this manual traces back, through that chain, to a CSV file in
`results/` that a script actually produced. This is a discipline, not an accident: the
project's own quality-assurance passes (`lab/qa/`) specifically checked that no number
in any document was typed by hand instead of computed from a result file, because a
hand-typed number is exactly the kind of error that is invisible until someone tries to
reproduce it.

### The role of `lab/`

Running parallel to the code is a research lab notebook (`lab/`), which is not
incidental documentation — it is the project's record of *why*, not just *what*:

- `lab/charter.md` — the research question and mode (discovery vs. synthesis).
- `lab/assumptions.md` — every unverified modeling choice, tagged A1 through A12,
  each with its status (untested, supported, violated, or accepted) and which
  headline claim it underpins.
- `lab/decisions.md` — an append-only log of every design decision, each with its
  alternatives considered, its dissenting view, and when it should be revisited.
  Twenty-four decisions (D1 through D24) are recorded at the time of this manual.
- `lab/experiments/` — one card per hypothesis tested (E1 through E9), each with its
  prediction written *before* the run, so that what counts as success or failure was
  fixed in advance.
- `lab/notebook/` — a dated, chronological log of what was done each day and why.

This manual draws on all of these directly, and where a design choice is explained, it
is almost always because a specific entry in `lab/decisions.md` or
`lab/assumptions.md` already made the reasoning explicit — this manual's job is to
teach that reasoning, not invent new justifications after the fact.
