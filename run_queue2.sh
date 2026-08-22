#!/usr/bin/env bash
set -u
cd "$(dirname "$0")"
log() { echo "[$(date -u +%H:%M:%S)] Q2 $*" >> logs/queue.log; }
while pgrep -f "run_queue.sh" > /dev/null; do sleep 15; done
log "queue1 finished, starting queue2"

log "E3b start";  python3 experiments/e03/run_polarity.py --reps 8 --workers 11 > logs/e03b.out 2> logs/e03b.err; log "E3b done rc=$?"
log "E7 start";   python3 experiments/e07/run.py --reps 8 --workers 10 > logs/e07.out 2> logs/e07.err;  log "E7 done rc=$?"
log "E4 start";   python3 experiments/e04/run.py --items 16 --gen 12 --reps 2 --workers 8 > logs/e04.out 2> logs/e04.err; log "E4 done rc=$?"
log "QUEUE2 COMPLETE"
