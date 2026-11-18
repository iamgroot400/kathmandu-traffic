#!/usr/bin/env bash
# Download the public Kaggle run's outputs into results/clean/, the only folder the paper reads.
# Every number in the paper, paper/claims.md and paper/numbers.tex comes from these files.
#   bash tools/fetch_results.sh        (needs the Kaggle CLI in .venv and a Kaggle API token)
set -e
cd "$(dirname "$0")/.."
K="$PWD/.venv/Scripts/kaggle"; [ -x "$K" ] || K=kaggle
U=aashikkhatri
OUT=results/clean
TMP=$(mktemp -d)
get() { "$K" kernels output "$U/kathmandu-traffic-$1" -p "$TMP/$1" --file-pattern "$2" >/dev/null; }

get 2-baseline-and-validation 'jica_sweep_summary|_geh_main|_geh_yield|tolls_jica'
get 3a-interventions-seeds-1-8 'jica_h1h7'
get 3b-interventions-seeds-9-15 'jica_h1h7'
get 4a-projection-seeds-1-8 'projection_seeds'
get 4b-projection-seeds-9-15 'projection_seeds'

mkdir -p "$OUT/jica_sweep"
cp "$TMP"/2-baseline-and-validation/sim/results/jica_sweep_summary.csv "$OUT/"
cp "$TMP"/2-baseline-and-validation/sim/results/tolls_jica.csv "$OUT/"
cp "$TMP"/2-baseline-and-validation/sim/results/jica_sweep/_geh_*.csv "$OUT/jica_sweep/"
# the two halves of a stage share one header; keep the first
cat_csv() { head -1 "$1" > "$3"; tail -n +2 "$1" >> "$3"; tail -n +2 "$2" >> "$3"; }
cat_csv "$TMP"/3a-*/sim/results/jica_h1h7.partial.csv "$TMP"/3b-*/sim/results/jica_h1h7.partial.csv "$OUT/jica_h1h7.csv"
cat_csv "$TMP"/4a-*/projection_seeds1-8.csv "$TMP"/4b-*/projection_seeds9-15.csv "$OUT/jica_projection.csv"
rm -rf "$TMP"
echo "results/clean: $(($(wc -l < "$OUT/jica_h1h7.csv") - 1)) intervention runs, $(($(wc -l < "$OUT/jica_projection.csv") - 1)) projection runs, $(ls "$OUT"/jica_sweep | wc -l) validation files"
