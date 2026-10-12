# Kathmandu Traffic

Road geometry for Kathmandu, as a starting point for traffic simulation work.

This repository deliberately contains **only the map**. No model, no simulation code,
no results — those come next, built with a fresh approach.

## The map

`data/kathmandu.osm.xml` — OpenStreetMap road geometry covering the Ring Road and the
city core.

| | |
|---|---|
| Bounding box | `85.268, 27.635, 85.392, 27.750` (lon/lat, W S E N) |
| Road classes | `trunk`, `primary`, `secondary`, plus their `*_link` connectors |
| Source | Overpass API |
| OSM snapshot | 2026-09-20T14:36:36Z |
| Size | ~1.4 MB |

Link roads are kept so interchanges stay routable. **Nepal drives on the left** — any
network built from this must be converted with left-hand traffic enabled, or every
junction will be mirrored.

### Re-fetching it

The map is committed, so this is only needed to refresh the snapshot. Overpass query:

```
[out:xml][timeout:180];
(
  way["highway"~"^(trunk|primary|secondary)(_link)?$"](27.635,85.268,27.750,85.392);
);
(._;>;);
out body;
```

POST that as the `data` field to `https://overpass-api.de/api/interpreter`.
Note Overpass takes bounds as `south,west,north,east` — the reverse order of the
bbox above.

## Attribution

Map data © OpenStreetMap contributors, available under the
[Open Database License (ODbL)](https://opendatacommons.org/licenses/odbl/).
Any derived network or published result must carry this attribution.

## Scope note

This is geometry only. It contains no traffic counts, no demand matrix and no
activity zones. Those have to be surveyed — a simulation run on invented demand
describes the model, not the city.
