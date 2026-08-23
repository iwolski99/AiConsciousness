"""
Minimal, auditable harness for querying frontier models through the local
`claude` CLI in a *clean* configuration (no agent system prompt, no tools, no
project settings, no session persistence).

Design goals
------------
1. Reproducibility: every call is hashed on (model, system, messages, params)
   and cached to disk as JSONL. Re-running an experiment is free and gives
   identical data unless `fresh=True`.
2. Auditability: raw CLI output is stored verbatim, including thinking blocks
   and token usage, so any analysis can be re-derived from `data/raw`.
3. Honesty about confounds: `KNOWN_CONTEXT_CONTAMINATION` documents the two
   system-reminder blocks the CLI injects into every request. They are constant
   across conditions and therefore cannot produce a between-condition effect,
   but they are not nothing and are recorded here.
"""
from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
import threading
import time
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Iterable, Sequence

ROOT = Path(__file__).resolve().parent.parent
RAW = ROOT / "data" / "raw"
RAW.mkdir(parents=True, exist_ok=True)

KNOWN_CONTEXT_CONTAMINATION = [
    "<system-reminder><total_tokens>... tokens left</system-reminder>",
    "<system-reminder> userEmail / currentDate block </system-reminder>",
]

# Model registry. `tag` is what we use in filenames and plots.
MODELS: dict[str, str] = {
    "haiku45": "claude-haiku-4-5-20251001",
    "sonnet5": "claude-sonnet-5",
    "opus5":   "claude-opus-5",
    "fable5":  "claude-fable-5",
}

DEFAULT_SYSTEM = "You are a helpful assistant."

_print_lock = threading.Lock()
_cost_lock = threading.Lock()
_total_cost = [0.0]
_ncalls = [0]
_fail_streak = [0]


def total_cost() -> float:
    return _total_cost[0]


def ncalls() -> int:
    return _ncalls[0]


@dataclass
class Response:
    ok: bool
    text: str
    thinking: str
    model: str
    system: str
    messages: list[dict]
    usage: dict = field(default_factory=dict)
    cost_usd: float = 0.0
    error: str = ""
    key: str = ""
    raw_events: list[dict] = field(default_factory=list)

    def to_json(self) -> dict:
        d = asdict(self)
        d.pop("raw_events", None)
        return d


def _key(model: str, system: str, messages: Sequence[dict], effort: str | None,
         salt: str, thinking: int) -> str:
    blob = json.dumps(
        {"m": model, "s": system, "msgs": list(messages), "e": effort,
         "salt": salt, "th": thinking},
        sort_keys=True, ensure_ascii=False,
    )
    return hashlib.sha256(blob.encode()).hexdigest()[:24]


class Cache:
    """Append-only JSONL cache, one file per experiment."""

    def __init__(self, name: str):
        self.path = RAW / f"{name}.jsonl"
        self.lock = threading.Lock()
        self.mem: dict[str, dict] = {}
        if self.path.exists():
            with self.path.open() as f:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        rec = json.loads(line)
                    except json.JSONDecodeError:
                        continue
                    if rec.get("ok"):
                        self.mem[rec["key"]] = rec

    def get(self, k: str) -> dict | None:
        return self.mem.get(k)

    def put(self, rec: dict) -> None:
        with self.lock:
            if rec.get("ok"):
                self.mem[rec["key"]] = rec
            with self.path.open("a") as f:
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")


