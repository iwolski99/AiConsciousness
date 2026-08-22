"""A pool of long-lived `claude` processes.

Spawning a CLI process costs ~6 CPU-seconds, which caps throughput at roughly
0.6 calls/s on this 4-core box. Instead we keep N processes alive in
`--input-format stream-json` mode and reset the conversation between queries
with `/clear`.

Context-equivalence caveat (verified, see LOG.md 2026-08-22): a query issued
after `/clear` sees ~104 extra tokens that a query in a fresh process does not
(a `<local-command-caveat>` block plus the `/clear` command echo). We therefore
*always* burn one warm-up query + `/clear` when a worker starts, so that every
measured query in a pooled experiment sees exactly the same context. The extra
block is constant across all conditions within an experiment.
"""
from __future__ import annotations

import json, os, queue, subprocess, threading, time, uuid
from pathlib import Path
from typing import Any

CLI_BASE = [
    "claude", "-p", "--verbose",
    "--input-format", "stream-json",
    "--output-format", "stream-json",
    "--tools", "",
    "--strict-mcp-config",
    "--setting-sources", "",
    "--no-session-persistence",
]


class Worker:
    def __init__(self, model: str, system: str, thinking: int, cwd: Path):
        self.model, self.system, self.thinking, self.cwd = model, system, thinking, cwd
        self.proc: subprocess.Popen | None = None
        self.lock = threading.Lock()
        self.n = 0
        self._start()

    def _start(self) -> None:
        env = dict(os.environ)
        env["MAX_THINKING_TOKENS"] = str(int(self.thinking))
        cmd = CLI_BASE + ["--model", self.model, "--system-prompt", self.system,
                          "--session-id", str(uuid.uuid4())]
        self.proc = subprocess.Popen(cmd, stdin=subprocess.PIPE,
                                     stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                     text=True, bufsize=1, cwd=str(self.cwd), env=env)
        self.n = 0
        self._send("warmup")           # burn-in so every real query looks alike
        self._read_result()
        self._send("/clear")
        self._read_result()

    def _send(self, text: str) -> None:
        assert self.proc and self.proc.stdin
        self.proc.stdin.write(json.dumps(
            {"type": "user",
             "message": {"role": "user", "content": [{"type": "text", "text": text}]}}) + "\n")
        self.proc.stdin.flush()

    def _read_result(self, timeout: float = 300.0) -> dict | None:
        assert self.proc and self.proc.stdout
        deadline = time.time() + timeout
        events: list[dict] = []
        while time.time() < deadline:
            line = self.proc.stdout.readline()
            if not line:
                return None
            line = line.strip()
            if not line:
                continue
            try:
                e = json.loads(line)
            except json.JSONDecodeError:
                continue
            events.append(e)
            if e.get("type") == "result":
                e["_events"] = events
                return e
        return None

    def ask(self, prompt: str) -> dict | None:
        with self.lock:
            try:
                self._send(prompt)
                res = self._read_result()
            except (BrokenPipeError, OSError):
                res = None
            if res is None:
                self.close()
                self._start()
                return None
            try:
                self._send("/clear")
                self._read_result(timeout=60)
            except (BrokenPipeError, OSError):
                self.close(); self._start()
            self.n += 1
            # recycle occasionally to bound memory growth
            if self.n >= 200:
                self.close(); self._start()
            return res

    def close(self) -> None:
        if self.proc:
            try:
                self.proc.stdin.close()
            except Exception:
                pass
            try:
                self.proc.terminate(); self.proc.wait(timeout=10)
            except Exception:
                try: self.proc.kill()
                except Exception: pass
        self.proc = None


class Pool:
    """One pool per (model, system, thinking) configuration."""

    def __init__(self, model: str, system: str, thinking: int, size: int, cwd: Path):
        cwd.mkdir(parents=True, exist_ok=True)
        self.workers = [Worker(model, system, thinking, cwd) for _ in range(size)]
        self.q: queue.Queue[Worker] = queue.Queue()
        for w in self.workers:
            self.q.put(w)

    def ask(self, prompt: str, retries: int = 2) -> dict | None:
        for _ in range(retries + 1):
            w = self.q.get()
            try:
                res = w.ask(prompt)
            finally:
                self.q.put(w)
            if res is not None and not res.get("is_error"):
                return res
            time.sleep(1.0)
        return None

    def close(self) -> None:
        for w in self.workers:
            w.close()
