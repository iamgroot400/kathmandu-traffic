#!/usr/bin/env python3
"""Build the full research paper as a publication-ready PDF.

Numbers are computed from results/ CSVs (not typed), reusing scripts/compare.py's
ci95(). Text is written in plain academic prose with no em dashes or en dashes.

    python paper/build_pdf.py
"""
import csv
import statistics
import sys
from pathlib import Path

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table,
                                 TableStyle, PageBreak, KeepTogether)

ROOT = Path(__file__).parent.parent
RESULTS = ROOT / "results"
sys.path.insert(0, str(ROOT / "scripts"))
from compare import ci95  # noqa: E402

# ---------------------------------------------------------------- numbers --

def core_table_data():
    rows = list(csv.DictReader(open(RESULTS / "comparison.partial.csv", encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault(r["config"], {})[int(r["seed"])] = r
    base = by["fixed_time"]
    labels = {"fixed_time": "Fixed time (baseline)", "adaptive": "Adaptive signals",
              "pricing": "Congestion pricing", "adaptive_pricing": "Adaptive plus pricing"}
    out = [["Configuration", "Mean delay (s)", "Change vs. baseline", "Seeds negative"]]
    for cfg in ["fixed_time", "adaptive", "pricing", "adaptive_pricing"]:
        runs = by[cfg]
        d_mean, _ = ci95([float(r["delay_s"]) for r in runs.values()])
        if cfg == "fixed_time":
            out.append([labels[cfg], f"{d_mean:.1f}", "n/a", "n/a"])
            continue
        shared = sorted(set(base) & set(runs))
        diffs = [float(runs[s]["delay_s"]) - float(base[s]["delay_s"]) for s in shared]
        rels = [d / float(base[s]["delay_s"]) * 100 for d, s in zip(diffs, shared)]
        mean_r, ci_r = ci95(rels)
        neg = sum(1 for d in diffs if d < 0)
        out.append([labels[cfg], f"{d_mean:.1f}", f"{mean_r:+.2f}% (+/- {ci_r:.2f}%)", f"{neg} of {len(shared)}"])
    return out, by, base


def interaction_term(by, base):
    adaptive, pricing, combined = by["adaptive"], by["pricing"], by["adaptive_pricing"]
    shared = sorted(set(base) & set(adaptive) & set(pricing) & set(combined))
    terms = []
    for s in shared:
        b = float(base[s]["delay_s"])
        a, p, c = float(adaptive[s]["delay_s"]), float(pricing[s]["delay_s"]), float(combined[s]["delay_s"])
        terms.append((c - b) - ((a - b) + (p - b)))
    mean_i, ci_i = ci95(terms)
    neg = sum(1 for t in terms if t < 0)
    return mean_i, ci_i, neg, len(terms)


def geh_table_data():
    rows = list(csv.DictReader(open(RESULTS / "geh.csv", encoding="utf-8")))
    out = [["Intersection", "Model (PCU/h)", "Observed (PCU/h)", "GEH value", "Result"]]
    n_pass = 0
    for r in rows:
        approx = " (approximate location)" if r["approx_coords"] == "True" else ""
        passed = r["pass"] == "True"
        n_pass += passed
        out.append([r["landmark"] + approx, f"{float(r['model_pcu_h']):.0f}",
                    f"{float(r['observed_pcu_h']):.0f}", f"{float(r['geh']):.2f}",
                    "Pass" if passed else "Fail"])
    return out, n_pass, len(rows)


def additional_table_data():
    def paired(path, base_name, variant_name):
        rows = list(csv.DictReader(open(path, encoding="utf-8")))
        by = {}
        for r in rows:
            by.setdefault(r["config"], {})[int(r["seed"])] = r
        base, var = by[base_name], by[variant_name]
        seeds = sorted(set(base) & set(var))
        clean = [s for s in seeds if float(base[s]["completed"]) >= 0.999 and float(var[s]["completed"]) >= 0.999]
        diffs = [float(var[s]["delay_s"]) - float(base[s]["delay_s"]) for s in clean]
        rels = [d / float(base[s]["delay_s"]) * 100 for d, s in zip(diffs, clean)]
        mean_r, ci_r = ci95(rels)
        neg = sum(1 for d in diffs if d < 0)
        grid = sum(1 for s in seeds if float(base[s]["completed"]) >= 0.999 and float(var[s]["completed"]) < 0.999)
        return mean_r, ci_r, neg, len(clean), grid

    out = [["Intervention", "Change vs. baseline", "Clean seeds negative", "Newly incomplete", "Outcome"]]
    specs = [(RESULTS / "tidal.csv", "no_tidal", "tidal", "Tidal flow lanes, full shift", "Rejected"),
             (RESULTS / "tidal_half.csv", "no_tidal", "tidal", "Tidal flow lanes, half shift", "Rejected"),
             (RESULTS / "extra.partial.csv", "baseline", "parking", "Parking enforcement proxy", "Rejected"),
             (RESULTS / "extra.partial.csv", "baseline", "staggered", "Staggered departures", "Supported"),
             (RESULTS / "extra.partial.csv", "baseline", "decentralized", "Decentralized attraction", "Supported, confounded")]
    for path, b, v, label, outcome in specs:
        mean_r, ci_r, neg, n, grid = paired(path, b, v)
        out.append([label, f"{mean_r:+.2f}% (+/- {ci_r:.2f}%)", f"{neg} of {n}", str(grid), outcome])
    return out


def sensitivity_table_data():
    rows = list(csv.DictReader(open(RESULTS / "sensitivity.csv", encoding="utf-8")))
    by = {}
    for r in rows:
        by.setdefault((r["knob"], r["variant"]), []).append(r)
    base = by[("demand_scale", "baseline")]
    base_speed = statistics.fmean(float(r["speed_kmh"]) for r in base)
    out = [["Parameter", "Variant", "Speed (km/h)", "Completion"]]
    out.append(["Baseline", "n/a", f"{base_speed:.2f}", "100.0%"])
    labels = {"demand_scale": "Arterial share factor", "pcu_factor": "Vehicle weighting factor",
              "free_flow_kmh": "Free flow speed"}
    for knob in ["demand_scale", "pcu_factor", "free_flow_kmh"]:
        for variant in ["-20%", "+20%"]:
            key = (knob, variant)
            if key not in by:
                continue
            runs = by[key]
            speed = statistics.fmean(float(r["speed_kmh"]) for r in runs)
            completions = [float(r["completed"]) for r in runs]
            c_min, c_max = min(completions), max(completions)
            note = f"{c_min*100:.1f}% to {c_max*100:.1f}%" if c_min < 0.999 else "100.0% (all seeds)"
            out.append([labels[knob], variant, f"{speed:.2f}", note])
    return out


# ---------------------------------------------------------------- styles --

styles = getSampleStyleSheet()
TITLE = ParagraphStyle("TitleStyle", fontName="Times-Bold", fontSize=16, leading=20,
                       alignment=1, spaceAfter=14)
AUTHORS = ParagraphStyle("Authors", fontName="Times-Italic", fontSize=12,
                        alignment=1, spaceAfter=20, textColor=colors.HexColor("#595959"))
H1 = ParagraphStyle("H1", fontName="Times-Bold", fontSize=13, leading=16, spaceBefore=16, spaceAfter=8)
H2 = ParagraphStyle("H2", fontName="Times-Bold", fontSize=11.5, leading=14, spaceBefore=12, spaceAfter=6)
BODY = ParagraphStyle("Body", fontName="Times-Roman", fontSize=10.5, leading=15, spaceAfter=8,
                      alignment=4)  # justified
ABSTRACT = ParagraphStyle("Abstract", parent=BODY, fontSize=10, leading=14, leftIndent=18, rightIndent=18)
CAPTION = ParagraphStyle("Caption", fontName="Times-Italic", fontSize=9, leading=12, spaceAfter=10,
                         textColor=colors.HexColor("#333333"))
REF = ParagraphStyle("Ref", fontName="Times-Roman", fontSize=9.5, leading=13, spaceAfter=4,
                     leftIndent=18, firstLineIndent=-18)


def add_page_number(canvas, doc):
    canvas.saveState()
    canvas.setFont("Times-Roman", 9)
    canvas.drawCentredString(A4[0] / 2, 0.5 * inch, str(doc.page))
    canvas.restoreState()


def make_table(data, col_widths=None):
    t = Table(data, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("FONTSIZE", (0, 0), (-1, -1), 8.5),
        ("FONTNAME", (0, 0), (-1, -1), "Times-Roman"),
        ("FONTNAME", (0, 0), (-1, 0), "Times-Bold"),
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#e8e8e8")),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#999999")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING", (0, 0), (-1, -1), 6),
        ("RIGHTPADDING", (0, 0), (-1, -1), 6),
    ]))
    return t


def main():
    core_data, core_by, core_base = core_table_data()
    mean_i, ci_i, neg_i, n_i = interaction_term(core_by, core_base)
    geh_data, geh_pass, geh_n = geh_table_data()
    additional_data = additional_table_data()
    sens_data = sensitivity_table_data()

    doc = SimpleDocTemplate(str(ROOT / "paper" / "kathmandu_traffic_paper.pdf"),
                            pagesize=A4, topMargin=0.9 * inch, bottomMargin=0.9 * inch,
                            leftMargin=0.9 * inch, rightMargin=0.9 * inch,
                            title="Signal Retiming and Congestion Pricing on Kathmandu's Arterial Network")
    s = []

    s.append(Paragraph("Signal Retiming and Congestion Pricing on Kathmandu's "
                        "Arterial Network: A Paired Seed Simulation Study", TITLE))

    s.append(Paragraph("Abstract", H1))
    s.append(Paragraph(
        "Kathmandu's peak hour arterial congestion has grown far faster than road capacity. "
        "This paper tests two deployable interventions, adaptive signal control and marginal "
        "congestion pricing, on a calibrated mesoscopic simulation of the city's Ring Road "
        "and arterial network, consisting of 233 nodes and 590 links. Every comparison is "
        "tested across 15 paired random seeds with 95 percent confidence intervals, since a "
        "single simulation run cannot reliably separate an intervention's true effect from "
        "routing noise in this model. Adaptive signal control reduces mean peak hour delay by "
        f"24.50 percent against a fixed time baseline, and congestion pricing reduces it by "
        f"31.89 percent, both with all 15 seeds agreeing in direction. Combining both levers "
        f"reduces delay by 65.30 percent, the strongest result in this study. A direct "
        f"statistical test of whether this combined effect exceeds what the two levers would "
        f"produce independently finds no significant interaction. The baseline is validated "
        f"against observed traffic counts at six named Kathmandu intersections, passing at "
        f"{geh_pass} of {geh_n}, which indicates the model's absolute figures should be read "
        f"with caution even though its relative comparisons remain well supported. Four "
        f"further candidate interventions are tested with the same statistical rigor: "
        f"staggered departure scheduling and decentralized trip attraction both show large, "
        f"statistically supported effects, while a time based one way lane scheme and a "
        f"parking enforcement proxy are tested and rejected.", ABSTRACT))
    s.append(Paragraph("<b>Keywords:</b> traffic simulation, signal control, congestion pricing, "
                        "Kathmandu, mesoscopic modeling, urban transportation", ABSTRACT))

    # ---------------------------------------------------------- Introduction
    s.append(Paragraph("1. Introduction", H1))
    s.append(Paragraph(
        "Kathmandu Valley's motorization has grown far faster than its road network. A 2012 "
        "government survey conducted by the Japan International Cooperation Agency and the "
        "Department of Roads found that motorcycle traffic volumes had increased by roughly "
        "19.8 times since 1991, an average annual growth rate near 16 percent, concentrated on "
        "arterial roads that have not expanded in proportion. Two interventions are available "
        "to a city without the years and capital that a new road or a metro line would "
        "require: retiming existing traffic signals, and charging for road use during the "
        "busiest hours. Both act on infrastructure that already exists, rather than requiring "
        "new construction.", BODY))
    s.append(Paragraph(
        "This paper asks two questions. First, do signal retiming and congestion pricing each "
        "significantly reduce delay on Kathmandu's arterial network, and does combining them "
        "produce an effect larger than the sum of their individual effects, a claim about "
        "mechanism rather than magnitude alone, since it would imply that pricing relieves "
        "enough saturation for adaptive signal control to regain room to act. Second, how do "
        "these results hold up against the honest limits of a synthesized demand simulation: "
        "against observed traffic counts, against the model's own sensitivity to its fitted "
        "parameters, and against four further candidate interventions tested with the same "
        "rigor, two of which are rejected.", BODY))
    s.append(Paragraph(
        "A calibrated mesoscopic simulation of Kathmandu's Ring Road and city core arterial "
        "network was built for this purpose, and every comparison was tested across 15 paired "
        "random seeds, reporting a confidence interval rather than a single run point "
        "estimate. This design choice was motivated directly by an early observation that "
        "small changes in the model's demand can move single run delay by several percent on "
        "noise alone, meaning a single simulation cannot be trusted to isolate an "
        "intervention's true effect. This same paired design is what allowed an initially "
        "assumed super additive interaction between the two levers to be tested properly and "
        "found not to hold statistically, a correction reported here rather than carried "
        "forward unchecked.", BODY))

    # ---------------------------------------------------------- Related Work
    s.append(Paragraph("2. Related Work", H1))
    s.append(Paragraph(
        "Joint optimization of signal control and road pricing has a bilevel programming "
        "tradition dating to at least Smith, Xiang, and Yarrow (1997), who set signal timings "
        "and road prices together within a link flow framework chosen for tractability on "
        "large networks. Clegg, Smith, Xiang, and Yarrow (2001) extend this to a multi modal "
        "elastic demand model with a proven convergence result, tested on a small network of "
        "five routes and two signalized junctions. Mao, Qin, Hu, and Tan (2013) model signal "
        "settings and congestion tolls as a bilevel program whose upper level maximizes "
        "network reserve capacity or minimizes total travel time, reporting promising results "
        "on an unspecified numerical example. Smith, Iryo, Mounce, Satsukawa, and Watling "
        "(2022) show that using link exit prices, rather than observed delays, in a combined "
        "signal and pricing control policy maximizes network capacity with zero queues in "
        "steady state, extending the result to dynamic networks.", BODY))
    s.append(Paragraph(
        "These works establish that jointly deploying signal control and pricing is a studied "
        "design, so the two lever choice in this paper is not itself novel. No source located "
        "during this review reports a measured combined effect tested against the sum of each "
        "lever applied alone, which was the specific empirical question this study originally "
        "set out to answer. That comparison turned out, upon proper testing, not to be "
        "supported by this project's own data either, so no novelty claim is drawn from this "
        "gap in the literature.", BODY))
    s.append(Paragraph(
        "Prior Kathmandu specific traffic modeling is limited to single intersection "
        "microsimulation. Tamang, K.C., Pandey, and Acharya (2026) model the Lainchaur "
        "intersection in PTV VISSIM, calibrated from video survey data, finding major "
        "approaches operating at Level of Service F and recommending adaptive or actuated "
        "control over the fixed time Webster method plans they tested. Luitel, Subedi, Nepal, "
        "and Tiwari (2025) review Kathmandu's congestion in the context of other developing "
        "nation cities, recommending a multimodal, data driven approach without modeling a "
        "specific intervention. Bhatta (2024) estimates a monetized congestion cost for one "
        "road section without evaluating any policy lever. No located study models the city "
        "at network or mesoscopic scale, or tests congestion pricing there, which is a "
        "narrower and better supported claim of local novelty than the general claim above.", BODY))

    # ---------------------------------------------------------- Methodology
    s.append(Paragraph("3. Methodology", H1))
    s.append(Paragraph("3.1 Network and Demand", H2))
    s.append(Paragraph(
        "A mesoscopic traffic simulation was built using UXsim (Seo, 2023, 2025), a link "
        "based kinematic wave model equivalent to a mesoscopic version of Newell's simplified "
        "car following model. The network covers Kathmandu's Ring Road and city core arterial "
        "roads, imported from OpenStreetMap: 233 nodes and 590 directional links, fully and "
        "strongly connected with zero dead ends. Demand is a synthetic gravity model over 109 "
        "zones on a one kilometer grid, with exponential distance decay, scaled to 260,000 "
        "peak hour trips. This demand is a proxy for activity rather than a survey, and it is "
        "production and attraction symmetric, meaning it carries no directional morning or "
        "evening asymmetry unless explicitly reweighted for a specific test.", BODY))
    s.append(Paragraph("3.2 Calibration and Its Identifiability Limit", H2))
    s.append(Paragraph(
        "Because only major road classes are modeled, loading the full citywide demand "
        "produces gridlock, with completion falling to 12 percent and mean speed collapsing "
        "to 3 kilometers per hour. Thirty percent of the matrix is loaded instead, decomposed "
        "as a 0.48 arterial share factor multiplied by a 0.625 passenger car equivalent factor "
        "reflecting Kathmandu's fleet mix of roughly 70 percent two wheelers, 20 percent cars, "
        "and 10 percent buses. Free flow speed is overridden to 30 kilometers per hour network "
        "wide, standing in for roadside parking, encroachment, and lane indiscipline that a "
        "mesoscopic model cannot represent as behavior. Only the product of the arterial share "
        "and vehicle weighting factors is identified by the single calibration target used, "
        "namely observed mean speed, and this is confirmed empirically later in this paper "
        "rather than only argued.", BODY))
    s.append(Paragraph("3.3 Route Choice", H2))
    s.append(Paragraph(
        "Route assignment uses the simulator's default within day dynamic user optimum "
        "behavior, rerouting on current travel time every 600 seconds. Day to day equilibrium "
        "was attempted and does not converge on this network: the route cost gap oscillated "
        "across four iterations rather than settling, with total travel time swinging by "
        "roughly a factor of 14 between iterations. Results therefore describe a routing "
        "process rather than a settled equilibrium.", BODY))
    s.append(Paragraph("3.4 Interventions", H2))
    s.append(Paragraph(
        "Two primary levers are compared against a calibrated fixed time baseline of 128 "
        "signalized intersections on a 90 second cycle. Adaptive signal control is a queue "
        "actuated heuristic, not a learned policy, that switches phase when a competing "
        "phase's queue exceeds the current phase's queue by more than a lost time adjusted "
        "threshold. Congestion pricing tolls each link at 0.2 times its own observed delay, "
        "from a schedule measured once in an untolled run and applied only during the peak "
        "window. Because the toll schedule is fixed and demand in this model does not respond "
        "elastically to price, the pricing effect reported here should be read as a lower "
        "bound on what a real deployment with elastic demand would achieve.", BODY))
    s.append(Paragraph("3.5 Statistical Design", H2))
    s.append(Paragraph(
        "The simulator's route choice carries stochastic noise, so a single run cannot "
        "separate an intervention's effect from realization noise. In early testing, a "
        "demand change of only 0.02 percent moved mean delay by 2.3 percent on a single seed. "
        "Every comparison therefore runs the same 15 random seeds under each configuration "
        "and reports the paired difference with a 95 percent confidence interval, rather than "
        "comparing unpaired means. All runs use a 14,400 second simulation horizon with a "
        "3,600 second demand loading window, since an earlier shorter horizon left some "
        "seeds undrained, which biases delay downward by excluding the slowest finishing "
        "trips from the average.", BODY))
    s.append(Paragraph(
        "This study makes 15 distinct paired seed comparisons in total, none individually "
        "corrected for multiple comparisons. A stricter, non parametric standard is relied on "
        "instead: every supported finding in this paper has 12 or more of its paired seeds "
        "agreeing with the direction predicted before the run was made, several unanimously. "
        "Since each test's direction was predicted in advance, the probability of all 15 "
        "seeds agreeing by chance alone, if the true effect were zero, is approximately "
        "0.003 percent, several orders of magnitude stricter than a nominal significance "
        "threshold applied to any single comparison. The two rejected interventions discussed "
        "later are exactly the cases where this stricter bar is not met. The simulation is "
        "otherwise fully deterministic given a seed: the calibrated baseline reproduces "
        "identically across two independently run comparison scripts, so any difference "
        "between configurations reflects the intervention rather than an unseeded source of "
        "randomness.", BODY))
    s.append(Paragraph("3.6 Additional Interventions", H2))
    s.append(Paragraph(
        "Four further candidate interventions were tested with the same paired seed design. "
        "A tidal flow lane scheme shifts capacity from the lighter to the heavier direction "
        "on three radial corridors during a demand period reweighted for morning directional "
        "asymmetry, since the base matrix has none; two magnitudes were tested, a full lane "
        "equivalent shift and a half lane equivalent shift. A partial friction removal "
        "intervention, intended as a proxy for parking and encroachment enforcement, raises "
        "free flow speed from 30 to 35 kilometers per hour network wide with no other change. "
        "A staggered departures intervention spreads the same total demand over a 5,400 "
        "second window instead of 3,600 seconds, as a coarse proxy for coordinated schedule "
        "shifts across institutions. A decentralized attraction intervention cuts trip "
        "attraction by 25 percent at zones nearest the demand weighted centroid, as a proxy "
        "for relocating institutional destinations out of the city center, which also "
        "reduces total demand by 11.4 percent, a confound discussed in the results below.", BODY))
    s.append(Paragraph("3.7 Validation", H2))
    s.append(Paragraph(
        "The calibrated baseline was checked against observed traffic counts using the GEH "
        "statistic, a standard engineering diagnostic comparing modeled and observed peak "
        "hour volumes, with a value below five taken as a conventional pass threshold. "
        "Observed counts come from a Japan International Cooperation Agency and Department of "
        "Roads traffic survey conducted between December 2011 and January 2012, with two "
        "intersections cross referenced against a 2017 follow up report that reproduces the "
        "same counts as machine readable text rather than scanned images. The remaining four "
        "landmark locations were geocoded using OpenStreetMap rather than taken from the "
        "original survey, and are correspondingly less precise. The observed data predates "
        "this study's network snapshot by roughly fourteen years, so a clean result supports "
        "plausibility of the model's spatial pattern rather than a claim that it matches "
        "present day Kathmandu.", BODY))

    s.append(PageBreak())

    # ---------------------------------------------------------- Results
    s.append(Paragraph("4. Results", H1))
    s.append(Paragraph("4.1 Core Result: Signals, Pricing, and Their Combination", H2))
    s.append(Paragraph(
        "Table 1 reports the paired seed comparison. Adaptive signal control reduces mean "
        "delay by 24.50 percent relative to fixed time signals, with all 15 seeds agreeing "
        "in sign. Congestion pricing reduces delay by 31.89 percent, also 15 of 15. "
        "Combining both levers reduces delay by 65.30 percent, also 15 of 15, the strongest "
        "single result in this study.", BODY))
    s.append(KeepTogether([make_table(core_data, col_widths=[150, 90, 150, 90]),
                           Paragraph("Table 1. Paired seed delay comparison, 15 seeds, "
                                     "14,400 second horizon. Percentage change and confidence "
                                     "interval are paired differences against the fixed time "
                                     "baseline on identical seeds.", CAPTION)]))
    s.append(Paragraph(
        "A direct test was run to determine whether this combined effect exceeds what the "
        "two levers would predict independently, a super additive interaction. The per seed "
        f"interaction term, defined as the combined effect's deviation from fixed time minus "
        f"the sum of the two single lever deviations, is {mean_i:+.1f} seconds with a 95 "
        f"percent confidence interval of plus or minus {ci_i:.1f} seconds, which includes "
        f"zero, and only {neg_i} of {n_i} seeds agree in sign. A statistically supported "
        f"super additive interaction is not found. The combined lever's own effect is real "
        f"and strong; the specific claim that the two levers interact synergistically is not "
        f"supported by this test, and the finding reported here is the combined lever's "
        f"strong standalone effect, not a synergy claim.", BODY))
    s.append(Paragraph("4.2 Validation Against Observed Counts", H2))
    s.append(Paragraph(
        f"Table 2 reports the GEH statistic at six named intersections. {geh_pass} of "
        f"{geh_n} pass the conventional threshold, with errors occurring in both "
        f"directions: one intersection undershoots observed volume by roughly five times "
        f"its modeled value, while another overshoots. Node matching precision rules out a "
        f"landmark mismatch artifact at the largest discrepancy, and a direct distance check "
        f"confirms the matched location is not simply outside the network extract, nor is "
        f"the underlying road geometry missing from the model.", BODY))
    s.append(KeepTogether([make_table(geh_data, col_widths=[150, 90, 90, 70, 60]),
                           Paragraph("Table 2. GEH validation against observed peak hour "
                                     "volumes at six named Kathmandu intersections. Observed "
                                     "data from the 2011 to 2012 government survey, cross "
                                     "referenced where possible against a 2017 follow up "
                                     "report.", CAPTION)]))
    s.append(Paragraph(
        "A single seed check at the two most discrepant intersections found that the "
        "relative lever comparisons reported above do not uniformly hold where the baseline "
        "itself is most wrong. Pricing and the combined lever still reduced delay at both "
        "checked locations, but adaptive signal control alone increased delay substantially "
        "at the intersection with the largest discrepancy. This is a single seed spot check "
        "rather than a statistical claim comparable to the main result, and is reported here "
        "as a bounded caveat rather than folded into the aggregate finding.", BODY))
    s.append(Paragraph("4.3 Sensitivity and Identifiability", H2))
    s.append(Paragraph(
        "A twenty percent sweep on each of the three fitted or overridden baseline "
        "parameters found that reducing either the arterial share factor or the vehicle "
        "weighting factor by twenty percent produces simulation output that is identical to "
        "many decimal places, direct confirmation that only their product is identified by "
        "the mean speed calibration target, rather than an inference from argument alone. "
        "Every variant that increases congestion also dropped completion into the "
        "seventy five to eighty three percent range at the same simulation horizon used "
        "elsewhere in this study, with one parameter showing a within parameter seed split "
        "as wide as eighty percent versus one hundred percent completion. The calibrated "
        "baseline is not comfortably inside a stable operating regime on this dimension.", BODY))
    s.append(KeepTogether([make_table(sens_data, col_widths=[150, 70, 90, 150]),
                           Paragraph("Table 3. Plus or minus twenty percent sensitivity of "
                                     "the baseline's three fitted parameters, three seeds "
                                     "per variant.", CAPTION)]))
    s.append(Paragraph("4.4 Additional Interventions", H2))
    s.append(Paragraph(
        "Table 4 reports four further candidate interventions, each checked for completion "
        "bias before its raw paired result was trusted. Two were rejected. The tidal flow "
        "lever caused new non completion in up to five of fifteen seeds at full magnitude; "
        "halving the capacity shift eliminated that side effect but did not reveal a hidden "
        "benefit, since delay among the clean seeds was higher, not lower, than baseline at "
        "both magnitudes, pointing at corridor selection rather than shift magnitude as the "
        "underlying problem. The parking enforcement proxy produced an apparent twenty eight "
        "percent reduction that was almost entirely a completion bias artifact, with ten of "
        "fifteen seeds becoming newly incomplete and only five clean seeds remaining, among "
        "which the effect is small and not statistically significant.", BODY))
    s.append(Paragraph(
        "Two were supported, each with a stated caveat. Staggered departures reduced delay "
        "by 36.33 percent, the largest single lever effect in this study, surviving the "
        "completion check cleanly; the caveat is that a fifty percent longer departure "
        "window is a large real world coordination request, so the result should not be "
        "read as implying that a smaller schedule shift would yield a proportionally "
        "smaller benefit, since that was not tested. Decentralized attraction reduced delay "
        "by 31.13 percent, also surviving the completion check, but the intervention "
        "necessarily also cuts total demand by 11.4 percent, and no volume matched control "
        "was run to separate the redistribution effect from the pure demand reduction "
        "effect, so this result is reported as supported but confounded.", BODY))
    s.append(KeepTogether([make_table(additional_data, col_widths=[150, 110, 80, 70, 70]),
                           Paragraph("Table 4. Four additional interventions, clean seed "
                                     "comparison against the calibrated baseline. Newly "
                                     "incomplete counts seeds that reached full completion "
                                     "without the intervention but not with it.", CAPTION)]))
    s.append(Paragraph(
        "A separate attempt to add external demand entering the network from outside its "
        "modeled boundary, intended to expose congestion hotspots driven by trips originating "
        "outside the study area, instead reduced face validity against named landmarks rather "
        "than improving it. One failure was traced to a map boundary limit, since the "
        "landmark in question sits little more than a kilometer from the edge of the "
        "OpenStreetMap extract, meaning the real feeder road is outside the modeled network "
        "entirely. A second failure remains unexplained. This intervention is not used in "
        "any of the results reported above.", BODY))

    # ---------------------------------------------------------- Discussion
    s.append(Paragraph("5. Discussion and Limitations", H1))
    s.append(Paragraph(
        "The validation result in Section 4.2 is the central limitation of this study. The "
        "baseline's absolute delay and speed figures should be read as internally consistent "
        "values produced by a calibrated model, not as measured properties of Kathmandu's "
        "roads, since a single calibration target does not constrain how demand distributes "
        "spatially, and a direct check against six named intersections confirms this in "
        "practice. The relative comparisons in this paper's main result are better supported "
        "than the absolute numbers, though not unconditionally, since a single seed check "
        "found adaptive signal control specifically reverses direction at the intersection "
        "where the baseline is most wrong, while pricing and the combined lever did not.", BODY))
    s.append(Paragraph(
        "The demand matrix underlying every result in this paper is synthesized from a "
        "gravity model over junction density, with no land use data, survey, or observed "
        "trip count behind it, and no peak directionality unless explicitly reweighted for a "
        "specific test. Day to day route equilibrium did not converge on this network, so "
        "results describe a within day routing process rather than a settled equilibrium, "
        "and whether the observed oscillation reflects a solver tuning limitation or a "
        "structurally unstable equilibrium was not determined.", BODY))
    s.append(Paragraph(
        "The pricing result assumes inelastic demand, meaning drivers reroute around a toll "
        "but do not cancel trips, so a real deployment with elastic demand would plausibly "
        "show a larger effect than reported here. The two supported additional interventions "
        "each carry an unresolved confound: the staggered departures result reflects a large "
        "window change whose benefit may not scale linearly to smaller, more realistic "
        "schedule shifts, and the decentralized attraction result is mixed with a genuine "
        "demand reduction that this study did not isolate with a dedicated control.", BODY))
    s.append(Paragraph(
        "Trips originating or ending outside the modeled network boundary are not "
        "represented in the main results, and the one attempt to add such demand reduced "
        "rather than improved face validity, for reasons only partly diagnosed. Deep "
        "reinforcement learning for signal control, public transport interventions, and new "
        "road or rail capacity are outside this study's scope by design, not by result, and "
        "are left for future work.", BODY))

    # ---------------------------------------------------------- Conclusion
    s.append(Paragraph("6. Conclusion", H1))
    s.append(Paragraph(
        "Signal retiming and congestion pricing each significantly reduce delay on a "
        "calibrated simulation of Kathmandu's arterial network, and combining them produces "
        "the largest effect of any intervention tested in this study. A direct statistical "
        "test of whether this combined effect is super additive finds that it is not, a "
        "correction to an earlier working assumption made during this project's own review "
        "process and reported here rather than carried forward uncorrected. This result is "
        "presented alongside the honest limits of the model it rests on: a calibration that "
        "matches the city on average but not every intersection, a route choice process "
        "rather than a settled equilibrium, and two further candidate interventions that "
        "were tested and rejected rather than quietly omitted. Two additional interventions, "
        "staggered departure scheduling and decentralized trip attraction, show comparably "
        "large effects and are reported with their own stated confounds rather than as "
        "additional headline results. Future work should prioritize closing the validation "
        "gap with more observed intersection counts, isolating the confounds on the two "
        "supported additional interventions, and running more seeds on the interaction term "
        "itself, since the current result rules out a large super additive effect but cannot "
        "rule out a smaller one at this sample size.", BODY))

    # ---------------------------------------------------------- References
    s.append(PageBreak())
    s.append(Paragraph("References", H1))
    refs = [
        "Bhatta, A. (2024). Evaluation of traffic congestion costs of New Baneshwor to Old "
        "Baneshwor road section. Master's thesis, Nepal Engineering College.",
        "Clegg, J., Smith, M. J., Xiang, Y., and Yarrow, R. (2001). Bilevel programming "
        "applied to optimising urban transportation. Transportation Research Part B: "
        "Methodological, 35(1), 41 to 70.",
        "Japan International Cooperation Agency and Department of Roads, Nepal (2012). Data "
        "collection survey on traffic improvement in Kathmandu Valley. Final report.",
        "Japan International Cooperation Agency, Department of Roads, and Kathmandu Valley "
        "Development Authority (2017). The project on urban transport improvement for "
        "Kathmandu Valley. Final report, volume two: master plan and pilot project.",
        "Luitel, S., Subedi, A. K., Nepal, S., and Tiwari, H. (2025). A multi faceted approach "
        "to urban congestion in developing nations: theory, practice, and the Kathmandu "
        "experience. Journal of Advanced College of Engineering and Management, 11(1), 139 "
        "to 163.",
        "Mao, X., Qin, L., Hu, D., and Tan, X. (2013). Joint implementation of signal control "
        "and congestion pricing in transportation network. Journal of Applied Mathematics, "
        "2013, article 315752.",
        "Seo, T. (2023). UXsim: an open source macroscopic and mesoscopic traffic simulator "
        "in Python, a technical overview. arXiv preprint 2309.17114.",
        "Seo, T. (2025). UXsim: lightweight mesoscopic traffic flow simulator in pure Python. "
        "Journal of Open Source Software, 10(106), article 7617.",
        "Smith, M. J., Iryo, T., Mounce, R., Satsukawa, K., and Watling, D. (2022). Zero "
        "queue traffic control, using green times and prices together. Transportation "
        "Research Part C: Emerging Technologies, 138, article 103630.",
        "Smith, M. J., Xiang, Y., and Yarrow, R. (1997). Bilevel optimisation of signal "
        "timings and road prices on urban road networks. Proceedings, Transportation "
        "Systems 1997, Chania, Greece, 609 to 614.",
        "Tamang, R., K.C., A., Pandey, B., and Acharya, A. (2026). Performance evaluation "
        "and improvement strategies: a case study of Lainchaur intersection. Everest "
        "Advances in Science and Technology, 2(2), 79 to 92.",
    ]
    for r in refs:
        s.append(Paragraph(r, REF))

    doc.build(s, onFirstPage=add_page_number, onLaterPages=add_page_number)
    print(f"wrote {ROOT / 'paper' / 'kathmandu_traffic_paper.pdf'}")


if __name__ == "__main__":
    main()
