#!/usr/bin/env python3
"""Write the public Kaggle notebooks (one folder each) into public/notebooks/.

    python tools/make_notebooks.py
Then from each folder: kaggle kernels push -p .
"""
import json
import re
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "public" / "notebooks"
USER = "aashikkhatri"
DATASET = f"{USER}/kathmandu-traffic-sim"
SLUG = {k: f"kathmandu-traffic-{k}" for k in
        ("1-build-demand", "2-baseline-and-validation", "3a-interventions-seeds-1-8",
         "3b-interventions-seeds-9-15", "4a-projection-seeds-1-8", "4b-projection-seeds-9-15",
         "5-results")}

SETUP = r'''import glob, os, shutil, subprocess, sys, zipfile

def find_project(marker):
    """Copy the project tree that contains `marker` from /kaggle/input to /kaggle/working/sim."""
    hits = sorted(glob.glob(f"/kaggle/input/**/{marker}", recursive=True),
                  key=lambda h: ("build-demand" not in h, len(h)))   # prefer step 1's copy
    if not hits:                                        # dataset delivered as a zip
        for z in glob.glob("/kaggle/input/**/*.zip", recursive=True):
            zipfile.ZipFile(z).extractall("/kaggle/working/_unzipped")
        hits = sorted(glob.glob(f"/kaggle/working/_unzipped/**/{marker}", recursive=True), key=len)
    src = hits[0][: -len(marker)].rstrip("/")
    shutil.copytree(src, "/kaggle/working/sim", dirs_exist_ok=True)
    os.chdir("/kaggle/working/sim")
    print("project from", src)

def run(*cmd, tries=1):
    """Run a script, streaming its output; retry resumable drivers if a worker is killed."""
    for attempt in range(tries):
        p = subprocess.Popen([sys.executable, "-u", *cmd], stdout=subprocess.PIPE,
                             stderr=subprocess.STDOUT, text=True)
        for line in p.stdout:
            print(line, end="")
        if p.wait() == 0:
            return
        print(f"exit code {p.returncode}, attempt {attempt + 1} of {tries}")
    raise RuntimeError(" ".join(cmd))
'''
INSTALL = "!pip install -q uxsim==1.14.2"


def md(s): return {"cell_type": "markdown", "metadata": {}, "source": s.strip()}
def code(s): return {"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": s.strip()}


