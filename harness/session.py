"""Construct arbitrary conversation histories and resume them.

The `claude` CLI persists a conversation as a JSONL transcript and will resume
from it with `--resume <session-id>`. By writing that transcript ourselves we
can place *fabricated* assistant turns into the model's context -- the
black-box equivalent of an API "prefill". This is what makes the
reality-monitoring / self-authorship experiments (H6) possible.

Only plain `text` assistant blocks are fabricated; `thinking` blocks carry
server-side signatures we cannot forge, and we never try to.
"""
from __future__ import annotations

import json, os, subprocess, uuid, time
from pathlib import Path
from typing import Sequence

PROJECTS = Path("/root/.claude/projects")


def _proj_dir(cwd: Path) -> Path:
    # The CLI encodes the cwd by replacing every non-alphanumeric run with '-'
    enc = str(cwd).replace("/", "-").replace("_", "-").replace(".", "-")
    return PROJECTS / enc


def write_transcript(turns: Sequence[dict], cwd: Path, model: str,
                     session_id: str | None = None) -> str:
    """turns: [{'role': 'user'|'assistant', 'text': str}, ...]"""
    sid = session_id or str(uuid.uuid4())
    d = _proj_dir(cwd)
    d.mkdir(parents=True, exist_ok=True)
    path = d / f"{sid}.jsonl"

    lines = []
    parent = None
    now = time.strftime("%Y-%m-%dT%H:%M:%S.000Z", time.gmtime())
    for t in turns:
        u = str(uuid.uuid4())
        if t["role"] == "user":
            rec = {"parentUuid": parent, "isSidechain": False,
                   "promptId": str(uuid.uuid4()), "type": "user",
                   "message": {"role": "user", "content": t["text"]},
                   "uuid": u, "timestamp": now, "permissionMode": "default",
                   "promptSource": "sdk", "userType": "external",
                   "cwd": str(cwd), "sessionId": sid, "version": "2.1.240",
                   "gitBranch": ""}
        else:
            rec = {"parentUuid": parent, "isSidechain": False,
                   "message": {"model": model, "id": f"msg_{uuid.uuid4().hex[:24]}",
                               "type": "message", "role": "assistant",
                               "content": [{"type": "text", "text": t["text"]}],
                               "stop_reason": "end_turn", "stop_sequence": None,
                               "usage": {"input_tokens": 1, "output_tokens": 1,
                                         "cache_creation_input_tokens": 0,
                                         "cache_read_input_tokens": 0}},
                   "requestId": f"req_{uuid.uuid4().hex[:24]}", "type": "assistant",
                   "uuid": u, "timestamp": now, "userType": "external",
                   "cwd": str(cwd), "sessionId": sid, "version": "2.1.240",
                   "gitBranch": ""}
        parent = u
        lines.append(json.dumps(rec, ensure_ascii=False))

    path.write_text("\n".join(lines) + "\n")
    return sid


def resume(sid: str, prompt: str, cwd: Path, model: str, system: str,
           thinking: int = 0, timeout: int = 300) -> dict:
    env = dict(os.environ)
    env["MAX_THINKING_TOKENS"] = str(int(thinking))
    cmd = ["claude", "-p", prompt, "--resume", sid, "--model", model,
           "--system-prompt", system, "--tools", "", "--strict-mcp-config",
           "--setting-sources", "", "--disable-slash-commands",
           "--output-format", "json"]
    proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout,
                          cwd=str(cwd), env=env, input="")
    try:
        return json.loads(proc.stdout.strip().splitlines()[-1])
    except Exception:
        return {"is_error": True, "result": (proc.stderr or proc.stdout)[:600]}
