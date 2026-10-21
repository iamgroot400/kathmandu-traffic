# Part III — Modeling Demand

## Chapter 8: The Gravity Model, Explained

### The problem: there is no survey

To simulate traffic, you need to know not just the road network, but **how many
trips happen between every pair of locations** during the hour being modeled — an
origin-destination (OD) matrix. Kathmandu has no publicly available, recent,
comprehensive household travel survey that this project could draw such a matrix
from directly (the JICA survey this project uses for *validation*, Part IX, is a
set of point traffic counts at named intersections, not an origin-destination survey
covering the whole valley, and it is from 2011-2012, predating this project's
network snapshot by roughly 14 years). Lacking that, this project **synthesizes** a
plausible demand matrix using a gravity model, and is explicit, everywhere this
matrix is used, that it is a *hypothesis about where activity happens*, not a
measurement of real trips.

### The gravity model's core idea

The gravity model is named for its structural resemblance to Newton's law of
gravitation: the "pull" between two zones is proportional to how much activity each
one has, and falls off with the distance between them. Formally, this project's
implementation computes an unnormalized trip weight between every ordered pair of
zones $i$ and $j$ as:

```latex
w_{ij} = m_i \cdot m_j \cdot e^{-\beta d_{ij}}
```

where $m_i$ and $m_j$ are each zone's **mass** (an activity proxy, Chapter 9), $d_{ij}$
is the distance between them in kilometers, and $\beta$ is a **distance-decay rate**
(this project uses $\beta = 0.2$ per kilometer). These weights are then scaled so that
the whole matrix sums to the target total trip count — 260,000 peak-hour trips in this
project's main demand file.

### Why exponential decay, not a power law

Trip frequency between two places generally falls off with distance — nearby zones
exchange proportionally more trips than distant ones — and a modeler has to pick a
functional form for that falloff. A power-law decay ($d^{-\alpha}$) is a common
alternative in the gravity-model literature, but it diverges (blows up toward
infinity) as distance approaches zero, which is a serious practical problem for the
**intrazonal** term — the trips that start and end within the *same* zone, where a
literal distance of zero would otherwise need to be plugged into the formula.
Exponential decay ($e^{-\beta d}$) stays well-behaved (equal to 1, not infinite) as
distance approaches zero, so this project uses a small, nonzero **intrazonal
distance** (half a zone's grid-cell width) for the same-zone case rather than needing
a special-case rule, and the exponential form never produces a division-by-zero or an
unbounded weight anywhere in the matrix.

### What the decay rate controls, and how to check it

$\beta$ controls how "local" versus "cross-town" the synthesized demand pattern looks:
raise it, and trips concentrate more tightly around short, nearby journeys; lower it,
and long cross-town trips become relatively more common. This project's own demand
generation script prints the resulting **intrazonal trip share** (the fraction of all
trips that start and end in the same zone) every time the matrix is built, specifically
so that an extreme or implausible value is visible immediately, before it propagates
into a multi-hour simulation run. At the chosen settings, roughly 4.2 percent of
trips are intrazonal — a plausible, non-extreme figure for a city-scale demand matrix.

---

## Chapter 9: Zones — Where Trips Start and End

### The spatial unit: a one-kilometer grid

This project's demand model does not use administrative boundaries (wards,
municipalities) or named neighborhoods to define its zones. Instead, every road
junction extracted from the OpenStreetMap data (Chapter 5) is treated as a point of
activity, and these points are grouped into square grid cells **one kilometer on a
side**. Any cell with at least one junction in it becomes a zone; empty cells are
dropped entirely. This produced **109 zones** for this project's final demand matrix.

### Why junction density as the activity proxy, not population or land use

The honest, blunt reason: this project did not have access to a reliable, granular
population or land-use dataset for Kathmandu Valley at the time it was built. Junction
density — literally, how many road intersections fall inside a given one-kilometer
cell — was available directly from the same OpenStreetMap data already being used for
the network itself, and it is a defensible, if imperfect, *proxy* for activity:
commercial, mixed-use areas tend to have denser street grids than purely residential
suburbs or open land, so junction count correlates, loosely, with the kind of built-up
intensity that generates trips. This project's own assumption register records this
explicitly as **A1** — "demand is synthesized from a gravity model over junction
density, not survey/counted" — status **untested**, and flags it as the single
assumption that every other result in the project ultimately depends on, since it
determines the entire shape of where simulated traffic goes.

### A later, honest experiment: weighting junctions by road capacity

Much later in this project's life (Part X, robustness work), the question arose
directly: is junction *count* really the right proxy, or would junction *capacity*
(how many lanes converge there, reflecting that a junction on a four-lane highway
carries more real-world significance than one where two single-lane streets cross)
be a better one? This was tested properly — a lane-weighted version of zone mass was
built and compared directly against the plain-count version on the project's own GEH
validation (Part IX) — and the result was a **negative finding**, reported honestly
rather than discarded: the lane-weighted version did not improve the fit against
observed traffic counts, and in one case made a previously-good intersection's fit
noticeably worse. This is recorded as Decision D23, and it matters for a reason
broader than this one test: it would have been easy, after building a more
"principled-sounding" demand weighting, to simply report it as an improvement without
actually checking. Testing it against real data and reporting that it did *not* help is
exactly the discipline this manual keeps returning to.