NOTEBOOKS = {
"1-build-demand": ("Kathmandu traffic 1 - build demand", [DATASET], [], [
    md("""# 1. Build the demand

Builds every input the simulations need from the public dataset:

* **Side streets:** tertiary roads that are not part of the main-road network (one lane, reduced capacity).
* **Peak-hour OD matrix** from the JICA 2011 surveys: the 9-zone vehicle OD table (PCU/day) is split over the 51 person-trip zones in proportion to person trips, times a peak-hour factor of 0.10, and loaded at up to four junctions per zone.
* **Scenario variants:** morning-biased demand (tidal lanes test), decentralized destinations, and a uniform cut to the same total (its control).
* **Growth scenarios:** the base matrix grown from 2011 at 4.52%/yr (JICA/DoR 2024 forecast) by x1.20 (4.2 years, for comparison with an earlier version of the model), to 2026 (x1.94) and to the end of 2030 (x2.32), in whole platoons of five vehicles."""),
    code(SETUP + '\nfind_project("scripts/build_od_jica.py")'),
    code('''run("scripts/build_minor_ways.py")
run("scripts/build_od_jica.py", "--data", "data/jica_net")
for v in ("am", "decentralized", "uniform"):
    run("scripts/build_od_jica.py", "--data", "data/jica_net", "--variant", v)
run("scripts/build_growth_od.py")'''),
    code('''import csv
for f in sorted(glob.glob("data/jica_net/od_matrix*.csv")):
    rows = list(csv.DictReader(open(f)))
    print(f"{os.path.basename(f):<30} {len(rows):>6} pairs {sum(int(r['demand']) for r in rows):>9,} PCU/h")'''),
]),
"2-baseline-and-validation": ("Kathmandu traffic 2 - baseline and validation", [], ["1-build-demand"], [
    md("""# 2. Baseline and validation

The baseline is calibrated to one target only, the JICA 2011 weekday morning travel speeds (Ring Road 24.0 km/h, inner main roads about 15.3 km/h). The intersection counts are held out and used here only to check the result.

* 15 seeds of the baseline, plus 5 seeds each with the side streets' give-way priority at 0.1 and 0.4 (assumed 0.2).
* Two-hour steady peak; volumes are measured in the second hour, after the network has filled.
* At the end, one untolled run records each link's delay: the toll schedule for the pricing test (step 3)."""),
    code(SETUP + '\nfind_project("data/jica_net/od_matrix.csv")'),
    code(INSTALL),
    code('run("scripts/sweep_jica_seeds.py", "--jobs", "4", tries=3)'),
    code('''import pandas as pd
s = pd.read_csv("results/jica_sweep_summary.csv")
print(s.groupby("config")[["ring_kmh", "inner_kmh", "completed_pct", "share", "corr", "within_1_5", "geh_pass"]]
      .agg(["mean", "std", "count"]).round(3).T)
print("survey: Ring Road 24.0 km/h, inner main roads 15.3 km/h")'''),
    code('''run("scripts/run_pricing.py", "--data", "data/jica_net", "--minor-ways", "data/jica_net/minor_ways.txt",
    "--free-flow-kmh", "60", "--minor-free-flow-kmh", "30", "--priority-junctions",
    "--demand-scale", "1", "--pcu-factor", "1", "--demand-window", "7200", "--demand-growth", "2",
    "--tmax", "14400", "--seed", "0", "--save-tolls", "results/tolls_jica.csv")'''),
]),
}
for part, (a, b) in (("a", (1, 8)), ("b", (9, 15))):
    NOTEBOOKS[f"3{part}-interventions-seeds-{a}-{b}"] = (
        f"Kathmandu traffic 3{part} - interventions, seeds {a}-{b}", [],
        ["1-build-demand", "2-baseline-and-validation"], [
        md(f"""# 3{part}. Interventions, seeds {a} to {b}

Ten configurations on the same seeds, so every comparison is paired (split over two notebooks to fit Kaggle's session limit):

| Test | Configuration | Compared with |
|---|---|---|
| H1 | queue-actuated adaptive signals | baseline |
| H2 | congestion pricing: toll = 0.2 x each link's untolled delay (from step 2) | baseline |
| H3 | both | baseline |
| H4 | tidal lanes on morning-biased demand | same demand, no tidal lanes |
| H5 | parking enforcement proxy: free-flow speeds x35/30 | baseline |
| H6 | staggered departures: same demand over a 50% longer window | baseline |
| H7 | trips into the 10 core zones x0.75 | baseline, and a uniform cut to the same total |

Horizon 4 hours. Main measure: mean time in system over all vehicles."""),
        code(SETUP + '\nfind_project("data/jica_net/od_matrix.csv")\n'
             'tolls = glob.glob("/kaggle/input/**/results/tolls_jica.csv", recursive=True)[0]\n'
             'os.makedirs("results", exist_ok=True); shutil.copy(tolls, "results/tolls_jica.csv")\n'
             'if os.path.exists("results/jica_h1h7.partial.csv"): os.remove("results/jica_h1h7.partial.csv")'),
        code(INSTALL),
        code(f'run("scripts/compare_jica.py", "--first-seed", "{a}", "--seeds", "{b}", "--jobs", "4", tries=3)\n'
             f'shutil.copy("results/jica_h1h7.partial.csv", "/kaggle/working/interventions_seeds{a}-{b}.csv")'),
    ])
    NOTEBOOKS[f"4{part}-projection-seeds-{a}-{b}"] = (
        f"Kathmandu traffic 4{part} - projection, seeds {a}-{b}", [], ["1-build-demand"], [
        md(f"""# 4{part}. Demand growth projection, seeds {a} to {b}

The baseline demand is the 2011 survey. It is grown at 4.52%/yr, the JICA/DoR 2024 forecast for the Ring Road's main section, with no intervention, over a 6-hour horizon:

* x1.20 (4.2 years), x1.94 (2011 to 2026, about today), x2.32 (2011 to end of 2030).

Assumes peak-hour trips grow one to one with daily traffic, which is not tested. Vehicle positions are logged every 60 steps to fit memory; trip times are unaffected. Three runs at a time, since gridlocked runs need more memory."""),
        code(SETUP + '\nfind_project("data/jica_net/od_matrix.csv")\n'
             'if os.path.exists("results/jica_projection.partial.csv"): os.remove("results/jica_projection.partial.csv")'),
        code(INSTALL),
        code(f'run("scripts/project_jica.py", "--first-seed", "{a}", "--seeds", "{b}", "--jobs", "3", tries=3)\n'
             f'shutil.copy("results/jica_projection.partial.csv", "/kaggle/working/projection_seeds{a}-{b}.csv")'),
    ])

