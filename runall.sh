#!/usr/bin/env bash
# Every step is idempotent (results cached by content hash). If the account's
# usage limit is hit, the runner raises and this script stops at that step;
# re-running later resumes from exactly there.
set -u
cd /home/user/AiConsciousness
L=logs/queue.log
step(){ n=$1; shift; echo "[$(date -u +%H:%M:%S)] START $n" >> $L; "$@"; rc=$?; echo "[$(date -u +%H:%M:%S)] END $n rc=$rc" >> $L; if [ $rc -ne 0 ]; then echo "[$(date -u +%H:%M:%S)] STOPPING (rc=$rc)" >> $L; exit $rc; fi; }
step e03c  python3 experiments/e03/run_context.py --reps 10 --workers 8 >logs/e03c.out 2>logs/e03c.err
step e03d  python3 experiments/e03/run_tiers.py --reps 8 --workers 8 >logs/e03d.out 2>logs/e03d.err
step e05b  python3 experiments/e05/run_behaviour.py --reps 8 --workers 8 >logs/e05b.out 2>logs/e05b.err
step e05i  python3 experiments/e05/run_introspect.py --reps 8 --workers 8 >logs/e05i.out 2>logs/e05i.err
step e08   python3 experiments/e08/run.py --reps 8 --workers 8 >logs/e08.out 2>logs/e08.err
step e02a  python3 experiments/e02/run.py --phase answer --reps 5 --workers 8 >logs/e02a.out 2>logs/e02a.err
step e02c  python3 experiments/e02/run.py --phase conf --conf-reps 3 --workers 8 >logs/e02c.out 2>logs/e02c.err
step e01D  python3 experiments/e01/phase_d_labels.py --reps 4 --workers 8 >logs/e01_phaseD.out 2>logs/e01_phaseD.err
step e01C2 python3 experiments/e01/phase_c2_named.py --reps 1 --workers 8 >logs/e01_phaseC2.out 2>logs/e01_phaseC2.err
step e04   python3 experiments/e04/run.py --items 16 --gen 12 --reps 2 --workers 7 >logs/e04.out 2>logs/e04.err
step e07 python3 experiments/e07/run.py --reps 14 --workers 7 >logs/e07.out 2>logs/e07.err
echo "[$(date -u +%H:%M:%S)] ALL DONE" >> $L