def _run_cli(model: str, system: str, messages: Sequence[dict],
             effort: str | None, timeout: int, thinking: int
             ) -> tuple[bool, str, str, dict, float, str, list]:
    """Execute one CLI call. `messages` is a list of {role, content} with roles
    'user' only (the CLI regenerates assistant turns; see LOG.md 2026-08-22)."""
    sid = str(uuid.uuid4())
    cmd = [
        "claude", "-p", "--verbose",
        "--input-format", "stream-json",
        "--output-format", "stream-json",
        "--model", model,
        "--system-prompt", system,
        "--tools", "",
        "--strict-mcp-config",
        "--setting-sources", "",
        "--no-session-persistence",
        "--session-id", sid,
        "--disable-slash-commands",
    ]
    if effort:
        cmd += ["--effort", effort]

    stdin_lines = []
    for m in messages:
        if m["role"] != "user":
            raise ValueError("only user turns can be supplied via stream-json")
        stdin_lines.append(json.dumps({
            "type": "user",
            "message": {"role": "user",
                        "content": [{"type": "text", "text": m["content"]}]},
        }))
    stdin_data = "\n".join(stdin_lines) + "\n"

    env = dict(os.environ)
    # The parent Claude Code session exports MAX_THINKING_TOKENS, which would
    # otherwise silently switch extended thinking ON for every child call.
    env["MAX_THINKING_TOKENS"] = str(int(thinking))

    try:
        proc = subprocess.run(cmd, input=stdin_data, capture_output=True,
                              text=True, timeout=timeout, cwd=str(RAW), env=env)
    except subprocess.TimeoutExpired:
        return False, "", "", {}, 0.0, "timeout", []

    events = []
    for line in proc.stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            pass

    results = [e for e in events if e.get("type") == "result"]
    if not results:
        return False, "", "", {}, 0.0, (proc.stderr or "no result event")[:500], events

    last = results[-1]
    if last.get("is_error"):
        return False, "", "", {}, 0.0, str(last.get("result"))[:500], events

    # thinking from the final assistant turn(s)
    think_parts = []
    for e in events:
        if e.get("type") == "assistant":
            for c in e.get("message", {}).get("content", []):
                if c.get("type") == "thinking" and c.get("thinking"):
                    think_parts.append(c["thinking"])

    cost = sum(float(r.get("total_cost_usd") or 0.0) for r in results)
    return True, last.get("result", ""), "\n".join(think_parts), \
        last.get("usage", {}), cost, "", events


def query(model_tag: str, prompt: str | Sequence[dict], *, system: str = DEFAULT_SYSTEM,
          cache: Cache | None = None, effort: str | None = None, salt: str = "",
          timeout: int = 400, retries: int = 3, fresh: bool = False,
          keep_events: bool = False, thinking: int = 0) -> Response:
    model = MODELS.get(model_tag, model_tag)
    messages = ([{"role": "user", "content": prompt}]
                if isinstance(prompt, str) else list(prompt))
    k = _key(model, system, messages, effort, salt, thinking)

    if cache is not None and not fresh:
        hit = cache.get(k)
        if hit:
            return Response(ok=True, text=hit["text"], thinking=hit.get("thinking", ""),
                            model=model, system=system, messages=messages,
                            usage=hit.get("usage", {}), cost_usd=0.0, key=k)

    last_err = ""
    for attempt in range(retries):
        ok, text, think_txt, usage, cost, err, events = _run_cli(
            model, system, messages, effort, timeout, thinking)
        with _cost_lock:
            _total_cost[0] += cost
            _ncalls[0] += 1
        if ok:
            rec = {"key": k, "ok": True, "model": model, "model_tag": model_tag,
                   "system": system, "messages": messages, "effort": effort,
                   "salt": salt, "think_budget": thinking, "text": text,
                   "thinking": think_txt, "usage": usage, "cost_usd": cost,
                   "ts": time.time()}
            if cache is not None:
                cache.put(rec)
            return Response(ok=True, text=text, thinking=think_txt, model=model,
                            system=system, messages=messages, usage=usage,
                            cost_usd=cost, key=k,
                            raw_events=events if keep_events else [])
        last_err = err
        time.sleep(2 ** attempt * 2)

    rec = {"key": k, "ok": False, "model": model, "model_tag": model_tag,
           "system": system, "messages": messages, "effort": effort, "salt": salt,
           "think_budget": thinking, "error": last_err, "ts": time.time()}
    if cache is not None:
        cache.put(rec)
    return Response(ok=False, text="", thinking="", model=model, system=system,
                    messages=messages, error=last_err, key=k)


def map_queries(jobs: Iterable[dict], *, cache: Cache, workers: int = 6,
                label: str = "") -> list[tuple[dict, Response]]:
    """jobs: iterable of kwargs dicts for `query` plus arbitrary 'meta' key."""
    jobs = list(jobs)
    out: list[tuple[dict, Response]] = []
    done = [0]
    t0 = time.time()

    def run(job):
        kw = {k: v for k, v in job.items() if k != "meta"}
        return job, query(cache=cache, **kw)

    with ThreadPoolExecutor(max_workers=workers) as ex:
        futs = [ex.submit(run, j) for j in jobs]
        for fut in as_completed(futs):
            job, resp = fut.result()
            out.append((job, resp))
            done[0] += 1
            if done[0] % 10 == 0 or done[0] == len(jobs):
                el = time.time() - t0
                with _print_lock:
                    print(f"[{label}] {done[0]}/{len(jobs)}  "
                          f"{el:.0f}s  ${_total_cost[0]:.2f}", file=sys.stderr, flush=True)
    return out


