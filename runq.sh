#!/usr/bin/env bash
set -u
cd /home/user/AiConsciousness
L=logs/queue.log
step(){ n=$1; shift; echo "[$(date -u +%H:%M:%S)] START $n" >> $L; "$@"; echo "[$(date -u +%H:%M:%S)] END $n rc=$?" >> $L; }
step e03  python3 experiments/e03/run.py --reps 6 --workers 9 >logs/e03.out 2>logs/e03.err
step e03b python3 experiments/e03/run_polarity.py --reps 8 --workers 9 >logs/e03b.out 2>logs/e03b.err
step e03c python3 experiments/e03/run_context.py --reps 10 --workers 9 >logs/e03c.out 2>logs/e03c.err
step e05b python3 experiments/e05/run_behaviour.py --reps 8 --workers 9 >logs/e05b.out 2>logs/e05b.err
step e05i python3 experiments/e05/run_introspect.py --reps 8 --workers 9 >logs/e05i.out 2>logs/e05i.err
step e01D python3 experiments/e01/phase_d_labels.py --reps 4 --workers 9 >logs/e01_phaseD.out 2>logs/e01_phaseD.err
step e01C2 python3 experiments/e01/phase_c2_named.py --reps 1 --workers 9 >logs/e01_phaseC2.out 2>logs/e01_phaseC2.err
step e02a python3 experiments/e02/run.py --phase answer --reps 5 --workers 9 >logs/e02a.out 2>logs/e02a.err
step e02c python3 experiments/e02/run.py --phase conf --conf-reps 3 --workers 9 >logs/e02c.out 2>logs/e02c.err
step e07  python3 experiments/e07/run.py --reps 8 --workers 8 >logs/e07.out 2>logs/e07.err
step e04  python3 experiments/e04/run.py --items 16 --gen 12 --reps 2 --workers 8 >logs/e04.out 2>logs/e04.err
echo "[$(date -u +%H:%M:%S)] ALL DONE" >> $L
