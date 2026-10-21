# Part II — Building the Network

## Chapter 5: Getting Real Roads from OpenStreetMap

### Why OpenStreetMap and not a proprietary GIS dataset

Nepal's government does not publish a machine-readable, routable road network dataset
for Kathmandu Valley that is freely available to a research project. OpenStreetMap
(OSM), by contrast, is a crowd-sourced but surprisingly complete and actively
maintained map of the city, free to download, and directly importable into a traffic
simulator via existing tooling (`osmnx`, which UXsim's `OSMImporter` uses internally).
This project uses the OSM snapshot committed at `data/kathmandu.osm.xml`, fetched
2026-09-20, covering a bounding box of `85.268, 27.635, 85.392, 27.750` (west, south,
east, north in degrees).

### Choosing which roads to include

OpenStreetMap tags every road with a `highway` class (`trunk`, `primary`, `secondary`,
`tertiary`, `residential`, and so on, following a rough hierarchy of importance). This
project's import filter keeps only `trunk`, `primary`, and `secondary` roads (plus
their `_link` connector variants, which represent ramps and short connecting segments
at interchanges — keeping these is what stops an interchange from becoming
unroutable). This is a deliberate scope decision, not an oversight: residential streets
and alleys are where most of Kathmandu's local, short trips happen, but they are not
where through-traffic congestion concentrates, and including them would have exploded
the network's node count (and this project's simulation time) without changing the
answer to the two questions this project actually asks (signal retiming and pricing on
the arterial network). The explicit cost of this choice: any trip that genuinely starts
or ends on a residential street is not represented at all, which is one reason this
project's demand had to be scaled down rather than loaded at its full citywide value
(Chapter 11).

### The left-hand traffic trap

Nepal drives on the left. This sounds like a detail, but it is a correctness-critical
one: if a network is built and its route-choice or signal logic assumes right-hand
traffic (the default assumption baked into many simulation tools and examples,
including UXsim's own documentation, since it was written with Japan's — also
left-hand, as it happens — or more commonly right-hand-traffic countries in mind), an
entire network's junctions will effectively be mirrored, and every turn movement will
be modeled backward. This project's own README flags this explicitly as a standing
warning for anyone rebuilding the network from scratch: left-hand traffic must be
enabled, or every junction comes out wrong.

### Re-fetching the map

The map is committed directly to the repository specifically so that this project does
not depend on OpenStreetMap's live servers being reachable, or on the map not having
changed, every time someone reruns the pipeline. The query used to fetch it (callable
again only if the snapshot needs refreshing) goes through the Overpass API, which is
OpenStreetMap's query service for extracting a bounded region's raw data rather than
downloading the entire planet file.

---

## Chapter 6: Cleaning the Network — Node Merging and Connectivity

### Why raw OSM data is not simulation-ready

A raw OpenStreetMap extract is drawn for human cartography, not for traffic
simulation. The same physical road is frequently split into many short "way" segments
every time a tag changes (for instance, where a speed limit sign or a name change
occurs), and two roads that meet at a real intersection may be represented by two
nodes a few meters apart rather than one shared node, if the original map data was
surveyed imprecisely. If this is fed directly into a traffic simulator, the result is
an unrealistically fragmented network: a single real junction might appear as three or
four separate, tiny links with free-merge behavior between them, and route-choice
noise is introduced purely by geometric artifacts that have nothing to do with real
traffic.

### The node-merge threshold

This project's network-cleaning step (`osm_network_postprocessing`, part of UXsim's
own import tooling, invoked from `scripts/build_network.py`) merges any two nodes
connected by a link shorter than a threshold distance, repeating this for five
iterations so that chains of several short segments collapse down to one real node.
The threshold chosen is **0.0005 degrees, roughly 55 meters** — deliberately much
tighter than UXsim's own example scripts use (which default to roughly 0.005 degrees,
about 550 meters). The reasoning, recorded in this project's own documentation: a
550-meter merge threshold is coarse enough to erase real topology — two genuinely
distinct intersections a few hundred meters apart on the same arterial could be
collapsed into one node, destroying exactly the kind of mid-corridor detail (where is
delay actually concentrated?) that this project's bottleneck analysis (Part VI, and
Chapter 45's `find_bottlenecks.py`) depends on. 55 meters merges genuinely coincident
survey points without collapsing real, physically distinct junctions.

