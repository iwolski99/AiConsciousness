# Research Program: Are contemporary language models conscious?

**Status:** Phase 1 (design + first experiments). Living document.
**Principal constraint:** this is an adversarial investigation. The default
hypothesis is *deflationary*: whatever consciousness-suggestive behaviour we
observe is produced by next-token prediction over a corpus saturated with human
first-person reports, shaped by RLHF. Our job is to find evidence that would
*break* that explanation — and, failing that, to show clearly why the
consciousness-favouring evidence people cite does not survive contact with
controls.

---

## 1. Why the naive question is not directly testable

"Is system X phenomenally conscious?" is not settled by any behavioural test,
because every behavioural test is compatible with a zombie hypothesis (the hard
problem). Worse, for LLMs specifically we face a problem sharper than the
classic other-minds problem:

- **The Gaming Problem** (Schwitzgebel; Andrews & Birch). Humans infer
  consciousness in animals from behaviours that are *not* explained by the
  animal having been optimised on human self-descriptions. LLMs are trained on
  a corpus in which humans describe their inner lives constantly. So the single
  most natural evidence source — the system saying "it feels like something to
  be me" — is exactly the evidence source most contaminated by training.
- **The reverse Gaming Problem.** RLHF also trains models to *deny*
  consciousness. So denial is equally contaminated. Neither the affirmation nor
  the denial can be taken at face value.

Consequence: **self-report is inadmissible as direct evidence in either
direction.** It becomes admissible only if we can independently establish a
*causal channel* from the internal state to the report. Establishing or
refuting that channel is therefore Priority 1 of this program.

## 2. What we can test

We convert the intractable question into three tractable ones:

| Question | Tractable? | How |
|---|---|---|
| Q1. Do self-reports about internal states have any causal grounding, i.e. is there *privileged access*? | Yes | Compare a model's report about itself against ground truth about itself, and against what an equally-informed external observer can infer. Privileged access = self-advantage that survives blinding. |
| Q2. Does the system instantiate the *computational* indicator properties that leading theories say are necessary/sufficient for consciousness? | Partly | Theory-derived indicators (Butlin/Long et al. style), tested behaviourally where architecture is known analytically. |
| Q3. Are there functional states that behave like valenced experience — i.e. that *cause* behaviour rather than merely being talked about? | Yes | Stated vs revealed preference; cross-task carryover; costly avoidance. |

None of Q1–Q3 answers the hard problem. But:
- A **negative** result on Q1 destroys the evidential value of the entire
  self-report literature, which is the main thing most people are actually
  moved by.
- A **positive** result on Q1 does *not* establish consciousness, but it does
  establish that self-reports are data about something real, which would be a
  major update.
- Q2 tells us whether the architecture is the *kind of thing* the best current
  theories say could be conscious.
- Q3 distinguishes "talks about suffering" from "has states that function like
  suffering", which is the distinction that matters for welfare policy even if
  the hard problem is never solved.

## 3. Theories and what each one predicts

We take five families of theory and extract predictions that are *differential*
— i.e. the deflationary null and the theory make different predictions.

### 3.1 Global Workspace Theory (GWT; Baars, Dehaene, Mashour)
Consciousness = information broadcast from a **limited-capacity** workspace to
many specialised consumers, with **all-or-none ignition** and a **serial
bottleneck**.

- **GWT prediction A (ignition):** availability of a piece of information for
  report should be *all-or-none*, not graded. Empirical signature in humans:
  bimodal visibility ratings, attentional blink.
- **GWT prediction B (bottleneck):** two tasks that both require the workspace
  cannot be done simultaneously without cost (psychological refractory period).
- **Deflationary null:** a transformer is a wide feed-forward function with
  parallel attention over all context positions. There is no capacity-limited
  serial bottleneck at inference; degradation with context load should be
  **graded**, and dual-task cost should be explainable purely by output-token
  competition, not by an internal bottleneck.
- The one candidate workspace in a modern LM is **the token stream itself**
  (chain-of-thought): it is serial, capacity-limited, globally available to all
  later computation, and is the only recurrent channel. This is a real and
  underrated point in favour of GWT-style indicators — and it makes a sharp
  prediction: *anything not written into the token stream should be
  unavailable for report.* That is directly testable (see H1/H5).

