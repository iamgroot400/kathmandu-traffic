#!/usr/bin/env python3
"""Extract the JICA 2011 person-trip OD table (51 small zones; the printout omits origin 901's row, rebuilt from the column totals; all purposes, all modes,
Appendix 1.1.2, AP 1-5/1-6, PDF pages 8-9) into data/jica_od/ptod_2011.csv.

The pages are rotated, so pdfplumber returns each cell's text reversed and the table
transposed (one row per destination). Every row and column is checked against the
report's printed totals, which catches any mis-read cell.

    python scripts/extract_jica_ptod.py
"""
import csv
from pathlib import Path

import pdfplumber

ROOT = Path(__file__).parent.parent
PDF = ROOT / "data" / "jica2012" / "12082459_04.pdf"


def num(cell):
    return int(cell[::-1].replace(",", ""))


def main():
    pdf = pdfplumber.open(PDF)
    dest_rows = {}                                   # destination -> {origin: trips}
    origin_total, dest_total = {}, {}
    header = [(c or "")[::-1] for c in pdf.pages[7].extract_tables()[0][-2]][2:]
    assert header[-1] == "Total", header[-3:]
    origins = header[:-1]                            # 50 zones: 901 is a destination only
    for page in (7, 8):
        for r in pdf.pages[page].extract_tables()[0]:
            dest = (r[1] or "")[::-1]
            if not dest.isdigit() and dest != "Total":
                continue                             # header / axis-label rows
            vals = [num(c) for c in r[2:]]
            assert len(vals) == len(origins) + 1, (page, dest, len(vals))
            if dest == "Total":
                origin_total = dict(zip(origins, vals[:-1]))
                grand = vals[-1]
                continue
            dest_rows[dest] = dict(zip(origins, vals[:-1]))
            dest_total[dest] = vals[-1]
    zones = sorted(dest_rows)
    assert len(zones) == 51 and set(origins) == set(zones) - {"901"}, (len(zones), set(zones) - set(origins))
    # The printed table omits origin 901's row, but every destination total includes it,
    # so the row is exactly each destination's shortfall.
    for d in zones:
        dest_rows[d]["901"] = dest_total[d] - sum(dest_rows[d].values())
        assert dest_rows[d]["901"] >= 0, (d, dest_rows[d]["901"])
    origin_total["901"] = sum(dest_rows[d]["901"] for d in zones)
    origins.append("901")
    for o in origins:
        assert sum(dest_rows[d][o] for d in zones) == origin_total[o], o
    assert sum(origin_total.values()) == grand == sum(dest_total.values())
    out = ROOT / "data" / "jica_od" / "ptod_2011.csv"
    with out.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["origin", "destination", "person_trips"])
        for o in origins:
            for d in zones:
                w.writerow([o, d, dest_rows[d][o]])
    print(f"wrote {out}: 51 x 51 zones, {grand:,} person trips/day, all totals match; origin 901 rebuilt, {origin_total['901']:,} trips")


if __name__ == "__main__":
    main()
