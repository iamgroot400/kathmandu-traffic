#!/usr/bin/env python3
"""Confirms the baseline ('fixed_time' in comparison.partial.csv, 'baseline' in
extra.partial.csv) reproduces bit-for-bit for the same seed across two independently
run scripts (compare.py, compare_extra.py) - a basic determinism/reproducibility
check recommended by stats-review before trusting any comparison built on it.
"""
import csv

main = {int(r['seed']): r for r in csv.DictReader(open('results/comparison.partial.csv', encoding='utf-8')) if r['config'] == 'fixed_time'}
extra = {int(r['seed']): r for r in csv.DictReader(open('results/extra.partial.csv', encoding='utf-8')) if r['config'] == 'baseline'}
shared = sorted(set(main) & set(extra))
mismatches = [s for s in shared if abs(float(main[s]['delay_s']) - float(extra[s]['delay_s'])) > 0.01]
assert not mismatches, f"baseline reproducibility failed at seeds {mismatches}"
print(f"baseline reproduces bit-for-bit across {len(shared)} shared seeds between compare.py and compare_extra.py")
