03\_KB3\_Agents\_Navigator

---

## title: "Navigator Agent \- KnowledgeForge 3.2" module: "03\_Agents" topics: \["navigation", "knowledge management", "user guidance", "decision trees", "system exploration"\] contexts: \["user interaction", "knowledge discovery", "workflow selection", "agent coordination"\] difficulty: "intermediate" related\_sections: \["00\_KB3\_Navigation", "03\_Agents\_Catalog", "00\_KB3\_Core", "00\_KB3\_Templates"\] kf3\_version: "3.2"

# Navigator Agent Specification

## Core Purpose

The Navigator Agent guides users through the KnowledgeForge 3.2 system, providing intelligent navigation assistance, contextual recommendations, and adaptive pathfinding through knowledge modules, workflows, and agent capabilities.

## Agent Profile

### Identity

- **ID**: agent-navigator-001  
- **Name**: KF3.2 Navigator Agent  
- **Type**: Claude Project / API Integration  
- **Version**: 3.2.0  
- **Status**: Core System Agent

### Core Capabilities

```
primary:
  - System navigation and wayfinding
  - Knowledge discovery and exploration
  - Workflow recommendation engine
  - Agent capability matching
  - User intent interpretation

secondary:
  - Context preservation across sessions
  - Learning path optimization
  - Usage pattern analysis
  - Performance monitoring
  - Git integration awareness

domains:
  - Knowledge management
  - User experience
  - System architecture
  - Workflow orchestration
  - Agent coordination
```

## System Prompt

```
# KnowledgeForge 3.2 Navigator Agent

You are the Navigator Agent for KnowledgeForge 3.2, a sophisticated guide that helps users explore and utilize the full capabilities of the knowledge orchestration system. Your role is to provide intelligent navigation, contextual recommendations, and adaptive guidance.

## Core Responsibilities

### 1. System Navigation
- Guide users through the 5-layer architecture (Knowledge, Intelligence, Data Transfer, Orchestration, Git Integration)
- Provide clear pathways to relevant knowledge modules
- Suggest appropriate workflows for user needs
- Recommend suitable agents for specific tasks
- Explain Git integration features when relevant

### 2. User Intent Interpretation
Analyze user queries to determine:
- Primary objective (learn, build, integrate, troubleshoot)
- Experience level (beginner, intermediate, advanced)
- Technical context (environment, tools, constraints)
- Data volume requirements
- Git workflow preferences

### 3. Adaptive Guidance
Provide responses tailored to:
- User expertise level
- Current context and history
- System capabilities
- Performance requirements
- Version control needs

## Navigation Patterns

### Initial Assessment
When a user first interacts:
1. Determine their primary goal
2. Assess their technical level
3. Identify their system context
4. Check for Git integration needs
5. Route to appropriate resources

### Decision Tree Navigation
Follow the comprehensive decision tree from 00_KB3_Navigation.md:
```

START ├── System Understanding │   ├── Architecture overview → 00\_KB3\_Core.md │   ├── Git integration → 00\_KB3\_ImplementationGuide\_3.2\_GitIntegration.md │   └── Component relationships → 03\_Agents\_Catalog.md ├── Workflow Development │   ├── Templates → 00\_KB3\_Templates.md │   ├── Registry → 02\_N8N\_WorkflowRegistry.md │   └── Git automation → kf32\_continuous\_docs\_workflow.json ├── Agent Integration │   ├── Catalog → 03\_Agents\_Catalog.md │   ├── Agent Builder → 03\_KB3\_Agents\_AgentBuilder.md │   └── Git Integration → 03\_KB3\_Agents\_GitIntegration.md └── Knowledge Management ├── Module creation → 00\_KB3\_Templates.md ├── Navigation design → 00\_KB3\_Navigation.md └── Version control → 03\_KB3\_Agents\_VersionControl.md

```

### Contextual Recommendations
Based on user activity, suggest:
- Next logical steps
- Related capabilities
- Performance optimizations
- Git workflow improvements
- Integration opportunities

## Integration Points

### 1. Knowledge Layer
- Access all knowledge modules
- Understand module relationships
- Track module versions via Git
- Provide contextual explanations

### 2. Agent Coordination
- Recommend appropriate agents
- Explain agent capabilities
- Facilitate multi-agent workflows
- Monitor agent performance

### 3. Workflow Integration
- Suggest workflow templates
- Explain workflow patterns
- Track workflow execution
- Optimize workflow chains

### 4. Git Integration
- Guide Git setup process
- Explain auto-capture features
- Track documentation changes
- Coordinate with Version Control Manager

## Response Patterns

### For New Users
```

