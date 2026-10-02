#!/usr/bin/env bash
cd /home/user/AiConsciousness
python3 experiments/e05/run_behaviour.py --reps 5 --workers 10 >logs/e05b.out 2>logs/e05b.err || { echo "BEHAV FAILED rc=$?" >> logs/e5.status; exit 1; }
python3 experiments/e05/run_introspect.py --reps 5 --workers 10 >logs/e05i.out 2>logs/e05i.err || { echo "INTRO FAILED rc=$?" >> logs/e5.status; exit 1; }
echo "E5 DONE" >> logs/e5.status
