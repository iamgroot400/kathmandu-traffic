#!/usr/bin/env python3
"""H6 rerun with --platoon-fix on both arms (D39). Built for Kaggle.

D37's staggered arm created 108,340 vehicles against the baseline's 114,090 (UXsim drops a
pair's last platoon to float error, more often over the longer window), so H6's "same total
demand" was not met. Here both arms create exactly 117,050. Everything else as D37
(horizon 14400 s, seeds 1-15). Reuses project_jica's resumable run loop and summary.

    python scripts/rerun_h6.py --seeds 15 --jobs 4
"""
from pathlib import Path

import project_jica as p

p.CONFIGS = {"baseline": {"platoon_fix": True},
             "staggered": {"platoon_fix": True, "demand_window": 10800}}
p.OUT = Path(__file__).parent.parent / "results" / "jica_h6_fix.partial.csv"

if __name__ == "__main__":
    p.main()