### Zones must be reachable

Every zone's trips are injected into the simulation at its nearest *connected*
network node (Chapter 6) — a zone whose nearest raw node happened to lie outside the
network's main connected component would have its trips silently routed to the wrong
place, or fail to load at all. This project's zone-mapping step explicitly reports how
many zones ended up more than one kilometer from any node in the connected network, as
a visible check that the demand model and the road network actually agree on
geography.

---

## Chapter 10: Vehicle Mix and Passenger Car Equivalents

### Why Kathmandu's traffic cannot be measured in "vehicles" alone

A single lane carrying a stream of small motorcycles behaves very differently from the
same lane carrying buses: a motorcycle takes up a fraction of a car's road space and
can filter through gaps a car cannot, while a bus takes up multiple car-lengths and
accelerates far more slowly. Counting "vehicles per hour" without accounting for this
mix would treat a lane of 100 motorcycles as equivalent, from a capacity perspective,
to a lane of 100 buses — which is obviously wrong. Traffic engineering handles this
with **passenger car equivalents (PCU)**: every vehicle type is converted to a
standard unit (one passenger car = 1.0 PCU) by a weighting factor reflecting its real
road-space and performance impact.

### This project's fleet-mix weights

This project represents Kathmandu's fleet mix as roughly **70 percent two-wheelers**
(motorcycles and scooters, the dominant vehicle type on Kathmandu's roads by a wide
margin), **20 percent cars**, and **10 percent buses**, with PCU weights of **0.25**
for a two-wheeler, **1.0** for a car, and **2.5** for a bus. Combined, this gives a
blended **fleet PCU factor of 0.625** — meaning, on average, one real vehicle in
Kathmandu's traffic stream occupies about 0.625 of a standard passenger car's worth of
road capacity, once the heavy weighting of small, nimble motorcycles is accounted for.

### Why this matters for a single-class simulator

UXsim, like most mesoscopic simulators, is **single-class**: it does not track
different vehicle types moving at different speeds or occupying different amounts of
road space within the same simulation run. This project's fleet mix therefore cannot
enter the model as distinct motorcycle, car, and bus agents — it has to enter as a
single, PCU-weighted **demand multiplier** applied uniformly to the whole matrix. This
is explicitly a simplification, logged in this project's own assumption register
(**A2**): the fleet-mix weighting changes how much total *capacity-equivalent* demand
is loaded, but it cannot represent, for example, motorcycles filtering between stopped
cars in a way that genuinely increases a lane's real-world effective throughput beyond
what a single PCU number can capture.

---

## Chapter 11: Scaling Demand to a Loadable Level

### The gridlock problem

The first time this project attempted to load its full, citywide synthetic demand
matrix onto the arterial-only network (Chapter 5 explains why only arterial roads are
modeled at all), the result was outright gridlock: only **12 percent** of trips
completed, and mean network speed collapsed to **3 kilometers per hour**. This is not
a subtle calibration problem — it is the network being asked to carry far more demand
than it can physically process, because the full citywide demand matrix implicitly
assumes trips can also use the residential and local streets this project's network
does not include (Chapter 5), and because it assumes every vehicle counts the same
(Chapter 10), neither of which is true.

### The two-factor decomposition

Rather than load the full matrix and then apply one opaque "scale it down until it
works" multiplier, this project decomposes the scaling into two separately-justified
factors, multiplied together:

- **0.48 — the arterial-share factor.** An estimate of what fraction of citywide trips
  actually use the trunk/primary/secondary road network this project models, as
  opposed to staying entirely on local streets this project does not represent.
- **0.625 — the PCU factor** from Chapter 10, converting raw vehicle counts into
  capacity-equivalent demand.

Multiplied together, **0.48 × 0.625 = 0.30**: this project loads 30 percent of the
full citywide demand matrix. At this level, the calibrated baseline achieves roughly
17.7 kilometers per hour mean speed, a delay ratio of 0.65 (meaning the average trip
takes about 65 percent longer than it would at free-flow speed), and 99 percent of
trips complete — a workable, non-degenerate baseline that the project's interventions
can meaningfully be tested against.

### The problem this decomposition creates — and defers to Part IV

Decomposing a single scaling factor (0.30) into two separately-named pieces (0.48 and
0.625) makes the reasoning behind the number legible, but it creates a subtler
problem: **only the product of the two factors is actually constrained by anything
this project measures.** Nothing in the calibration process (Chapter 14) can tell the
two factors apart — a different split, say 0.60 × 0.50, would produce the exact same
simulated traffic, because it multiplies out to the same 0.30. This is the
project's **identifiability problem**, and because it is central enough to deserve
full treatment on its own, it is picked up in depth in Chapter 15, after the rest of
the calibration process has been explained.
