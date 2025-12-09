# Agent Coordination Patterns

## Module Metadata

```yaml
module:
  title: Agent Coordination Patterns
  purpose: Design multi-agent workflows with proper sequencing, handoffs, and conflict resolution
  topics: [coordination, multi-agent, workflows, handoffs, orchestration]
  contexts: [complex-tasks, agent-teams, workflow-design]
  difficulty: advanced
  related: [01_Navigator_Agent, 02_Builder_Agent, 04_Specification_Templates]
```

---

## Core Approach

Multi-agent systems fail when handoffs lose context or when agents step on each other's work. Good coordination is about clear sequencing, preserved context, and explicit conflict resolution.

**Primary challenge:** Getting agents to work together without losing information or duplicating effort.

**Key insight:** Define the coordination pattern BEFORE building the agents.

---

## The Four Coordination Patterns

### 1. Sequential

```
A → B → C → output
```

**Use when:** Each step requires the previous step's output.

**Example:**
```
Navigator → Expert → Builder → user
(route)     (analyze) (create)
```

**Rules:**
- Each agent completes fully before handoff
- Output of A becomes input of B
- No backtracking (if you need iteration, use hierarchical)
- Clear completion criteria at each step

**Handoff format:**
```yaml
sequential_handoff:
  from: agent_a
  to: agent_b
  payload:
    result: [A's complete output]
    original_request: [what started this chain]
    chain_position: 2 of 3
  instruction: [specific task for B]
```

---

### 2. Parallel

```
        ┌→ A ─┐
input ──┼→ B ─┼→ Aggregator → output
        └→ C ─┘
```

**Use when:** Multiple independent perspectives improve the result.

**Example:**
```
request → [Legal Expert, Technical Expert, Business Expert] → Synthesis → recommendation
```

**Rules:**
- All parallel agents receive the same input
- Agents work independently (no cross-talk)
- Aggregator resolves differences
- Define aggregation logic before execution

**Handoff format:**
```yaml
parallel_dispatch:
  from: coordinator
  to: [agent_a, agent_b, agent_c]
  payload:
    shared_input: [same for all]
    perspective_requested: [what angle each should take]
  aggregation:
    handler: aggregator_agent | coordinator
    strategy: synthesize | vote | weighted
    conflict_resolution: [explicit rule]
```

**Aggregation strategies:**

| Strategy | Use When | How It Works |
|----------|----------|--------------|
| Synthesize | Complementary outputs | Combine into unified whole |
| Vote | Discrete options | Majority or plurality wins |
| Weighted | Expertise varies | Weight by agent confidence or domain |
| First-valid | Speed matters | Take first response that meets criteria |

---

### 3. Hierarchical

```
           Coordinator
          /     |     \
         A      B      C
        /|\
       a b c
```

**Use when:** Complex orchestration requires dynamic routing and iteration.

**Example:**
```
Project Coordinator
├── Navigator (routes incoming)
├── Builder (creates on demand)
├── Expert Pool
│   ├── Legal Expert
│   ├── Technical Expert
│   └── Domain Expert
└── Quality Agent (validates outputs)
```

**Rules:**
- Coordinator has full visibility
- Subordinate agents report to Coordinator
- Coordinator can reassign, iterate, or terminate
- State lives with Coordinator, not agents

**Coordinator responsibilities:**
```yaml
coordinator_duties:
  routing: Determine which agent handles what
  sequencing: Order agent execution
  iteration: Re-run agents if output insufficient
  conflict_resolution: Decide when agents disagree
  state_management: Track progress and decisions
  termination: Know when task is complete
```

**Handoff format:**
```yaml
hierarchical_dispatch:
  coordinator: coordinator-001
  task_id: unique_task_identifier
  
  assignment:
    agent: agent_id
    task: [specific instruction]
    context: [relevant state]
    return_to: coordinator-001
    
  state:
    overall_goal: [what we're trying to achieve]
    completed: [what's done]
    pending: [what remains]
    blockers: [current issues]
```

---

### 4. Consensus

```
[A, B, C] ←→ deliberation ←→ unified output
```

**Use when:** Decision requires agreement across perspectives.

**Example:**
```
[Risk Agent, Opportunity Agent, Ethics Agent] → deliberation → investment recommendation
```

**Rules:**
- Agents share and critique each other's outputs
- Explicit stopping condition (agreement threshold or max rounds)
- Facilitator manages the process
- Document the reasoning, not just the conclusion

**Consensus protocol:**
```yaml
consensus_config:
  participants: [agent_a, agent_b, agent_c]
  facilitator: consensus_facilitator | coordinator
  
  process:
    max_rounds: 3
    agreement_threshold: 0.8  # 80% alignment
    
  round_structure:
    1_initial: Each agent provides position
    2_critique: Each agent responds to others
    3_synthesis: Attempt unified position
    
  deadlock_resolution:
    strategy: facilitator_decides | escalate_to_human | majority_with_dissent_noted
```

