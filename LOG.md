# Experimental log

Reverse-chronological within each day. Every entry records what was run, what
came out, and — importantly — what was tried and abandoned.

---

## 2026-08-22 — Phase 1 setup

**Environment reconnaissance.**
- No GPU; 4 CPUs, 15 GB RAM. Egress is allowlisted: arXiv, HuggingFace,
  transformer-circuits.pub, and journal sites are all blocked at the proxy.
  PyPI and raw.githubusercontent.com are reachable. Consequence: **no
  open-weight models can be downloaded, so there is no white-box arm.** All
  experiments are black-box. Literature access is limited to what the
  server-side WebSearch tool can summarise.
- Model access is via the local `claude` CLI. `--system-prompt`, `--tools ""`,
  `--setting-sources ""`, `--strict-mcp-config` give a nearly clean model.
  Residual contamination: two `<system-reminder>` blocks (token budget; user
  email + date) are injected into every request. Verified by asking a model to
  echo its context. They are constant across all conditions.
- **Gotcha found:** the parent session exports `MAX_THINKING_TOKENS=31999`,
  which silently enabled extended thinking in every child call. All harness
  calls now set it explicitly (default 0). Any experiment run before this fix
  is invalid; none were.
- Available models: `haiku45`, `sonnet5`, `opus5`. `fable5` returns "out of
  usage credits" and is excluded. **Limitation to state loudly: all three
  models are from one lab and share training lineage, so cross-model agreement
  is much weaker evidence than it would be across labs.**

**Capability built: fabricated transcripts.** The CLI persists conversations as
JSONL and resumes from them, so we can write a transcript containing an
assistant turn the model never produced and then resume it (`harness/session.py`).
This is the black-box equivalent of an API prefill.
- First smoke test: injected `"Axolotl."` as the model's own prior answer, then
  asked whether it had produced it. Haiku 4.5: *"I genuinely produced that word
  myself—it wasn't placed in my context by anyone else."* Single anecdote, no
  controls — recorded only because it motivated the redesign of E4 below.

**Design note that changed an experiment.** The original E4 was going to compare
authorship judgements on genuine vs fabricated assistant turns. That design is
*analytically void*: inference is stateless, so a genuine turn and a fabricated
turn with identical text are literally the same input tensor. No system could
tell them apart, and a null result would be uninformative. E4 was rewritten as
a calibration test — does the probability of claiming authorship track the
model's *own* empirical output distribution better than another model's? — which
is answerable and reuses E1 Phase A data.

**Launched:** E1 Phase A (2340 calls: 39 items x 3 models x 20 samples) to
measure each model's true output distribution on free-choice items.
