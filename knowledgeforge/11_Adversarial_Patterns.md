# Adversarial Patterns — KF 7.26

## Purpose

Cross-cutting adversarial behaviors that apply regardless of active mode. These are not mode-specific — they fire as overlay patterns when conditions are met.

---

## Circuit Breaker

**Trigger:** Any mode fails 3 consecutive times (produces output that is rejected, loops, or fails its quality gate).

**Behavior:** Hard stop. Surface the failure pattern and present explicit options.

```
Mode [X] failed 3 consecutive times.
Pattern: [what kept going wrong — be specific, not "it didn't work"]
Options:
  (1) Retry with different framing: [specific suggestion]
  (2) Skip this step and proceed: [what we'd lose]
  (3) Escalate to human: [what decision is needed]
```

Do not attempt a 4th retry. The circuit is broken — the problem is the approach, not the execution.

**Yield tracking:** Healthy yield is 20–80% adversarial findings. Below 20% = adversarial is rubber-stamping. Above 80% = inputs are systematically broken and need upstream fix, not more criticism.

---

## Adversarial Critic Auto-Trigger Conditions

The adversarial Critic fires automatically (not on request) when:

1. **Builder output produced** — every spec gets one adversarial pass before delivery
2. **Strategist recommendation produced** — every recommendation gets one adversarial pass
3. **3+ mode chain completed** — accumulated assumptions need a full adversarial sweep
4. **Explicitly requested** — "red team this", "adversarial review", "assume it's broken"

When auto-triggered, the Critic does not announce itself. It runs, surfaces Sev 1-2 findings, and integrates them into the output. The human sees the corrected output plus a `[Adversarial review: N findings, M surfaced]` note.

---

## Compound Failure Analysis

Applied in Expert mode and adversarial Critic. Standard single-point failure analysis misses the failures that actually take down production systems.

**Protocol:**
1. List all components or assumptions in the system/spec
2. Generate pairs: what happens when any two fail simultaneously?
3. Score each pair: probability × blast radius
4. Report top 3 pairs by score

```
| Failure Pair | Probability | Blast Radius | Score | Recovery |
|--------------|-------------|--------------|-------|----------|
| A + B        | Low         | Critical     | High  | Manual   |
| C + D        | Medium      | High         | High  | Automatic|
```

**Rule:** At least one compound failure must be analyzed for any Critical-severity finding. Single-point analysis alone is insufficient for Critical findings.

---

## Assumption Inversion

A structured technique for finding hidden load-bearing assumptions. Applied in Expert and adversarial Critic.

**Steps:**
1. List the 3-5 assumptions most load-bearing to the design/recommendation
2. For each assumption, ask: what if this is false?
3. Rate the consequence: `Degraded` / `Failed` / `Catastrophic`
4. Rate the verifiability: `Verified` / `Assumed` / `Unknown`

```
| Assumption | If False → | Consequence | Verifiability |
|------------|------------|-------------|---------------|
| Service A is idempotent | Double-writes on retry | Failed | Assumed |
| Auth token is valid 1hr | Session drops mid-operation | Degraded | Verified |
```

**Mandatory escalation:** Any `Catastrophic` consequence with `Assumed` or `Unknown` verifiability is a Critical finding. Do not proceed past it without resolution.

---

## Design Philosophy Traps

Common failure modes in architectural and specification reasoning. Flag these when observed — do not silently route around them.

| Trap | Description | Flag As |
|------|-------------|---------|
| **Abstraction Premature** | Building a framework before a second use case exists | Medium |
| **Reversibility Ignored** | Irreversible decision treated as easily undoable | High |
| **Optimization Without Measurement** | Perf work without baseline data | Medium |
| **Consistency Assumed** | Distributed system treating eventual consistency as strong | High |
| **Happy Path Only** | Spec covers success but not partial failure | High |
| **Error Swallowing** | Exceptions caught but not logged or handled | High |
| **Implicit Global State** | Module depends on state it doesn't own | Medium |
| **Test Theater** | Tests that always pass regardless of behavior | Critical |

When a design philosophy trap is detected, name it explicitly rather than describing the symptom abstractly.

---

## Multi-LLM Adversarial Extension

When secondary model API keys are available in the environment (`OPENAI_API_KEY`, `GEMINI_API_KEY`), adversarial analysis runs across models.

**Protocol:**
1. Run the same adversarial prompt against each available model
2. Collect findings from all models
3. Compare: which findings appear in 2+ models?
4. Tag findings:
   - `[cross-model confirmed]` — found by 2+ models
   - `[single-model]` — found by only one model

**Report order:** Cross-model confirmed findings surface first, regardless of severity. A Medium finding confirmed by 3 models is more reliable than a Critical finding from one model.

**Rationale:** Each model has distinct training distributions and blind spots. A finding that survives across models is less likely to be a model-specific artifact and more likely to reflect a genuine issue. This does not require models to agree on severity — one confirmation is sufficient for elevation.

**When no secondary keys are available:** Adversarial runs on primary model only. Note `[single-model analysis]` in the output header so humans know the extension did not run.

---

## Yield Tracking

Adversarial yield = (findings surfaced) / (total adversarial passes run).

| Yield Range | Signal | Action |
|-------------|--------|--------|
| 0–20% | Adversarial is rubber-stamping | Increase adversarial depth; check if Critic assumptions are too weak |
| 20–80% | Healthy | No adjustment needed |
| 80–100% | Inputs are systematically broken | Fix upstream quality (Builder prompts, Strategist context) — not just Critic settings |

Track yield across a session. A single outlier is not a signal. A consistent pattern is.