NOTEBOOKS["5-results"] = ("Kathmandu traffic 5 - results", [],
    ["2-baseline-and-validation", "3a-interventions-seeds-1-8", "3b-interventions-seeds-9-15",
     "4a-projection-seeds-1-8", "4b-projection-seeds-9-15"], [
    md("""# 5. Results

Collects the outputs of steps 2 to 4. Every intervention is compared with its control on the same 15 seeds; the tables give the mean paired change with a 95% confidence interval, and whether it survives a Bonferroni correction for the 8 tests."""),
    code('''import glob, math
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy import stats

def one(pattern):
    return sorted(glob.glob(f"/kaggle/input/**/{pattern}", recursive=True), key=len)[0]

def ci(x, conf=0.95):
    x = np.asarray(x, float)
    return x.mean(), stats.t.ppf(0.5 + conf / 2, len(x) - 1) * x.std(ddof=1) / math.sqrt(len(x))

h = pd.concat([pd.read_csv(f) for f in glob.glob("/kaggle/input/**/interventions_seeds*.csv", recursive=True)])
p = pd.concat([pd.read_csv(f) for f in glob.glob("/kaggle/input/**/projection_seeds*.csv", recursive=True)])
print(len(h), "intervention runs,", len(p), "projection runs")'''),
    md("## Validation"),
    code('''s = pd.read_csv(one("results/jica_sweep_summary.csv"))
m = s[s.config == "main_y0.2"]
for k, label in [("ring_kmh", "Ring Road km/h (survey 24.0)"), ("inner_kmh", "inner main roads km/h (survey 15.3)"),
                 ("share", "model / counted volume, 9 junctions"), ("corr", "correlation across junctions"),
                 ("within_1_5", "junctions within a factor 1.5"), ("geh_pass", "junctions with GEH < 5")]:
    mean, half = ci(m[k]); print(f"{label:<40} {mean:7.2f} +/- {half:.2f}")

geh = pd.concat([pd.read_csv(f) for f in glob.glob("/kaggle/input/**/results/jica_sweep/_geh_main_y0.2_s*.csv", recursive=True)])
r = (geh.model_pcu_h / geh.observed_pcu_h).groupby(geh.intersection).agg(["mean", "std", "count"]).sort_values("mean")
ax = r["mean"].plot.barh(xerr=r["std"] / np.sqrt(r["count"]) * 2.145, figsize=(6, 4), color="#2a5a8c")
ax.axvline(1, color="k"); ax.axvspan(1 / 1.5, 1.5, color="green", alpha=0.1)
ax.set_xlabel("model / observed peak entering volume"); plt.tight_layout(); plt.show()'''),
    md("## Interventions (H1 to H7)"),
    code('''tests = [("H1 adaptive signals", "adaptive", "baseline"), ("H2 congestion pricing", "pricing", "baseline"),
         ("H3 adaptive + pricing", "adaptive_pricing", "baseline"), ("H4 tidal lanes", "am_tidal", "am_no_tidal"),
         ("H5 parking enforcement", "parking", "baseline"), ("H6 staggered departures", "staggered", "baseline"),
         ("H7 decentralized", "decentralized", "baseline"), ("H7 vs equal uniform cut", "decentralized", "uniform_cut")]
w = {k: h.pivot(index="seed", columns="config", values=k) for k in ("tis_s", "delay_s", "completed", "trips")}
conf_b = 1 - 0.05 / len(tests)
rows = []
for name, c, b in tests:
    rel = (w["tis_s"][c] - w["tis_s"][b]) / w["tis_s"][b] * 100
    dl = (w["delay_s"][c] - w["delay_s"][b]) / w["delay_s"][b] * 100
    t, th = ci(rel); d, dh = ci(dl); cm, chh = ci((w["completed"][c] - w["completed"][b]) * 100)
    rows.append({"test": name, "time in system %": f"{t:+.1f} +/- {th:.1f}", "delay %": f"{d:+.1f} +/- {dh:.1f}",
                 "completion pts": f"{cm:+.1f} +/- {chh:.1f}", "seeds better": f"{(rel < 0).sum()}/{len(rel)}",
                 "Bonferroni": "yes" if abs(t) > ci(rel, conf_b)[1] else "no",
                 "vehicles": f"{int(w['trips'][c].iloc[0]):,} vs {int(w['trips'][b].iloc[0]):,}",
                 "_m": t, "_h": th})
res = pd.DataFrame(rows)
display(res.drop(columns=["_m", "_h"]))
x = w["tis_s"]
inter = (x.adaptive_pricing - x.adaptive - x.pricing + x.baseline) / x.baseline * 100
im, ih = ci(inter)
print(f"H3 interaction (combined minus both single effects, % of baseline): {im:+.1f} +/- {ih:.1f}")'''),
    code('''fig, ax = plt.subplots(figsize=(6, 4.5))
ax.barh(res.test, res._m, xerr=res._h, capsize=4, color=["#2a5a8c" if abs(m) > e else "#999" for m, e in zip(res._m, res._h)])
ax.axvline(0, color="k"); ax.invert_yaxis(); ax.set_xlabel("change in mean time in system (%), 15 paired seeds")
plt.tight_layout(); plt.show()'''),
    md("## Demand growth projection"),
    code('''pw = {k: p.pivot(index="seed", columns="config", values=k) for k in ("tis_s", "completed", "trips")}
for c in ["baseline", "x1.20_4yr", "x1.94_2026", "x2.32_2030"]:
    comp, ch = ci(pw["completed"][c] * 100)
    line = f"{c:<12} {int(pw['trips'][c].iloc[0]):>8,} vehicles   completed {comp:5.1f}% +/- {ch:.1f}"
    if c != "baseline":
        t, th = ci((pw["tis_s"][c] - pw["tis_s"].baseline) / pw["tis_s"].baseline * 100)
        line += f"   time in system {t:+.0f}% +/- {th:.0f}"
    print(line)'''),
])

