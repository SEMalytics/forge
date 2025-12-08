# 02\_Workflows\_Agents

# KnowledgeForge 3.1: Agent Workflow Integration

---

## title: "Agent Workflow Integration"

module: "02\_Workflows" topics: \["agent communication", "workflow coordination", "multi-agent systems", "agent routing", "performance monitoring"\] contexts: \["agent integration", "workflow automation", "system coordination", "performance optimization"\] difficulty: "intermediate" related\_sections: \["ImplementationGuide", "WorkflowRegistry", "AgentCatalog", "DataTransfer"\]

## Core Approach

This module defines comprehensive workflows for agent integration within KnowledgeForge 3.1. It covers agent communication patterns, multi-agent coordination, lifecycle management, and performance monitoring. All agent configurations are consolidated in `03_Agents_Catalog.md`, while workflow implementations are documented in `02_N8N_WorkflowRegistry.md`.

## Agent Communication Workflows

### Basic Agent Request Processing

```json
{
  "name": "Basic Agent Request",
  "description": "Handle individual agent requests with context management",
  "trigger": "webhook",
  "nodes": [
    {
      "parameters": {
        "functionCode": `
// Basic agent request processing workflow
// Updated to reference consolidated agent catalog

async function processAgentRequest(agentRequest) {
  const request = {
    requestId: agentRequest.requestId || generateRequestId(),
    agentId: agentRequest.agentId,
    agentType: agentRequest.agentType || 'navigator',
    query: agentRequest.query || agentRequest.payload?.query,
    context: agentRequest.context || {},
    metadata: {
      timestamp: new Date().toISOString(),
      source: 'agent_workflow',
      processingStart: Date.now()
    }
  };

  // Agent selection logic references consolidated catalog
  // See 03_Agents_Catalog.md for complete agent configurations
  const agentConfig = await getAgentConfiguration(request.agentType);
  if (!agentConfig) {
    return {
      success: false,
      error: 'Agent type not found in catalog',
      availableTypes: ['navigator', 'expert', 'utility', 'custom'],
      catalogReference: '03_Agents_Catalog.md'
    };
  }

  // Process request with agent
  try {
    const agentResponse = await invokeAgent(agentConfig, request);
    const processedResponse = await postprocessResponse(agentResponse, request.context);
    
    return {
      success: true,
      requestId: request.requestId,
      agentType: request.agentType,
      response: processedResponse.enhancedResponse,
      metrics: {
        processingTime: Date.now() - request.metadata.processingStart,
        agentResponseTime: agentResponse.responseTime,
        qualityScore: processedResponse.qualityScore,
        compressionRatio: agentResponse.compressionRatio || null
      },
      references: {
        agentConfig: '03_Agents_Catalog.md',
        workflowDocs: '02_N8N_WorkflowRegistry.md',
        implementation: '00_KB3_ImplementationGuide.md'
      }
    };
  } catch (error) {
    return {
      success: false,
      error: error.message,
      requestId: request.requestId,
      troubleshooting: 'See 00_KB3_ImplementationGuide.md - Troubleshooting section'
    };
  }
}

async function getAgentConfiguration(agentType) {
  // Reference consolidated agent catalog
  // All agent configurations are now in 03_Agents_Catalog.md
  const agentConfigurations = {
    'navigator': {
      id: 'navigator-001',
      type: 'claude-project',
      capabilities: ['knowledge_discovery', 'decision_guidance'],
      endpoint: process.env.NAVIGATOR_AGENT_URL,
      catalogReference: '03_Agents_Catalog.md - Navigator Agent section'
    },
    'expert': {
      id: 'expert-001', 
      type: 'claude-project',
      capabilities: ['domain_analysis', 'technical_expertise'],
      endpoint: process.env.EXPERT_AGENT_URL,
      catalogReference: '03_Agents_Catalog.md - Expert Agent section'
    },
    'utility': {
      id: 'utility-001',
      type: 'api',
      capabilities: ['data_processing', 'format_conversion'],
      endpoint: process.env.UTILITY_AGENT_URL,
      catalogReference: '03_Agents_Catalog.md - Utility Agent section'
    },
    'custom': {
      id: 'custom-001',
      type: 'custom',
      capabilities: ['specialized_tasks'],
      endpoint: process.env.CUSTOM_AGENT_URL,
      catalogReference: '03_Agents_Catalog.md - Custom Agent section'
    }
  };
  
  return agentConfigurations[agentType] || null;
}

// ... [Additional functions would continue here - truncated for space]

// Execute the workflow
const result = await processAgentRequest(agentRequest);
return { json: result };
`
      },
      "id": "basic_agent_request",
      "name": "Basic Agent Request",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    }
  ]
}

Next Steps
1️⃣ Review agent catalog → Check 03_Agents_Catalog.md for available agent configurations 
2️⃣ Deploy workflow templates → Import workflows from 02_N8N_WorkflowRegistry.md 
3️⃣ Follow setup procedures → Use 00_KB3_ImplementationGuide.md for deployment 
4️⃣ Test agent coordination → Validate multi-agent collaboration patterns 
5️⃣ Monitor performance → Track agent response times and success rates


```

