# Part XII — Looking Forward

## Chapter 42: Projecting Five Years of Demand Growth

### The source of the growth rate

Chapter 1 already introduced the key historical figure this project relies on: the
2012 JICA/Department of Roads survey found motorcycle traffic volumes grew roughly
**19.8 times between 1991 and 2011** — an average annual growth rate close to **16
percent**, sustained for two decades. This project reuses that same, already-verified
figure (rather than deriving a new one) to ask a forward-looking question: if that
same historical growth rate continued unchanged for five more years, what would
happen to this project's calibrated network?

### Applying exponential growth, and being honest about the assumption it rests on

A quantity growing at a constant annual rate $r$ for $n$ years grows by a factor of
$(1+r)^n$. At $r = 0.16$ and $n = 5$:

```latex
(1 + 0.16)^5 \approx 2.1003
```

— meaning this projection assumes peak-hour demand in five years would be roughly
**2.1 times** today's calibrated level. This project is explicit that this rests on
two separate, named, **untested** extrapolations (logged as assumption **A12**):
first, that the historical 1991-2011 registration growth rate continues unchanged for
five more years; second, that peak-hour trips scale one-to-one with total vehicle
fleet size, which need not be true (fleet growth could, for instance, partly reflect
more vehicles per household rather than proportionally more peak-hour trips). The
projection is reported as a **directional warning**, not a precise forecast, and this
caveat travels with the result everywhere it is reported.

### Running it properly — the same paired-seed design, not a single run

Consistent with this project's standing discipline (Part VII), this projection was
not run as a single, illustrative simulation — it was run as a full, **15-seed paired
comparison** against today's calibrated baseline, exactly like every other
comparison in this project.

### The result: not slower, but gridlocked

The headline percentage is **+18.59% ± 14.42%** mean delay — a statistically
significant increase, with 12 of 15 seeds agreeing in direction. But the far more
important number sits beside it: **completion collapses from 100 percent to 36.8
percent.** The network does not simply get somewhat slower under this projected
demand — it **gridlocks outright**: a companion, link-level congestion report
(Chapter 43 explains the tool that produced it) found mean network speed falling to
near zero and **staying there for the final simulated hour**, with roughly 60,570
vehicles stuck in the network and not draining, and **97 of 590 links (16.4 percent)**
reaching this project's "jammed" classification — a figure of zero at today's
calibrated demand level.

### Why the reported percentage almost certainly understates the real effect

This project's own completion-bias discipline (Chapter 28) applies here with full
force, and this project states the consequence plainly rather than leaving it
implicit: because incomplete trips are excluded from the delay average entirely, and
this projection's completion rate collapsed to barely more than a third, the reported
+18.59% almost certainly **understates** how much worse the network's true,
"everyone eventually arrives" delay would be — the very worst, longest-delayed trips
are precisely the ones most likely to be among the 63.2 percent that never finished
at all, and are therefore excluded from the number being reported. The honest
headline from this projection is not "delay rises by about 19 percent" — it is "this
network cannot absorb five more years of unchanged historical growth without
gridlocking outright," a qualitatively different and more urgent claim than the
percentage alone would suggest.

---

## Chapter 43: Density, Bridges, and Chain-Reaction Jams

### Nothing new was added to the physics — only new reporting

It is worth being precise about what this chapter's work actually is, because it is
easy to describe it in a way that overstates what was built: UXsim's underlying
kinematic-wave model (Chapter 2) already represents vehicle **density** and
**backward-propagating queue spillback** as core physical mechanisms — when a link
saturates, the simulator already throttles inflow from its upstream neighbors
automatically, which *is* the mechanism behind a traffic jam propagating backward
through a network, exactly as the fundamental diagram's falling branch predicts. This
project's work here **surfaces that existing physics at specific, real locations**,
rather than inventing a new mechanism to produce it.

### Recovering real bridge locations from a tag the simulator discards

OpenStreetMap tags real bridges with `bridge=yes`, but UXsim's own network-import
tooling discards this tag entirely along with every other OSM attribute beyond name,
lane count, and speed limit. This project recovered bridge locations by re-parsing
the raw OpenStreetMap extract directly, rather than relying on the already-processed
network. This turned out to be harder than a first attempt assumed: matching bridge
way endpoints by their **exact original OpenStreetMap node ID** against the
already-merged network (Chapter 6's node-merging step) succeeded for only **1 of 112**
raw node-pairs, because the merge step renumbers or entirely discards most short
spans' endpoints. The working fix instead snaps each bridge's endpoint coordinates to
the *nearest surviving node* in the merged network, with a tolerance generous enough
to account for the merge step's own effect. This recovered **13 of 71** raw bridge
ways as distinct, identifiable links in the final simulated network (2 of them on the
Ring Road specifically) — the rest were either fully absorbed into a single
intersection node by the merge step (18 of them, meaning the bridge is no longer
geometrically distinct in the simulation at all) or fell outside what this project's
specific network extract actually covers (40 of them). This project reports this
incomplete recovery rate honestly, rather than implying its bridge list is
exhaustive — a real, named limitation on this specific piece of analysis.

### What the surfaced data shows

Reporting density directly (via UXsim's own Edie's-generalized-definitions output — a
standard way of computing density, flow, and speed consistently from simulated
vehicle trajectories, used elsewhere in traffic engineering, not invented for this
project) at these recovered, real locations lets this project classify every link's
severity (free-flowing, congested, or jammed, based on how its measured density
compares to its own computed jam capacity) and, separately, test for a **chain
reaction**: does a given bridge's own saturation measurably precede its upstream
approach links becoming congested in turn? At calibrated, present-day demand, this
project found real, measurable examples of exactly this sequence — a real bridge
(for instance, Manohara Pul) saturating, followed some time later by its upstream
approach links following suit — direct, location-specific confirmation of the
backward-propagating jam-wave mechanism Chapter 2 introduced in the abstract, now
observed concretely rather than only asserted theoretically.