# Count-tuning experiments: one lever per notebook, independent of steps 1-5 (they build their own
# demand from the dataset, so they always use the dataset's current code).
TUNE_NB = {
    "6a-tune-peak-demand": ("peak", "peak demand",
        "The model carries about two thirds of the counted traffic. This notebook raises the peak-hour factor "
        "(the share of daily trips made in the peak hour) from 0.10 to 0.12, 0.14 and 0.16."),
    "6b-tune-valley-gateways": ("gateways", "valley entry roads",
        "Trips from the 18 survey zones outside the network box currently enter at the nearest edge junctions, "
        "which can be side streets. Here they enter only on main roads, at 4, 2 or 1 junctions per zone."),
    "6c-tune-side-streets": ("sidestreets", "side streets",
        "Side streets carry 0.353 of a main-road lane (JICA's capacity table). Lower values keep more traffic "
        "on the main roads that pass the counted junctions: 0.25, 0.18, 0.12, and 0.25 at 20 km/h."),
    "6d-tune-loading-points": ("loading", "loading points",
        "Each zone loads at up to 4 junctions, and the 30% of trips that start and end inside one zone are "
        "left off the network. This notebook tries 8 loading junctions, and puts half or all of those "
        "inside-zone trips back on the network between the zone's own junctions."),
    # round 2: in round 1 the busy junctions' approaches were queued at 3-25x free-flow travel time,
    # each lane passing about 500-1,000 PCU/h, so their limit is junction capacity
    "7a-tune-lanes": ("lanes", "main-road lanes",
        "Round 1 showed the busy junctions' approaches queued, some with only 1-2 lanes because OpenStreetMap "
        "often has no lane count. Main roads are raised to at least 2 or 3 lanes per direction, and 2 lanes is "
        "also combined with the best entry-road setting from round 1."),
    "7b-tune-saturation-flow": ("saturation", "saturation flow",
        "Motorcycle-heavy traffic passes more PCU per lane per hour than the car-based default of one "
        "vehicle every second. The reaction time is lowered to 0.8, 0.67 and 0.5 s (up to twice the lane capacity)."),
    "7c-tune-signal-cycle": ("signals", "signal cycle",
        "Every signal runs a 90 s cycle. Here it is 60, 120 and 150 s."),
    "7d-tune-combined": ("combined", "combined levers",
        "The best entry-road setting from round 1 (outer zones on main roads, one loading junction per zone) "
        "with higher lane saturation flow and at least 2 main-road lanes."),
}
# round 3: capacity x demand, so volumes rise without roads becoming faster than the speed survey
R3 = "Round 2 showed that more junction capacity brings volumes up but leaves the roads far faster than the " \
     "speed survey. Here a capacity setting from round 2, with outer zones on main roads at one loading junction, " \
     "is combined with higher peak demand (peak-hour factor {k}), to load that capacity back to surveyed speeds."