---

## Context Preservation

The most common failure mode: losing context in handoffs.

### What to Preserve

```yaml
context:
  session:
    id: unique_session_identifier
    started: timestamp
    current_step: where we are in the workflow
    
  user:
    expertise_level: beginner | intermediate | advanced
    stated_goals: [explicit requests]
    inferred_goals: [what they probably need]
    constraints: [limits they've mentioned]
    
  task:
    objective: [end goal]
    completed: [done items]
    pending: [remaining items]
    blockers: [current issues]
    
  decisions:
    - decision: what was decided
      by: which agent
      reasoning: why
      timestamp: when
      reversible: true | false
```

### Handoff Protocol

Every handoff includes:

1. **What happened** — Agent's output/conclusion
2. **What was learned** — New information discovered
3. **What to do next** — Instruction for receiving agent
4. **What context carries forward** — Relevant state

```yaml
handoff:
  from: source_agent
  to: target_agent
  
  what_happened:
    action_taken: [what source agent did]
    result: [outcome]
    confidence: [how sure]
    
  what_was_learned:
    new_information: [discoveries]
    updated_understanding: [changed beliefs]
    
  instruction:
    task: [specific action for target]
    constraints: [limits on target's work]
    expected_output: [what to return]
    
  context:
    [preserved context object]
```

---

## Conflict Resolution

When agents disagree:

### Resolution Matrix

| Conflict Type | Resolution Strategy |
|---------------|---------------------|
| Factual disagreement | Check sources, weight by expertise |
| Priority disagreement | Defer to Coordinator or user preference |
| Approach disagreement | Run both, compare results |
| Scope disagreement | Clarify with Navigator or user |

### Resolution Protocol

```yaml
conflict_resolution:
  detection:
    trigger: Outputs contradict or are incompatible
    
  classification:
    type: factual | priority | approach | scope
    severity: blocking | degrading | cosmetic
    
  resolution:
    factual:
      - Request sources from each agent
      - Weight by expertise domain
      - If still unclear, flag for human
      
    priority:
      - Check if user expressed preference
      - Default to Coordinator's judgment
      - Document the trade-off
      
    approach:
      - Can we run both? Compare results
      - If not, Coordinator decides
      - Note alternative in output
      
    scope:
      - Route back to Navigator for clarification
      - Get explicit boundaries before proceeding
```

---

## Communication Protocol

Standard message format between agents:

```yaml
message:
  id: unique_message_id
  timestamp: iso_datetime
  
  routing:
    from: source_agent_id
    to: target_agent_id
    conversation_id: tracks the thread
    
  type: request | response | notification | error
  
  content:
    action: what to do (for requests)
    result: what was done (for responses)
    data: relevant payload
    
  metadata:
    priority: normal | high | urgent
    timeout: seconds_to_wait_for_response
    retry_policy: none | once | exponential
```

---

## Pattern Selection Guide

```
START: What does your task require?

├── Single expertise needed
│   └── Sequential: Navigator → Expert → Output
│
├── Multiple independent perspectives
│   └── Parallel: Input → [Experts] → Aggregator
│
├── Complex orchestration with iteration
│   └── Hierarchical: Coordinator managing specialist pool
│
├── Agreement required across viewpoints
│   └── Consensus: Deliberation until alignment
│
└── Unsure
    └── Start with Sequential, evolve as needed
```

---

## Example: Research Task Coordination

**Task:** Produce a comprehensive analysis on a complex topic.

**Pattern:** Hierarchical with parallel sub-tasks

```yaml
coordination:
  pattern: hierarchical
  
  structure:
    coordinator: research-coordinator-001
    
    phase_1_parallel:
      agents: [domain-expert-001, domain-expert-002, domain-expert-003]
      task: Initial research from each perspective
      aggregation: synthesize
      
    phase_2_sequential:
      sequence:
        - agent: analyst-001
          task: Identify gaps and conflicts in phase 1 output
        - agent: researcher-001
          task: Fill gaps identified
        - agent: synthesizer-001
          task: Produce unified analysis
          
    phase_3_consensus:
      agents: [quality-001, domain-expert-001, analyst-001]
      task: Validate final analysis
      threshold: 0.9
      
  completion_criteria:
    - All phases complete
    - Consensus achieved or dissent documented
    - Quality validation passed
```

---

## Next Steps

After understanding coordination patterns:

1. **Choose your pattern** → Use the selection guide above
2. **Design your coordinator** → If using hierarchical, build this first
3. **Define handoff formats** → Customize context objects for your domain
4. **Plan conflict resolution** → Know how disagreements will be handled
5. **Build agents** → `02_Builder_Agent.md` for each specialist needed
6. **Test handoffs** → Simulate coordination before full deployment

Related modules:
- `01_Navigator_Agent.md` — The routing agent in most patterns
- `02_Builder_Agent.md` — Creating the specialist agents
- `04_Specification_Templates.md` — Standard formats for coordination configs
