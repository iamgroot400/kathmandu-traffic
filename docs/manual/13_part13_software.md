# Part XIII — The Software Itself

## Chapter 44: Repository Tour

This project's repository is organized so that each top-level directory has one clear
job, and no file's purpose has to be guessed from its name alone:

- **`data/`** — the raw and processed inputs every simulation run reads: the committed
  OpenStreetMap extract, the cleaned network CSVs, the synthetic zones and
  origin-destination matrices, and small derived files like the recovered bridge list
  (Chapter 43).
- **`scripts/`** — every piece of executable logic: building the network, building
  demand, running the baseline, running every intervention and every statistical
  comparison, and every validation or robustness check. Chapter 45 covers every file
  here individually.
- **`results/`** — the raw, per-seed CSV output of every comparison ever run. This
  directory is deliberately **not committed to version control** (it is listed in
  `.gitignore`): every number inside it is regenerable by rerunning the relevant
  script against the committed network and demand files, so committing it would only
  duplicate information already recoverable from the code, while risking the files
  silently drifting out of sync with the scripts that produced them.
- **`paper/`** — the academic paper itself: its LaTeX source sections, its
  bibliography, the Python scripts that generate every table and chart directly from
  `results/` CSVs (never a hand-typed number), and the final, built PDF.
- **`lab/`** — the research notebook described in Chapter 4: the charter, the
  assumption register, the decision log, one card per experiment, and a dated,
  chronological notebook of what was done and why, each day.
- **`docs/`** — this manual.

### The committed, reproducible chain

