#!/usr/bin/env bash
cd /home/user/AiConsciousness
while ! grep -q "ALL DONE" logs/queue.log 2>/dev/null; do sleep 20; done
bash runq2.sh
