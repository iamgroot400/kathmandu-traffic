# Part IV — Calibration

## Chapter 12: The Free-Flow Speed Override

### The gap between a speed limit and a real speed

OpenStreetMap tags most of Kathmandu's arterial roads with a legal speed limit around
50 kilometers per hour. No arterial road in Kathmandu actually sustains anything close
to that in practice, even at low traffic volumes, because of factors a speed-limit tag
cannot capture: roadside parking narrowing the effective carriageway, informal stops
and encroachment onto the road surface by roadside activity, and generally
inconsistent lane discipline. This project overrides every link's free-flow speed to
**30 kilometers per hour**, network-wide, rather than trusting OSM's tagged legal
limit.

### Why a single override number, and not per-link behavior modeling

As explained in Chapter 3, UXsim is mesoscopic: it has no genuine car-following model,
no individual driver reaction time, and no lane-level behavior simulation. This means
none of the real causes of Kathmandu's slow arterial speeds — parking, encroachment,
indiscipline — can be represented as *behavior* inside this model, because the model
has no concept of an individual car swerving around a parked vehicle or an individual
driver hesitating. The only lever available is **a link-level parameter**: free-flow
speed, the speed a link's traffic would move at in the complete absence of
congestion. Lowering this parameter reproduces the *outcome* of all those real-world
frictions combined — slower arterial traffic — without being able to say anything
about which specific friction is responsible, or distinguish "parking is the problem
here" from "this intersection's geometry is just bad."

This tradeoff is recorded formally as **Decision D1**, including its explicit
dissent: the model reproduces the outcome of poor driving conditions, but cannot test
whether driver behavior specifically is the *cause*, and any claim this project makes
about *why* speeds are low — as opposed to *that* they are low — would be
unsupported by this modeling choice. The alternative considered and rejected was
building a microscopic model instead, which Chapter 3 already explains was ruled out
on grounds of computational cost and scope.

---

## Chapter 13: Jam Density — What It Means and Why 0.2

### What jam density represents physically

Recall from Chapter 2 that the triangular fundamental diagram's falling branch ends at
**jam density** — the density at which vehicles are packed bumper-to-bumper and speed
has dropped to zero. This project's default, `jam_density_per_lane = 0.2` (vehicles
per meter per lane), corresponds to roughly **5 meters of road length per vehicle at a
complete standstill** — a car's length plus a modest following gap, a standard,
textbook traffic-engineering default rather than a number derived from any
Kathmandu-specific survey. This is logged explicitly in this project's assumption
register as **A10**, status untested, flagged as influencing specifically the timing
and shape of how congestion onset is modeled (how quickly a link transitions from
flowing to jammed as demand rises).

### How it scales with lane count

A link's actual jam capacity (`kappa` in the code, following UXsim's own internal
naming) is this per-lane jam density multiplied by the link's number of lanes, so a
four-lane road has four times the standstill vehicle capacity of a single-lane road at
the same per-lane density setting — this scaling is handled by UXsim itself
(`jam_density_per_lane` times `number_of_lanes`), and it is important to note, because
this project discovered partway through its later robustness work (Part X) that a
*different*, flatter attribute UXsim also exposes (`jam_density`, without the
per-lane qualifier) does **not** scale with lane count — it stays fixed at whatever
flat default was passed in, regardless of how many lanes a link has. Using the wrong
one of these two attributes when trying to characterize a link's real jam capacity
would silently produce a lane-count-blind, misleading number. This project's
discussion of the model's own calibrated capacity (Part XI, Chapter 39) is careful to
compute the correct, lane-scaled value rather than read the flat one.

### An empirically measured consequence: the model's implied per-lane capacity

