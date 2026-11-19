# Kathmandu peak-hour traffic simulation

Which interventions reduce peak-hour congestion in Kathmandu without building roads, and by how
much? This repository simulates the city's arterial and tertiary road network under demand from
the JICA 2011 travel survey. It tests seven interventions on 15 paired random seeds, validates the
model against independent traffic counts, and projects demand growth to 2030.

**Every simulated number comes from one public run on Kaggle.** Anyone can open its code, logs and
outputs, or rerun it:

| Stage | Kaggle notebook | What it produces |
|---|---|---|
| Inputs | [dataset `kathmandu-traffic-sim`](https://www.kaggle.com/datasets/aashikkhatri/kathmandu-traffic-sim) | code, OpenStreetMap network, JICA survey tables |
| 1 | [1-build-demand](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-1-build-demand) | peak-hour origin-destination tables, scenario variants, growth tables |
| 2 | [2-baseline-and-validation](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-2-baseline-and-validation) | 25 baseline runs: speeds vs the speed survey, volumes vs the junction counts, toll schedule |
| 3 | [3a-interventions-seeds-1-8](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-3a-interventions-seeds-1-8), [3b-interventions-seeds-9-15](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-3b-interventions-seeds-9-15) | 10 configurations x 15 seeds = 150 runs (H1-H7) |
| 4 | [4a-projection-seeds-1-8](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-4a-projection-seeds-1-8), [4b-projection-seeds-9-15](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-4b-projection-seeds-9-15) | 4 demand levels x 15 seeds = 60 runs |
| 5 | [5-results](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-5-results) | every summary table, read from stages 2-4 |

## Results

Generated from the Kaggle outputs by `paper/evidence.py`; [`paper/claims.md`](paper/claims.md)
traces each number to its notebook, file and computation.

<!-- results:start -->
| Test | Change in time in system (15 paired seeds, 95% CI) | Verdict (Bonferroni x8) |
|---|---|---|
| H1 adaptive signals vs baseline | -23.2% +/- 2.0% | reduces |
| H2 congestion pricing vs baseline | -5.9% +/- 1.9% | reduces |
| H3 adaptive signals + pricing vs baseline | -28.9% +/- 1.7% | reduces |
| H4 tidal lanes vs same AM demand without | -0.2% +/- 0.4% | no reliable effect |
| H5 parking enforcement proxy vs baseline | -1.3% +/- 1.9% | no reliable effect |
| H6 staggered departures vs baseline | -26.7% +/- 1.3% | reduces |
| H7 decentralized attraction vs baseline | -9.1% +/- 1.3% | reduces |
| H7u decentralized vs volume-matched uniform cut | +0.3% +/- 1.7% | no reliable effect |

- H3 interaction (combined minus both single effects): +0.2% +/- 3.1%, so the two levers add up rather than reinforce each other.
- Validation: Ring Road 18.9 +/- 1.2 km/h (survey 24.0), inner roads 13.8 +/- 0.3 km/h (survey 15.3); 64% of counted volume at 9 junctions, correlation 0.31 +/- 0.09.
- Demand growth: trips completed in 6 h fall from 98.1% at 2011 demand to 33.6% at 2026 demand and 24.1% at 2030 demand.
<!-- results:end -->

## Part of a three-repository project

| Repository | Contents |
|---|---|
| `kathmandu-traffic-docs` | project overview, data sources, technology, roadmap |
| **`kathmandu-traffic`** (this one) | the simulation |
| `kathmandu-traffic-vision` | junction cameras: counting, red-light violations, number plates |

Calibration against the junction counts (rounds 1-5, ongoing): [`docs/count-calibration.md`](docs/count-calibration.md).

## How a number gets from Kaggle into the paper

```
Kaggle notebooks 2-4  ->  tools/fetch_results.sh  ->  results/clean/*.csv
results/clean/  ->  paper/evidence.py  ->  paper/claims.md   (ledger: number, notebook, file, computation)
                                       ->  paper/numbers.tex (LaTeX macros used by paper/sections/*.tex)
                                       ->  README.md results table (above)
results/clean/  ->  paper/figures/make_charts.py  ->  fig_jica_validation.png, fig_jica_levers.png
results/clean/  ->  paper/build_pdf.py  ->  paper/kathmandu_traffic_paper.pdf
```

No number is typed by hand. The paper build also checks its own wording against the data: it
stops if a result called significant is not, if an interaction called additive is not, or if the
two arms of a comparison generated different numbers of vehicles.

To rebuild everything from the public run:

```bash
bash tools/fetch_results.sh
python paper/evidence.py
python paper/figures/make_charts.py
python paper/build_pdf.py
```

To rerun the simulations themselves on Kaggle (several hours; stages 3 and 4 run in parallel):

```bash
python tools/make_public.py      # package code + data -> public/kathmandu-traffic-sim/
python tools/make_notebooks.py   # write the 7 notebooks -> public/notebooks/
bash tools/run_chain.sh          # push them in order, waiting for each stage
```

[`docs/pipeline.md`](docs/pipeline.md) explains each stage, its settings and its outputs.

## The model in brief

- **Simulator:** [UXsim](https://github.com/toruseo/UXsim) 1.14.2, a mesoscopic link-based
  kinematic wave model. Drivers reroute to current travel times every 600 s.
- **Network:** OpenStreetMap trunk, primary, secondary and tertiary roads in a 12 x 12.5 km box
  around the Ring Road: 472 nodes, 1,242 directional links. Residential streets and lanes are
  not modelled.
  - Main roads: 60 km/h.
  - Side streets: one lane, 30 km/h, 0.353 of a main-road lane's capacity (JICA tables). They
    give way where they meet main roads.
  - Every other junction: fixed-time signals on a 90 s cycle.
- **Demand:** the JICA 2011 vehicle origin-destination survey.
  - 840,775 PCU per day, split over 51 zones by person trips.
  - Peak factor 0.10 gives 58,525 PCU per hour, held for two hours (117,050 vehicles) within a
    four-hour horizon.
- **Calibration:** road speeds against the JICA travel-speed survey only. The junction counts are
  kept for validation.
- **Measure:** mean time in system over all vehicles, counting unfinished trips up to the horizon,
  so an intervention cannot look better by leaving slow trips unfinished.
  - Paired by seed, with 95% intervals.
  - Bonferroni correction over the 8 tests.

## Repository map

| Path | Contents |
|---|---|
| `scripts/` | the model: network, demand, signals, pricing, interventions, run drivers (`compare_jica.py`, `project_jica.py`, `sweep_jica_seeds.py`) |
| `checks/` | validation against the JICA counts (`geh_jica2012.py`) and speeds (`speed_jica2012.py`) |
| `data/` | network (`jica_net/`), JICA survey tables (`jica_od/`, `jica2012/`), source report PDFs |
| `tools/` | public packaging, Kaggle notebooks, run chain, result download |
| `public/` | the exact package and notebooks published on Kaggle |
| `results/clean/` | downloaded Kaggle outputs (git-ignored; recreate with `tools/fetch_results.sh`) |
| `paper/` | the paper (PDF and LaTeX), its evidence ledger and figures; see [`paper/README.md`](paper/README.md) |
| `lab/` | research log: [`FINDINGS.md`](lab/FINDINGS.md), [`decisions.md`](lab/decisions.md), [`assumptions.md`](lab/assumptions.md) |
| `archive/` | everything before the clean public run (earlier lab notebook, results, drafts) |
| `docs/first_version.md`, `docs/manual/` | the study's first version (synthetic demand, main roads only), kept for comparison |

## Attribution

Road network © OpenStreetMap contributors (ODbL). Demand, speeds and counts: Japan International
Cooperation Agency and Department of Roads, Nepal (2012), *Data Collection Survey on Traffic
Improvement in Kathmandu Valley*.
