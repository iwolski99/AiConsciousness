#!/usr/bin/env bash
cd /home/user/AiConsciousness
if pgrep -f "bash runall.sh" >/dev/null 2>&1; then echo "queue already running"; exit 0; fi
if tail -1 logs/queue.log 2>/dev/null | grep -q "ALL DONE"; then echo "queue complete"; exit 0; fi
setsid nohup bash runall.sh >/dev/null 2>&1 </dev/null &
echo "queue restarted"