for key, idea, what, k in (("8a-tune-rt0.8-demand", "cap_rt0.8", "0.8s + demand", "0.11, 0.12, 0.13"),
                           ("8b-tune-rt0.67-demand", "cap_rt0.67", "0.67s + demand", "0.12, 0.13, 0.14"),
                           ("8c-tune-lanes3-demand", "cap_lanes3", "3 lanes + demand", "0.11, 0.12, 0.13"),
                           ("8d-tune-rt0.5-lanes2-demand", "cap_rt0.5_lanes2", "0.5s 2 lanes demand", "0.12, 0.14, 0.16")):
    TUNE_NB[key] = (idea, what, R3.format(k=k))
TUNE_NB["9a-tune-midblock-loading"] = ("midblock", "mid-block loading",
    "Each zone loaded its trips at its highest-degree nodes, which are the big junctions themselves: about 1,860 "
    "PCU/h started or ended at each Baneshwor junction node, never passing its approach roads or its count. Here "
    "trips load at mid-block nodes (on one road, at least 50 m from any junction and 100 m from a counted one) "
    "nearest each zone's centre, with outer zones on main roads, across the best capacity and demand settings so far.")
R5 = ("Rounds 1-4 always left the Ring Road junctions (Chabahil, Gausala) and Kalimati too high and the "
      "Baneshwor / Thapathali junctions too low. A network check found why: UXsim's OpenStreetMap importer reads "
      "the `lanes` tag as lanes per direction, but on a two-way road OpenStreetMap counts both directions, so every "
      "tagged two-way road (the Ring Road among them) had twice its width, while the one-way Baneshwor and Thapathali "
      "roads were right. Here every tagged two-way road gets half its lanes per direction{extra}. The rules apply "
      "to the whole city and were fixed before any run; they do not look at the counts. Trips load at mid-block "
      "nodes as in round 4.")
TUNE_NB["10a-tune-osm-lanes"] = ("osmlanes", "two-way lane fix", R5.format(extra=""))
TUNE_NB["10b-tune-osm-lanes-friction"] = ("osmlanes_friction", "lanes + friction", R5.format(
    extra=", and the 10% of main road links with the most shops, amenities and offices within 100 m (from "
          "OpenStreetMap) get a 30 km/h free-flow speed instead of 60, for stopping buses, pedestrians and street trade"))
TUNE_NB["11a-tune-lanes-pedestrians"] = ("net6", "lanes + pedestrians",
    "Round 5's best setting still left Kalimati too high. A check of its approach roads found that they have no "
    "lane count in OpenStreetMap, so the importer gave them its generic default: 3-4 lanes per direction for a trunk "
    "road, where the tagged trunk roads of Kathmandu have a median of 2 (secondary: default 2, tagged median 1). Here "
    "untagged main roads get the median of the tagged roads of their class (trunk 2, primary 2, secondary 1). Also new: "
    "pedestrian friction on side streets and non-trunk main roads (trunk roads such as the Ring Road have footpaths "
    "and are exempt). Links within 50 m of an OpenStreetMap pedestrian street (the pedestrianised core: Basantapur, "
    "Thamel, Ason) get 15 km/h; the top 10% of the remaining links by OpenStreetMap shops, amenities and offices "
    "within 100 m along the whole link, per km, get 30 km/h. Both rules apply to the whole city, come from "
    "OpenStreetMap only, and were fixed before any run; they replace round 5's midpoint rule.")
