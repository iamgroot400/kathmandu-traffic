#!/usr/bin/env python3
"""Network check at the 6 tuning junctions: which links feed each junction, their OSM lanes,
free-flow speed and side-street status, and what the model sends down them (mean over seed dumps).
Held-out junctions are never printed.

    python checks/junction_approaches.py <dir with *_s<n>.csv dumps> <config prefix> [radius_m]
"""
import csv
import glob
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path[:0] = [str(ROOT / "checks"), str(ROOT / "scripts")]
from geh_jica2012 import NODES, cluster_group  # noqa: E402
from tune_counts import TUNE  # noqa: E402

PCU = 0.786


def main(dump_dir, prefix, radius=100):
    radius = float(radius)
    net = {}
    for r in csv.reader(open(ROOT / "data/jica_net/network_links.csv", encoding="utf-8")):
        net[r[1], r[2]] = {"name": r[0].rsplit("-", 1)[0], "way": r[0].rsplit("-", 1)[-1],
                           "lanes": int(float(r[3])), "ff_kmh": float(r[4]) * 3.6}
    minor = set((ROOT / "data/jica_net/minor_ways.txt").read_text(encoding="utf-8").split())
    runs = [list(csv.DictReader(open(f, encoding="utf-8")))
            for f in sorted(glob.glob(str(Path(dump_dir) / f"{prefix}_s[0-9]*.csv")))]
    obs = {r["intersection"]: (float(r["am_entering_veh_h"]) + float(r["pm_entering_veh_h"])) / 2 * PCU
           for r in csv.DictReader(open(ROOT / "data/jica2012/intersection_counts_2011.csv", encoding="utf-8"))
           if r["intersection"] in TUNE}
    out = []
    for k in TUNE:
        grp = cluster_group(runs[0], NODES[k], radius)
        app = {}
        for rows in runs:
            for r in rows:
                if r["end"] in grp and r["start"] not in grp:
                    a = app.setdefault((r["start"], r["end"]), {"vol": [], "ratio": [], "len": float(r["length_m"])})
                    a["vol"].append(float(r["vol_pcu_h"]))
                    meta = net.get((r["start"], r["end"]), {})
                    ff = meta.get("ff_kmh", 40) / 3.6
                    a["ratio"].append(float(r["tt_s"]) / max(float(r["length_m"]) / ff, 1))
        total = sum(statistics.fmean(a["vol"]) for a in app.values())
        lanes = sum(net.get(e, {}).get("lanes", 1) for e in app)
        print(f"\n{k}: observed {obs[k]:,.0f}  model {total:,.0f}  ratio {total / obs[k]:.2f}  "
              f"approach links {len(app)}  entering lanes {lanes}  model PCU/h per lane {total / lanes:,.0f}  "
              f"observed per lane {obs[k] / lanes:,.0f}")
        for e, a in sorted(app.items(), key=lambda x: -statistics.fmean(x[1]["vol"])):
            m = net.get(e, {"name": "?", "way": "?", "lanes": 1, "ff_kmh": 0})
            v, q = statistics.fmean(a["vol"]), statistics.fmean(a["ratio"])
            side = "side" if m["way"] in minor else "main"
            print(f"  {m['name'][:28]:<28} way {m['way']:<11} {side}  lanes {m['lanes']}  ff {m['ff_kmh']:>3.0f} km/h  "
                  f"len {a['len']:>5.0f} m  vol {v:>6,.0f}  tt/ff {q:>5.1f}")
            out.append({"junction": k, "road": m["name"], "way": m["way"], "side_street": side == "side",
                        "lanes": m["lanes"], "ff_kmh": round(m["ff_kmh"]), "vol_pcu_h": round(v),
                        "per_lane": round(v / m["lanes"]), "tt_over_ff": round(q, 1)})
    dest = ROOT / "results" / f"approaches_{prefix}.csv"
    with open(dest, "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0]))
        w.writeheader()
        w.writerows(out)
    print(f"\nwrote {dest}")


if __name__ == "__main__":
    main(*sys.argv[1:])
