#!/usr/bin/env python3
"""Extract the JICA 2011 vehicle OD table between the 9 large zones, by vehicle type,
in PCU/day (Appendix 2.2.7, PDF page 48) and in vehicles/day (PDF page 52), into
data/jica_od/vtod_2011.csv. Every row is checked against the printed row total and
every block against its printed column subtotals.

JICA PCU weights (same appendix): motorcycle 0.3, car/taxi 1.0, light truck 1.5,
heavy truck 4.0, tempo 1.0, microbus 1.5, minibus 3.0, large bus 4.0.

    python scripts/extract_jica_vtod.py
"""
import csv
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).parent.parent
PAGES = {"pcu": 47, "veh": 51}                 # 0-based: report pages AP 2-16 / AP 2-20
ZONES = [str(z) for z in range(100, 1000, 100)]


def num(s):
    return int(s.replace(",", ""))


def read(page_no):
    rows = pdfplumber.open(ROOT / "data" / "jica2012" / "12082459_04.pdf").pages[page_no].extract_tables()[0]
    out, mode, block = {}, None, {}
    for r in rows:
        # zone label first: in the "Total" block the mode cell itself reads "Total"
        k = next((i for i, c in enumerate(r[:3]) if c in ZONES), None)
        if k is None:
            k = next((i for i, c in enumerate(r[:3]) if c in ("Sub Total", "Total") and r[i + 1]
                      and r[i + 1][0].isdigit()), None)
        if k is None or "Large Zone" in r or not (r[k + 1] or "")[:1].isdigit():
            continue                                 # column-header row
        if k > 0 and r[k - 1]:
            mode = r[k - 1]
        label, cells = r[k], r[k + 1:k + 11]
        if label in ZONES:
            vals = [num(c) for c in cells]
            assert sum(vals[:9]) == vals[9], (page_no, mode, label)
            block[label] = vals[:9]
        elif block:
            tot = [num(c) for c in cells[:9]]
            for j in range(9):
                assert sum(block[o][j] for o in ZONES) == tot[j], (page_no, mode, j)
            out[mode.lower()] = block
            block = {}
    assert set(out) == {"motorcycle", "car", "truck", "bus", "total"}, out.keys()
    for o in ZONES:                              # classes add up to the Total block
        for j in range(9):
            parts = sum(out[m][o][j] for m in ("motorcycle", "car", "truck", "bus"))
            assert abs(parts - out["total"][o][j]) <= 2, (page_no, o, j, parts, out["total"][o][j])
    return out


def main():
    data = {k: read(p) for k, p in PAGES.items()}
    path = ROOT / "data" / "jica_od" / "vtod_2011.csv"
    with path.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["origin_large", "dest_large", "mode", "veh_per_day", "pcu_per_day"])
        for m in ("motorcycle", "car", "truck", "bus"):
            for o in ZONES:
                for j, d in enumerate(ZONES):
                    w.writerow([o, d, m, data["veh"][m][o][j], data["pcu"][m][o][j]])
    for k in data:
        print(k, {m: sum(map(sum, data[k][m].values())) for m in data[k]})
    print(f"wrote {path}; all row and column totals match")


if __name__ == "__main__":
    main()
