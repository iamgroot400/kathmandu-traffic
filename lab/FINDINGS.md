# Important findings carried into the clean run

Everything before 2026-11-15 is archived in `archive/2026-11-15_before_clean_run.zip`
(full decision log, notebooks, QA reports, all result files). This file keeps only what the
clean run must know.

## Model

- Demand from the JICA 2011 survey: the 9-large-zone vehicle OD table (840,775 PCU/day,
  count-calibrated by JICA to within ~20% at 50 points), split over the 51 person-trip zones in
  proportion to person trips, peak factor 0.10 -> 58,525 PCU/h. Zones georeferenced from the
  survey map (41 control points, median residual 0.59 km).
- Network: OpenStreetMap trunk/primary/secondary/tertiary roads in a 12 x 12.5 km box
  (472 nodes, 1,242 links). Residential streets and lanes are not modelled.
- Side streets (tertiary roads outside the main network): 1 lane, 30 km/h, outflow capacity
  0.353 of a main-road lane (JICA capacity table: 6,000 vs 17,000 PCU/day). Main roads 60 km/h.
- Junctions where one whole approach group is side streets get no signal; those streets give
  way (merge priority 0.2). Results barely move between 0.1 and 0.4.
- Two-hour steady peak, measured in the second hour (the first hour of an empty network
  undercounts badly).

## Calibration and validation

- Calibrated to the JICA travel-speed survey only; intersection counts held out.
- 16 seeds: Ring Road 20.6 km/h (survey 24.0), inner main roads 14.7 (survey 15.3).
- Against JICA 2011-12 counts at 9 junctions: 61% of counted volume, correlation +0.50,
  4 of 9 within a factor 1.5. Busiest junctions (Thapathali, Old/New Baneshwor, Kalanki) get
  40-52% of their counts.
- The earlier gravity-demand model carried a similar total (~64% on the same measure) but with
  a negative junction correlation, and gridlocked when its peak was sustained.

## Simulator pitfalls (must be handled in every run)

- **Lost vehicles:** UXsim releases each OD pair's demand in platoons of 5 and drops the last
  platoon when its float accumulator ends at 4.999.., so 2.5-7.5% of vehicles vanish, by
  different amounts in different demand files. Fix: pass volume + 0.5 (`--platoon-fix`).
  Without it, staggered departures had 5% fewer vehicles than its baseline.
- **Fractional demand multipliers** break the whole-platoon rounding: build scaled demand as
  its own rounded OD file instead (`build_growth_od.py`, `build_od_jica.py --variant`).
- **Memory:** full per-vehicle logs of 270k gridlocked vehicles exceed 30 GB. Log every 60 steps
  (`--vehicle-log-interval 60`); trip times are identical, only mean speed becomes sampled.
- Always check the `trips` column matches between compared arms before reading an effect.
- Primary measure: time in system over all vehicles (unfinished trips counted to the horizon).
  Delay over completed trips is biased whenever completion differs between arms.

## Clean public run (2026-11-17): done

The clean run reproduced every conclusion below; each effect is slightly larger because every
arm now carries all its vehicles. The current numbers live in `paper/claims.md` (generated from
the Kaggle outputs by `paper/evidence.py`), not in this file. The open questions at the end are
answered there and in `decisions.md` D4: pricing stays small (-5.9%); Ring Road is now 5 km/h
below the survey.

## Results before the clean run (archive values, superseded)

| Test | Time in system | Note |
|---|---|---|
| H1 adaptive signals | -19.9% +/- 1.9 | |
| H2 congestion pricing | -5.2% +/- 2.0 | was -32% on the main-roads-only model |
| H3 both | -26.2% +/- 1.7 | additive; interaction -1.1% +/- 3.4 |
| H4 tidal lanes | -0.1% +/- 0.5 | null |
| H5 parking enforcement | -3.0% +/- 2.5 | not significant after Bonferroni |
| H6 staggered departures | -26.7% +/- 1.3 | equal vehicles; -29.4% with 5% fewer cars |
| H7 decentralized | -8.6% +/- 2.1 | +1.3% +/- 2.8 vs equal uniform cut: no location effect |

Projection at 4.52%/yr from 2011 (JICA/DoR 2024 forecast), 6 h horizon: completion
98.1% (base), 96.9% (x1.20), 33.6% (x1.94, about today), 24.1% (x2.32, 2030). The model
gridlocks at the demand that growth rate implies for today, which the real city does not, so
peak-hour traffic grew less than 1:1 with the forecast and/or model capacity is low. Not a
forecast.

## Open questions for the clean run

- Does pricing's small effect hold, and is it the side streets' low capacity that limits it?
- Ring Road is 3-4 km/h slower than the survey.
- How much has peak-hour (not daily) traffic actually grown since 2011?
