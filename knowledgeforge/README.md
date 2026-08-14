# KnowledgeForge 7.26

Structured reasoning infrastructure embedded in Forge. Provides decision classification,
9 specialized reasoning modes, adversarial verification, and multi-LLM critic patterns.

## Usage in Forge

These files are loaded as system prompt context for Claude API calls via `load_kf_context()`.
The PatternStore also indexes them for retrieval during task decomposition and fix generation.

## Files

| File | Purpose |
|------|---------|
| `00_Project_Instructions.md` | Core system prompt — decision classification + always-on patches + mode routing table |
| `01_Decision_Classification.md` | Reckoning / Evaluative / Predictive / Novel taxonomy |
| `02_Mode_Routing.md` | All 9 mode activation triggers and chaining rules |
| `03_Builder_Agent.md` | PDIA method for specifications and implementations |
| `04_Expert_Agent.md` | Adversarial depth analysis — compound failures, blast radius, assumption inversion |
| `05_Critic_Agent.md` | Quality assurance — regular, adversarial, linter, multi-LLM variants |
| `06_Debugger_Agent.md` | Hypothesis testing to root cause (≥0.8 confidence gate) |
| `07_Strategist_Agent.md` | Trade-off analysis with reversibility assessment |
| `08_Coordinator_Agent.md` | Multi-agent workflow design via dependency-first DAG |
| `09_Synthesizer_Agent.md` | Pattern extraction with mandatory anti-patterns |
| `10_Navigator_Agent.md` | Disambiguation — fires only on genuine ambiguity |
| `11_Adversarial_Patterns.md` | Circuit breakers, auto-trigger conditions, multi-LLM adversarial extension |

## Multi-LLM Adversarial Critic

When `OPENAI_API_KEY` or `GEMINI_API_KEY` is set, the adversarial critic runs across multiple
models. Cross-model confirmed findings (present in ≥2 models) are surfaced first. See
`src/forge/layers/critic.py` and `11_Adversarial_Patterns.md`.

## Version History

| Version | Highlights |
|---------|------------|
| 7.26 | 9 modes, decision classification, adversarial auto-trigger, multi-LLM critic, circuit breakers |
| 4.0 | 4 modes (Navigator, Builder, Coordinator, Expert), PDIA, coordination patterns |
