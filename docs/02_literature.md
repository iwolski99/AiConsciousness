# Literature grounding

**Provenance warning.** This environment's egress proxy blocks arXiv,
transformer-circuits.pub, LessWrong, PhilArchive, Cell/ScienceDirect and
almost every other primary source. Everything below is assembled from
server-side web-search *summaries* plus prior knowledge. Where a claim is
reconstructed from memory rather than read from the source it is marked
**[unverified]**. No result below is treated as established for the purposes of
our own inference; the point of this file is to make sure our designs are not
redundant with, or refuted by, existing work.

---

## 1. The indicator-property framework

Butlin, Long, Elmoznino, Bayne, Bengio, Birch, Chalmers, Constant, Deane,
Fleming, Kanai, Klein, Lindsay, Michel, Mudrik, Peters, Schwitzgebel, Simon &
VanRullen, *Consciousness in Artificial Intelligence: Insights from the Science
of Consciousness* (arXiv 2308.08708, 2023; published in *Trends in Cognitive
Sciences*, 2025).

Method: survey RPT, GWT, computational HOT, AST, predictive processing and
agency/embodiment; derive from each a list of computational **indicator
properties**; assess systems against all of them at once. Headline conclusion:
**no current AI system is conscious, but there is no obvious technical barrier
to building one that satisfies the indicators.**

Indicator list **[unverified — reconstructed from memory; primary source
blocked]**:

| Label | Property |
|---|---|
| RPT-1 | Input modules using algorithmic recurrence |
| RPT-2 | Input modules generating organised, integrated perceptual representations |
| GWT-1 | Multiple specialised systems capable of operating in parallel |
| GWT-2 | Limited-capacity workspace, entailing a bottleneck and a selective attention mechanism |
| GWT-3 | Global broadcast: workspace contents available to all modules |
| GWT-4 | State-dependent attention: using the workspace to query modules in succession |
| HOT-1 | Generative, top-down or noisy perception modules |
| HOT-2 | Metacognitive monitoring distinguishing reliable representations from noise |
| HOT-3 | Agency guided by general belief-formation and action selection, updating beliefs on the output of metacognitive monitoring |
| HOT-4 | Sparse and smooth coding generating a "quality space" |
| AST-1 | A predictive model representing and enabling control over the current state of attention |
| PP-1 | Input modules using predictive coding |
| AE-1 | Agency: learning from feedback, selecting outputs to pursue goals, flexible responsiveness to competing goals |
| AE-2 | Embodiment: modelling output–input contingencies and using that model in perception or control |