Jam density, combined with free-flow speed (Chapter 12) and the simulator's internal
reaction-time parameter, together determine a link's **maximum sustainable flow** —
its capacity, in the fundamental-diagram sense from Chapter 2. This project measured
that implied capacity directly, empirically, rather than relying on a formula: a
single-link flood test (load far more demand than the link can carry, and measure the
steady-state discharge rate once a queue has formed) found this project's calibrated
settings imply roughly **2,400 vehicles per hour per lane**. This number matters later
in two separate places in this manual: it is compared directly against Tiwari et al.'s
(2024) real, field-measured saturation flow rates at two actual Kathmandu
intersections (Part XI, Chapter 39, where this project's assumption turns out to run
somewhat *above* the real measured range), and it anchors the specific capacity values
tested in this project's robustness sweep (Part X, Chapter 38).

---

## Chapter 14: Calibrating Against Reality

### The single calibration target

This project's baseline was tuned against exactly one real-world number: Kathmandu's
observed **mean network speed** during peak hour. The demand-scaling decomposition
(Chapter 11) and the free-flow speed override (Chapter 12) were adjusted until the
simulated baseline's mean speed matched this target, landing on the roughly 17.7
kilometers per hour baseline described earlier.

### Why one target is not enough — a preview of Chapter 15

Calibrating against a single aggregate number (mean speed across the whole network)
constrains the model's overall level of congestion, but it says nothing about *where*
that congestion is distributed. Two very different demand patterns — one that
concentrates heavily around one corridor, another that spreads evenly across the whole
network — could, in principle, produce the exact same mean speed, while making very
different, specific predictions about which named intersection is most congested.
This is precisely what this project's validation work (Part IX) later checked
directly, with real consequences: the model matches the city on average, but checked
against six real, named intersections, it passes at only two of them. Chapter 15 takes
up the mathematical version of this same problem — not just "one target doesn't pin
down location," but "one target doesn't even pin down the *individual parameter
values* that produced it."

---

## Chapter 15: The Identifiability Problem

### What "identifiability" means

A model parameter is **identifiable** from a given calibration target if, in
principle, no other value of that parameter (holding everything else fixed) could have
produced the same observed output. If two different parameter values produce
indistinguishable output, the calibration target cannot tell them apart — the
parameter is **unidentified** by that target, no matter how precisely the target
itself was measured.

### Why this project's two demand-scaling factors are not separately identifiable

Recall from Chapter 11 that this project's effective demand load is the product of two
named factors: the 0.48 arterial-share factor and the 0.625 PCU factor. Both enter the
simulation multiplicatively — as `demand_scale × pcu_factor` — and the single
calibration target (Chapter 14) is mean network speed, which depends only on that
product, not on the two factors individually. This means the calibration process
cannot, even in principle, tell the difference between, say, a 0.48 arterial-share
factor paired with a 0.625 PCU factor, and a 0.60 arterial-share factor paired with a
0.50 PCU factor — both multiply out to the same 0.30 effective load, and would produce
bit-for-bit identical simulated traffic.

### Proving it empirically, not just arguing it

A weaker research process might simply assert this and move on. This project instead
**tested it directly**: a sensitivity sweep (Part X, Chapter 37) reduced each of the
two factors by 20 percent independently and compared the resulting simulation output.
The result: reducing either factor by 20 percent produced output that was **identical
to many decimal places** — not merely similar, but numerically indistinguishable,
exactly as the identifiability argument predicts. This is reported in this project's
paper as confirmed **empirically**, not argued from theory alone, precisely because an
argument can contain a hidden error that an actual numerical test cannot.

### Why this matters beyond demand scaling

The same free-flow-speed-override and jam-density defaults discussed in Chapters 12
and 13 share a version of this same problem in spirit, if not in the exact
multiplicative form: this project's baseline matches the one aggregate number it was
tuned against, but that does not mean every individual parameter inside it has been
independently verified against reality. This is precisely why this project's
validation work (Part IX) exists as a separate, independent check, rather than being
treated as redundant with calibration — calibration can only ever confirm that a
model's *output* matches a target; it cannot confirm that the model's internal
parameters are individually correct, and conflating the two is a common and serious
modeling error this project goes out of its way to avoid repeating.