A specific design discipline runs through this layout: **everything regenerable is
either regenerated or explicitly marked as not committed**, and everything that
genuinely cannot be regenerated from scratch (the raw OpenStreetMap extract, since it
depends on OpenStreetMap's live data at the moment it was fetched) **is** committed,
specifically so the project does not depend on an external service being reachable,
or unchanged, every time someone reruns the pipeline (Chapter 5 explains this choice
for the map specifically).

---

## Chapter 45: Script-by-Script Reference

This chapter is a complete, one-entry-per-script reference to everything in
`scripts/`, each with what it does and, where it is not already obvious from its
name, why it exists as a separate script rather than folded into another one.

**`build_network.py`** — imports the raw OpenStreetMap extract, applies the
node-merging and connectivity cleanup (Chapter 6), and writes the final,
simulation-ready `network_nodes.csv` and `network_links.csv`. Run once, re-run only
if the map snapshot itself needs refreshing.

**`build_od.py`** — builds the synthetic gravity-model demand matrix (Part III):
extracts junctions from the raw map, groups them into one-kilometer zones, computes
the gravity-model weights, and scales the result to a target total trip count.

**`build_od_directional.py`** and **`build_od_decentralized.py`** — produce two
specific *variant* demand matrices needed by individual interventions: a
directionally-reweighted matrix for the tidal-flow test (Chapter 20, since the base
matrix carries no morning/evening asymmetry on its own), and a core-attraction-reduced
matrix for the decentralized-attraction test (Chapter 23).

**`signals.py`** — places fixed-time signals at intersections using the angular-gap
heuristic (Chapter 7), and provides a self-check that verifies every signalised
intersection's phase plan is internally consistent before a simulation run begins.

**`adaptive_signals.py`** — implements the queue-actuated adaptive signal controller
(Chapter 18): the lost-time-adjusted, queue-comparison switching rule, attached to an
already-signalised network.

**`run_baseline.py`** — the project's central, shared entry point. It defines
`add_model_args()` (every command-line parameter every other script in this project
also accepts — demand scale, PCU factor, free-flow speed, jam density, random seed,
and more) and `build_world()` (loads the network, checks connectivity, signalises
intersections, loads demand, and returns a ready-to-run UXsim `World` object). Every
other script in this project that runs a simulation imports and calls these same two
functions, rather than re-implementing network loading independently — this is the
same "one shared, correct implementation" discipline Chapter 26 describes for the
statistics, applied here to the simulation setup itself.

**`run_due.py`** — attempts day-to-day dynamic user equilibrium (Chapter 16), the
solver this project found does not converge on this network.

**`run_pricing.py`** — measures a per-link toll schedule from a single untolled
baseline run, and applies that schedule (at the 0.2× multiplier explained in Chapter
19) to a subsequent, priced run.

**`tidal_lanes.py`** — implements the tidal-flow lane-capacity shift (Chapter 20) on
a configurable set of corridors and magnitudes.

**`compare.py`** — the project's core statistical engine: runs a set of named
configurations (fixed-time, adaptive, pricing, combined) across many seeds in
parallel, and reports the paired-seed comparison with confidence intervals. This file
also defines `ci95()`, the single, shared confidence-interval function every other
comparison script in this project imports (Chapter 26).

**`compare_extra.py`** — runs the additional interventions (parking/encroachment
proxy, staggered departures, decentralized attraction — Chapters 21 through 23)
against the baseline, using the same paired-seed pattern as `compare.py`.

**`compare_tidal.py`** — runs the tidal-flow lane intervention (Chapter 20) at both
tested magnitudes.

**`compare_future_demand.py`** — runs the five-year demand-growth projection
(Chapter 42): the calibrated baseline against a demand-scaled variant, with a
RAM-aware worker-count scheduler (explained below) added specifically after this
project observed a single worker's memory usage spike unpredictably high on
severely gridlocked seeds.

**`compare_capacity_sweep.py`** — runs the capacity-sensitivity robustness check
(Chapter 38): every main lever, at four different per-lane capacity assumptions,
with a `--capacities` flag added later specifically to let a subset of capacity
levels be extended with more seeds without re-running ones that did not need it.

**`find_bottlenecks.py`** — ranks every signalised intersection by how much total
delay it causes, attributing a link's delay to the downstream node it feeds into
(since that is the node a signal-control change could actually act on), and reports
what share of total network delay the worst intersections carry.

**`find_bridges.py`** — recovers real bridge locations from the raw OpenStreetMap
data that UXsim's own import tooling discards (Chapter 43), matching them to the
already-merged simulated network by nearest-coordinate snapping.

**`congestion_report.py`** — reports per-link density, severity classification, and
bridge-to-upstream chain-reaction timing (Chapter 43), using UXsim's own Edie's-
generalized-definitions output rather than inventing a new density measure.

**`geh_check.py`** — runs the GEH validation against the six named, observed
intersections (Part IX): builds the baseline, matches each observed landmark to its
nearest simulated node, and computes and reports the GEH statistic at each.

**`validate_hotspots.py`** — a lighter-weight, face-validity check against named
landmarks (used, for instance, when diagnosing the cordon-demand failure in Chapter
24), distinct from the full GEH statistical check.

**`sensitivity.py`** — runs the ±20% parameter sweep (Chapter 37) across demand
scale, PCU factor, and free-flow speed.

**`node_robustness_check.py`** and **`verify_bottleneck.py`** — supporting checks
used during the project's bottleneck and validation diagnosis work, verifying that a
specific node-level finding (for instance, a bottleneck's delay share, or a validation
discrepancy at a specific intersection) is not an artifact of a single run, by
checking it against additional seeds directly.

**`add_cordon.py`** — builds the external, boundary-crossing cordon demand variant
(Chapter 24), the intervention this project tested and explicitly chose not to use,
after it reduced rather than improved validation face-validity.

---

## Chapter 46: Reproducibility and Determinism

### The claim, and why it was checked rather than assumed

A simulation is only as trustworthy as its reproducibility: if running the exact same
configuration twice produces two different results, something is wrong, either with
the simulator itself or with how this project is calling it. This project did not
simply assume its baseline was deterministic given a fixed seed — it **checked this
directly**, with a dedicated script (`checks/check_reproducibility.py`) that runs the
calibrated baseline through two **independently written** comparison scripts
(`compare.py`'s `fixed_time` configuration, and `compare_extra.py`'s `baseline`
configuration) for the same set of seeds, and confirms the two produce **bit-for-bit
identical output.**

### Why this matters, specifically

This is a genuine, positive finding, not a formality: it confirms that any difference
this project ever measures between two configurations reflects the **intervention
itself**, not some hidden, unseeded source of randomness leaking into the comparison
from how the two scripts happen to call the simulator slightly differently. Without
this check, a skeptical reader would be entitled to ask whether two scripts computing
"the same" baseline independently might actually differ in some subtle way that
contaminates every comparison built on top of them — this project closed that
question directly, with a check, rather than leaving it as an assumption.

### A practical consequence: managing memory across long, background runs

This project's statistical design (Part VII) requires running many simulations per
comparison, and a single simulation run's memory footprint is not fixed — it depends
heavily on how congested that particular seed's realization turns out to be, since a
more gridlocked simulation keeps more vehicle-platoon objects alive simultaneously
over a longer horizon. This project observed this directly and concretely: a single
worker's memory usage, on this project's development machine, ranged from under a
gigabyte on lightly congested seeds to as high as **9 gigabytes** on the most severely
gridlocked ones encountered during the five-year demand-growth projection (Chapter
42) and the low-capacity levels of the robustness sweep (Chapter 38).

This led directly to two concrete engineering responses, both recorded in this
project's own history rather than treated as incidental: first, every long-running
comparison script writes its **per-seed results incrementally**, to a `.partial.csv`
file, the moment each individual run finishes — not only at the very end — specifically
so that an interrupted run (this project's background processes were killed by
session restarts on more than one occasion during development) never loses already-
completed work, and can simply be resumed, skipping whatever is already saved. Second,
`compare_future_demand.py` and `compare_capacity_sweep.py` both implement a
RAM-aware worker-count calculator: rather than hard-coding a parallelism level, these
scripts estimate how many simultaneous simulation workers will fit within a target
fraction (by default, half) of the machine's total physical memory, using an observed,
not merely assumed, per-worker memory estimate — and this project revised that
estimate upward, directly from observed data, after an initial, lower estimate proved
too optimistic on the most severely congested scenarios and risked destabilizing the
host machine.
