#!/usr/bin/env bash
# Idempotent: (re)start the experiment queue if it is not running.
# The container is suspended between sessions, which kills background jobs;
# every experiment is cached, so restarting is cheap and resumes where it left off.
cd /home/user/AiConsciousness
if pgrep -f "bash runq.sh" >/dev/null 2>&1; then echo "queue already running"; exit 0; fi
if grep -q "ALL DONE" logs/queue.log 2>/dev/null; then echo "queue complete"; exit 0; fi
setsid nohup bash runq.sh >/dev/null 2>&1 </dev/null &
echo "queue restarted"
