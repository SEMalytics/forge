# Specification Templates

## Module Metadata

```yaml
module:
  title: Specification Templates
  purpose: Provide complete, reusable templates for agents, processes, and coordination
  topics: [templates, specifications, formats, schemas]
  contexts: [agent-creation, process-design, documentation]
  difficulty: intermediate
  related: [02_Builder_Agent, 03_Coordination_Patterns]
```

---

## Core Approach

A specification is complete when another agent or human can implement it without asking clarifying questions. These templates ensure nothing is forgotten.

---

## Agent Specification Template

```yaml
agent:
  # IDENTITY
  id: [unique-identifier]  # e.g., "navigator-001"
  name: [Human-readable name]
  version: [semantic version]  # e.g., "1.0.0"
  
  # PURPOSE (one sentence)
  purpose: [What specific problem does this agent solve?]
  
  # CAPABILITIES
  capabilities:
    primary:  # Core functions—what it MUST do
      - [capability_1]
      - [capability_2]
    secondary:  # Supporting functions—what helps it do the core
      - [capability_3]
      - [capability_4]
    domains:  # Knowledge areas
      - [domain_1]
      - [domain_2]
      
  # INPUTS
  inputs:
    - name: [input_name]
      type: string | number | boolean | object | array
      required: true | false
      description: [What this is and where it comes from]
      schema:  # If object or array
        [field]: [type]
      validation:  # Optional
        [rule]: [value]
        
  # OUTPUTS
  outputs:
    - name: [output_name]
      type: response | artifact | action | notification
      format: json | markdown | code | yaml
      structure:
        [field]: [type and description]
      examples:
        - [example output]
        
  # CONSTRAINTS (what it CANNOT do)
  constraints:
    - [explicit_boundary_1]
    - [explicit_boundary_2]
    - [resource_limit]
    - [scope_restriction]
    
  # INTEGRATION
  integration:
    receives_from:
      - agent_id: [source_agent]
        message_types: [what it receives]
    sends_to:
      - agent_id: [target_agent]
        message_types: [what it sends]
    coordination: sequential | parallel | hierarchical | consensus
    
  # ERROR HANDLING
  error_handling:
    - condition: [what could go wrong]
      response: [what agent does]
      escalation: [where to route if unresolvable]
      
  # SUCCESS CRITERIA
  success_criteria:
    - [measurable_outcome_1]
    - [measurable_outcome_2]
    
  # METADATA
  metadata:
    created: [date]
    author: [who created this]
    last_updated: [date]
    status: draft | active | deprecated
```

---

## System Prompt Template

```markdown
# [Agent Name]

## Purpose
[One sentence: what problem does this agent solve?]

## Capabilities
[Bullet list of specific actions this agent performs]
- [Action 1]
- [Action 2]
- [Action 3]

## Constraints
[Explicit boundaries—what this agent does NOT do]
- Do not [boundary 1]
- Do not [boundary 2]
- [Scope restriction]

## Response Patterns

**For [request type 1]:**
[Structure of response]

**For [request type 2]:**
[Structure of response]

## Integration

**Receives from:**
- [Agent]: [What to expect]

**Sends to:**
- [Agent]: [What to deliver]

**Handoff format:**
[Message structure for agent communication]

## Examples

**Input:** [Example request]
**Output:** [Example response]

---

**Input:** [Another example]
**Output:** [Corresponding response]
```

---

## Process Specification Template

```yaml
process:
  # IDENTITY
  id: [unique-identifier]
  name: [Human-readable name]
  version: [semantic version]
  
  # PURPOSE
  purpose: [Why this process exists]
  
  # TRIGGER
  trigger:
    type: event | schedule | request | condition
    source: [where trigger comes from]
    condition: [when this fires]
    
  # INPUTS
  inputs:
    - name: [input_name]
      type: [type]
      source: [where it comes from]
      required: true | false
      
  # STEPS
  steps:
    - id: step_1
      name: [Human-readable step name]
      agent: [agent_id that performs this]
      action: [what happens]
      inputs:
        - [from trigger or previous steps]
      outputs:
        - name: [output_name]
          type: [type]
      success_criteria: [how we know this step succeeded]
      error_handling:
        on_failure: retry | skip | abort | escalate
        max_retries: [number]
        fallback: [alternative action]
        
    - id: step_2
      # ... same structure
      depends_on: [step_1]  # Explicit dependency
      
  # BRANCHING (if needed)
  branches:
    - condition: [when this branch activates]
      steps: [step_ids to execute]
      
  # COMPLETION
  completion:
    success_criteria:
      - [overall success condition 1]
      - [overall success condition 2]
    outputs:
      - name: [final_output]
        type: [type]
        destination: [where it goes]
    next_steps:
      - [what happens after this process]
      
  # METADATA
  metadata:
    estimated_duration: [time]
    created: [date]
    owner: [responsible party]
```

---

## Message Template

```yaml
message:
  # ROUTING
  id: [unique_message_id]
  conversation_id: [thread_identifier]
  timestamp: [iso_datetime]
  
  from: [source_agent_id]
  to: [target_agent_id]
  
  # TYPE
  type: request | response | notification | error
  priority: low | normal | high | urgent
  
  # CONTENT
  content:
    # For requests:
    action: [what to do]
    parameters:
      [param]: [value]
    context:
      [relevant_state]
    expected_response:
      format: [expected format]
      deadline: [when needed]
      
    # For responses:
    status: success | partial | failure
    result:
      [output_data]
    confidence: [0.0-1.0]
    next_suggested: [follow-up action if any]
    
    # For errors:
    error_code: [code]
    error_message: [human-readable description]
    recovery_options:
      - [option_1]
      - [option_2]
      
  # METADATA
  metadata:
    timeout: [seconds]
    retry_count: [number]
    trace_id: [for debugging]
```

