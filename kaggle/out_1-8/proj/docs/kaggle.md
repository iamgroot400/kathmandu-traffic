# Running the simulations on Kaggle, step by step

Kaggle's free CPU notebooks give about 30 GB RAM and 4 CPU cores, with a 12-hour limit
per session. One simulation needs 4-5 GB, so 4 run side by side there (1 on the home PC).

## 0. One-time setup

1. Sign up at kaggle.com.
2. Verify your phone number: profile picture > Settings > Phone Verification.
   Without it, notebooks have no internet and pip cannot install packages.

## 1. Upload the project bundle

The bundle is `kaggle/kathmandu_sim.zip` (1 MB): scripts, checks, network and demand data,
existing results. No environments, PDFs or videos.

1. kaggle.com > **Create** (top left) > **New Dataset**.
2. Drag in `kathmandu_sim.zip`. Title: `kathmandu-sim`. Keep it **Private**.
3. Click **Create**. Kaggle unzips it automatically.

## 2. Create the notebook

1. Open the dataset page > **New Notebook** (top right).
2. Right-hand panel > **Session options**:
   - **Accelerator: None.** UXsim runs on the CPU, so a GPU only uses up your quota.
   - **Internet: On.**
   - **Persistence: Files only** (keeps `/kaggle/working` between sessions).

## 3. Cells to paste (one per cell, run in order)

**Cell 1, copy the project and install** (about 2 minutes):
```
!cp -r /kaggle/input/kathmandu-sim/* /kaggle/working/
%cd /kaggle/working
!ls
!pip install -q uxsim==1.14.2 networkx osmnx
!python -c "import uxsim; print('uxsim', uxsim.__version__)"
```
Check that `ls` shows `scripts checks data results`. If the dataset folder has a different
name, look under **Input** in the right-hand panel and fix the path.

**Cell 2, check the machine:**
```
!nproc && free -g
```
You should see 4 CPUs and about 30 GB. Use `--jobs` = memory in GB / 5, rounded down (4 here).

**Cell 3, the seed sweep** (25 runs; about 2-3 hours at 4 at a time):
```
!python -u scripts/sweep_jica_seeds.py --jobs 4
```
Progress prints one line per finished run, for example
`[3/25] main_y0.2_s2.csv: ... speed 16.1 km/h, completed 79.5%`.
The summary prints at the end.

## 4. Save the results before the session ends

Kaggle deletes running sessions after 12 hours, or after about 20 minutes idle in a
browser tab you closed. To keep the files:

```
!cd /kaggle/working && zip -qr sweep_results.zip results/jica_sweep results/jica_sweep_summary.csv && ls -lh sweep_results.zip
```
Then right-hand panel > **Output** (`/kaggle/working`) > `sweep_results.zip` > **Download**.

If a session is cut off: start a new one, run Cell 1 again, upload the results zip as a
new dataset (or copy back `results/jica_sweep/`), and run Cell 3 again. Finished runs are
skipped, so it carries on where it stopped.

## 5. Bring the results home

Unzip `sweep_results.zip` into the project folder (`C:\Users\aashi\kathmandu-traffic`),
replacing `results/jica_sweep/`. Then on the PC:
```
.venv/Scripts/python.exe scripts/sweep_jica_seeds.py --summary-only
```

## H1-H7 on the new baseline (D37): 150 runs, about 6-8 hours

Bundle: `kaggle/kathmandu_sim_h1h7.zip`. Upload it as a **new** dataset (e.g. `kathmandu-h1h7`),
open a new notebook on it (Accelerator None, Internet On), then:

**Cell 1, find and copy the project:**
```
import glob, os, shutil
hits = glob.glob('/kaggle/input/**/scripts/compare_jica.py', recursive=True)
print(hits)
src = os.path.dirname(os.path.dirname(hits[0]))
shutil.copytree(src, '/kaggle/working', dirs_exist_ok=True)
os.chdir('/kaggle/working'); print(os.listdir('.'))
```
**Cell 2, install:**
```
!pip install -q uxsim==1.14.2 networkx osmnx
```
**Cell 3, run:**
```
!python -u scripts/compare_jica.py --seeds 15 --jobs 4
```
One line per finished run; the H1-H7 summary prints at the end. Seeds run in order (all
10 configurations of seed 1, then seed 2, ...), so a cut-off session still leaves complete
pairs.

**Cell 4, save (any time, and at the end):**
```
!cp results/jica_h1h7.partial.csv /kaggle/working/jica_h1h7_results.csv && ls -lh jica_h1h7_results.csv
```
Download `jica_h1h7_results.csv` from Output > /kaggle/working (refresh the panel first).

**If the session is cut off:** start a new session, run Cells 1-2, upload the downloaded
`jica_h1h7_results.csv` (Add Input > Upload), copy it to
`/kaggle/working/results/jica_h1h7.partial.csv`, and run Cell 3 again. Finished runs are skipped.

## Optional: the paused follow-up queue (62 runs)

Same notebook, after the sweep:
```
!python -u scripts/compare_followups.py --seeds 15 --jobs 4
```
It resumes from `results/followups.partial.csv`. Download that file afterwards.

## If something goes wrong

| Message | Fix |
|---|---|
| `Killed` or a run `FAILED` with no Python error | out of memory: use `--jobs 3` |
| `No such file or directory: scripts/...` | Cell 1 path is wrong; check the Input panel name |
| `pip` cannot connect | Internet is off, or the phone is not verified |
| Session ended mid-run | rerun Cells 1 and 3; finished runs are kept if you saved them |
