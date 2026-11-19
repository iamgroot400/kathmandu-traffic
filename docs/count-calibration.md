# Calibrating to the junction counts

The published model carries 64% of the counted volume at the 9 JICA 2011-12 junctions, with a
correlation of 0.31. This record covers the attempt to match the counts: GEH < 5 at all 6 tuning
junctions, with speeds still near the JICA speed survey (Ring Road 24.0, inner roads 15.3 km/h).
Decisions in full: [`lab/decisions.md`](../lab/decisions.md), D6 to D10.

## Design

- **Held-out split, drawn before any run:** `random.Random(20261118).sample(sorted(9 names), 3)`.
  Tuning: Chabahil, Gausala, Kalimati, New Baneshwor, Old Baneshwor, Thapathali. Held out: Balaju,
  Kalanki, Koteshwor. [`scripts/tune_counts.py`](../scripts/tune_counts.py) never prints them unless
  `--reveal-test`, used once on the chosen setting.
- **Each idea is a public Kaggle notebook** (`public/notebooks/6a-...` to `10b-...`), 5 seeds per
  setting next to the unchanged baseline; volumes measured in the second hour of a two-hour peak.
- **Defaults leave the published model unchanged:** every new option is off unless given.

## Rounds

| Round | Notebooks | Idea | Best (of 6) | Finding |
|---|---|---|---|---|
| 1 | 6a-6d | peak factor, valley entry roads, side-street capacity, loading points | 1 | the busy junctions' approaches are queued: they are capacity-bound, not short of demand |
| 2 | 7a-7d | lanes, saturation flow (reaction time), signal cycle, combined | 2 | capacity raises volumes but makes roads far faster than the survey (34 km/h) |
| 3 | 8a-8d | each capacity setting x higher peak demand | 2 | total volume solved, spatial pattern not: Kalimati always high, Baneshwor / Thapathali low |
| 4 | 9a-9c | 100 m junction clusters; trips loaded mid-block, not inside junctions; OD flows fitted to counts | 1 | OD fitting diverged: extra demand only lengthened queues at saturated junctions |
| 5 | 10a-10b | two-way OpenStreetMap lane fix; roadside friction | **2** | see below |

## Round 5: the lane-count bug

A network check ([`checks/junction_approaches.py`](../checks/junction_approaches.py)) compared each
tuning junction's approach links with the counts. UXsim's OpenStreetMap importer reads the `lanes`
tag as lanes per direction, but on a two-way road OpenStreetMap counts both directions. Every tagged
two-way road was modelled at double width, the Ring Road at Chabahil and Gausala among them, while the
one-way Baneshwor and Thapathali roads were right. That matches the pattern of rounds 1 to 4.

Two rules, applied city-wide and fixed before any run:

1. `--osm-way-tags data/jica_net/osm_way_tags.csv`: tagged two-way roads get ceil(lanes / 2) per
   direction (268 links). Tags fetched by [`scripts/build_way_tags.py`](../scripts/build_way_tags.py).
2. `--friction-kmh 30 --friction-share 0.10`: the 10% of main links with the most OpenStreetMap
   shops, amenities and offices within 100 m get 30 km/h free flow (86 links).

| Setting (100 m measure, 5 seeds) | Pass | Mean GEH | Share of counts | Ring / inner km/h |
|---|---|---|---|---|
| Published model | 0 | 42.3 | 0.62 | 19.4 / 13.8 |
| Lane fix, mid-block loading, peak 0.14, reaction 0.5 s | 1 | 32.5 | 0.86 | 22.5 / 13.3 |
| + roadside friction | **2** | **20.0** | **0.91** | **22.3 / 15.1** |

In the best setting, Chabahil (1.00) and Gausala (0.95) pass; Thapathali is at 0.86, Old Baneshwor
0.77, New Baneshwor 0.67, and Kalimati 1.71.

## Status

Not yet at 6 of 6; the held-out junctions have not been revealed. Camera counts by approach at
Kalimati and the Baneshwor junctions would show where the model's routing differs from reality.
If a setting is adopted, the interventions (H1-H7) must be rerun on it before the paper changes.