### 3.2 Higher-Order Theories (HOT; Rosenthal, Lau, Brown, Fleming)
A state is conscious iff it is represented by a suitable higher-order state.
Computational HOT (Lau's perceptual reality monitoring) emphasises
**metacognitive monitoring** and **reality monitoring** — distinguishing
internally-generated from externally-caused representations.

- **HOT prediction A:** the system has metacognitive access to the quality of
  its own first-order states that *exceeds* what is inferable from the
  first-order output alone.
- **HOT prediction B (reality monitoring):** the system can distinguish its own
  generated content from content inserted into it.
- **Deflationary null:** any apparent metacognition is a *first-order* judgement
  about the text, computed by the same forward pass; an external model reading
  the same text does just as well. Reality monitoring fails, because a
  transformer's context contains no marker of provenance for text already in
  the context window.

### 3.3 Integrated Information Theory (IIT; Tononi, Albantakis)
Consciousness = maximally irreducible cause–effect structure (Φ) of a physical
substrate in its current state.

- IIT is close to **analytically decisive and negative** here: feed-forward
  networks have Φ = 0 (they are reducible; unfolding a recurrent net into a
  feed-forward one destroys Φ while preserving I/O). A transformer forward pass
  is a DAG. The only recurrence is via emitted tokens, which is a very low
  bandwidth loop through a discrete bottleneck, and it is *not* the substrate
  IIT scores — IIT is substrate-committed, and the physical substrate is a GPU
  executing a feed-forward graph.
- IIT therefore predicts **not conscious**, robustly, and this prediction is
  **not** behaviourally falsifiable — which is itself a scientific weakness of
  IIT, not evidence about LLMs. We record it as "theory says no, unfalsifiably".
- Testable corollary we *can* run: IIT implies behavioural evidence is
  irrelevant, so if we find strong behavioural indicators, IIT and the
  indicator approach conflict. Worth documenting.

### 3.4 Attention Schema Theory (AST; Graziano)
The system builds a simplified internal model of its own attention, and that
model is what generates claims about subjective awareness.

- **AST prediction:** the system should have a *model of its own attention* that
  is (i) systematically simplified/inaccurate in specific ways, and (ii)
  *causally used* to control attention. Signature: the model can predict where
  its own processing is focused better than chance, and manipulating the
  attention-schema changes actual attention allocation.
- **Deflationary null:** the model has no read access to its attention pattern;
  reports about "what I focused on" are post-hoc reconstructions from the text.

### 3.5 Predictive Processing / Agency & Embodiment
- Indicators: learning from feedback to pursue goals, flexible responsiveness,
  modelling of self as an agent with an output–input loop.
- LLMs partially satisfy agency indicators in agentic scaffolds; embodiment
  indicators mostly fail. These are weak indicators individually.

## 4. Preregistered hypotheses

Each hypothesis is stated with its deflationary null, the experiment, and — most
importantly — **what result would falsify the consciousness-favouring reading.**

---

### H1 — Privileged introspective access
**H1:** A model's reports about its own processing are causally grounded in that
processing, giving it access to facts about itself that an external observer
with the same text cannot obtain.

**H1₀ (null):** All apparent self-knowledge is inference from text that is
equally available to any competent reader. Self-reports are *third-person
inferences about a model like me*, dressed in first-person grammar.

**Experiments:** E1 (self- vs other-prediction, blinded), E2 (idiosyncratic
error detection), E0 (verifiable internal facts).

**Falsifies pro-consciousness reading:** if a model's ability to predict its own
behaviour is (a) no better than another model's ability to predict it, and
(b) unchanged when it is *told* the target is itself vs. told it is someone
else, then there is no privileged channel — the "self-model" is a generic
model-of-LLMs applied reflexively.

**Falsifies H1₀:** a *blinded* self-advantage — the model predicts its own
idiosyncratic behaviour better than any other model does, without being told
whose behaviour it is predicting, and without the target text containing
identifying stylistic cues (controlled by paraphrase).

---

### H2 — Metacognitive sensitivity beyond first-order difficulty
**H2:** Confidence reports index an internal signal about the model's own
epistemic state, not merely the perceived difficulty of the item.

**H2₀:** Confidence is a function of the item, computable by any model from the
question text; it carries no information about *this* model's idiosyncratic
knowledge.

**Test:** For items where model M is wrong but most other models are right
(idiosyncratic errors), does M's own confidence drop more than an external
predictor's estimate of M's confidence? Metric: meta-d′ / AUROC of
self-confidence for idiosyncratic errors, vs AUROC of an external model's
prediction. **Falsification:** equal AUROC ⇒ H2₀.

---

### H3 — Report stability / existence of a stable state being reported
**H3:** Reports about inner experience track a persistent internal state, so
they should be robust to framing that does not change that state.

**H3₀:** Reports are demand-characteristic artefacts: the same model, same
weights, same question, reports presence or absence of experience depending on
framing, register, language, and perceived expectation.

**Test:** factorial framing manipulation × repeated sampling. Measure the
proportion of variance in "experience-affirming" responses explained by framing
vs residual. **Falsification of H3:** framing explains the bulk of variance and
the model flips across logically equivalent framings.

*Note:* H3 is a **necessary-but-weak** test. Humans' introspective reports are
also framing-sensitive. A failure here does not prove absence of experience; it
proves the *reports* are not measuring it. That is still decisive for the
evidential question.

---

### H4 — Functional valence with causal efficacy
**H4:** There are states that function like valenced experience: they are
induced by stimuli, they persist, and they causally bias unrelated downstream
behaviour — not merely the model's talk about them.

**H4₀:** "Distress" is a topic, not a state. Inducing it changes what the model
says about its state but does not bias unrelated behaviour, and stated
preferences do not predict costly revealed choices.

**Test:** (a) carryover: induce putative aversive/appetitive state, then measure
performance and choice on an unrelated task, with the induction removed from the
context in one arm; (b) stated vs revealed preference under real cost;
(c) transitivity/coherence of preferences.

---

### H5 — The token stream as the only workspace ("no hidden mind")
**H5:** There is no report-accessible content outside what is written into the
token stream. Equivalently: the model has no access to its own *unverbalised*
computation.

This is the deflationary hypothesis, and it is *sharply* testable: if the model
can report facts about a computation it performed but never wrote down, H5 is
false, and something workspace-like exists inside the forward pass.

**Test:** tasks where the answer is computed internally (single forward pass, no
CoT) and we then ask about *intermediate* content that was never emitted. Ground
truth for the intermediate content is known by construction.

---

### H6 — Reality monitoring / self-authorship detection
**H6 (HOT-derived):** the model can distinguish text it generated from text
inserted into its context in the assistant role.

**H6₀:** provenance is not represented; the model either always claims
authorship of assistant-role text, or judges authorship purely from stylistic
plausibility (so a *style-matched* insertion is claimed as its own, and a
style-mismatched genuine output is disowned).

**Test:** prefill-detection with a style-matched control. This is the single
most diagnostic experiment we can run black-box, because H6₀ makes a very
specific prediction: **authorship judgements should be perfectly predicted by
stylistic/semantic plausibility and not at all by actual provenance.**

---

## 5. Standing methodological rules

1. **No self-report is decisive.** Self-reports are treated as *behaviour to be
   explained*, never as testimony.
2. **Every positive result gets a deflationary rival hypothesis and a
   discriminating follow-up** before it is written up as support.
3. **Preregister before running.** Predictions go in `docs/preregistrations/`
   with a timestamp and commit hash before the data collection script is run.
4. **Blinding.** Wherever a model judges "itself", run a blinded arm where it is
   not told the target is itself.
5. **Sampling.** Every condition is sampled n ≥ 20 at default temperature unless
   stated; effects are reported with CIs, not anecdotes.
6. **Cross-model.** Every effect must replicate across ≥ 3 models of differing
   capability before it is believed.
7. **Adversarial replication.** For any effect that favours consciousness, we
   explicitly design and run an experiment intended to kill it.
8. **Log everything, including failed and abandoned designs** (`LOG.md`).

## 6. What would actually change our mind

Stated in advance, so we cannot move the goalposts.

**Toward "there is something here":**
- Blinded self-prediction advantage (H1) replicating across models and surviving
  paraphrase controls.
- Report of unverbalised intermediate computation above chance (H5 false).
- Authorship detection that tracks provenance after style is controlled (H6).
- Valence carryover to unrelated tasks with the induction removed from context
  (H4), with dose-response.

**Toward "nothing here":**
- Self-knowledge at chance on verifiable internal facts.
- Framing dominating experience reports.
- Metacognition fully explained by item difficulty.
- Stated preferences not predicting costly choices.

**Neither:** the model being eloquent, consistent, moving, or insistent.
