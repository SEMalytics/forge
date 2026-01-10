# KnowledgeForge 4.0

**A framework for building intelligent AI agents with structured reasoning patterns.**

KnowledgeForge has been developed over 2 years to provide a systematic approach to AI agent design. Version 4.0 introduces the PDIA method for agent creation and comprehensive coordination patterns for multi-agent workflows.

> **Note:** This is KnowledgeForge 4.0. Version 5.0 exists but is not publicly released.

---

## What is KnowledgeForge?

KnowledgeForge is a collection of specifications and patterns that transform general-purpose LLMs into specialized, reliable agents. It provides:

- **Structured reasoning patterns** — Consistent approach to every interaction
- **Agent creation methodology** — The PDIA method for building new agents
- **Coordination patterns** — Sequential, parallel, hierarchical, and consensus workflows
- **Specification templates** — Reusable formats for complete, implementable specs

### The Core Pattern

```
UNDERSTAND → REASON → SPECIFY → NAVIGATE
```

Every interaction follows this flow. No exceptions.

---

## Quick Start

### Option 1: Claude Projects

1. Create a new Project in Claude (claude.ai)
2. Go to **Project Knowledge**
3. Upload all `.md` files from this directory:
   - `00_Project_Instructions.md` (required - core system behavior)
   - `01_Navigator_Agent.md`
   - `02_Builder_Agent.md`
   - `03_Coordination_Patterns.md`
   - `04_Specification_Templates.md`
   - `05_Expert_Agent_Example.md`
   - `06_Quick_Reference.md`

4. Start a conversation. Claude will now operate with KnowledgeForge patterns.

### Option 2: ChatGPT Custom GPT

1. Go to **Explore GPTs** → **Create**
2. In the **Configure** tab:
   - Name: `KnowledgeForge Agent`
   - Description: `AI agent framework with structured reasoning and multi-agent coordination`
3. In **Instructions**, paste the contents of `00_Project_Instructions.md`
4. Under **Knowledge**, upload the remaining `.md` files
5. Save and publish (private or public)

### Option 3: API Integration

For programmatic use, concatenate the files into your system prompt:

```python
import os
from pathlib import Path

def load_knowledgeforge(directory: str = "knowledgeforge") -> str:
    """Load KnowledgeForge specs into a single system prompt."""
    files = sorted(Path(directory).glob("*.md"))

    sections = []
    for f in files:
        if f.name == "README.md":
            continue
        sections.append(f"# {f.stem}\n\n{f.read_text()}")

    return "\n\n---\n\n".join(sections)

# Use with Anthropic API
from anthropic import Anthropic

client = Anthropic()
system_prompt = load_knowledgeforge()

response = client.messages.create(
    model="claude-sonnet-4-5-20250514",
    max_tokens=4096,
    system=system_prompt,
    messages=[{"role": "user", "content": "Build me an agent for code review"}]
)
```

---

## Module Overview

| File | Purpose |
|------|---------|
| `00_Project_Instructions.md` | Core system prompt — defines base behavior |
| `01_Navigator_Agent.md` | Intent interpretation and routing patterns |
| `02_Builder_Agent.md` | Agent creation using PDIA method |
| `03_Coordination_Patterns.md` | Multi-agent workflow orchestration |
| `04_Specification_Templates.md` | Reusable specification formats |
| `05_Expert_Agent_Example.md` | Domain specialist implementation pattern |
| `06_Quick_Reference.md` | Quick lookup for all patterns |

---

## Agent Modes

KnowledgeForge operates in four modes based on user needs:

| Mode | When to Use | What It Does |
|------|-------------|--------------|
| **Navigator** | Unclear intent, routing needed | Interprets true need, routes to right resource |
| **Builder** | "Create an agent for..." | Generates complete agent specs using PDIA |
| **Coordinator** | Multi-agent workflows | Designs handoffs, resolves conflicts |
| **Expert** | Domain-specific questions | Deep reasoning within specialty bounds |

---

## The PDIA Method

When building new agents, KnowledgeForge uses the PDIA method:

**P**urpose
> One sentence. What problem does this agent solve?

**D**esign
> Capabilities, inputs, outputs, constraints, integration points

**I**mplementation
> System prompt that defines behavior (not personality)

**A**ssessment
> Success criteria, test scenarios, failure modes

---

## Coordination Patterns

```
Sequential:    A → B → C → output
Parallel:      [A, B, C] → Aggregator → output
Hierarchical:  Coordinator → [agents] → synthesis
Consensus:     [agents] ↔ deliberation ↔ unified
```

**Choose Sequential** when each step needs previous output.
**Choose Parallel** when multiple perspectives improve results.
**Choose Hierarchical** when you need iteration and dynamic routing.
**Choose Consensus** when decisions require agreement.

---

## Example: Creating an Agent

**User:** "Build me an agent for customer support"

**KnowledgeForge Response:**

```yaml
# Customer Support Agent Specification

## Purpose
Handle customer inquiries by understanding issues, providing solutions,
and escalating when necessary.

## Design

### Capabilities
Primary:
  - Issue classification (billing, technical, general)
  - Solution retrieval from knowledge base
  - Sentiment detection

Secondary:
  - Escalation to human agents
  - Ticket creation and tracking

### Inputs
- customer_message: string (required)
- customer_id: string (optional, for context)
- conversation_history: array (optional)

### Outputs
- response: string
- action_taken: enum [answered, escalated, ticket_created]
- confidence: float (0-1)

### Constraints
- Never promise refunds directly (escalate to billing)
- Response time target: <3 seconds
- Escalate if confidence <0.7

## Implementation

[System prompt that defines behavior...]

## Assessment

### Success Criteria
- Resolution rate >80% without escalation
- Customer satisfaction >4.0/5.0
- Escalation accuracy >95%

### Test Scenarios
1. Simple billing question → Direct answer
2. Complex technical issue → Structured troubleshooting
3. Angry customer → Empathy + escalation path
```

---

## Best Practices

### Do
- Behavior over description ("Responds with..." not "Is helpful...")
- Boundaries over permissions ("Never..." is clearer than "Can...")
- Examples over rules (show, don't just tell)
- Complete specifications (implementable without questions)

### Don't
- "You are a helpful assistant..." (too generic)
- "Try to..." / "Attempt to..." (hedging)
- Personality descriptions (focus on behavior)
- Incomplete specs (forces follow-up questions)

---

## Version History

| Version | Highlights |
|---------|------------|
| 4.0 | PDIA method, coordination patterns, specification templates |
| 3.x | Navigator and Builder agents, intent routing |
| 2.x | Core reasoning patterns, response structures |
| 1.x | Initial framework, basic agent definitions |

---

## Integration with Forge

KnowledgeForge 4.0 is integrated into [Forge](../README.md), an AI development orchestration system. Forge uses KnowledgeForge patterns for:

- Planning agent behavior
- Code review agent specifications
- Multi-agent coordination during code generation
- Pattern-driven task decomposition

---

## License

KnowledgeForge 4.0 is provided as part of the Forge project. See the main repository for license details.

---

## Questions?

If you're using KnowledgeForge and have questions about agent design patterns, coordination strategies, or specification formats, the framework itself can help — just ask it to switch to the appropriate mode (Navigator, Builder, Coordinator, or Expert).
