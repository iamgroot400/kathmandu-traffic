# Part V — How Vehicles Choose Routes

## Chapter 16: Dynamic User Optimum vs. Dynamic User Equilibrium

### Two different notions of "everyone is routing sensibly"

When many drivers share a road network, there are two classical ways to define what
"rational routing" means in aggregate:

- **User equilibrium (UE)**, in its classical, static form due to Wardrop (1952): no
  driver can switch to a different route and reduce their own travel time, given
  everyone else's choices. At equilibrium, all used routes between a given origin and
  destination have equal (and minimal) travel time, and every unused route would take
  at least as long. This is a *settled state* — a fixed point that the whole system
  has converged to.
- **Dynamic user optimum (DUO)**, this project's actual route-choice mechanism: drivers
  periodically reroute based on the *current* travel time they observe on the network,
  without necessarily converging to a stable, mutually consistent equilibrium. It
  describes an ongoing *process*, not a destination the process necessarily reaches.

This project's simulation uses UXsim's default **`homogeneous_DUO`** behavior:
vehicles reroute onto whichever path currently looks fastest, recalculated every 600
simulated seconds. This means the simulated traffic pattern is an evolving response to
real-time congestion, which is a reasonably realistic description of how real drivers
with real-time navigation (or even just local knowledge of which roads are backed up
right now) actually behave — but it is explicitly *not* a claim that the network ever
settles into a mutually-consistent, equilibrium state where no one could benefit from
switching.

### Why day-to-day equilibrium was attempted — and why it was abandoned

A more classical modeling choice would be **day-to-day dynamic user equilibrium
(DUE)**: run the simulation repeatedly, with drivers incrementally adjusting their
*habitual* route choice (not their real-time choice) based on the previous day's
experienced travel times, until the pattern stabilizes into something close to
Wardrop's static equilibrium. This project did attempt this, using UXsim's
`SolverDUE` solver, specifically because an equilibrium result is often considered a
more defensible basis for policy comparison than a route-choice process that might
still be shifting.

It did not converge on this network. Across four solver iterations, the route-cost
gap (a measure of how far the current routing is from equilibrium — zero would mean
equilibrium has been reached) moved **611.6, then 13.5, then 510.0, then 36.5** —
oscillating rather than settling down toward zero, and total network travel time
swung by roughly a **factor of 14** between iterations. This is not a subtle numerical
precision issue; it is qualitative instability, and it was not fixed by any
straightforward solver-tuning attempt within this project's time budget.

### What this means for every result in this project

Because day-to-day equilibrium does not converge, **every result in this project
describes a within-day dynamic user optimum process, not a settled equilibrium.**
This is stated plainly in the paper rather than hidden, and it carries a genuine,
honest limitation: whether the DUE solver's oscillation reflects a *solver-tuning*
limitation specific to this implementation, or a *structurally unstable* equilibrium
on this particular network topology and demand pattern, was not determined, and this
project does not claim to know which it is. This uncertainty is recorded as part of
the project's claim ledger rather than resolved by assumption, and it is one of the
items flagged for future work (Part XIV).

It is worth being precise about what this does *not* undermine: the project's paired-
seed statistical design (Part VII) compares the *same* route-choice process (DUO)
across every intervention being tested, on matched random seeds. The absence of a
settled equilibrium affects how confidently this project can describe *what the
network's steady state would eventually look like* — it does not undermine a
same-process, same-seed comparison of how much delay a given intervention removes
relative to a fixed-time baseline, which is the actual comparison every headline
result in this project rests on.
