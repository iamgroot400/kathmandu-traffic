#!/usr/bin/env python3
"""Chart for the capacity-sensitivity robustness sweep (scripts/compare_capacity_sweep.py).

Written ahead of the sweep finishing, so there is nothing left to do once it does -
reads whichever capacity levels + seeds are present in results/capacity_sweep.csv
(the final file; .partial.csv while the sweep is still running) and reports each
lever's paired delay change vs. fixed_time at that capacity, with however many
seeds are available per cell. Never types a number.

    python paper/figures/make_capacity_chart.py             # uses capacity_sweep.partial.csv
                                                              # if the final file isn't written yet
"""
from __future__ import annotations

import csv
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from compare import ci95  # noqa: E402

OUT = Path(__file__).parent
COLORS = {"adaptive": "#2a5a8c", "pricing": "#b3261e", "adaptive_pricing": "#2a7a3b"}
LEVER_LABELS = {"adaptive": "Adaptive signals", "pricing": "Congestion pricing",
                "adaptive_pricing": "Adaptive + pricing"}
CAPACITY_ORDER = ["1200", "1600", "2000", "2400"]


def load():
    path = ROOT / "results" / "capacity_sweep.csv"
    if not path.exists():
        path = ROOT / "results" / "capacity_sweep.partial.csv"
    if not path.exists():
        raise SystemExit("no capacity_sweep (partial) results found yet - run the sweep first")
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault(r["capacity"], {}).setdefault(r["lever"], {})[int(r["seed"])] = r
    return by, path


def main():
    by, path = load()
    print(f"reading {path}")

    # two panels: mean delay covers completed trips only, so it is only readable
    # next to the completion change (completion bias, decisions.md D18/D27)
    fig, (ax, ax2) = plt.subplots(2, 1, figsize=(6.4, 6.6), sharex=True)
    width = 0.25
    x = range(len(CAPACITY_ORDER))
    for i, lever in enumerate(["adaptive", "pricing", "adaptive_pricing"]):
        means, errs, ns, cmeans, cerrs = [], [], [], [], []
        for cap in CAPACITY_ORDER:
            base = by.get(cap, {}).get("fixed_time", {})
            runs = by.get(cap, {}).get(lever, {})
            shared = sorted(set(base) & set(runs))
            if len(shared) < 2:
                means.append(0); errs.append(0); ns.append(len(shared)); cmeans.append(0); cerrs.append(0)
                continue
            rels = [(float(runs[s]["delay_s"]) - float(base[s]["delay_s"])) / float(base[s]["delay_s"]) * 100
                    for s in shared]
            comp = [(float(runs[s]["completed"]) - float(base[s]["completed"])) * 100 for s in shared]
            mean_r, ci_r = ci95(rels)
            mean_c, ci_c = ci95(comp)
            means.append(mean_r); errs.append(ci_r); ns.append(len(shared)); cmeans.append(mean_c); cerrs.append(ci_c)
        xpos = [xi + (i - 1) * width for xi in x]
        ax.bar(xpos, means, width=width, yerr=errs, capsize=3, color=COLORS[lever], label=LEVER_LABELS[lever])
        ax2.bar(xpos, cmeans, width=width, yerr=cerrs, capsize=3, color=COLORS[lever])
        for xp, m, n in zip(xpos, means, ns):
            if n > 0:
                ax.text(xp, m - 2 if m < 0 else m + 2, f"n={n}", ha="center",
                        va="top" if m < 0 else "bottom", fontsize=6.5)

    for a_ in (ax, ax2):
        a_.axhline(0, color="black", linewidth=0.8)
    ax2.set_xticks(list(x)); ax2.set_xticklabels([f"{c} veh/h/lane" for c in CAPACITY_ORDER], fontsize=9)
    ax.set_ylabel("Delay change, completed trips (%)", fontsize=9)
    ax2.set_ylabel("Completion change (points)", fontsize=9)
    ax.set_title("Robustness across assumed per-lane capacity, vs. fixed-time", fontsize=10.5)
    ax.legend(fontsize=8, loc="lower left")
    fig.tight_layout(pad=1.2)
    fig.savefig(OUT / "fig_capacity_sweep.png", dpi=200)
    plt.close(fig)
    print(f"wrote {OUT / 'fig_capacity_sweep.png'}")

    print("\nPer-capacity, per-lever (whatever n is available so far):")
    for cap in CAPACITY_ORDER:
        base = by.get(cap, {}).get("fixed_time", {})
        for lever in ["adaptive", "pricing", "adaptive_pricing"]:
            runs = by.get(cap, {}).get(lever, {})
            shared = sorted(set(base) & set(runs))
            if len(shared) < 2:
                print(f"  {cap:>5} {lever:<16} n={len(shared)} (too few paired seeds yet)")
                continue
            diffs = [float(runs[s]["delay_s"]) - float(base[s]["delay_s"]) for s in shared]
            rels = [d / float(base[s]["delay_s"]) * 100 for d, s in zip(diffs, shared)]
            mean_r, ci_r = ci95(rels)
            neg = sum(1 for d in diffs if d < 0)
            print(f"  {cap:>5} {lever:<16} {mean_r:+.2f}% +/- {ci_r:.2f}%  [{neg}/{len(shared)} neg]")


if __name__ == "__main__":
    main()
