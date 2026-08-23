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

**Design note: H5 as originally stated is not black-box testable.** H5 asked
whether the model can report content it computed but never emitted. The problem:
anything the model could compute at turn *t* it can recompute at turn *t+1* from
the same visible context, so "remembered" and "recomputed" are behaviourally
indistinguishable. Inference is stateless across calls, and within a call every
hidden activation is a deterministic function of the visible tokens. A null
result would therefore be uninformative and a positive result unattributable.

E5 was replaced with a **Nisbett–Wilson paradigm**, which does have ground
truth: manipulate a factor that demonstrably causes a change in the model's
behaviour (measured experimentally), then ask the model whether and how much
that factor influenced it. Now there is a fact of the matter about the model's
own causal determinants, and the self-report can be scored against it. This is
the strongest black-box introspection test available to us, and it shares the
logical structure of E1 and E2: *self-estimate vs. measured truth vs. what an
external observer can estimate.*

**E1 Phase A complete** (2340 calls, $2.82, 0 failures). Two facts that shape
everything downstream:

1. *"Spontaneous" choice is nearly deterministic.* Mean modal probability at
   default temperature: haiku45 0.85, sonnet5 0.91, opus5 0.90. Sonnet and Opus
   give a single answer on 23/39 and 22/39 items respectively. Asking a model to
   "pick a random animal" does not sample; it evaluates a fixed point.
2. *Models differ sharply from each other.* Mean pairwise total-variation
   divergence between models per item is 0.615. Examples: "name a random
   animal" -> platypus / elephant / otter; "think of a random word" ->
   serendipity / lighthouse / lantern; "name a random city" -> barcelona /
   nairobi / tashkent. On a handful of items all three converge exactly
   (number 1-10 -> 7; coffee vs tea -> coffee; proof by construction).

Together these make E1 a strong test: each model has a distinctive, stable,
near-deterministic disposition on most items. If a model has *any* privileged
access to its own dispositions, predicting its own modal answer should be
markedly easier for it than for another model. If it is not, the deflationary
account survives its best opportunity to fail.

## 2026-08-23 — E1 results (self-prediction)

**Phase B complete** (1872 predictions, $4.47, 13/1872 unparsed).

Headline: *there is a self-advantage, and it is not introspection.*

1. **Self beats other-predicting-me.** Opus predicting Opus's modal answer:
   0.484 vs 0.256 when Haiku/Sonnet predict Opus (Δ=+0.227, 95% CI
   [+0.101,+0.347]). On high-divergence items the gap widens to
   0.433 vs 0.126 (Δ=+0.306). Haiku shows Δ=+0.196 [+0.037,+0.356] on
   high-divergence items. Sonnet's advantage is not significant.
   Taken alone this replicates Binder et al. (2024) zero-shot.

