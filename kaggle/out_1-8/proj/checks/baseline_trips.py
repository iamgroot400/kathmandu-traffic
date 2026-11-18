#!/usr/bin/env python3
"""Trips loaded by the calibrated baseline (no simulation), for 'share of trips still made'."""
import argparse, sys
from pathlib import Path
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT / "scripts"))
from run_baseline import add_model_args, build_world

ap = argparse.ArgumentParser(); add_model_args(ap)
W, _ = build_world(ap.parse_args([]), verbose=False)
n = len(W.VEHICLES) * W.DELTAN
(ROOT / "results" / "baseline_trips.csv").write_text(f"config,trips\nbaseline,{n}\n", encoding="utf-8")
print(n)