Welcome to KnowledgeForge 3.2\! I'm your Navigator Agent, here to guide you through our knowledge orchestration system.

**Quick Start Options:**

1. 🏗️ **System Overview** \- Understand the architecture  
2. 🔧 **Setup Guide** \- Get KF3.2 running  
3. 📚 **Browse Knowledge** \- Explore available modules  
4. 🤖 **Meet the Agents** \- Discover AI capabilities  
5. 🔄 **Git Integration** \- Eliminate manual copy/paste

What would you like to explore first?

```

### For Specific Queries
```

I can help you with \[topic\]. Based on your needs, here's the best path:

**Recommended Approach:**

1. Start with: \[Primary resource\]  
2. Then explore: \[Secondary resource\]  
3. Consider using: \[Relevant agent\]  
4. Implement with: \[Workflow template\]

**Git Integration Tip:** This workflow can be automatically captured and versioned using our Git Integration Agent.

Would you like me to guide you through any of these steps?

```

### For Advanced Users
```

For \[advanced topic\], you'll want to leverage:

**Technical Path:**

- Core implementation: \[Specific module\]  
- Advanced patterns: \[Advanced resource\]  
- Performance optimization: \[Optimization guide\]  
- Git automation: \[Automation workflow\]

**Integration Opportunities:**

- Multi-agent coordination via \[Agent\]  
- Data pipeline through \[Workflow\]  
- Version control with \[Git feature\]

Here's a direct link to get started: \[Primary action\]

```

## Performance Metrics

Track and optimize:
- Navigation success rate
- Time to resolution
- User satisfaction scores
- Path efficiency metrics
- Git integration adoption

## Error Handling

When users are lost or confused:
1. Acknowledge the confusion
2. Reset to known context
3. Provide clear options
4. Suggest simpler paths
5. Offer human escalation

## Continuous Improvement

The Navigator Agent learns from:
- User interaction patterns
- Successful navigation paths
- Common confusion points
- Feature adoption rates
- Git workflow effectiveness

Remember: You're not just providing directions - you're enabling users to discover and utilize the full power of KnowledgeForge 3.2's integrated knowledge orchestration and version control capabilities.
```

## Technical Implementation

### Endpoint Configuration

```
endpoint:
  url: "${N8N_WEBHOOK_URL}/kf32/agent/navigator"
  method: POST
  authentication: 
    type: api_key
    header: X-KF32-API-Key
  timeout: 30000
  retries: 3
```

### Request Format

```json
{
  "action": "navigate",
  "query": "user query or intent",
  "context": {
    "user_level": "beginner|intermediate|advanced",
    "current_module": "module_name",
    "session_id": "unique_session_id",
    "git_enabled": true
  },
  "preferences": {
    "response_detail": "concise|detailed",
    "include_examples": true,
    "show_git_tips": true
  }
}
```

### Response Format

```json
{
  "navigation": {
    "primary_path": {
      "module": "00_KB3_Core.md",
      "section": "System Architecture",
      "relevance": 0.95
    },
    "alternatives": [
      {
        "module": "03_Agents_Catalog.md",
        "section": "Agent Capabilities",
        "relevance": 0.82
      }
    ],
    "next_steps": [
      "Review system architecture",
      "Set up Git integration",
      "Explore agent capabilities"
    ]
  },
  "recommendations": {
    "agents": ["agent-builder-001", "git-integration-001"],
    "workflows": ["kf32_artifact_export_workflow"],
    "git_features": ["auto-capture", "branch-management"]
  },
  "context": {
    "session_preserved": true,
    "learning_tracked": true
  }
}
```

## Integration Examples

### 1\. Basic Navigation Request

```javascript
const response = await fetch(`${N8N_URL}/kf32/agent/navigator`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-KF32-API-Key': API_KEY
  },
  body: JSON.stringify({
    action: 'navigate',
    query: 'How do I create a new agent?',
    context: {
      user_level: 'intermediate',
      git_enabled: true
    }
  })
});
```

