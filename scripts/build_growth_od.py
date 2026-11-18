#!/usr/bin/env python3
"""Grow the JICA base OD matrix by a factor, keeping its pairs and whole platoons (D38).

UXsim releases a pair's demand in platoons of deltan (5) and drops the leftover, so a
fractional multiplier on od_matrix.csv (all multiples of 5) loses up to 4 vehicles per
pair: x1.20 created 122,590 of 140,462 requested. Instead the grown total is spread over
the same 7,508 pairs in whole platoons with build_od_jica's largest_remainder.

    python scripts/build_growth_od.py   # writes od_matrix_g4yr / g2026 / g2030
"""
import csv
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_od_jica import largest_remainder  # noqa: E402

NET = Path(__file__).parent.parent / "data" / "jica_net"
RATE, DN = 0.0452, 5
GROWTH = {"g4yr": 4.19, "g2026": 15, "g2030": 19}   # years from the 2011 survey (2030: end of year)


def main() -> None:
    rows = list(csv.DictReader(open(NET / "od_matrix.csv", encoding="utf-8")))
    base = [int(r["demand"]) for r in rows]
    assert all(d % DN == 0 for d in base), "base demand is not in whole platoons"
    for name, years in GROWTH.items():
        units = round(sum(base) * (1 + RATE) ** years / DN)
        grown = [u * DN for u in largest_remainder(units, base)]
        with open(NET / f"od_matrix_{name}.csv", "w", newline="", encoding="utf-8") as fh:
            w = csv.DictWriter(fh, fieldnames=list(rows[0]))
            w.writeheader()
            w.writerows({**r, "demand": g} for r, g in zip(rows, grown))
        print(f"{name}: x{(1 + RATE) ** years:.3f}, {sum(grown):,} PCU/h over {len(rows):,} pairs")


if __name__ == "__main__":
    main()
