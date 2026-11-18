# The public pipeline, stage by stage

The paper's results come from one run of seven Kaggle notebooks over one public dataset. This page
says what each stage does, which settings it uses and what it writes. Numbers are not repeated here:
they are in [`paper/claims.md`](../paper/claims.md), generated from the outputs.

## The package

`tools/make_public.py` copies the code and data the pipeline needs into
`public/kathmandu-traffic-sim/` and zips it. That zip is the Kaggle dataset
[`kathmandu-traffic-sim`](https://www.kaggle.com/datasets/aashikkhatri/kathmandu-traffic-sim).

- **Licence:** ODbL-1.0, inherited from the OpenStreetMap network.
- **Self-check:** the script refuses to finish if the package would not compile, or if internal
  notes are left in comments.

`tools/make_notebooks.py` writes the seven notebooks to `public/notebooks/<stage>/`, each with its
`kernel-metadata.json` (public, internet on, CPU). Every notebook starts with the same setup cell:
it installs `requirements.txt`, finds the project copy, and runs each command with live output and
a retry if Kaggle kills a worker.

`tools/run_chain.sh` pushes the notebooks in dependency order and waits for each stage to
complete. A later stage reads the earlier stage's output as an input (`kernel_sources`), so
nothing is passed by hand.

## Stage 1: build demand ([notebook](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-1-build-demand))

| Script | Output |
|---|---|
| `scripts/build_minor_ways.py` | `data/jica_net/minor_ways.txt`: tertiary roads outside the main network, modelled as side streets |
| `scripts/build_od_jica.py --data data/jica_net` | `od_matrix.csv`: 9-zone vehicle OD split over 51 zones by person trips, peak factor 0.10 |
| `... --variant am` | morning-biased demand for the tidal-lane test (H4) |
| `... --variant decentralized` | core-zone attraction cut by a quarter (H7) |
| `... --variant uniform` | every trip cut to the same total as `decentralized` (H7 control) |
| `scripts/build_growth_od.py` | `od_matrix_g4yr/g2026/g2030.csv`: demand grown at 4.52%/yr, in whole platoons of 5 so no vehicles are lost |

## Stage 2: baseline and validation ([notebook](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-2-baseline-and-validation))

- `scripts/sweep_jica_seeds.py` runs the baseline on 15 seeds (`main_y0.2`, give-way priority 0.2).
  It also runs 5 seeds each at priority 0.1 and 0.4 to test that assumption.
  - Each run is scored by `checks/speed_jica2012.py`: Ring Road and inner-road speeds against the
    JICA travel-speed survey.
  - It is also scored by `checks/geh_jica2012.py`: entering volume in the second peak hour against
    the counts at 9 junctions, converted to PCU at 0.786 per vehicle.
  - Per run: `results/jica_sweep/_geh_<config>_s<seed>.csv`.
  - Summary: `results/jica_sweep_summary.csv`.
- `scripts/run_pricing.py --save-tolls` records each link's delay in an untolled run. The result,
  `results/tolls_jica.csv`, is the toll schedule for H2 and H3.

## Stage 3: interventions ([3a](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-3a-interventions-seeds-1-8), [3b](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-3b-interventions-seeds-9-15))

`scripts/compare_jica.py` runs 10 configurations on seeds 1-8 (3a) and 9-15 (3b). Each run writes
one row to `results/jica_h1h7.partial.csv`:

- `completed`: share of trips finished
- `delay_s`: mean delay of completed trips
- `tis_s`: mean time in system over all vehicles, the primary measure
- `speed_kmh`
- `trips`: vehicles generated

| Config | What changes | Compared with |
|---|---|---|
| `baseline` | fixed-time signals, no tolls | |
| `adaptive` | queue-actuated signals | baseline (H1) |
| `pricing` | toll = 0.2 x link delay from `tolls_jica.csv` | baseline (H2) |
| `adaptive_pricing` | both | baseline (H3), and both single arms (interaction) |
| `am_no_tidal` / `am_tidal` | morning demand without / with one lane shifted to the peak direction | each other (H4) |
| `parking` | free-flow speeds 70 / 35 km/h (enforcement proxy) | baseline (H5) |
| `staggered` | same demand over a 50% longer window | baseline (H6) |
| `decentralized` | core attraction cut by a quarter | baseline (H7) and `uniform_cut` (H7u) |
| `uniform_cut` | every trip cut to the same total | decentralized |

## Stage 4: demand growth ([4a](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-4a-projection-seeds-1-8), [4b](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-4b-projection-seeds-9-15))

`scripts/project_jica.py` runs the baseline and the three grown OD tables (x1.20, x1.94 for 2026,
x2.32 for 2030) on a six-hour horizon. Vehicle logging is thinned (every 60 steps) so gridlocked
runs fit in memory; trip times are unaffected. The output is `projection_seeds1-8.csv` /
`projection_seeds9-15.csv`, with the same columns as stage 3.

## Stage 5: results ([notebook](https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-5-results))

This stage reads the outputs of stages 2-4 and prints the validation summary, the paired H1-H7
tests and the projection table, so the headline numbers can be checked on Kaggle without
downloading anything.

## Statistics

`scripts/stats.py` holds the shared code:

- **`ci95`:** mean and 95% t interval.
- **Paired tests:** every comparison uses the same seed in both arms. The per-seed change is
  `(arm - base) / base x 100`.
- **Multiple comparisons:** 8 tests are made. `paper/build_pdf.py` widens each interval by the
  Bonferroni factor and checks the paper's wording against it.
- **Equal vehicles:** `--platoon-fix` (on by default) adds half a vehicle to each OD pair, so
  UXsim's platoon rounding never drops vehicles. Both arms of every comparison generate the same
  `trips`; H7 against the baseline is the exception, because it removes trips by design.

## From Kaggle to the paper

```bash
bash tools/fetch_results.sh   # stage 2-4 outputs -> results/clean/
python paper/evidence.py      # -> paper/claims.md, paper/numbers.tex, README results table
python paper/figures/make_charts.py
python paper/build_pdf.py
```