for key, (idea, what, why) in TUNE_NB.items():
    title = f"Kathmandu traffic {key[:2]} - tuning: {what}"
    assert len(title) <= 50, title   # Kaggle limit
    SLUG[key] = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")   # Kaggle derives the URL from the title
    NOTEBOOKS[key] = (title, [DATASET], [], [
        md(f"""# {key[:2]}. Tuning to the junction counts: {what}

**Question:** which lever brings the model's junction volumes to the JICA 2011-12 counts?
**Target:** GEH < 5 at all 6 tuning junctions (Chabahil, Gausala, Kalimati, New Baneshwor, Old Baneshwor, Thapathali), on the mean volume over 5 seeds, with road speeds still near the JICA speed survey (Ring Road 24.0, inner main roads 15.3 km/h).

The other 3 counted junctions (Balaju, Kalanki, Koteshwor) were set aside by a fixed random draw before any tuning run and are not shown here; they are checked only once a configuration has been chosen.

**This notebook:** {why} Every configuration runs on seeds 1-5, next to the unchanged baseline. Volumes are measured in the second hour of a two-hour steady peak."""),
        code(SETUP + '\nfind_project("scripts/tune_counts.py")'),
        code(INSTALL),
        code('run("scripts/build_minor_ways.py")\nrun("scripts/build_od_jica.py", "--data", "data/jica_net")'),
        code(f'run("scripts/tune_counts.py", "--idea", "{idea}", "--seeds", "5", "--jobs", "3", tries=3)'),
    ])

# round 4: trips no longer start inside junctions; a junction is counted as all nodes within 100 m
KEY_9A = "9a-tune-midblock-loading"
NOTEBOOKS[KEY_9A][3][0]["source"] += (
    "\n\n**Junction measure:** OpenStreetMap draws some large junctions as several nodes, so each junction is also "
    "scored as all traffic entering the nodes within 100 m of it (fixed before rescoring any run). Both measures are printed.")
NOTEBOOKS[KEY_9A][3].append(code(f'run("scripts/tune_counts.py", "--idea", "midblock", "--summary-only", "--radius", "100")'))
for key in ("10a-tune-osm-lanes", "10b-tune-osm-lanes-friction", "11a-tune-lanes-pedestrians"):   # 100 m measure too
    NOTEBOOKS[key][3].append(code(f'run("scripts/tune_counts.py", "--idea", "{TUNE_NB[key][0]}", "--summary-only", "--radius", "100")'))
ODME = {"9b-fit-od-0.67s": ("--midblock --outer-main --k-peak 0.14", "--reaction-time 0.67",
                             "0.67 s reaction time, peak factor 0.14"),
        "9c-fit-od-3-lanes": ("--midblock --outer-main --k-peak 0.13", "--min-main-lanes 3",
                               "at least 3 main-road lanes, peak factor 0.13")}
