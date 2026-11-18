#!/usr/bin/env python3
"""Recompute every hardcoded number in paper/build_pdf.py from results/, and run the
completion-bias check on the capacity sweep and demand projections."""
import csv, sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from compare import ci95

def load(path, keys):
    by = {}
    for r in csv.DictReader(open(ROOT / "results" / path, encoding="utf-8")):
        by.setdefault(tuple(r[k] for k in keys), {})[int(r["seed"])] = r
    return by

def paired(base, var, clean=False):
    seeds = sorted(set(base) & set(var))
    if clean:
        seeds = [s for s in seeds if float(base[s]["completed"]) >= 0.999 and float(var[s]["completed"]) >= 0.999]
    if len(seeds) < 2:
        return None
    rel = [(float(var[s]["delay_s"]) - float(base[s]["delay_s"])) / float(base[s]["delay_s"]) * 100 for s in seeds]
    m, ci = ci95(rel)
    return m, ci, sum(1 for x in rel if x < 0), len(seeds)

def show(label, res):
    print(f"  {label:<34}", "too few clean seeds" if res is None else f"{res[0]:+7.2f}% +/- {res[1]:5.2f}%  [{res[2]}/{res[3]} neg]")

def comp(runs):
    return sum(float(r["completed"]) for r in runs.values()) / len(runs)

print("CORE (comparison.partial.csv)")
core = load("comparison.partial.csv", ["config"])
for c in ["adaptive", "pricing", "adaptive_pricing"]:
    show(c, paired(core[("fixed_time",)], core[(c,)]))
    print(f"      completion: base {comp(core[('fixed_time',)]):.3f}  {c} {comp(core[(c,)]):.3f}")

print("\nEXTRA (extra.partial.csv)  raw / clean")
ex = load("extra.partial.csv", ["config"])
for (c,) in ex:
    if c != "baseline":
        show(c + " raw", paired(ex[("baseline",)], ex[(c,)])); show(c + " clean", paired(ex[("baseline",)], ex[(c,)], True))

print("\nCAPACITY SWEEP  raw / clean-seed / completion")
cap = load("capacity_sweep.csv", ["capacity", "lever"])
for capv in ["1200", "1600", "2000", "2400"]:
    b = cap[(capv, "fixed_time")]
    print(f" {capv}: fixed_time completion {comp(b):.3f}, fully complete seeds {sum(float(r['completed'])>=0.999 for r in b.values())}/{len(b)}")
    for l in ["adaptive", "pricing", "adaptive_pricing"]:
        v = cap[(capv, l)]
        show(f"{l} raw (compl {comp(v):.3f})", paired(b, v)); show(f"{l} clean", paired(b, v, True))
        # total-delay proxy: unfinished trips are at least as delayed as the horizon allows
        seeds = sorted(set(b) & set(v))
        dc = [float(v[s]["completed"]) - float(b[s]["completed"]) for s in seeds]
        m, ci = ci95([d * 100 for d in dc])
        print(f"      completion change: {m:+.1f} pts +/- {ci:.1f}")

for f in ["future_demand.csv", "future_demand_projected_2030.partial.csv"]:
    p = ROOT / "results" / f
    if not p.exists(): continue
    print(f"\n{f}")
    fd = load(f, ["config"])
    for (c,) in fd:
        print(f"  {c}: n={len(fd[(c,)])} completion {comp(fd[(c,)]):.3f}")
        if c != "baseline":
            show(c + " raw", paired(fd[("baseline",)], fd[(c,)]))
