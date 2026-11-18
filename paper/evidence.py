#!/usr/bin/env python3
"""Every number in the paper, computed once from the public Kaggle run, with where it comes from.

Writes two files from the same values, so they cannot disagree:
  paper/numbers.tex  LaTeX macros used by paper/sections/*.tex (\\HoneTis, \\ValShare, ...)
  paper/claims.md    the claim ledger: each number, its Kaggle notebook, output file and computation

    bash tools/fetch_results.sh     # download the Kaggle outputs into results/clean/
    python paper/evidence.py

build_pdf.py computes the PDF's numbers with the same functions (jica_numbers, sweep_numbers, ...).
"""
import csv
import statistics
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from build_pdf import (CLEAN, ROOT, TESTS, ci95, jica_numbers, junction_ratios, load_by,  # noqa: E402
                       old_numbers, projection_numbers, sweep_numbers, tolled_links, yield_shift)

KAGGLE = "https://www.kaggle.com/code/aashikkhatri/kathmandu-traffic-"
DATASET = "https://www.kaggle.com/datasets/aashikkhatri/kathmandu-traffic-sim"
NB = {  # notebook key -> (title, output file(s) the numbers are read from)
    "1": ("1-build-demand", "demand and network inputs (od_matrix*.csv, minor_ways.txt)"),
    "2": ("2-baseline-and-validation", "sim/results/jica_sweep_summary.csv, sim/results/jica_sweep/_geh_*.csv, "
          "sim/results/tolls_jica.csv"),
    "3": ("3a-interventions-seeds-1-8", "sim/results/jica_h1h7.partial.csv (3a: seeds 1-8, 3b: seeds 9-15)"),
    "4": ("4a-projection-seeds-1-8", "projection_seeds1-8.csv (4a) + projection_seeds9-15.csv (4b)"),
    "5": ("5-results", "reads 2, 3a/3b, 4a/4b and prints every table below"),
}
WORD = {"H1": "One", "H2": "Two", "H3": "Three", "H4": "Four", "H5": "Five", "H6": "Six", "H7": "Seven",
        "H7u": "SevenU"}
NAME = {"H1": "adaptive signals vs baseline", "H2": "congestion pricing vs baseline",
        "H3": "adaptive signals + pricing vs baseline", "H4": "tidal lanes vs same AM demand without",
        "H5": "parking enforcement proxy vs baseline", "H6": "staggered departures vs baseline",
        "H7": "decentralized attraction vs baseline", "H7u": "decentralized vs volume-matched uniform cut"}


def ci(m, h, d=1, unit="\\%", sign=True):
    return f"${m:{'+' if sign else ''}.{d}f} \\pm {h:.{d}f}${unit}"


