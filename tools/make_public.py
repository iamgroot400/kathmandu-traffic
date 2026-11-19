#!/usr/bin/env python3
"""Build the public, self-contained package for Kaggle: public/kathmandu-traffic-sim/.

Copies only what the pipeline needs, strips internal notebook references from comments,
and fails if any internal or personal text is left. Re-run after any code change.

    python tools/make_public.py
"""
import py_compile
import re
import shutil
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
OUT = ROOT / "public" / "kathmandu-traffic-sim"

CODE = [
    "scripts/stats.py", "scripts/run_baseline.py", "scripts/signals.py", "scripts/adaptive_signals.py",
    "scripts/tidal_lanes.py", "scripts/run_pricing.py", "scripts/dump_link_volumes.py",
    "scripts/build_minor_ways.py", "scripts/build_od_jica.py", "scripts/build_growth_od.py",
    "scripts/sweep_jica_seeds.py", "scripts/compare_jica.py", "scripts/project_jica.py", "scripts/tune_counts.py", "scripts/fit_od_counts.py", "scripts/build_way_tags.py", "scripts/build_pedestrian_ways.py", "scripts/future_jica.py",
    "checks/geh_jica2012.py", "checks/speed_jica2012.py",
    # how the inputs were made (need the JICA report PDFs / internet, not run in the pipeline)
    "scripts/build_network.py", "scripts/extract_jica_ptod.py", "scripts/extract_jica_vtod.py",
    "scripts/georef_jica_zones.py",
]
DATA = [
    "data/network_nodes.csv", "data/network_links.csv",
    "data/jica_net/network_nodes.csv", "data/jica_net/network_links.csv",
    "data/jica_net/osm_way_tags.csv", "data/kathmandu_pois.json", "data/jica_net/osm_pedestrian_points.json",
    "data/jica_od/ptod_2011.csv", "data/jica_od/vtod_2011.csv", "data/jica_od/zones_2011.csv",
    "data/jica_od/geocode_cache.json",
    "data/jica2012/intersection_counts_2011.csv", "data/jica2012/route_speeds_2011.csv",
    "requirements.txt",
]
# (pattern, replacement) applied to code only
SCRUB = [
    (r" \(assumed, [DA]\d+\)", " (assumed)"),
    (r"\(D38: 2\.5-6%% of vehicles lost otherwise", "(2.5-7.5%% of vehicles are lost otherwise"),
    (r" \((?:[DAE]\d+(?: test \d+)?(?:[,;] ?(?:[DAE]\d+))*)\)", ""),
    (r"[ \t]*# ASSUME A\d+.*$", ""),
    (r",? ?the\s+volume-matched control the 2026-11-10 audit required", ", a volume-matched control"),
    (r"target for road speeds in D36;", "target for road speeds;"),
    (r"\(D36\): ", ": "),
]
FORBIDDEN = re.compile(r"\b[DAE]\d{1,2}\b|(?-i:ASSUME)|human|judge|hackathon|pitch|aashi|claude|assistant|"
                       r"[Cc]:\\\\|audit|Anthropic|lab/", re.I)


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    bad = []
    for rel in CODE:
        text = (ROOT / rel).read_text(encoding="utf-8")
        for pat, rep in SCRUB:
            text = re.sub(pat, rep, text, flags=re.M)
        dst = OUT / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        dst.write_text(text, encoding="utf-8")
        py_compile.compile(str(dst), doraise=True)
        bad += [f"{rel}:{i}: {line.strip()}" for i, line in enumerate(text.splitlines(), 1)
                if FORBIDDEN.search(line)]
    for rel in DATA:
        (OUT / rel).parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(ROOT / rel, OUT / rel)
    shutil.copy(ROOT / "public" / "README.md", OUT / "README.md")
    bad += [f"README.md:{i}: {l.strip()}" for i, l in
            enumerate((OUT / "README.md").read_text(encoding="utf-8").splitlines(), 1) if FORBIDDEN.search(l)]
    if bad:
        raise SystemExit("internal or personal text left:\n" + "\n".join(bad))
    for p in OUT.rglob("__pycache__"):
        shutil.rmtree(p)
    z = OUT.parent / "dataset" / "kathmandu-traffic-sim.zip"
    z.parent.mkdir(exist_ok=True)
    with zipfile.ZipFile(z, "w", zipfile.ZIP_DEFLATED) as f:
        for p in sorted(OUT.rglob("*")):
            if p.is_file():
                f.write(p, p.relative_to(OUT).as_posix())
    print(f"{sum(1 for p in OUT.rglob('*') if p.is_file())} files, clean -> {z} "
          f"({z.stat().st_size / 1e6:.1f} MB)")


if __name__ == "__main__":
    main()
