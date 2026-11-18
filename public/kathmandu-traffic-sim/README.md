# Kathmandu peak-hour traffic simulation

A mesoscopic simulation of peak-hour traffic in Kathmandu and Lalitpur, used to test seven
interventions: adaptive signal control, congestion pricing, both together, tidal-flow lanes,
parking enforcement, staggered departure times, and decentralizing trip destinations, plus a
demand growth projection to 2030.

Simulator: [UXsim](https://github.com/toruseo/UXsim) 1.14.2 (link-based kinematic wave model).

## Data

- **Road network:** OpenStreetMap (© OpenStreetMap contributors, ODbL), trunk to tertiary
  roads in a 12 x 12.5 km box around the Ring Road: `data/jica_net/network_*.csv`
  (472 nodes, 1,242 directional links). `data/network_*.csv` is the main-road subset, used
  to tell main roads from side streets. Built with `scripts/build_network.py`.
- **Travel demand:** JICA and Department of Roads, Nepal (2012), *Data collection survey on
  traffic improvement in Kathmandu Valley*: the 2011 vehicle origin-destination table
  (`data/jica_od/vtod_2011.csv`, 9 zones x 4 vehicle types, PCU/day), the 2011 person-trip
  table (`ptod_2011.csv`, 51 zones), and zone locations georeferenced from the survey's zone
  map (`zones_2011.csv`). Extracted with `scripts/extract_jica_*.py` and
  `scripts/georef_jica_zones.py`, which need the report PDFs.
- **Observations:** the same survey's weekday travel speeds by route
  (`data/jica2012/route_speeds_2011.csv`, used for calibration) and peak-hour entering
  counts at nine intersections (`intersection_counts_2011.csv`, used only for validation).

## Pipeline (one Kaggle notebook per step)

1. **Build demand:** side-street list, peak-hour OD matrix (58,525 PCU/h) and its variants
   (morning-biased, decentralized, uniform cut) and growth scenarios.
2. **Baseline and validation:** 15 seeds; speeds against the speed survey, volumes against the
   intersection counts; toll schedule for the pricing test.
3. **Interventions:** 10 configurations x 15 paired seeds (H1 to H7).
4. **Projection:** demand grown from 2011 at 4.52%/yr (JICA/DoR 2024 forecast) to 2026 and 2030.
5. **Results:** tables and figures from steps 2 to 4.

Model settings: main roads 60 km/h; side streets one lane, 30 km/h, outflow capacity 0.353 of
a main-road lane (JICA capacity table), giving way at junctions where they meet main roads;
other junctions fixed-time signals, 90 s cycle; two-hour steady peak; dynamic user-optimal
routing, rerouting every 600 s.

## Measures

The primary measure is mean time in system over all vehicles, counting trips that have not
finished by the horizon up to the horizon, so a scenario cannot look better by leaving slow
trips unfinished. Delay over completed trips and completion share are reported alongside.
Every comparison is paired by random seed and reported with a 95% confidence interval.

UXsim releases each origin-destination pair's demand in platoons of five vehicles; its
floating-point accumulation can drop a pair's last platoon, by different amounts in different
scenarios. `run_baseline.py` adds 0.5 to each pair's volume (`--platoon-fix`, on by default) so
every scenario generates exactly the demand requested; each result row records the vehicles
generated (`trips`) so this can be checked.

## Running locally

```
pip install -r requirements.txt
python scripts/build_minor_ways.py
python scripts/build_od_jica.py --data data/jica_net
python scripts/sweep_jica_seeds.py --jobs 1
python scripts/compare_jica.py --seeds 15 --jobs 1
```
One run needs about 4 GB of memory; heavy projection runs need more.
