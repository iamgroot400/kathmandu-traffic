# Glossary

This glossary exists so that no term used anywhere in this manual is ever left
unexplained. If a word appears in the body of this manual and you are not sure what
it means, it should be defined here.

**Adaptive signal control** — A traffic-signal control strategy that changes its
phase-switching behavior in response to real-time conditions (in this project,
queue length), rather than running a fixed, predetermined cycle. See Chapter 18.
Distinct from a *learned* policy (see Reinforcement learning, below) — this
project's adaptive controller is a hand-specified heuristic rule, not something
trained from data.

**Calibration** — The process of adjusting a model's free parameters so that its
output matches one or more real, observed quantities. See Chapter 14. Distinct from
*validation* (checking the model against data it was not tuned to match).

**Capacity (of a road link)** — The maximum flow (vehicles per hour) a link can
sustain, corresponding to the peak of the fundamental diagram (see below). See
Chapter 2 and Chapter 13.

**Completion bias** — The statistical trap where an intervention's apparent
improvement is actually caused by incomplete trips being excluded from the average,
rather than a genuine reduction in delay. The single most recurring methodological
hazard in this project. See Chapter 28.

**Confidence interval (95%)** — A range, computed from sample data, that is expected
to contain the true value of a quantity 95% of the time the same sampling procedure
is repeated. This project reports every comparison as a 95% confidence interval
rather than a single point estimate. See Chapter 26.

**Cordon demand** — Demand representing trips that cross the boundary of the modeled
network (entering or leaving from outside the simulated area). This project tested
and ultimately rejected adding this kind of demand. See Chapter 24.

**`deltan` (platoon size)** — UXsim's unit of simulation granularity: the number of
real vehicles one simulated "platoon" object represents. This project uses
`deltan=5` throughout. See Chapter 3.

**Demand matrix / origin-destination (OD) matrix** — A table recording how many
trips occur between every pair of zones during the period being modeled. See
Chapter 8.

**DUO (Dynamic User Optimum)** — A route-choice process where drivers periodically
reroute based on currently observed travel times, without necessarily reaching a
stable, mutually consistent equilibrium. This project's actual route-choice
mechanism. See Chapter 16.

**DUE (Dynamic User Equilibrium)** — A route-choice process, evaluated day-to-day,
that is said to have converged once no driver could improve their own travel time
by unilaterally switching habitual route. This project attempted to compute this
and found it does not converge on its network. See Chapter 16.

**Fundamental diagram** — The relationship between traffic density, flow, and speed
on a road segment. The single foundational object of traffic flow theory. See
Chapter 2.

**GEH statistic** — A standard transportation-engineering measure of how well a
modeled traffic volume matches an observed one, defined as
$\sqrt{(M-C)^2/((M+C)/2)}$. GEH < 5 is the conventional pass threshold. See
Chapter 33.

**Gravity model** — A method for synthesizing a demand matrix by assuming trip
volume between two zones is proportional to each zone's "mass" (activity) and falls
off with distance between them. See Chapter 8.

**Identifiability (statistical)** — A parameter is identifiable from a given
calibration target if no other value of that parameter could have produced the same
observed output. This project's demand-scale and PCU factors are *not* separately
identifiable from its single calibration target. See Chapter 15.

**Jam density** — The vehicle density at which traffic has come to a complete
standstill (zero speed), corresponding to the bottom of the fundamental diagram's
falling branch. See Chapter 2 and Chapter 13.

**Kinematic wave model** — A traffic-flow theory (Lighthill-Whitham-Richards, 1955-
1956) treating traffic as a continuous fluid obeying a conservation law, from which
phenomena like backward-propagating jam waves emerge as direct physical
predictions. The theoretical basis of UXsim, this project's simulator. See Chapter 2.

**Macroscopic / mesoscopic / microscopic (simulation)** — The three broad families
of traffic simulation tools, distinguished by how individually they represent
vehicles: not at all (macroscopic, pure fluid), as platoons moving through
kinematic-wave physics (mesoscopic, this project's choice), or individually with
full car-following and lane-changing behavior (microscopic). See Chapter 2 and
Chapter 3.

**Marginal-cost pricing** — A congestion-pricing theory that charges a driver for
the delay their trip imposes on other road users, rather than for using the road
itself. The theoretical basis of this project's congestion-pricing intervention. See
Chapter 19.

**Mean network speed** — The average speed of all vehicles across the simulated
network, this project's single calibration target. See Chapter 14.

**Multiple comparisons (problem)** — The statistical concern that running many
separate significance tests increases the chance that at least one will appear
"significant" purely by chance, even if every underlying effect is actually zero.
See Chapter 27.

**Newell's simplified car-following model** — A car-following theory shown to be
mathematically equivalent to the kinematic wave model with a triangular fundamental
diagram. Explains why a mesoscopic, platoon-based simulator can be considered a
legitimate, if coarser, stand-in for individual-vehicle car-following behavior. See
Chapter 2.

**PCU (Passenger Car Equivalent)** — A standard traffic-engineering unit converting
different vehicle types (motorcycles, cars, buses) into an equivalent road-capacity
impact, relative to one standard passenger car (PCU = 1.0). See Chapter 10.

**Paired-seed comparison** — This project's core statistical method: running two
configurations on the identical set of random seeds, and comparing the
per-seed differences, rather than comparing the two configurations' unpaired
overall averages. See Chapter 26.

**Reinforcement learning** — A machine-learning approach where a controller's
behavior is learned from (simulated or real) experience, rather than specified by a
fixed rule. This project's adaptive signal controller (Chapter 18) is explicitly
*not* this — it is a hand-specified heuristic.

**Strongly connected component** — In a directed network, the largest set of nodes
where every node can reach every other node by a directed path. This project
checks this before trusting any simulation result. See Chapter 6.

**Super-additive (interaction)** — A combined effect that exceeds the sum of two
individual effects measured separately, implying the two interventions
"synergize." This project originally believed, then corrected, that its combined
lever showed this property. See Part VIII.

**Triangular fundamental diagram** — A specific, piecewise-linear shape for the
fundamental diagram: flow rises linearly with density to a peak (capacity), then
falls linearly to zero at jam density, with the two slopes representing free-flow
speed and backward jam-wave speed respectively. The shape UXsim's kinematic-wave
model builds on. See Chapter 2.

**UXsim** — The open-source, pure-Python mesoscopic traffic simulator this project
uses. See Chapter 3.

**Validation** — Checking a model's output against real-world data it was not
tuned (calibrated) to match, to test whether the model is correct in a way
calibration alone cannot confirm. See Part IX.