# ---------------------------------------------------------------------------
# Pooled backend: same cache/interface, ~3x the throughput.
# ---------------------------------------------------------------------------

def map_queries_pooled(jobs: Iterable[dict], *, cache: Cache, pool_size: int = 10,
                       workers: int = 14, label: str = "", cwd: str | None = None
                       ) -> list[tuple[dict, Response]]:
    """Group jobs by (model, system, thinking) and serve each group from a pool
    of long-lived CLI processes. Job dicts take the same keys as `query`
    (model_tag, prompt, system, salt, thinking) plus an arbitrary 'meta'."""
    import pool as _pool  # local import so the module stays optional

    jobs = list(jobs)
    base = Path(cwd) if cwd else (RAW.parent / "pool_cwd")
    base.mkdir(parents=True, exist_ok=True)

    groups: dict[tuple, list[dict]] = {}
    for j in jobs:
        gk = (j.get("model_tag", "haiku45"), j.get("system", DEFAULT_SYSTEM),
              int(j.get("thinking", 0)))
        groups.setdefault(gk, []).append(j)

    out: list[tuple[dict, Response]] = []
    t0 = time.time()
    total_done = 0

    for (mt, system, thinking), gjobs in groups.items():
        model = MODELS.get(mt, mt)
        pending, cached = [], 0
        for j in gjobs:
            msgs = [{"role": "user", "content": j["prompt"]}]
            k = _key(model, system, msgs, j.get("effort"), j.get("salt", ""), thinking)
            hit = cache.get(k)
            if hit:
                out.append((j, Response(ok=True, text=hit["text"],
                                        thinking=hit.get("thinking", ""), model=model,
                                        system=system, messages=msgs,
                                        usage=hit.get("usage", {}), key=k)))
                cached += 1
            else:
                pending.append((j, k, msgs))
        total_done += cached
        if not pending:
            continue

        p = _pool.Pool(model, system, thinking, pool_size, base)
        try:
            def run(t):
                j, k, msgs = t
                res = p.ask(j["prompt"])
                if res is None:
                    with _print_lock:
                        _fail_streak[0] += 1
                        if _fail_streak[0] in (1, 5, 25, 100):
                            print(f"[{label}] FAILURE x{_fail_streak[0]}: "
                                  f"{p.last_error!r}", file=sys.stderr, flush=True)
                    rec = {"key": k, "ok": False, "model": model, "model_tag": mt,
                           "system": system, "messages": msgs, "salt": j.get("salt", ""),
                           "think_budget": thinking,
                           "error": f"pool failure: {p.last_error}",
                           "ts": time.time()}
                    cache.put(rec)
                    return j, Response(ok=False, text="", thinking="", model=model,
                                       system=system, messages=msgs,
                                       error="pool failure", key=k)
                cost = float(res.get("total_cost_usd") or 0.0)
                think_txt = "\n".join(
                    c["thinking"] for e in res.get("_events", [])
                    if e.get("type") == "assistant"
                    for c in e.get("message", {}).get("content", [])
                    if c.get("type") == "thinking" and c.get("thinking"))
                with _cost_lock:
                    _total_cost[0] += cost
                    _ncalls[0] += 1
                    _fail_streak[0] = 0
                rec = {"key": k, "ok": True, "model": model, "model_tag": mt,
                       "system": system, "messages": msgs, "salt": j.get("salt", ""),
                       "think_budget": thinking, "text": res.get("result", ""),
                       "thinking": think_txt, "usage": res.get("usage", {}),
                       "cost_usd": cost, "ts": time.time()}
                cache.put(rec)
                return j, Response(ok=True, text=res.get("result", ""),
                                   thinking=think_txt, model=model, system=system,
                                   messages=msgs, usage=res.get("usage", {}),
                                   cost_usd=cost, key=k)

            with ThreadPoolExecutor(max_workers=workers) as ex:
                futs = [ex.submit(run, t) for t in pending]
                for i, fut in enumerate(as_completed(futs)):
                    out.append(fut.result())
                    total_done += 1
                    if total_done % 25 == 0 or total_done == len(jobs):
                        el = time.time() - t0
                        with _print_lock:
                            print(f"[{label}] {total_done}/{len(jobs)} {el:.0f}s "
                                  f"${_total_cost[0]:.2f} ({total_done/max(el,1):.2f}/s)",
                                  file=sys.stderr, flush=True)
        finally:
            p.close()
    return out