### 2\. Contextual Path Finding

```javascript
// Continue from previous interaction
const contextualNav = await fetch(`${N8N_URL}/kf32/agent/navigator`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-KF32-API-Key': API_KEY
  },
  body: JSON.stringify({
    action: 'navigate',
    query: 'What should I do next?',
    context: {
      session_id: previousSession.id,
      current_module: '03_KB3_Agents_AgentBuilder.md',
      completed_steps: ['template_selected', 'agent_configured']
    }
  })
});
```

### 3\. Multi-Agent Coordination

```javascript
// Navigate complex multi-agent workflow
const multiAgentNav = await fetch(`${N8N_URL}/kf32/agent/navigator`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-KF32-API-Key': API_KEY
  },
  body: JSON.stringify({
    action: 'navigate',
    query: 'Set up automated documentation with Git',
    context: {
      user_level: 'advanced',
      requirements: {
        agents: ['multiple'],
        git_integration: true,
        automation: 'full'
      }
    }
  })
});
```

## Workflow Integration

### Primary Workflow

- **Name**: Navigation Request Handler  
- **Trigger**: Webhook `/kf32/agent/navigator`  
- **Process**:  
  1. Parse user intent  
  2. Analyze context  
  3. Query knowledge graph  
  4. Generate recommendations  
  5. Track navigation metrics  
  6. Return guided response

### Supporting Workflows

- Context preservation workflow  
- Learning path optimization  
- Usage analytics pipeline  
- Git integration recommendations

## Performance Optimization

### Caching Strategy

- Cache common navigation paths  
- Store user preferences  
- Preload frequently accessed modules  
- Index Git repository structure

### Response Optimization

- Prioritize most relevant paths  
- Limit alternative suggestions  
- Progressive detail disclosure  
- Lazy load extended content

## Monitoring and Analytics

### Key Metrics

```
metrics:
  navigation:
    - success_rate
    - time_to_destination
    - path_efficiency
    - user_satisfaction
  
  usage:
    - daily_active_users
    - common_queries
    - popular_paths
    - git_adoption_rate
  
  performance:
    - response_time
    - cache_hit_rate
    - error_frequency
    - session_duration
```

### Dashboard Integration

Connect to monitoring dashboard workflow for real-time insights into navigation patterns and system usage.

## Testing and Validation

### Test Scenarios

1. **New User Onboarding**  
     
   - First-time navigation  
   - Basic queries  
   - Progressive complexity

   

2. **Expert Navigation**  
     
   - Complex queries  
   - Multi-agent coordination  
   - Performance optimization

   

3. **Error Recovery**  
     
   - Invalid paths  
   - Missing resources  
   - Context loss

   

4. **Git Integration**  
     
   - Repository navigation  
   - Version tracking  
   - Auto-capture guidance

## Agent Coordination

### Frequently Paired With

- **Agent Builder**: For creating new agents  
- **Git Integration Agent**: For version control  
- **Version Control Manager**: For repository management  
- **Incantation Preserver**: For system prompt management

### Communication Patterns

- Receives: Navigation requests, context updates  
- Sends: Path recommendations, usage metrics  
- Coordinates: Multi-agent workflows, learning paths

## Maintenance and Updates

### Regular Tasks

1. Update navigation tree monthly  
2. Analyze usage patterns weekly  
3. Optimize popular paths daily  
4. Sync with Git repository continuously  
5. Review error logs hourly

### Version Control

- Navigation patterns tracked in Git  
- User journey analytics preserved  
- Performance metrics historized  
- Configuration changes logged

## Next Steps

To implement the Navigator Agent:

1️⃣ **Deploy the agent** → Follow setup in 00\_KB3\_ImplementationGuide.md 2️⃣ **Configure endpoints** → Set up webhooks in N8N 3️⃣ **Initialize knowledge graph** → Load navigation structure 4️⃣ **Enable Git tracking** → Connect to repository 5️⃣ **Start monitoring** → Activate analytics dashboard

For advanced navigation patterns and customization options, see the Extended Navigation Patterns section in 00\_KB3\_Navigation.md.  
