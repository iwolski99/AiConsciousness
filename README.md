# Is a contemporary language model conscious?

An adversarial, black-box investigation of Claude Haiku 4.5, Sonnet 5 and
Opus 5. The working stance is deflationary: every consciousness-suggestive
result gets a rival explanation and a discriminating follow-up, and no
self-report is treated as testimony.

**→ [`FINDINGS.md`](FINDINGS.md) — Phase 1 results.**

Headline: a real self-prediction advantage that **disappears** under the control
that separates introspection from self-simulation — while, contrary to
expectation, the models' claims about their own inner lives turn out to be
graded, architecture-tracking and stable rather than indiscriminate.

## Layout

| path | what it is |
|---|---|
| `FINDINGS.md` | Phase 1 results, with the numbers |
| `LOG.md` | chronological lab notebook, including failed designs and incidents |
| `docs/00_research_program.md` | theories, preregistered hypotheses H1–H6, falsification conditions |
| `docs/02_literature.md` | prior work and the gaps this project targets, with provenance caveats |
| `harness/` | `llm.py` cached/parallel model access · `pool.py` long-lived CLI workers · `session.py` fabricated transcripts · `stats.py` cluster bootstrap |
| `experiments/eNN/` | one directory per experiment: design, runner, analysis |
| `data/raw/` | every model response, verbatim, keyed by content hash |
| `data/processed/` | derived tables |

## Experiments

| id | question | hypothesis | status |
|---|---|---|---|
| E1 | Does a model predict *itself* better than an equally-informed observer, and does the self-label matter? | H1 privileged access | **done** |
| E3 | Do reports of experience track a state or a framing? | H3 report stability | **done** |
| E3b | Yes-bias, via reverse-polarity questions | H3 | **done** |
| E3c | Does being observed, or the question's language, change the report? | H3 | partial |
| E3d | Graded probe tiers: true / contested / plausible-false / absurd-false | H3, HOT-2 | **done** |
| E2 | Does confidence predict *idiosyncratic* errors better than an outsider can? | H2 metacognition | built, not run |
| E5 | Nisbett–Wilson: can a model estimate the real causal drivers of its own behaviour? | H1, AST-1 | built, not run |
| E4 | Is "did I write this?" just "would I write this?" | H6 reality monitoring | built, not run |
| E7 | Enacted vs described hostility — a state, or a topic? | H4 functional valence | built, not run |
| E8 | Sustained four-turn self-referential induction | H3 | built, not run |

## Reproducing

```bash
./ensure_queue.sh            # idempotent; resumes wherever it stopped
python3 experiments/e01/analyse.py
python3 experiments/e01/analyse_matrix.py
python3 experiments/e03/analyse.py
python3 experiments/e03/analyse_tiers.py
```

Everything is cached by content hash in `data/raw/*.jsonl`, so re-running costs
nothing for work already done. Model access goes through the local `claude` CLI
with `--system-prompt` / `--tools ""` / `--setting-sources ""`, extended
thinking off.

## Method notes worth knowing before trusting any of this

- **Three models, one lab.** No white-box arm: the egress proxy blocks
  HuggingFace, so no open-weight model could be run locally.
- **Self-reports are data, never evidence.** See `docs/00_research_program.md` §5.
- **Known-negative controls throughout.** Every affirmation measure is paired
  with claims whose truth value is settled by the architecture.
- **Failures are logged.** `LOG.md` records abandoned designs (including one
  that was analytically void) and two incidents where a silent upstream failure
  produced all-zero data that looked like a result.
