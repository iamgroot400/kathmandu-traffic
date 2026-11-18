#!/usr/bin/env python3
"""Generate the paper's result charts as PNGs from the real result CSVs.

Replaces the LaTeX tables (table_core.py etc.) as the paper's primary visual
for these results, per the journal-format rewrite. Never types a number -
every value comes from the same result files and the same ci95() the tables
used.

    python paper/figures/make_charts.py

Outputs PNGs into paper/figures/.
"""
from __future__ import annotations

import csv
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from compare import ci95  # noqa: E402

OUT = Path(__file__).parent
PALETTE = {"pass": "#2a7a3b", "fail": "#b3261e", "neutral": "#2a5a8c", "bar": "#2a5a8c"}
plt.rcParams.update({"font.size": 11, "font.family": "serif"})


def fig_core():
    rows = list(csv.DictReader(open(ROOT / "results" / "comparison.partial.csv", encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault(r["config"], {})[int(r["seed"])] = r
    base = by["fixed_time"]
    labels = {"adaptive": "Adaptive\nsignals", "pricing": "Congestion\npricing",
              "adaptive_pricing": "Adaptive +\npricing"}
    names, means, errs = [], [], []
    for cfg in ["adaptive", "pricing", "adaptive_pricing"]:
        runs = by[cfg]
        shared = sorted(set(base) & set(runs))
        diffs = [float(runs[s]["delay_s"]) - float(base[s]["delay_s"]) for s in shared]
        rels = [d / float(base[s]["delay_s"]) * 100 for d, s in zip(diffs, shared)]
        mean_r, ci_r = ci95(rels)
        names.append(labels[cfg]); means.append(mean_r); errs.append(ci_r)

    fig, ax = plt.subplots(figsize=(6.0, 4.4))
    bars = ax.bar(names, means, yerr=errs, capsize=6, color=PALETTE["bar"], width=0.55)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Delay change vs. baseline (%)", fontsize=10)
    ax.set_title("Core result: 15-seed paired comparison", fontsize=11)
    ax.tick_params(axis="x", labelsize=9)
    ax.set_ylim(min(m - e for m, e in zip(means, errs)) - 8, 3)
    for b, m, e in zip(bars, means, errs):
        ax.text(b.get_x() + b.get_width() / 2, m - e - 2, f"{m:+.1f}%", ha="center",
                va="top", fontsize=10, color="black")
    fig.tight_layout(pad=1.2)
    fig.savefig(OUT / "fig_core.png", dpi=200)
    plt.close(fig)


def fig_geh():
    rows = list(csv.DictReader(open(ROOT / "results" / "geh_jica2012.csv", encoding="utf-8")))
    names = [r["intersection"] for r in rows]
    gehs = [float(r["geh"]) for r in rows]
    colors = [PALETTE["pass"] if g < 5 else PALETTE["fail"] for g in gehs]

    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    bars = ax.barh(names, gehs, color=colors)
    ax.axvline(5, color="black", linestyle="--", linewidth=1, label="GEH = 5 threshold")
    ax.set_xlabel("GEH statistic (lower is better fit)", fontsize=10)
    ax.set_title("Baseline validation, 9 intersections (JICA 2012 counts)", fontsize=11)
    ax.set_xlim(0, max(gehs) * 1.2)
    for b, g in zip(bars, gehs):
        ax.text(g + max(gehs) * 0.02, b.get_y() + b.get_height() / 2, f"{g:.1f}", va="center", fontsize=9)
    ax.legend(loc="lower right", fontsize=9)
    ax.invert_yaxis()
    fig.tight_layout(pad=1.2)
    fig.savefig(OUT / "fig_geh.png", dpi=200)
    plt.close(fig)


def paired(path, base_name, variant_name, clean_only=True):
    rows = list(csv.DictReader(open(path, encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault(r["config"], {})[int(r["seed"])] = r
    base, var = by[base_name], by[variant_name]
    seeds = sorted(set(base) & set(var))
    if clean_only:
        seeds = [s for s in seeds if float(base[s]["completed"]) >= 0.999 and float(var[s]["completed"]) >= 0.999]
    diffs = [float(var[s]["delay_s"]) - float(base[s]["delay_s"]) for s in seeds]
    rels = [d / float(base[s]["delay_s"]) * 100 for d, s in zip(diffs, seeds)]
    mean_r, ci_r = ci95(rels)
    return mean_r, ci_r, len(seeds)


def fig_additional():
    ROOT_R = ROOT / "results"
    items = [
        ("Tidal-flow\n1.0 lane-eq.", *paired(ROOT_R / "tidal.csv", "no_tidal", "tidal"), "fail"),
        ("Tidal-flow\n0.5 lane-eq.", *paired(ROOT_R / "tidal_half.csv", "no_tidal", "tidal"), "fail"),
        ("Parking /\nfree-flow enf.", *paired(ROOT_R / "extra.partial.csv", "baseline", "parking"), "fail"),
        ("Staggered\ndepartures", *paired(ROOT_R / "extra.partial.csv", "baseline", "staggered"), "pass"),
        ("Decentralized\ncore demand", *paired(ROOT_R / "extra.partial.csv", "baseline", "decentralized"), "pass"),
    ]
    names = [i[0] for i in items]
    means = [i[1] for i in items]
    errs = [i[2] for i in items]
    ns = [i[3] for i in items]
    colors = [PALETTE[i[4]] for i in items]

    fig, ax = plt.subplots(figsize=(6.4, 4.4))
    bars = ax.bar(names, means, yerr=errs, capsize=5, color=colors, width=0.6)
    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_ylabel("Delay change vs. baseline (%)", fontsize=10)
    ax.set_title("Additional interventions (H4-H7), clean seeds", fontsize=11)
    ax.tick_params(axis="x", labelsize=8)
    for b, m, n in zip(bars, means, ns):
        ax.text(b.get_x() + b.get_width() / 2, m + (2 if m > 0 else -2), f"n={n}",
                ha="center", va="bottom" if m > 0 else "top", fontsize=8)
    fig.tight_layout(pad=1.2)
    fig.savefig(OUT / "fig_additional.png", dpi=200)
    plt.close(fig)


def fig_sensitivity():
    rows = list(csv.DictReader(open(ROOT / "results" / "sensitivity.csv", encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault((r["knob"], r["variant"]), []).append(r)
    base_speed = statistics.fmean(float(r["speed_kmh"]) for r in by[("demand_scale", "baseline")])

    labels = {"demand_scale": "demand_scale", "pcu_factor": "pcu_factor",
              "free_flow_kmh": "free_flow_kmh"}
    names, lo, hi = [], [], []
    for knob in ["demand_scale", "pcu_factor", "free_flow_kmh"]:
        s_minus = statistics.fmean(float(r["speed_kmh"]) for r in by.get((knob, "-20%"), [])) \
            if (knob, "-20%") in by else base_speed
        s_plus = statistics.fmean(float(r["speed_kmh"]) for r in by.get((knob, "+20%"), [])) \
            if (knob, "+20%") in by else base_speed
        names.append(labels[knob]); lo.append(s_minus); hi.append(s_plus)

    fig, ax = plt.subplots(figsize=(6.0, 3.8))
    y = range(len(names))
    for i, (l, h) in enumerate(zip(lo, hi)):
        ax.plot([l, h], [i, i], color=PALETTE["neutral"], linewidth=4, solid_capstyle="round")
        ax.plot(l, i, "o", color=PALETTE["fail"])
        ax.plot(h, i, "o", color=PALETTE["pass"])
    ax.axvline(base_speed, color="black", linestyle="--", linewidth=1, label=f"baseline {base_speed:.1f} km/h")
    ax.set_yticks(list(y)); ax.set_yticklabels(names, fontsize=9)
    ax.set_xlabel("Mean network speed (km/h)", fontsize=10)
    ax.set_title("Sensitivity: +/-20% per parameter", fontsize=11)
    ax.legend(loc="lower right", fontsize=8)
    fig.tight_layout(pad=1.2)
    fig.savefig(OUT / "fig_sensitivity.png", dpi=200)
    plt.close(fig)


JICA_TESTS = [("H1 Adaptive signals", "adaptive", "baseline"), ("H2 Congestion pricing", "pricing", "baseline"),
              ("H3 Adaptive + pricing", "adaptive_pricing", "baseline"), ("H4 Tidal lanes (AM)", "am_tidal", "am_no_tidal"),
              ("H5 Parking enforcement", "parking", "baseline"), ("H6 Staggered departures", "staggered", "baseline"),
              ("H7 Decentralized", "decentralized", "baseline"),
              ("H7 vs equal uniform cut", "decentralized", "uniform_cut")]


def jica_paired(key="tis_s"):
    """(label, mean %, CI %) per test from the public clean run, paired by seed."""
    src = {}
    for r in csv.DictReader(open(ROOT / "results" / "clean" / "jica_h1h7.csv", encoding="utf-8")):
        src.setdefault(r["config"], {})[int(r["seed"])] = float(r[key])
    out = []
    for label, c, b in JICA_TESTS:
        shared = sorted(set(src[c]) & set(src[b]))
        m, h = ci95([(src[c][s] - src[b][s]) / src[b][s] * 100 for s in shared])
        out.append((label, m, h))
    return out


def fig_jica_levers():
    res = jica_paired()
    names = [r[0] for r in res]; means = [r[1] for r in res]; errs = [r[2] for r in res]
    colors = [PALETTE["bar"] if abs(m) > e else "#9a9a9a" for m, e in zip(means, errs)]
    fig, ax = plt.subplots(figsize=(6.0, 4.6))
    bars = ax.barh(names, means, xerr=errs, capsize=4, color=colors)
    ax.axvline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Change in mean time in system (%), 15 paired seeds", fontsize=10)
    ax.set_title("Interventions on the JICA-demand baseline", fontsize=11)
    ax.tick_params(axis="y", labelsize=9)
    ax.set_xlim(min(m - e for m, e in zip(means, errs)) - 8, 8)
    for b, m, e in zip(bars, means, errs):
        ax.text(min(m - e, 0) - 0.8, b.get_y() + b.get_height() / 2, f"{m:+.1f}%", ha="right",
                va="center", fontsize=8.5)
    ax.invert_yaxis()
    fig.tight_layout(pad=1.2)
    fig.savefig(OUT / "fig_jica_levers.png", dpi=200)
    plt.close(fig)


def fig_jica_validation():
    """Model / observed entering volume per junction, mean and 95% CI over the baseline seed sweep."""
    ratios = {}
    for f in sorted((ROOT / "results" / "clean" / "jica_sweep").glob("_geh_main_y0.2_s*.csv")):
        for r in csv.DictReader(open(f, encoding="utf-8")):
            ratios.setdefault(r["intersection"], []).append(float(r["model_pcu_h"]) / float(r["observed_pcu_h"]))
    rows = sorted(((k, *ci95(v), len(v)) for k, v in ratios.items()), key=lambda x: -x[1])
    fig, ax = plt.subplots(figsize=(6.0, 4.2))
    names = [r[0] for r in rows]; means = [r[1] for r in rows]; errs = [r[2] for r in rows]
    bars = ax.barh(names, means, xerr=errs, capsize=4, color=PALETTE["bar"])
    ax.axvline(1, color="black", linewidth=1, label="model = observed")
    ax.axvspan(1 / 1.5, 1.5, color="#2a7a3b", alpha=0.10, label="within a factor 1.5")
    ax.set_xlabel("Model / observed peak entering volume (PCU/h)", fontsize=10)
    ax.set_title(f"Validation against JICA 2011-12 counts, {rows[0][3]} seeds", fontsize=11)
    ax.set_xlim(0, 1.6)
    for b, m in zip(bars, means):
        ax.text(0.03, b.get_y() + b.get_height() / 2, f"{m:.2f}", va="center", fontsize=9, color="white")
    ax.legend(loc="lower right", fontsize=8.5)
    ax.invert_yaxis()
    fig.tight_layout(pad=1.2)
    fig.savefig(OUT / "fig_jica_validation.png", dpi=200)
    plt.close(fig)


if __name__ == "__main__":
    fig_core()
    fig_geh()
    fig_additional()
    fig_sensitivity()
    fig_jica_levers()
    fig_jica_validation()
    print("wrote fig_core.png, fig_geh.png, fig_additional.png, fig_sensitivity.png")