def build():
    """Return [(section, macro, latex value, plain value, claim, notebook key, computation)]."""
    J, S, P, O = jica_numbers(), sweep_numbers(), projection_numbers(), old_numbers()
    rows = []
    add = lambda *r: rows.append(r)  # noqa: E731
    pair = "paired over 15 seeds: per seed (arm - base) / base x 100, mean and 95% t interval"

    # ---- validation (notebook 2)
    sec = "Baseline against observations"
    for key, macro, label, d, scale, unit in [
            ("ring_kmh", "ValRing", "Ring Road speed, km/h (JICA survey 24.0)", 1, 1, " km/h"),
            ("inner_kmh", "ValInner", "inner main road speed, km/h (JICA survey 15.3)", 1, 1, " km/h"),
            ("corr", "ValCorr", "correlation of model with counted volume across 9 junctions", 2, 1, ""),
            ("within_1_5", "ValWithin", "junctions (of 9) within a factor 1.5 of the count", 1, 1, ""),
            ("geh_pass", "ValGeh", "junctions (of 9) with GEH < 5", 1, 1, "")]:
        m, h = S[key]
        add(sec, macro, ci(m, h, d, unit.replace(" km/h", "~km/h"), sign=key == "corr"), f"{m:.{d}f} +/- {h:.{d}f}{unit}", label, "2",
            f"`jica_sweep_summary.csv`, column `{key}`, rows `main_y0.2` ({S['n']} seeds): mean and 95% t interval")
    add(sec, "ValShare", f"{S['share'][0] * 100:.0f}\\%", f"{S['share'][0]:.0%}",
        "model volume / counted volume, summed over the 9 junctions", "2",
        "`jica_sweep_summary.csv`, column `share`, rows `main_y0.2`: mean")
    add(sec, "ValRingGap", f"{24.0 - S['ring_kmh'][0]:.0f}", f"{24.0 - S['ring_kmh'][0]:.0f} km/h",
        "Ring Road speed shortfall against the survey", "2", "24.0 minus `ring_kmh` mean")
    add(sec, "ValSeeds", f"{S['n']}", f"{S['n']}", "seeds in the baseline sweep", "2", "rows `main_y0.2`")
    lo, hi = junction_ratios()
    add(sec, "ValBusyLo", f"{lo:.0f}", f"{lo:.0f}%", "lowest model/count ratio, 4 busiest junctions", "2",
        "`jica_sweep/_geh_main_y0.2_s*.csv`: model_pcu_h / observed_pcu_h per junction, mean over seeds, "
        "for Thapathali, Old Baneshwor, New Baneshwor, Kalanki")
    add(sec, "ValBusyHi", f"{hi:.0f}", f"{hi:.0f}%", "highest model/count ratio, 4 busiest junctions", "2",
        "as above")
    dk, ds = yield_shift()
    add(sec, "ValYieldKmh", f"{dk:.1f}", f"{dk:.2f} km/h", "largest shift in inner speed when give-way priority "
        "is 0.1 or 0.4 instead of 0.2", "2", "`jica_sweep_summary.csv`: |mean(`yield_0.x`) - mean(`main_y0.2`)| "
        "of `inner_kmh`, 5 seeds each")
    add(sec, "ValYieldShare", f"{ds:.0f}", f"{ds:.1f} points", "largest shift in volume share, same test", "2",
        "as above, column `share` x 100")
    add(sec, "TolledLinks", f"{tolled_links():,}", f"{tolled_links():,}", "links with a toll (delay > 0 in the "
        "untolled baseline)", "2", "`tolls_jica.csv`: rows with `observed_delay_s` > 0")

    # ---- baseline (notebook 3)
    B = J["base"]
    sec = "Baseline run"
    add(sec, "BaseComp", f"{B['completed'] * 100:.1f}\\%", f"{B['completed']:.1%}",
        "baseline trips completed in the 4 h horizon", "3", "`jica_h1h7.csv`, config `baseline`, mean of `completed`")
    add(sec, "BaseTis", f"{B['tis_s'] / 60:.0f}", f"{B['tis_s'] / 60:.0f} min",
        "baseline mean time in system", "3", "config `baseline`, mean of `tis_s` / 60")
    add(sec, "BaseVeh", f"{B['trips']:,.0f}", f"{B['trips']:,.0f}", "vehicles generated per baseline run", "3",
        "config `baseline`, `trips` (identical in every seed)")

    # ---- interventions (notebook 3)
    sec = "Interventions (time in system over all vehicles, primary)"
    for h, c, b in TESTS:
        w, t = WORD[h], J[h]
        sig = "survives" if abs(t["tis"][0]) > t["bonf"] else "does not survive"
        add(sec, f"H{w}Tis", ci(*t["tis"]), f"{t['tis'][0]:+.1f}% +/- {t['tis'][1]:.1f}%",
            f"{h} {NAME[h]}: change in time in system ({sig} Bonferroni x8)", "3",
            f"`jica_h1h7.csv`, `{c}` vs `{b}`, column `tis_s`, {pair}")
        add(sec, f"H{w}TisMag", f"{-t['tis'][0]:.1f}", f"{-t['tis'][0]:.1f}%", f"{h} reduction, magnitude", "3",
            "minus the mean above")
        add(sec, f"H{w}Delay", ci(*t["delay"]), f"{t['delay'][0]:+.1f}% +/- {t['delay'][1]:.1f}%",
            f"{h}: change in delay of completed trips (secondary)", "3", f"as above, column `delay_s`")
        add(sec, f"H{w}Comp", ci(*t["comp"], unit="~points"), f"{t['comp'][0]:+.1f} +/- {t['comp'][1]:.1f} points",
            f"{h}: change in share of trips completed", "3", "as above, column `completed` x 100, paired difference")
        add(sec, f"H{w}Neg", f"{t['neg']}", f"{t['neg']}/{t['n']}", f"{h}: seeds where time in system fell", "3",
            "count of per-seed changes < 0")
    im, ih, ineg, inn = J["inter"]
    add(sec, "Inter", ci(im, ih), f"{im:+.1f}% +/- {ih:.1f}%", "H3 interaction: combined minus both single "
        "effects, % of baseline time in system", "3", "per seed (comb - adaptive - pricing + base) / base x 100")
    add(sec, "InterNeg", f"{ineg}", f"{ineg}/{inn}", "seeds with a negative interaction", "3", "count < 0")

    # ---- projection (notebook 4)
    sec = "Demand growth to 2030 (6 h horizon, 15 paired seeds)"
    for c, w in [("baseline", "Base"), ("x1.20_4yr", "Four"), ("x1.94_2026", "TwentySix"), ("x2.32_2030", "Thirty")]:
        p = P[c]
        add(sec, f"Proj{w}Veh", f"{p['trips']:,}", f"{p['trips']:,}", f"{c}: vehicles generated", "4",
            f"`jica_projection.csv`, config `{c}`, `trips`")
        add(sec, f"Proj{w}Comp", f"{p['comp'][0]:.1f}\\%", f"{p['comp'][0]:.1f}% +/- {p['comp'][1]:.1f}",
            f"{c}: trips completed", "4", "mean of `completed` x 100")
        if p["tis"]:
            add(sec, f"Proj{w}Tis", ci(*p["tis"], d=0), f"{p['tis'][0]:+.0f}% +/- {p['tis'][1]:.0f}%",
                f"{c}: change in time in system vs baseline", "4", f"`tis_s`, {pair}")

    # ---- first version (not in the public run)
    sec = "First version (NOT from the public run)"
    for c, w in [("adaptive", "Adaptive"), ("pricing", "Pricing"), ("adaptive_pricing", "Comb")]:
        add(sec, f"Old{w}", f"{-O[c][0]:.1f}", f"{-O[c][0]:.1f}%", f"first version, {c}: cut in completed-trip "
            "delay", "v1", "`results/comparison.partial.csv` (local runs of the earlier arterial model, "
            "kept in `archive/2026-11-15_before_clean_run.zip`), paired vs `fixed_time`")
    add(sec, "OldPricingLoss", f"{1 - J['H2']['delay'][0] / O['pricing'][0]:.0%}".replace("%", "\\%"),
        f"{1 - J['H2']['delay'][0] / O['pricing'][0]:.0%}", "share of the pricing effect lost vs first version",
        "v1+3", "1 - H2 delay change / first-version pricing delay change")
    add(sec, "OldCombLoss", f"{1 - J['H3']['delay'][0] / O['adaptive_pricing'][0]:.0%}".replace("%", "\\%"),
        f"{1 - J['H3']['delay'][0] / O['adaptive_pricing'][0]:.0%}", "share of the combined effect lost",
        "v1+3", "same, H3")
    return rows


