#!/usr/bin/env python3
"""Paired analysis of the E10 follow-ups (results/followups.partial.csv) against the
existing result files. Safe to run while the queue is still going: uses whatever
seeds are present and says how many.

    python checks/analyze_followups.py
"""
import csv
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from compare import ci95  # noqa: E402


def load(name, key="config"):
    by = {}
    p = ROOT / "results" / name
    if p.exists():
        for r in csv.DictReader(open(p, encoding="utf-8")):
            by.setdefault(r[key], {})[int(r["seed"])] = r
    return by


def paired(a, b, field="delay_s", rel=True, clean=False):
    """b vs a (a is the reference). Returns text, or None if under 2 shared seeds."""
    seeds = sorted(set(a) & set(b))
    if clean:
        seeds = [s for s in seeds if float(a[s]["completed"]) >= 0.999 and float(b[s]["completed"]) >= 0.999]
    if len(seeds) < 2:
        return None
    d = [float(b[s][field]) - float(a[s][field]) for s in seeds]
    if rel:
        d = [x / float(a[s][field]) * 100 for x, s in zip(d, seeds)]
    m, ci = ci95(d)
    unit = "%" if rel else (" pts" if field == "completed" else "")
    scale = 100 if field == "completed" and not rel else 1
    sig = "SIG" if abs(m) > ci else "n.s."
    return f"{m * scale:+8.2f}{unit} +/- {ci * scale:6.2f}  [{sum(x < 0 for x in d)}/{len(seeds)} neg]  {sig}"


def line(label, res):
    print(f"  {label:<46} {res or 'not enough seeds yet'}")


f = load("followups.partial.csv")
extra, core = load("extra.partial.csv"), load("comparison.partial.csv")
fut = load("future_demand_projected_2030.csv")
g = lambda d, k: d.get(k, {})

print("E10a  volume-matched control for H7 (clean seeds, delay)")
line("uniform_cut vs baseline", paired(g(extra, "baseline"), g(f, "uniform_cut"), clean=True))
line("decentralized vs baseline", paired(g(extra, "baseline"), g(extra, "decentralized"), clean=True))
line("decentralized vs uniform_cut  <- the test", paired(g(f, "uniform_cut"), g(extra, "decentralized"), clean=True))

print("\nE10b  half-size stagger (clean seeds, delay)")
line("staggered_4500 vs baseline", paired(g(extra, "baseline"), g(f, "staggered_4500"), clean=True))
line("staggered (5400) vs baseline", paired(g(extra, "baseline"), g(extra, "staggered"), clean=True))

print("\nE10f  elastic pricing, elasticity -0.3 (delay; trips = share of demand still served)")
for name, fixed in (("pricing_elastic", "pricing"), ("combined_elastic", "adaptive_pricing")):
    line(f"{name} vs fixed_time", paired(g(core, "fixed_time"), g(f, name)))
    line(f"{fixed} (fixed demand) vs fixed_time", paired(g(core, "fixed_time"), g(core, fixed)))
    line(f"{name} vs {fixed}", paired(g(core, fixed), g(f, name)))
    el = [float(r["trips"]) for r in g(f, name).values() if r.get("trips")]
    bt = ROOT / "results" / "baseline_trips.csv"      # written by checks/baseline_trips.py
    if el and bt.exists():
        base = float(next(csv.DictReader(open(bt)))["trips"])
        print(f"      trips served: {el[0] / base:.1%} of baseline")

print("\nE10c  combined lever at 2030 demand (completion, points)")
line("combined_2030 vs projected_2030", paired(g(fut, "projected_2030"), g(f, "combined_2030"), "completed", rel=False))
if g(f, "combined_2030"):
    m, ci = ci95([float(r["completed"]) * 100 for r in f["combined_2030"].values()])
    print(f"      combined_2030 completion: {m:.1f}% +/- {ci:.1f}  (n={len(f['combined_2030'])})")

print("\nE10d  capacity sweep on time in system (all vehicles, unfinished counted to the horizon)")
for cap in ("2000", "1600"):
    base = g(f, f"cap{cap}_fixed_time")
    for lever in ("adaptive", "pricing", "adaptive_pricing"):
        v = g(f, f"cap{cap}_{lever}")
        line(f"{cap} {lever}: time in system", paired(base, v, "tis_s"))
        line(f"{cap} {lever}: completion", paired(base, v, "completed", rel=False))