This choice has a real, documented cost, discovered later and reported honestly rather
than hidden: when this project tried to recover which of its simulated links are
physical bridges (Chapter 43), the 55-meter threshold turned out to be large enough,
applied over five iterations, to absorb about half of the area's short river-bridge
spans entirely into a single intersection node — the bridge still exists physically,
but it is no longer a distinct, separately measurable link in the simulated network.
This is exactly the kind of tradeoff a stricter research process catches and documents
rather than glossing over: a threshold tuned correctly for one purpose (realistic
intersection topology) has a side effect for a different purpose (bridge-level
analysis) that had to be discovered empirically and reported as a limitation, not
assumed away.

### Checking connectivity before trusting any result

A fragmented network — one where part of the city cannot actually reach another part
by any sequence of links — fails *silently* in a traffic simulator: trips between the
disconnected parts are simply never completed, and the simulation still "runs" and
reports statistics, but those statistics describe only the subset of demand that could
physically reach its destination. This is dangerous specifically because nothing in
the output looks obviously wrong; the completion percentage is just lower than it
should be, for a structural reason rather than a congestion reason.

This project's `scripts/run_baseline.py` therefore computes the network's **largest
strongly connected component** (the largest set of nodes where every node can reach
every other node by a directed path) before running any simulation, and refuses to
proceed if that component covers less than half of all nodes. At the project's actual,
final network — 233 nodes, 590 directional links — the largest strongly connected
component covers 100 percent of nodes, with zero dead ends: every point in the network
can reach every other point. This check exists specifically so that a future rebuild
of the network (say, after refetching a newer OSM snapshot) cannot silently introduce
a fragmentation bug that would bias every downstream result without anyone noticing.

---

## Chapter 7: Placing Traffic Signals

### Why OSM's own signal tags were not used

OpenStreetMap does tag some real intersections with `highway=traffic_signals`, but
this project's own OSM import (covering only trunk/primary/secondary roads, Chapter 5)
produces a network where every imported node defaults to an **unsignalised free
merge** — UXsim's own import tooling does not read or apply OSM's traffic-signal tags
automatically, and Kathmandu's actual, as-tagged signal coverage in OSM is incomplete
and inconsistently maintained relative to ground truth (many of the project's own
source documents note that installed signals are frequently operated manually by
traffic police rather than run on a fixed cycle at all, which is itself a separate,
real feature of Kathmandu traffic that a simulated "signal" cannot capture). This
project therefore needed its own rule for *which* intersections should be signalised
in the simulation, rather than trusting the map's own tags.

### The angular-gap heuristic

The rule this project settled on, after testing two alternatives and rejecting both
(documented as Decision D5): an intersection is signalised if it has **three or more
approach roads**, and the widest angular gap between any two consecutive approaches is
**at least 30 degrees**. Intuitively, this selects intersections that are genuine,
multi-directional crossings — not just a gentle bend in a single road, or a simple
two-way merge where one road feeds into another at a shallow angle, both of which do
not need signal control and are left as free merges.

### Why not stricter, and why not looser

Two alternative thresholds were tried and rejected, each for an empirically measured
reason, not a guess:

- **A stricter rule** (three or more approaches within a narrower, 45-degree spread)
  skipped one specific three-into-one merge that, when checked against the resulting
  simulation, turned out to carry **15.7 percent of all network delay** on its own.
  Leaving a junction that significant as an unsignalised free merge would have badly
  understated how much control over total network delay signal timing actually has.
- **A looser rule** (two or more approaches, with no angular restriction) produced 165
  signalised intersections rather than 128, and when simulated, this over-constrained
  network: only 78 percent of trips completed, at a mean speed of 11.5 kilometers per
  hour. The total delay number from that configuration looked *lower* than the
  eventually-chosen rule's — but only because 22 percent of trips never finished and
  were excluded from the average entirely. This is the project's first encounter with
  **completion bias** (Part VII, Chapter 28 covers this pattern in full depth): a
  result that looks better can simply be hiding its worst trips rather than actually
  performing better, and the only way to catch this is to check completion rate
  alongside delay, every time.

The rule this project settled on — three-plus approaches, 30-degree minimum spread —
signalises 128 of the network's 233 intersections, leaving 105 as free merges (bends,
simple two-way merges, and diverges that genuinely do not need signal control).

### The baseline cycle

Every signalised intersection in this project's fixed-time baseline runs a 90-second,
two-phase cycle. This is a deliberately simple, uniform choice, not meant to represent
Kathmandu's actual, heterogeneous (and frequently hand-operated) signal timings
precisely — it exists to give every intervention tested later in this manual (adaptive
control, Chapter 18; pricing, Chapter 19) a single, well-defined, reproducible
reference point to be compared against. Precisely because it is uniform and simple,
any improvement measured relative to it is attributable to the *intervention*, not to
an accidental advantage buried in an arbitrarily chosen, intersection-specific baseline
timing plan.