def write(rows):
    tex = ["% Generated by paper/evidence.py from results/clean/ (the public Kaggle run). Do not edit.",
           f"% Sources: {DATASET} and {KAGGLE}<notebook>", ""]
    tex += [f"\\newcommand{{\\{m}}}{{{v}}}" for _, m, v, *_ in rows]
    (ROOT / "paper" / "numbers.tex").write_text("\n".join(tex) + "\n", encoding="utf-8")

    md = ["# Claim ledger", "",
          "Every number in the paper, where it comes from, and how it is computed. Generated by "
          "`paper/evidence.py` from `results/clean/`; do not edit by hand.", "",
          "**Source of every number below, unless the section says otherwise:** one public run on Kaggle.", "",
          f"- Dataset (code, network, survey inputs): {DATASET}"]
    md += [f"- Notebook {k}, `{t}`: {KAGGLE}{t} -> {f}" for k, (t, f) in NB.items()]
    md += [f"- Notebooks 3b and 4b (seeds 9-15): {KAGGLE}3b-interventions-seeds-9-15, "
           f"{KAGGLE}4b-projection-seeds-9-15"]
    md += ["", "`tools/fetch_results.sh` downloads those outputs into `results/clean/`; the **Notebook** column "
           "names the stage that produced the file. Intervals are 95% t intervals over seeds; paired tests "
           "use the same seed in both arms, and both arms of each comparison generate the same vehicles "
           "(checked when the paper builds; H7 vs baseline removes trips by design).", ""]
    sec = None
    for s, m, _, plain, claim, nb, how in rows:
        if s != sec:
            md += ["", f"## {s}", "", "| Claim | Value | Notebook | Computed from | LaTeX macro |",
                   "|---|---|---|---|---|"]
            sec = s
        link = f"[{NB[nb][0]}]({KAGGLE}{NB[nb][0]})" if nb in NB else nb
        md.append(f"| {claim} | **{plain}** | {link} | {how} | `\\{m}` |")
    md += ["", "## Inputs taken from documents, not simulated", "",
           "| Number | Source |", "|---|---|",
           "| 24.0 km/h Ring Road, 15.3 km/h inner main roads | JICA & DoR (2012), Table 6.2.10, weekday AM travel speed survey; `data/jica2012/route_speeds_2011.csv` |",
           "| Counted peak volumes at 9 junctions | JICA & DoR (2012), appendix turning-movement diagrams; `data/jica2012/intersection_counts_2011.csv` |",
           "| 840,775 PCU/day, 9 large / 51 small zones | JICA & DoR (2012) vehicle and person trip OD tables; `data/jica_od/vtod_2011.csv`, `ptod_2011.csv` |",
           "| 58,525 PCU/h peak (peak factor 0.10), 117,050 over 2 h | computed in notebook 1 from the above |",
           "| 4.52%/yr growth; x1.94 (2026), x2.32 (2030) | JICA/DoR 2024 main-section forecast, Table 4.4.2; `scripts/build_growth_od.py` |",
           "| 472 nodes, 1,242 links, 194 side-street ways | OpenStreetMap network in the dataset, `data/jica_net/` |",
           "| 0.353 side-street capacity ratio, 60 / 30 km/h | JICA capacity and free-speed tables (6,000 / 17,000 PCU/day) |",
           "| 19.8x motorcycle growth since 1991; Tiwari et al. delays | cited literature (paper references) |",
           "", "## First-version numbers in the text that are not computed here", "",
           "Section 4.1 compares with the earlier arterial model: it carried about 64% of counted volume with a "
           "junction correlation of -0.23 (one seed) and completed 55% of trips; its published 46% used the "
           "first simulated hour. Section 4.3 cites its 10.5% decentralization advantage. These come from local "
           "runs of that model, recorded in the archived decision log (`archive/2026-11-15_before_clean_run.zip`, "
           "`lab/decisions.md`, D31-D33), and were not rerun on Kaggle."]
    (ROOT / "paper" / "claims.md").write_text("\n".join(md) + "\n", encoding="utf-8")

    # headline table between the README markers
    v = {m: plain for _, m, _, plain, *_ in rows}
    J = jica_numbers()
    verdict = lambda h: "reduces" if abs(J[h]["tis"][0]) > J[h]["bonf"] else "no reliable effect"  # noqa: E731
    lines = ["| Test | Change in time in system (15 paired seeds, 95% CI) | Verdict (Bonferroni x8) |",
             "|---|---|---|"]
    for h, _, _ in TESTS:
        lines.append(f"| {h} {NAME[h]} | {v[f'H{WORD[h]}Tis']} | {verdict(h)} |")
    lines += ["", f"- H3 interaction (combined minus both single effects): {v['Inter']}, so the two levers "
              "add up rather than reinforce each other.",
              f"- Validation: Ring Road {v['ValRing']} (survey 24.0), inner roads {v['ValInner']} (survey 15.3); "
              f"{v['ValShare']} of counted volume at 9 junctions, correlation {v['ValCorr']}.",
              f"- Demand growth: trips completed in 6 h fall from {v['ProjBaseComp'].split(' ')[0]} at 2011 demand to "
              f"{v['ProjTwentySixComp'].split(' ')[0]} at 2026 demand and {v['ProjThirtyComp'].split(' ')[0]} "
              "at 2030 demand."]
    readme = ROOT / "README.md"
    text = readme.read_text(encoding="utf-8")
    a, b = "<!-- results:start -->", "<!-- results:end -->"
    text = text[:text.index(a) + len(a)] + "\n" + "\n".join(lines) + "\n" + text[text.index(b):]
    readme.write_text(text, encoding="utf-8")
    print(f"{len(rows)} numbers -> paper/numbers.tex, paper/claims.md, README.md results table")


if __name__ == "__main__":
    write(build())