for key, (start, cap, what) in ODME.items():
    title = f"Kathmandu traffic {key[:2]} - fit OD to counts: {cap.split()[-1]}{'s' if 'reaction' in cap else ' lanes'}"
    assert len(title) <= 50, title
    SLUG[key] = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    NOTEBOOKS[key] = (title, [DATASET], [], [
        md(f"""# {key[:2]}. Fitting origin-destination flows to the junction counts

Rounds 1-4 found settings that carry the right *total* traffic at roughly the surveyed speeds, but not the right *spatial pattern*: Kalimati stays too high and the Baneshwor / Thapathali junctions too low, whatever the global setting. This notebook adjusts the zone-to-zone flows themselves.

**Method (path-based multiplicative OD estimation):** simulate 3 seeds; at each of the 6 tuning junctions take r = counted / modelled entering volume (all nodes within 100 m); route every OD pair on the shortest path over the simulated travel times; multiply its demand by r^0.5 for every tuning junction its path enters (at most x1.5 or /1.5 per iteration); repeat up to 6 times or until all 6 pass GEH < 5.

**Start:** trips loaded at mid-block nodes (never inside a junction), outer zones on main roads, {what}.

**Caveat:** this fits the 6 tuning junctions directly, so afterwards they are calibration targets, not validation. Only the 3 held-out junctions (Balaju, Kalanki, Koteshwor), never used here, can validate the result."""),
        code(SETUP + '\nfind_project("scripts/fit_od_counts.py")'),
        code(INSTALL),
        code('run("scripts/build_minor_ways.py")\nrun("scripts/build_od_jica.py", "--data", "data/jica_net")'),
        code(f'run("scripts/fit_od_counts.py", "--start", "{start}", "--run", "{cap}", "--iterations", "6", '
             f'"--seeds", "3", "--jobs", "3", "--radius", "100", tries=3)'),
        code('import pandas as pd\nprint(pd.read_csv("results/odme/log.csv").to_string(index=False))'),
    ])

# round 6 OD fitting: as 9b/9c, but the total is held at the survey total (round 4 ran away by adding trips
# to saturated junctions), on the corrected networks
LANES5 = "--osm-way-tags data/jica_net/osm_way_tags.csv"
ODME6 = {"11b-fit-od-round6": ("round-6 network", LANES5 + " --untagged-lanes trunk=2,primary=2,secondary=1 "
                               "--pedestrian-friction data/jica_net/osm_pedestrian_points.json --reaction-time 0.5",
                               "round 6's network rules (two-way lane fix, untagged lanes by class, pedestrian friction)"),
         "11c-fit-od-round5": ("round-5 network", LANES5 + " --friction-kmh 30 --friction-share 0.10 --reaction-time 0.5",
                               "round 5's best network (two-way lane fix, roadside friction)")}
for key, (short, cap, what) in ODME6.items():
    title = f"Kathmandu traffic {key[:2]} - fit OD, {short}"
    assert len(title) <= 50, title
    SLUG[key] = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    NOTEBOOKS[key] = (title, [DATASET], [], [
        md(f"""# {key[:2]}. Fitting origin-destination flows to the junction counts, fixed total

Round 4 fitted the zone-to-zone flows to the 6 tuning junctions and diverged: each step added trips on paths into the Baneshwor junctions, which were already saturated, so queues grew instead of counts. Since then two network errors were found and fixed (two-way roads at double width; untagged roads at generic widths). This notebook repeats the fit on the corrected network, and **keeps the total demand at the survey total**: trips move between origin-destination pairs, none are added overall.

**Method:** simulate 3 seeds; at each tuning junction r = counted / modelled entering volume (all nodes within 100 m); route every pair on simulated travel times; multiply its demand by r^0.5 for every tuning junction its path enters (at most x1.5 or /1.5 per iteration); rescale to the starting total; up to 6 iterations or until all 6 pass GEH < 5.

**Network:** {what}; 0.5 s reaction time. **Start:** mid-block loading, outer zones on main roads, peak factor 0.14.

**Caveat:** this fits the 6 tuning junctions directly, so afterwards they are calibration targets, not validation. Only the 3 held-out junctions (Balaju, Kalanki, Koteshwor), never used here, can validate the result."""),
        code(SETUP + '\nfind_project("scripts/fit_od_counts.py")'),
        code(INSTALL),
        code('run("scripts/build_minor_ways.py")\nrun("scripts/build_od_jica.py", "--data", "data/jica_net")'),
        code(f'run("scripts/fit_od_counts.py", "--start", "--midblock --outer-main --k-peak 0.14", "--run", "{cap}", '
             f'"--iterations", "6", "--seeds", "3", "--jobs", "3", "--radius", "100", "--fixed-total", tries=3)'),
        code('import pandas as pd\nprint(pd.read_csv("results/odme/log.csv").to_string(index=False))'),
    ])

