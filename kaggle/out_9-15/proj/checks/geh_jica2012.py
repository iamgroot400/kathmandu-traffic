#!/usr/bin/env python3
"""GEH against the primary JICA 2012 intersection counts (data/jica2012/
intersection_counts_2011.csv, transcribed from the scanned turning-movement
diagrams in Appendix 1.2.3), using a saved baseline link-volume dump. No simulation.

Observed = mean of the AM and PM peak-hour entering volume (veh/h), converted to the
model's PCU-weighted units with the project's own 0.625 factor (A2), the same
convention geh_check.py uses. Model = entering volume at the matched node in the
first simulated hour.

Node choice (fixed before looking at volumes): the four junctions found by road
name, else the coordinates already used in geh_check.py / validate_hotspots.py.
Balaju uses the Ring Road x Lekhnath Sadak node; the bypass node 1 km north is
printed as a sensitivity only.

    python checks/geh_jica2012.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from geh_check import OBSERVED as OLD, PCU_FACTOR, geh  # noqa: E402
from validate_hotspots import LANDMARKS, haversine_km  # noqa: E402

NODES = {"Gausala": "4879891022", "Chabahil": "3084565718", "Balaju": "31303568",
         "Koteshwor": "6275508137",
         # the nodes the coordinate rule picked on the arterial network (D31), pinned so a
         # denser network (D35) is compared at the same junctions, not the nearest new node
         "Kalanki": "10921097915", "Kalimati": "360831200", "Thapathali": "977642662",
         "Old Baneshwor": "1882601483", "New Baneshwor": "313735983"}
COORDS = {"Kalanki": LANDMARKS["Kalanki"],
          **{k: (OLD[k]["lat"], OLD[k]["lon"]) for k in ("Kalimati", "Thapathali", "Old Baneshwor", "New Baneshwor")}}


def main(dump="linkvol_base.csv", out_name="geh_jica2012.csv", pcu=PCU_FACTOR):
    """pcu: 0.625 for the calibrated model (A2); 0.786 for JICA-PCU demand (D35)."""
    pcu = float(pcu)
    rows = list(csv.DictReader(open(ROOT / "results" / dump, encoding="utf-8")))
    entering, pos = {}, {}
    for r in rows:
        entering[r["end"]] = entering.get(r["end"], 0.0) + float(r["vol_pcu_h"])
        pos[r["end"]] = (float(r["end_lat"]), float(r["end_lon"]))

    def node_for(name):
        if name in NODES:
            return NODES[name], 0.0
        lat, lon = COORDS[name]
        n = min(pos, key=lambda k: haversine_km(lat, lon, *pos[k]))
        return n, haversine_km(lat, lon, *pos[n])

    obs_rows = [r for r in csv.DictReader(open(ROOT / "data/jica2012/intersection_counts_2011.csv", encoding="utf-8"))
                if r["am_entering_veh_h"]]
    print(f"{'intersection':<14}{'obs veh/h':>10}{'obs pcu':>9}{'model':>8}{'GEH':>7}  {'old obs':>8}{'old GEH':>8}  node (km)")
    passes = 0
    out = []
    for r in obs_rows:
        name = r["intersection"]
        veh = (float(r["am_entering_veh_h"]) + float(r["pm_entering_veh_h"])) / 2
        o = veh * pcu
        n, km = node_for(name)
        m = entering.get(n, 0.0)
        g = geh(m, o)
        passes += g < 5
        old = OLD.get(name, {}).get("volume_pcu_h")
        old_txt = f"{old:>8.0f}{geh(m, old):>8.1f}" if old else f"{'':>8}{'':>8}"
        print(f"{name:<14}{veh:>10.0f}{o:>9.0f}{m:>8.0f}{g:>7.1f}  {old_txt}  {n} ({km:.2f})")
        out.append({"intersection": name, "observed_veh_h": round(veh), "observed_pcu_h": round(o),
                    "model_pcu_h": round(m), "geh": round(g, 2), "pass": g < 5, "node": n})
    print(f"\nGEH < 5: {passes}/{len(obs_rows)}   model/observed total: "
          f"{sum(x['model_pcu_h'] for x in out) / sum(x['observed_pcu_h'] for x in out):.0%}")
    bal = entering.get("31303549", 0.0)
    print(f"sensitivity: Balaju at the bypass node 31303549 -> model {bal:.0f}, GEH "
          f"{geh(bal, [x for x in out if x['intersection'] == 'Balaju'][0]['observed_pcu_h']):.1f}")
    with open(ROOT / "results" / out_name, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)


if __name__ == "__main__":
    main(*sys.argv[1:])
