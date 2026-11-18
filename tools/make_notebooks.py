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