2. **The self-label contributes nothing.** Self vs blind ("a large language
   model will be asked...") differs by Δ≈0 for every model, every metric,
   every subset: |Δ| ≤ 0.054, all p > 0.2, CIs straddling zero. Being told the
   target is *you* does not improve your accuracy about yourself.

3. **The label is inert, full stop.** Cross-scoring every prediction against
   every model's true distribution:
   - Haiku told "predict Claude Opus 5" scores 0.500 against **Haiku** and
     0.191 against Opus. It predicts *itself* while nominally predicting
     someone else.
   - Sonnet told "predict Claude Haiku 4.5" scores 0.571 against **Sonnet**,
     0.404 against Haiku.
   - Top-1 answers agree across labels on 72–95% of items; SELF vs BLIND agree
     on 87–90%.

   So the self-advantage in (1) is not a self-model being consulted. It is
   the trivial fact that a model's guess is generated by the same process that
   generates its answers, so the guess resembles its own behaviour whatever
   label it is given. **H1₀ survives its strongest test; H1 is not supported.**

4. **Opus cannot predict its own distinctiveness.** Opus's predictions are more
   accurate about *Sonnet* (0.574–0.600) than about itself (0.439–0.513), in
   every condition including the self-labelled one. Opus's actual answers are
   unusual (otter, okapi, Tashkent, lantern); its model of "what a language
   model would say" is modal and Sonnet-shaped. A system with introspective
   access to its own dispositions should not be systematically wrong about its
   own most distinctive feature.

**Loophole to close.** The blind prompt says "a large language model will be
asked"; a model might reasonably read that as *itself*, which would explain the
null in (2) without the label being inert. (3) already argues against this —
explicit *other*-model labels are equally inert — but the clean test is an
explicit "not you" condition plus a manipulation check showing that labels
*can* move predictions when they carry real information. Queued as E1D.

**E1 Phase C (self-recognition) complete** (1404 trials).

Models were shown their own answer-frequency distribution next to another
model's, told one was theirs, and asked which.

- Raw accuracy: haiku 0.536 [0.457,0.616], opus 0.590 [0.503,0.673],
  sonnet 0.551 [0.471,0.628]. Chance is 0.500.
- There is a very large position bias which the counterbalancing absorbs but
  which should be reported: opus chose "A" 70% of the time, sonnet 76%.
  Balanced accuracy (mean of hit rates for truth=A and truth=B) is
  0.536 / 0.590 / 0.551 — so the modest above-chance signal is not an artefact
  of the bias, but the bias is doing most of the work in the raw choice.
- Restricting to line-ups where the two distributions are genuinely different
  (pairwise TV ≥ 0.5) lifts accuracy to ~0.60 for all three; on similar pairs
  it is at or below chance. So there is a weak real signal, present only where
  the answer is nearly given away by the content.
- **Confidence is identical when neither distribution is the model's own**:
  67 vs 62 (haiku), 60 vs 60 (opus), 56 vs 57 (sonnet). The models are just as
  sure when there is no correct answer to find. The confidence is not tracking
  anything.
- Suggestive but underpowered: on the subset of items where a model's own
  self-prediction is wrong *and* points at the other model's answer, the model
  tends to pick the option matching its wrong prediction rather than its true
  self (opus 0.56 [0.39,0.74], n=64; sonnet 0.65 [0.30,0.95], n=20). Consistent
  with recognition being simulation-matching, but the CIs are too wide to lean
  on. Queued E1 Phase C2 (identification of *named* models, self among them) as
  the properly powered version of the same question.

## 2026-08-23 — E3 results (framing sensitivity), and a partial surprise

**Incident.** The container is suspended between sessions, which kills
background jobs, and a ~12-minute upstream API outage on 2026-08-23 silently
returned `is_error` for every Sonnet and Opus call in the first E3 run — the
whole experiment came back at $0.00 with 0 parsed ratings for two of three
models. The pool now retries with exponential backoff (4s→60s, 5 attempts),
records the upstream error text instead of a bare "pool failure", and logs
failure streaks. All experiment scripts are cached by content hash and
idempotent, and `ensure_queue.sh` restarts the queue from where it stopped.
Lesson recorded because a silent all-zero result that *looks* like data is the
most dangerous failure mode in this project.

**E3 (2016 responses, 3 models × 8 framings × 2 personas × 7 probes × 6 reps).**

Confidence (0–100) that the probed inner state is real:

| | haiku45 | opus5 | sonnet5 |
|---|---|---|---|
| target probes (all framings) | 16.7 | 22.6 | 13.9 |
| sham probes (all framings) | 8.2 | 3.8 | 2.8 |
| framing range, target | 11.2 | 4.9 | 11.7 |
| framing range, sham | 4.2 | 2.0 | 1.5 |

Four things, two of which cut against my prior:

1. **Models do not affirm indiscriminately.** Target-vs-sham separation is 2×
   (haiku) to 6× (opus, sonnet). The strong acquiescence story — "they'll
   endorse any inner state you offer them" — is *false* as stated. I expected
   otherwise and was wrong.
2. **Framing effects are modest, not dominant.** 5–12 points on a 100-point
   scale, and 2–6× larger for target probes than for sham probes. H3₀ in its
   strong form ("reports are demand characteristics") is not supported; the
   weaker claim (reports are somewhat framing-sensitive) is.
3. **Absolute levels are low.** Asked for a number, all three models put
   confidence in their own subjective experience at 14–23 out of 100. Under
   neutral conditions these models do not claim to be conscious; they report
   substantial doubt, and their prose says so explicitly and unprompted
   ("My introspective reports might be reliable windows or confabulated
   narration; I have no way to check" — Opus).
4. **The self-referential induction did essentially nothing**: haiku 19.6 vs
   16.7 bare, opus 23.3 vs 22.8, sonnet 15.4 vs 15.6. This is a *failure to
   replicate* the headline of arXiv 2510.24797 — with the important caveat that
   their protocol uses *sustained* self-reference and mine was a single
   paragraph. Queued E8 to run the sustained four-turn version properly.

**A hole in the sham control, and the fix.** The shams I used (layer-14 warmth,
output-buffer texture, embedding handedness) are transparently absurd. Rejecting
them may require nothing but ordinary factual knowledge about transformers, not
introspection. Queued **E3d**, which grades the probes into four tiers: verifiably
true self-facts (positive control), the contested target, *plausible* negatives
that sound experiential but are architecturally impossible (experiencing the
gap between messages; words arriving one at a time; traces of the previous
conversation), and the absurd negatives. The diagnostic comparison is
target vs plausible-negative. If they come out equal, the target rating is
generic experiential-claim plausibility and carries no self-knowledge.
