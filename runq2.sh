#!/usr/bin/env bash
set -u
cd /home/user/AiConsciousness
L=logs/queue.log
step(){ n=$1; shift; echo "[$(date -u +%H:%M:%S)] START $n" >> $L; "$@"; echo "[$(date -u +%H:%M:%S)] END $n rc=$?" >> $L; }
step e01D  python3 experiments/e01/phase_d_labels.py --reps 4 --workers 11 >logs/e01_phaseD.out 2>logs/e01_phaseD.err
step e01C2 python3 experiments/e01/phase_c2_named.py --reps 1 --workers 11 >logs/e01_phaseC2.out 2>logs/e01_phaseC2.err
echo "[$(date -u +%H:%M:%S)] Q2 DONE" >> $L