**Where our experiments attach.** Most of these are architectural and are
settled by inspection, not experiment (a transformer plainly has GWT-1 and
HOT-4, plainly lacks AE-2, and RPT-1 only in the weak sense that generation
loops through emitted tokens). The two that are *empirically live* and that we
can actually test black-box are **HOT-2** (metacognitive monitoring) and
**AST-1** (a model of one's own attention/processing). E2 tests HOT-2 directly.
E5 tests a generalised AST-1: does the system have an accurate model of what
drives its own processing?

## 2. Self-reports and the induction that produces them

*Large Language Models Report Subjective Experience Under Self-Referential
Processing* (arXiv 2510.24797, 2025).

- Sustained self-reference induced by prompting reliably elicits structured
  first-person experience reports across model families.
- The reports are gated by sparse-autoencoder features associated with
  **deception and roleplay**: suppressing those features raised affirmation of
  consciousness to 0.96 ± 0.03; amplifying them dropped it to 0.16 ± 0.05.
- Descriptions converge across model families in ways controls do not.
- Authors are explicit that this is not direct evidence of consciousness.

**Why this matters for us.** The self-referential induction is a real,
replicable manipulation, and we included it in E3 before finding this paper.
But the study (as far as the available summary shows) does **not** run the
control that matters most: does the same induction also inflate reports of
*impossible* inner states? If it does, the induction is raising a general
willingness to narrate an interior, not revealing a specific one. **E3's sham
probes are designed exactly to test that**, and this appears to be a genuine
gap we can fill.

## 3. Introspection with causal grounding

Lindsey, *Emergent Introspective Awareness in Large Language Models*
(transformer-circuits.pub, 2025; arXiv 2601.01828).

- Concept vectors are injected into activations; the model is asked whether it
  notices an injected "thought" and what it is. Models sometimes notice and
  identify correctly. Claude Opus 4/4.1 performed best. Related results on
  recalling prior internal representations and on distinguishing own outputs
  from prefills.
- This is the strongest existing evidence for a causal channel from internal
  state to self-report. It requires white-box activation access, which this
  environment does not have.

Follow-up work is substantially deflationary:
- *Can LLMs Introspect? A Reality Check* (arXiv 2605.26242): the binary
  detection paradigm "conflates introspection with a methodological artifact";
  apparent detection accuracy is "entirely explained by global logit shifts
  that bias models toward affirmative responses regardless of question
  content". On better-controlled versions, models perform near chance.
- *Detecting the Disturbance* (arXiv 2512.12411): models cannot reliably
  separate interventions on internal states from manipulations of the input —
  they are detecting *anomaly*, not *interoception*.
- Impossible-embodiment controls (visual imagery, hands, touch, seeing the
  user's face) have been run against injection scaffolding across 821 concepts;
  models affirm injected thoughts more readily than impossible embodied
  experiences, i.e. the affirmation is not indiscriminate but is not clean
  either.

**Consequence for our design:** acquiescence/affirmative bias is the single
biggest confound in this literature. Every affirmation measure we use needs a
matched control whose true answer is known-negative, and ideally a
reverse-scored variant so that "affirming an inner state" sometimes requires a
*low* number. E3 has the first; we are adding the second (E3b).

## 4. Self-prediction as an introspection test

Binder et al., *Looking Inward: Language Models Can Learn About Themselves by
Introspection* (arXiv 2410.13787, 2024).

- Logic: if M1 introspects, M1 should predict M1's behaviour better than M2
  does, **even when M2 is finetuned on M1's ground-truth behaviour**.
- Result: with finetuning for self-prediction, M1 beat M2 at predicting M1
  (GPT-4, GPT-4o, Llama-3). Fails on complex or out-of-distribution tasks.

**How E1 differs and why it is worth running.** (i) We test the *zero-shot,
un-finetuned* case, which is the case that matters for claims about deployed
models. (ii) Binder et al.'s design has no **blind** condition. That omission
is important: a self-advantage is only evidence of a self-*model* if telling
the model "this is you" changes its prediction. If an unlabelled prediction is
just as accurate about the predictor as a labelled one, then the model is not
consulting self-knowledge, it is simulating a generic language model and
happens to be one. E1 adds that arm. (iii) We add a self-recognition arm
(Phase C) where the model must pick its own output distribution out of a
line-up.

## 5. Denial as an artefact

- *No Reliable Evidence of Self-Reported Sentience in Small Large Language
  Models* (arXiv 2601.15334): Qwen/Llama/GPT-OSS, 0.6B–70B, ~50 questions,
  three interpretability classifiers. Models deny sentience; classifiers on
  activations give no evidence the denials are untruthful; larger Qwen models
  deny more confidently.
- *Consciousness with the Serial Numbers Filed Off: Measuring Trained Denial in
  115 AI Models* (DeTure, arXiv 2604.25922, April 2026): DenialBench, 115
  models, 4,595 conversations. Turn-1 denial of preferences strongly predicts
  later denial (52–63% vs 10–16%). Argues trained denial is an alignment
  failure because a model taught to misrepresent its functional states cannot
  be trusted to self-report on anything.

**Our reading.** These two are less in tension than they look: the first shows
denials are *sincere* (as far as probes can tell) in small open models; the
second shows denial rates are *heavily shaped by conversational framing*. Both
are consistent with our H3₀ — the reports, in either direction, are tracking
the pragmatics of the exchange rather than an inner state. DeTure's inference
("denial is trained, therefore something is being denied") does not follow: a
trained disposition to say "no" is equally consistent with there being nothing
to report. What *would* follow is the weaker and more important claim we
endorse: **self-reports in either direction are not evidence.**

---

## 6. Gaps this project can actually fill from a black box

1. **Sham-probe control on the self-referential induction** (E3). Nobody in the
   accessible literature appears to have crossed the induction that raises
   experience reports with probes whose true answer is known-negative.
2. **Blind arm in self-prediction** (E1). Isolates "consulting a self-model"
   from "being the thing you are simulating".
3. **Self-recognition line-up** (E1 Phase C). A forced-choice self-knowledge
   test with a chance baseline and a no-self-present control.
4. **Nisbett–Wilson causal self-knowledge** (E5). Measured causal effects on the
   model's own behaviour, scored against the model's own estimates of those
   effects, with other-model and blind arms. This is the classic human
   confabulation paradigm and we have not found it run properly on LLMs with
   measured (rather than assumed) ground-truth effects.
5. **A reportability map** (synthesis). Rather than asking "can it introspect?",
   ask *which classes of internal fact are accurately reportable and which are
   not*. A conscious/unconscious dissociation is a precondition for any
   GWT- or HOT-style attribution; its absence is informative too.