# future demand: do the interventions still work in 2026 and 2030? Published model, as notebooks 3-4; the
# new runner script comes from the dataset, the demand and tolls from notebooks 1 and 2
for key, levels, what in (("12a-future-2026", ("2011", "2026"), "2026 demand (x1.94), with the 2011 reference"),
                          ("12b-future-2030", ("2030",), "2030 demand (x2.32)")):
    title = f"Kathmandu traffic {key[:3]} - interventions at {key[-4:]}"
    assert len(title) <= 50, title
    SLUG[key] = re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-")
    NOTEBOOKS[key] = (title, [DATASET], ["1-build-demand", "2-baseline-and-validation"], [
        md(f"""# {key[:3]}. Do the interventions still work at future demand? {what}

The intervention results (H1-H7) were measured at 2011 demand. The projection (notebooks 4a-4b) showed that at grown demand most trips no longer finish within 6 hours. This notebook runs the strongest interventions at that grown demand, on the published model, each paired by seed with the no-intervention run at the same demand:

| Arm | What |
|---|---|
| baseline | no intervention |
| adaptive | queue-actuated signals (H1) |
| adaptive_pricing | signals + tolls (H3; the 2011 toll schedule, not re-derived for future congestion) |
| staggered | the same demand over a 50% longer window (H6) |
| all | signals + tolls + staggered departures |

Demand grown at 4.52%/yr (JICA/DoR 2024 forecast): x1.94 for 2026, x2.32 for 2030. Horizon 6 hours. 6 seeds.

**Criterion, fixed before any run:** an arm *solves* a demand level if its completion within 6 hours is at least the 2011 baseline's and its mean time in system is no worse than the 2011 baseline's (2011 reference run in notebook 12a)."""),
        code(SETUP + '\nfind_project("data/jica_net/od_matrix.csv")\n'
             'tolls = glob.glob("/kaggle/input/**/results/tolls_jica.csv", recursive=True)[0]\n'
             'os.makedirs("results", exist_ok=True); shutil.copy(tolls, "results/tolls_jica.csv")\n'
             'shutil.copy(glob.glob("/kaggle/input/**/scripts/future_jica.py", recursive=True)[0], "scripts/future_jica.py")\n'
             'if os.path.exists("results/jica_future.partial.csv"): os.remove("results/jica_future.partial.csv")'),
        code(INSTALL),
        code("\n".join(f'run("scripts/future_jica.py", "--level", "{lv}", "--first-seed", "1", "--seeds", "6", '
                       f'"--jobs", "3", tries=3)' for lv in levels) +
             f'\nshutil.copy("results/jica_future.partial.csv", "/kaggle/working/future_{key[-4:]}.csv")'),
        code('run("scripts/future_jica.py", "--summary-only")'),
    ])

FORBIDDEN = re.compile(r"\b[DAE]\d{1,2}\b|(?-i:ASSUME)|human|judge|hackathon|pitch|claude|assistant|audit|Anthropic", re.I)


def main() -> None:
    for key, (title, datasets, kernels, cells) in NOTEBOOKS.items():
        text = json.dumps([c["source"] for c in cells]) + title
        assert not FORBIDDEN.search(text), (key, FORBIDDEN.search(text).group(0))
        d = OUT / key
        d.mkdir(parents=True, exist_ok=True)
        nb = {"cells": cells, "metadata": {"kernelspec": {"name": "python3", "display_name": "Python 3",
              "language": "python"}, "language_info": {"name": "python"}}, "nbformat": 4, "nbformat_minor": 5}
        (d / "notebook.ipynb").write_text(json.dumps(nb, indent=1), encoding="utf-8")
        meta = {"id": f"{USER}/{SLUG[key]}", "title": title, "code_file": "notebook.ipynb",
                "language": "python", "kernel_type": "notebook", "is_private": False,
                "enable_gpu": False, "enable_tpu": False, "enable_internet": True,
                "dataset_sources": datasets, "competition_sources": [],
                "kernel_sources": [f"{USER}/{SLUG[k]}" for k in kernels]}
        (d / "kernel-metadata.json").write_text(json.dumps(meta, indent=1), encoding="utf-8")
        print(f"{key:<30} {len(cells)} cells, inputs: {datasets + kernels}")


if __name__ == "__main__":
    main()