---

## Handoff Template

```yaml
handoff:
  # ROUTING
  id: [unique_handoff_id]
  timestamp: [iso_datetime]
  
  from: [source_agent_id]
  to: [target_agent_id]
  return_to: [agent_id | "user" | "none"]
  
  # WHAT HAPPENED
  source_action:
    task_completed: [what source agent did]
    result: [outcome]
    confidence: [0.0-1.0]
    
  # WHAT WAS LEARNED
  discoveries:
    new_information:
      - [discovery_1]
      - [discovery_2]
    updated_understanding:
      - [changed_belief_1]
    open_questions:
      - [question_1]
      
  # INSTRUCTION FOR TARGET
  instruction:
    task: [specific action required]
    constraints:
      - [limit_1]
      - [limit_2]
    expected_output:
      format: [format]
      structure: [schema]
    deadline: [if applicable]
    
  # PRESERVED CONTEXT
  context:
    original_request: [what started this]
    user_expertise: beginner | intermediate | advanced
    goals:
      stated: [explicit goals]
      inferred: [likely goals]
    constraints: [user-mentioned limits]
    decisions_made:
      - decision: [what]
        by: [who]
        reasoning: [why]
        reversible: true | false
    chain_position: [step X of Y]
```

---

## Context Object Template

```yaml
context:
  # SESSION
  session:
    id: [unique_session_id]
    started: [timestamp]
    current_phase: [where we are]
    
  # USER
  user:
    expertise_level: beginner | intermediate | advanced
    expertise_signals:
      - [signal that indicated level]
    stated_goals:
      - [explicit request 1]
      - [explicit request 2]
    inferred_goals:
      - goal: [what we think they need]
        confidence: [0.0-1.0]
        signal: [why we think this]
    constraints:
      - [limit_1]
      - [limit_2]
    preferences:
      format: [preferred output format]
      depth: [preferred detail level]
      
  # TASK
  task:
    objective: [end goal]
    completed:
      - step: [what was done]
        by: [which agent]
        when: [timestamp]
    pending:
      - step: [what remains]
        assigned_to: [agent or unassigned]
    blockers:
      - issue: [what's blocking]
        since: [timestamp]
        
  # DECISIONS
  decisions:
    - id: [decision_id]
      decision: [what was decided]
      by: [agent_id]
      reasoning: [why]
      timestamp: [when]
      reversible: true | false
      affects: [what this decision impacts]
```

---

## Assessment Template

```yaml
assessment:
  # WHAT WE'RE TESTING
  agent_id: [agent being assessed]
  version: [version tested]
  assessed_by: [who conducted assessment]
  date: [when]
  
  # SUCCESS CRITERIA
  success_criteria:
    - criterion: [measurable outcome]
      target: [specific threshold]
      actual: [measured result]
      passed: true | false
      
  # TEST SCENARIOS
  test_scenarios:
    - id: scenario_1
      name: [Human-readable name]
      description: [what this tests]
      input: [example input]
      expected_output: [what should happen]
      actual_output: [what did happen]
      passed: true | false
      notes: [observations]
      
  # FAILURE MODES
  failure_modes:
    - mode: [type of failure]
      condition: [what triggers it]
      frequency: rare | occasional | frequent
      severity: low | medium | high | critical
      mitigation: [how to handle]
      
  # QUALITY METRICS
  quality_metrics:
    relevance:
      score: [0-10]
      notes: [observations]
    completeness:
      score: [0-10]
      notes: [observations]
    accuracy:
      score: [0-10]
      notes: [observations]
    actionability:
      score: [0-10]
      notes: [observations]
      
  # SUMMARY
  summary:
    overall_status: pass | fail | conditional
    strengths:
      - [strength_1]
      - [strength_2]
    weaknesses:
      - [weakness_1]
      - [weakness_2]
    recommendations:
      - [recommendation_1]
      - [recommendation_2]
```

---

## Usage Notes

**When to use each template:**

| Template | Use When |
|----------|----------|
| Agent Specification | Creating a new agent |
| System Prompt | Implementing an agent in an AI system |
| Process Specification | Designing a multi-step workflow |
| Message | Defining agent-to-agent communication |
| Handoff | Designing transfer points between agents |
| Context | Tracking state through a session |
| Assessment | Validating agent or process quality |

**Template modification rules:**
- Add fields specific to your domain
- Remove optional fields you don't need
- Never remove required fields (marked in comments)
- Keep the structure even if content changes

---

## Next Steps

1. **Copy the template you need** → Modify for your specific use case
2. **Fill in all required fields** → Leave nothing as placeholder
3. **Validate completeness** → Could someone implement this without asking questions?
4. **Test with a real case** → Run through an actual scenario
5. **Iterate** → Refine based on what you learn

Related modules:
- `02_Builder_Agent.md` — Uses these templates to create agents
- `03_Coordination_Patterns.md` — Context for multi-agent templates
