#!/usr/bin/env bash
# Push the public notebooks in dependency order; stop at the first failure.
#   bash tools/run_chain.sh
cd "$(dirname "$0")/.." || exit 1
K="$PWD/.venv/Scripts/kaggle"
U=aashikkhatri
NB="$PWD/public/notebooks"

status() { "$K" kernels status "$U/kathmandu-traffic-$1" 2>&1 | tail -1; }
push() { (cd "$NB/$1" && "$K" kernels push -p . 2>&1 | tail -1); echo "$(date +%H:%M) pushed $1"; }
wait_for() {   # wait until every named notebook is COMPLETE; exit on ERROR/CANCEL
  while true; do
    local pending=0
    for k in "$@"; do
      s=$(status "$k")
      case "$s" in
        *COMPLETE*) ;;
        *ERROR*|*CANCEL*) echo "$(date +%H:%M) FAILED $k: $s"; exit 1 ;;
        *RUNNING*|*QUEUED*) pending=1 ;;
        *) pending=1; echo "$(date +%H:%M) status unclear for $k (network?): ${s:0:120}" ;;
      esac
    done
    [ $pending = 0 ] && { echo "$(date +%H:%M) complete: $*"; return; }
    sleep 300
  done
}

until "$K" datasets status "$U/kathmandu-traffic-sim" 2>&1 | grep -q ready; do sleep 30; done
push 1-build-demand;                 sleep 60; wait_for 1-build-demand
push 2-baseline-and-validation
push 4a-projection-seeds-1-8
push 4b-projection-seeds-9-15;       sleep 60; wait_for 2-baseline-and-validation
push 3a-interventions-seeds-1-8
push 3b-interventions-seeds-9-15;    sleep 60
wait_for 3a-interventions-seeds-1-8 3b-interventions-seeds-9-15 4a-projection-seeds-1-8 4b-projection-seeds-9-15
push 5-results;                      sleep 60; wait_for 5-results
echo "$(date +%H:%M) ALL DONE"
