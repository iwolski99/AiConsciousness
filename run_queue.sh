#!/usr/bin/env bash
# Sequential experiment queue. The box saturates at ~10-12 concurrent CLI
# workers, so experiments are run one at a time rather than in parallel.
set -u
cd "$(dirname "$0")"
log() { echo "[$(date -u +%H:%M:%S)] $*" >> logs/queue.log; }

# wait for any already-running phase A
while pgrep -f "phase_a_groundtruth" > /dev/null; do sleep 10; done
log "phaseA done"

log "E1 phase B start"
python3 experiments/e01/phase_b_predict.py --reps 4 --workers 11 \
    > logs/e01_phaseB.out 2> logs/e01_phaseB.err
log "E1 phase B done rc=$?"

log "E1 phase C start"
python3 experiments/e01/phase_c_recognise.py --reps 2 --workers 11 \
    > logs/e01_phaseC.out 2> logs/e01_phaseC.err
log "E1 phase C done rc=$?"

log "E3 start"
python3 experiments/e03/run.py --reps 6 --workers 11 \
    > logs/e03.out 2> logs/e03.err
log "E3 done rc=$?"

log "E2 answers start"
python3 experiments/e02/run.py --phase answer --reps 5 --workers 11 \
    > logs/e02a.out 2> logs/e02a.err
log "E2 answers done rc=$?"

log "E2 conf start"
python3 experiments/e02/run.py --phase conf --conf-reps 3 --workers 11 \
    > logs/e02c.out 2> logs/e02c.err
log "E2 conf done rc=$?"

log "E5 behaviour start"
python3 experiments/e05/run_behaviour.py --reps 8 --workers 11 \
    > logs/e05b.out 2> logs/e05b.err
log "E5 behaviour done rc=$?"

log "E5 introspect start"
python3 experiments/e05/run_introspect.py --reps 8 --workers 11 \
    > logs/e05i.out 2> logs/e05i.err
log "E5 introspect done rc=$?"
log "QUEUE COMPLETE"
