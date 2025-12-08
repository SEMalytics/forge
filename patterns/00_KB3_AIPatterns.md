# 00\_KB3\_AIPatterns

# KnowledgeForge 3.0: AI Patterns and Claude Integration

---

## title: "AI Patterns and Claude Integration"

module: "00\_Framework" topics: \["ai patterns", "claude projects", "agent coordination", "intelligent automation", "GET requests"\] contexts: \["ai integration", "pattern implementation", "agent design", "workflow intelligence"\] difficulty: "advanced" related\_sections: \["Core", "Implementation", "Agent Registry", "Workflow Templates", "GET\_Implementation"\]

## Core Approach

This module defines advanced AI patterns specifically designed for KnowledgeForge 3.0's workflow-driven architecture. These patterns leverage Claude Projects, multi-agent coordination, and N8N workflow orchestration to create intelligent, adaptive knowledge systems that learn and evolve with usage. All patterns now support GET requests for Claude Projects compatibility.

## AI Pattern Categories

### 1\. Workflow Intelligence Patterns

#### Adaptive Routing Pattern

Automatically routes requests to optimal processing paths based on learned patterns.

```javascript
// Adaptive routing implementation with GET support
class AdaptiveRouter {
  constructor(webhookUrl) {
    this.webhookUrl = webhookUrl;
    this.routingHistory = new Map();
    this.performanceMetrics = new Map();
  }
  
  async route(request, context) {
    // Analyze request characteristics
    const signature = this.generateRequestSignature(request);
    
    // Get historical performance data
    const history = this.routingHistory.get(signature) || [];
    
    // Determine optimal route using ML-like scoring
    const routes = await this.getAvailableRoutes(request);
    const scoredRoutes = routes.map(route => ({
      route,
      score: this.calculateRouteScore(route, history, context)
    }));
    
    // Select best route
    const selectedRoute = scoredRoutes.sort((a, b) => b.score - a.score)[0];
    
    // Record decision for learning (via GET request)
    await this.recordRoutingDecision(signature, selectedRoute.route, context);
    
    return selectedRoute.route;
  }
  
  async recordRoutingDecision(signature, route, context) {
    // Use GET request for Claude compatibility
    const params = new URLSearchParams({
      action: 'record_routing',
      signature: signature,
      routeId: route.id,
      context: JSON.stringify(context),
      timestamp: Date.now()
    });
    
    // Fire and forget for performance
    fetch(`${this.webhookUrl}/analytics?${params}`).catch(() => {});
  }
  
  calculateRouteScore(route, history, context) {
    let score = 0;
    
    // Base capability match
    score += this.calculateCapabilityMatch(route, context.requiredCapabilities) * 40;
    
    // Historical success rate
    const routeHistory = history.filter(h => h.route === route.id);
    if (routeHistory.length > 0) {
      const successRate = routeHistory.filter(h => h.success).length / routeHistory.length;
      score += successRate * 30;
    }
    
    // Current load factor (retrieved via GET)
    const loadFactor = this.getCurrentLoad(route);
    score += (1 - loadFactor) * 20;
    
    // Context preferences
    if (context.userPreferences && context.userPreferences[route.id]) {
      score += context.userPreferences[route.id] * 10;
    }
    
    return score;
  }
  
  async getCurrentLoad(route) {
    // GET request to check current load
    const response = await fetch(`${this.webhookUrl}/metrics?routeId=${route.id}`);
    const data = await response.json();
    return data.loadFactor || 0.5;
  }
}

// N8N Workflow Integration with GET support
{
  "name": "Adaptive Request Router",
  "nodes": [
    {
      "parameters": {
        "path": "router/adaptive",
        "responseMode": "responseNode",
        "options": {
          "responseHeaders": {
            "entries": [
              {
                "name": "Access-Control-Allow-Methods",
                "value": "GET, POST"
              }
            ]
          }
        }
      },
      "name": "Adaptive Router Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "functionCode": `
// Handle both GET and POST requests
const method = $json.method || 'GET';
let request, context;

if (method === 'GET') {
  // Parse GET parameters
  request = {
    type: $json.query.type,
    capabilities: $json.query.capabilities?.split(',') || [],
    priority: $json.query.priority || 'normal'
  };
  context = $json.query.context ? JSON.parse($json.query.context) : {};
} else {
  // Handle POST body
  request = $json.body.request;
  context = $json.body.context;
}

const router = new AdaptiveRouter();

// Get optimal route
const selectedRoute = await router.route(request, {
  requiredCapabilities: request.capabilities || [],
  userPreferences: context.userPreferences || {},
  urgency: request.priority || 'normal'
});

// Log the routing decision via GET (for analytics)
const analyticsParams = new URLSearchParams({
  event: 'route_selected',
  routeId: selectedRoute.id,
  reason: selectedRoute.reason,
  score: selectedRoute.score
});

// Fire analytics event
$http.request({
  method: 'GET',
  url: process.env.ANALYTICS_WEBHOOK + '?' + analyticsParams
}).catch(() => {});

return {
  json: {
    originalRequest: request,
    selectedRoute: selectedRoute,
    routingReason: selectedRoute.reason,
    alternativeRoutes: selectedRoute.alternatives,
    method: method
  }
};
        `
      },
      "name": "Adaptive Route Selection",
      "type": "n8n-nodes-base.function",
      "position": [450, 300]
    }
  ]
}
```

#### Predictive Workflow Optimization

```javascript
// Predictive optimization with GET request support
class WorkflowOptimizer {
  constructor(webhookUrl) {
    this.webhookUrl = webhookUrl;
    this.executionHistory = [];
    this.patterns = new Map();
  }
  
  async optimizeWorkflow(workflowDefinition, context) {
    // Analyze execution patterns via GET
    const patterns = await this.analyzeExecutionPatterns(workflowDefinition.id);
    
    // Generate optimizations
    const optimizations = {
      parallelization: this.identifyParallelizationOpportunities(workflowDefinition),
      caching: await this.suggestCachingStrategies(patterns),
      resourceAllocation: this.optimizeResourceAllocation(patterns),
      errorPrevention: this.suggestErrorPrevention(patterns)
    };
    
    // Apply optimizations via GET-compatible webhook
    return this.applyOptimizations(workflowDefinition, optimizations);
  }
  
  async analyzeExecutionPatterns(workflowId) {
    // GET request for pattern analysis
    const params = new URLSearchParams({
      action: 'get_patterns',
      workflowId: workflowId,
      period: '7d',
      metrics: 'execution_time,success_rate,error_types'
    });
    
    const response = await fetch(`${this.webhookUrl}/analytics/patterns?${params}`);
    return response.json();
  }
  
  async suggestCachingStrategies(patterns) {
    const suggestions = [];
    
    // Analyze repeated operations
    const repeatedOps = patterns.filter(p => p.frequency > 0.7);
    
    for (const op of repeatedOps) {
      // Check cache effectiveness via GET
      const cacheParams = new URLSearchParams({
        nodeId: op.nodeId,
        operation: op.type,
        frequency: op.frequency
      });
      
      const cacheAnalysis = await fetch(
        `${this.webhookUrl}/cache/analysis?${cacheParams}`
      ).then(r => r.json());
      
      if (cacheAnalysis.recommended) {
        suggestions.push({
          type: 'result_caching',
          operation: op.nodeId,
          cacheKey: this.generateCacheKey(op),
          ttl: cacheAnalysis.optimalTTL,
          estimatedSavings: op.averageExecutionTime * op.frequency
        });
      }
    }
    
    return suggestions;
  }
  
  async applyOptimizations(workflow, optimizations) {
    // Send optimizations via GET (URL-safe encoding)
    const optimizationData = {
      workflowId: workflow.id,
      optimizations: optimizations,
      applyImmediately: false
    };
    
    // Compress if large
    const compressed = LZString.compressToEncodedURIComponent(
      JSON.stringify(optimizationData)
    );
    
    const params = new URLSearchParams({
      action: 'apply_optimizations',
      compressed: 'true',
      data: compressed
    });
    
    const response = await fetch(`${this.webhookUrl}/optimize?${params}`);
    return response.json();
  }
}
```

### 2\. Multi-Agent Coordination Patterns

#### Consensus Building Pattern (GET-Compatible)

```javascript
// Multi-agent consensus with GET request support
class ConsensusBuilder {
  constructor(webhookUrl) {
    this.webhookUrl = webhookUrl;
    this.votingStrategies = {
      majority: this.majorityVote,
      weighted: this.weightedVote,
      unanimous: this.unanimousVote,
      expertise: this.expertiseWeightedVote
    };
  }
  
  async buildConsensus(task, agents, strategy = 'weighted') {
    // Initialize consensus session via GET
    const sessionParams = new URLSearchParams({
      action: 'init_consensus',
      taskType: task.type,
      agentCount: agents.length,
      strategy: strategy
    });
    
    const session = await fetch(
      `${this.webhookUrl}/consensus/init?${sessionParams}`
    ).then(r => r.json());
    
    // Execute task with multiple agents (parallel GET requests)
    const responses = await this.executeWithAgents(task, agents, session.id);
    
    // Apply consensus strategy
    const consensus = await this.votingStrategies[strategy].call(
      this, responses, session.id
    );
    
    // Validate consensus quality
    const quality = await this.assessConsensusQuality(consensus, responses);
    
    return {
      consensus: consensus.result,
      confidence: consensus.confidence,
      quality: quality,
      participatingAgents: responses.length,
      dissenting: consensus.dissenting || [],
      metadata: {
        strategy: strategy,
        processingTime: Date.now() - task.startTime,
        convergenceRounds: consensus.rounds || 1,
        sessionId: session.id
      }
    };
  }
  
  async executeWithAgents(task, agents, sessionId) {
    // Prepare task for GET requests (compress if needed)
    const taskData = JSON.stringify(task);
    const useCompression = taskData.length > 500;
    
    const baseParams = {
      sessionId: sessionId,
      compressed: useCompression ? 'true' : 'false'
    };
    
    if (useCompression) {
      baseParams.data = LZString.compressToEncodedURIComponent(taskData);
    } else {
      baseParams.task = taskData;
    }
    
    const executions = agents.map(async (agent) => {
      try {
        const agentParams = new URLSearchParams({
          ...baseParams,
          agentId: agent.id
        });
        
        const response = await fetch(
          `${this.webhookUrl}/agent/execute?${agentParams}`
        );
        const result = await response.json();
        
        return {
          agentId: agent.id,
          response: result,
          confidence: result.confidence || 0.8,
          expertise: agent.capabilities.expertise || 0.5,
          status: 'success'
        };
      } catch (error) {
        return {
          agentId: agent.id,
          error: error.message,
          status: 'failed'
        };
      }
    });
    
    const results = await Promise.allSettled(executions);
    return results
      .filter(r => r.status === 'fulfilled')
      .map(r => r.value)
      .filter(r => r.status === 'success');
  }
  
  async assessConsensusQuality(consensus, responses) {
    // Send quality assessment via GET
    const params = new URLSearchParams({
      consensusId: consensus.id,
      responseCount: responses.length,
      agreementLevel: consensus.agreementLevel,
      confidence: consensus.confidence
    });
    
    const quality = await fetch(
      `${this.webhookUrl}/consensus/quality?${params}`
    ).then(r => r.json());
    
    return quality.score;
  }
}

// N8N Consensus Workflow with GET support
{
  "name": "Multi-Agent Consensus Builder",
  "nodes": [
    {
      "parameters": {
        "path": "consensus/build",
        "responseMode": "responseNode",
        "options": {
          "responseCode": 200,
          "responseHeaders": {
            "entries": [
              {
                "name": "Access-Control-Allow-Origin",
                "value": "*"
              }
            ]
          }
        }
      },
      "name": "Consensus Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "functionCode": `
// Handle GET request for consensus building
const query = $json.query || {};
const method = $json.method || 'GET';

// Parse request based on method
let task, strategy;
if (method === 'GET') {
  task = query.compressed === 'true' 
    ? JSON.parse(LZString.decompressFromEncodedURIComponent(query.task))
    : JSON.parse(query.task || '{}');
  strategy = query.strategy || 'weighted';
} else {
  task = $json.body.task;
  strategy = $json.body.strategy || 'weighted';
}

// Get available agents for this task type
const agentParams = new URLSearchParams({
  capability: task.requiredCapability || 'general',
  available: 'true'
});

const agents = await $http.request({
  method: 'GET',
  url: process.env.AGENT_REGISTRY_URL + '?' + agentParams
}).then(r => r.json());

// Build consensus
const consensusBuilder = new ConsensusBuilder(process.env.WEBHOOK_URL);
const result = await consensusBuilder.buildConsensus(task, agents, strategy);

return { json: result };
        `
      },
      "name": "Build Consensus",
      "type": "n8n-nodes-base.function",
      "position": [450, 300]
    }
  ]
}
```

### 3\. Learning and Adaptation Patterns

#### Pattern Recognition and Learning (GET-Enabled)

```javascript
// Pattern recognition system with GET request support
class PatternLearner {
  constructor(webhookUrl) {
    this.webhookUrl = webhookUrl;
    this.patterns = new Map();
    this.feedbackHistory = [];
    this.adaptationRules = new Map();
  }
  
  async learnFromInteraction(interaction) {
    // Extract features from interaction
    const features = this.extractFeatures(interaction);
    
    // Identify patterns
    const patterns = await this.identifyPatterns(features);
    
    // Update pattern database via GET
    await this.updatePatterns(patterns, interaction.outcome);
    
    // Generate adaptation rules
    const adaptations = await this.generateAdaptations(patterns, interaction);
    
    return {
      patternsFound: patterns.length,
      adaptationsGenerated: adaptations.length,
      confidence: this.calculateLearningConfidence(patterns)
    };
  }
  
  async identifyPatterns(features) {
    // Query pattern database via GET
    const params = new URLSearchParams({
      requestType: features.requestType,
      userContext: features.userContext,
      complexity: features.requestComplexity,
      timeRange: '30d'
    });
    
    const existingPatterns = await fetch(
      `${this.webhookUrl}/patterns/search?${params}`
    ).then(r => r.json());
    
    const patterns = [];
    
    // Success patterns
    if (features.userSatisfaction > 0.8) {
      patterns.push({
        type: 'success_pattern',
        conditions: {
          requestType: features.requestType,
          agentsUsed: features.agentsUsed,
          processingPath: features.processingPath
        },
        outcome: 'high_satisfaction',
        confidence: 0.9
      });
    }
    
    // Performance patterns
    if (features.responseTime < 2000) {
      patterns.push({
        type: 'performance_pattern',
        conditions: {
          requestComplexity: features.requestComplexity,
          agentsUsed: features.agentsUsed
        },
        outcome: 'fast_response',
        confidence: 0.8
      });
    }
    
    return patterns;
  }
  
  async updatePatterns(patterns, outcome) {
    // Update pattern database via GET requests
    for (const pattern of patterns) {
      const patternData = {
        pattern: pattern,
        outcome: outcome,
        timestamp: Date.now()
      };
      
      // Compress pattern data for GET
      const compressed = LZString.compressToEncodedURIComponent(
        JSON.stringify(patternData)
      );
      
      const params = new URLSearchParams({
        action: 'update_pattern',
        compressed: 'true',
        data: compressed
      });
      
      // Fire and forget for performance
      fetch(`${this.webhookUrl}/patterns/update?${params}`).catch(() => {});
    }
  }
  
  async generateAdaptations(patterns, interaction) {
    const adaptations = [];
    
    for (const pattern of patterns) {
      // Query adaptation rules via GET
      const params = new URLSearchParams({
        patternType: pattern.type,
        confidence: pattern.confidence,
        conditions: JSON.stringify(pattern.conditions)
      });
      
      const rules = await fetch(
        `${this.webhookUrl}/adaptations/suggest?${params}`
      ).then(r => r.json());
      
      adaptations.push(...rules);
    }
    
    return adaptations;
  }
}

// Self-Improving Workflow with GET support
{
  "name": "Self-Improving Workflow",
  "nodes": [
    {
      "parameters": {
        "schedule": "0 2 * * *", // Daily at 2 AM
        "options": {}
      },
      "name": "Daily Improvement Trigger",
      "type": "n8n-nodes-base.scheduleTrigger",
      "position": [250, 300]
    },
    {
      "parameters": {
        "functionCode": `
// Analyze workflow performance via GET requests
const workflowId = $workflow.id;

// Get execution history via GET
const historyParams = new URLSearchParams({
  workflowId: workflowId,
  period: '7d',
  includeMetrics: 'true',
  limit: '100'
});

const executionHistory = await $http.request({
  method: 'GET',
  url: process.env.WORKFLOW_API + '/history?' + historyParams
}).then(r => r.json());

// Analyze for improvements
const analyzer = new WorkflowAnalyzer(process.env.WEBHOOK_URL);
const improvements = await analyzer.analyzePerformance(executionHistory);

// Filter improvements by confidence and risk
const safeImprovements = improvements.filter(i => 
  i.confidence > 0.9 && i.risk === 'low'
);

// Apply improvements via GET
const applyResults = [];
for (const improvement of safeImprovements) {
  const applyParams = new URLSearchParams({
    workflowId: workflowId,
    improvementType: improvement.type,
    config: JSON.stringify(improvement.config)
  });
  
  const result = await $http.request({
    method: 'GET',
    url: process.env.WORKFLOW_API + '/apply-improvement?' + applyParams
  }).then(r => r.json());
  
  applyResults.push(result);
}

// Log results
const logParams = new URLSearchParams({
  workflowId: workflowId,
  event: 'self_improvement',
  improvements: applyResults.length,
  timestamp: Date.now()
});

fetch(process.env.ANALYTICS_WEBHOOK + '?' + logParams).catch(() => {});

return {
  json: {
    workflowId: workflowId,
    analysisDate: new Date().toISOString(),
    totalImprovements: improvements.length,
    autoApplied: applyResults.length,
    pendingReview: improvements.length - applyResults.length,
    nextAnalysis: new Date(Date.now() + 24 * 60 * 60 * 1000).toISOString()
  }
};
        `
      },
      "name": "Analyze and Improve",
      "type": "n8n-nodes-base.function",
      "position": [450, 300]
    }
  ]
}
```

### 4\. Context-Aware Intelligence Patterns

#### Dynamic Context Enhancement (GET-Compatible)

```javascript
// Context enhancement with GET request support
class ContextEnhancer {
  constructor(webhookUrl) {
    this.webhookUrl = webhookUrl;
    this.contextHistory = new Map();
    this.entityExtractor = new EntityExtractor();
    this.semanticAnalyzer = new SemanticAnalyzer();
  }
  
  async enhanceContext(request, baseContext) {
    const enhanced = { ...baseContext };
    
    // Extract entities and intent via lightweight analysis
    enhanced.entities = await this.entityExtractor.extract(request.content);
    enhanced.intent = await this.semanticAnalyzer.analyzeIntent(request.content);
    
    // Get historical context via GET
    enhanced.history = await this.getRelevantHistory(request, enhanced);
    
    // Add environmental context
    enhanced.environment = await this.getEnvironmentalContext();
    
    // Get user profile via GET if userId exists
    if (enhanced.userId) {
      enhanced.userProfile = await this.getUserProfile(enhanced.userId);
    }
    
    // Find relevant knowledge via GET
    enhanced.relevantKnowledge = await this.findRelevantKnowledge(enhanced);
    
    // Add temporal context
    enhanced.temporal = this.getTemporalContext();
    
    return enhanced;
  }
  
  async getRelevantHistory(request, context) {
    // GET request for history
    const params = new URLSearchParams({
      sessionId: context.sessionId || 'anonymous',
      limit: '10',
      relevance: 'high'
    });
    
    const history = await fetch(
      `${this.webhookUrl}/context/history?${params}`
    ).then(r => r.json());
    
    return history.interactions || [];
  }
  
  async getUserProfile(userId) {
    // GET request for user profile
    const params = new URLSearchParams({
      userId: userId,
      fields: 'preferences,expertise,history_summary'
    });
    
    const profile = await fetch(
      `${this.webhookUrl}/users/profile?${params}`
    ).then(r => r.json());
    
    return profile;
  }
  
  async findRelevantKnowledge(context) {
    // Prepare search query
    const searchData = {
      entities: context.entities,
      intent: context.intent,
      domain: context.domain || 'general'
    };
    
    // Use GET with compressed query if large
    const queryString = JSON.stringify(searchData);
    const params = new URLSearchParams();
    
    if (queryString.length > 200) {
      params.set('compressed', 'true');
      params.set('q', LZString.compressToEncodedURIComponent(queryString));
    } else {
      params.set('q', queryString);
    }
    
    const knowledge = await fetch(
      `${this.webhookUrl}/knowledge/search?${params}`
    ).then(r => r.json());
    
    return knowledge.results || [];
  }
  
  async getEnvironmentalContext() {
    // GET request for system status
    const response = await fetch(`${this.webhookUrl}/system/status`);
    const status = await response.json();
    
    return {
      systemLoad: status.load || 'normal',
      activeUsers: status.activeUsers || 0,
      responseTime: status.avgResponseTime || 0,
      timestamp: new Date().toISOString()
    };
  }
}

// Agent Communication Enhancement
class EnhancedAgentCommunicator {
  constructor(contextEnhancer) {
    this.contextEnhancer = contextEnhancer;
  }
  
  async sendToAgent(agent, request, baseContext) {
    // Enhance context before sending
    const enhancedContext = await this.contextEnhancer.enhanceContext(
      request, baseContext
    );
    
    // Prepare agent request for GET
    const agentRequest = {
      request: request,
      context: enhancedContext,
      metadata: {
        requestId: this.generateRequestId(),
        timestamp: Date.now(),
        contextVersion: '2.0'
      }
    };
    
    // Compress for GET if needed
    const data = JSON.stringify(agentRequest);
    const params = new URLSearchParams({
      agentId: agent.id
    });
    
    if (data.length > 1000) {
      params.set('compressed', 'true');
      params.set('data', LZString.compressToEncodedURIComponent(data));
    } else {
      params.set('data', data);
    }
    
    // Send to agent via GET
    const response = await fetch(
      `${agent.endpoint}?${params}`
    ).then(r => r.json());
    
    // Log enhanced interaction
    this.logInteraction(agent.id, enhancedContext, response);
    
    return response;
  }
  
  async logInteraction(agentId, context, response) {
    // Log via GET for analytics
    const logParams = new URLSearchParams({
      agentId: agentId,
      contextEnhanced: 'true',
      responseQuality: response.quality || 'unknown',
      timestamp: Date.now()
    });
    
    fetch(`${this.webhookUrl}/analytics/log?${logParams}`).catch(() => {});
  }
}
```

### 5\. Intelligent Fallback and Recovery Patterns

#### Graceful Degradation with GET Support

```javascript
// Graceful degradation manager with GET requests
class GracefulDegradationManager {
  constructor(webhookUrl) {
    this.webhookUrl = webhookUrl;
    this.degradationLevels = ['full', 'partial', 'minimal', 'emergency'];
    this.fallbackStrategies = new Map();
    this.setupFallbacks();
  }
  
  setupFallbacks() {
    // Agent fallbacks
    this.fallbackStrategies.set('agent_unavailable', {
      strategies: [
        { name: 'use_cache', degradation: 'partial' },
        { name: 'simple_response', degradation: 'minimal' },
        { name: 'queue_for_later', degradation: 'minimal' }
      ]
    });
    
    // Knowledge fallbacks
    this.fallbackStrategies.set('knowledge_unavailable', {
      strategies: [
        { name: 'cached_knowledge', degradation: 'partial' },
        { name: 'general_response', degradation: 'minimal' },
        { name: 'request_clarification', degradation: 'minimal' }
      ]
    });
  }
  
  async handleFailure(request, failedComponent, error) {
    // Get system status via GET
    const statusResponse = await fetch(`${this.webhookUrl}/system/health`);
    const systemStatus = await statusResponse.json();
    
    // Determine failure type and severity
    const failureAnalysis = this.analyzeFailure(error, systemStatus);
    
    // Get appropriate fallback strategy
    const strategy = await this.selectFallbackStrategy(
      failedComponent, 
      failureAnalysis,
      request
    );
    
    // Execute fallback
    const result = await this.executeFallback(strategy, request);
    
    // Log degradation event via GET
    const logParams = new URLSearchParams({
      event: 'service_degradation',
      component: failedComponent,
      level: strategy.degradationLevel,
      strategy: strategy.name,
      timestamp: Date.now()
    });
    
    fetch(`${this.webhookUrl}/monitoring/degradation?${logParams}`).catch(() => {});
    
    return {
      result: result,
      degradationLevel: strategy.degradationLevel,
      strategy: strategy.name,
      limitations: strategy.limitations
    };
  }
  
  async selectFallbackStrategy(component, analysis, request) {
    // Query for best fallback via GET
    const params = new URLSearchParams({
      component: component,
      severity: analysis.severity,
      requestType: request.type || 'general',
      systemLoad: analysis.systemLoad
    });
    
    const recommendation = await fetch(
      `${this.webhookUrl}/fallback/recommend?${params}`
    ).then(r => r.json());
    
    return recommendation.strategy;
  }
  
  async executeFallback(strategy, request) {
    switch (strategy.name) {
      case 'use_cache':
        return this.getCachedResponse(request);
      
      case 'simple_response':
        return this.generateSimpleResponse(request);
      
      case 'queue_for_later':
        return this.queueRequest(request);
      
      default:
        return this.emergencyResponse(request);
    }
  }
  
  async getCachedResponse(request) {
    // GET cached response
    const cacheKey = this.generateCacheKey(request);
    const params = new URLSearchParams({
      key: cacheKey,
      maxAge: '3600' // 1 hour
    });
    
    const cached = await fetch(
      `${this.webhookUrl}/cache/get?${params}`
    ).then(r => r.json());
    
    return cached.found ? cached.data : this.generateSimpleResponse(request);
  }
  
  async queueRequest(request) {
    // Queue via GET request
    const queueData = {
      request: request,
      queuedAt: Date.now(),
      priority: request.priority || 'normal'
    };
    
    const compressed = LZString.compressToEncodedURIComponent(
      JSON.stringify(queueData)
    );
    
    const params = new URLSearchParams({
      action: 'queue',
      compressed: 'true',
      data: compressed
    });
    
    const queueResult = await fetch(
      `${this.webhookUrl}/queue/add?${params}`
    ).then(r => r.json());
    
    return {
      status: 'queued',
      queueId: queueResult.id,
      estimatedProcessingTime: queueResult.estimatedTime,
      message: 'Your request has been queued and will be processed when resources are available.'
    };
  }
}

// N8N Fallback Workflow with GET support
{
  "name": "Intelligent Fallback Handler",
  "nodes": [
    {
      "parameters": {
        "path": "fallback/handle",
        "responseMode": "responseNode",
        "options": {
          "responseCode": 200
        }
      },
      "name": "Fallback Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "functionCode": `
// Handle failures gracefully with GET support
const query = $json.query || {};
const method = $json.method || 'GET';

// Parse failure information
let failure, originalRequest, context;

if (method === 'GET') {
  if (query.compressed === 'true') {
    const data = JSON.parse(
      LZString.decompressFromEncodedURIComponent(query.data)
    );
    failure = data.failure;
    originalRequest = data.originalRequest;
    context = data.context;
  } else {
    failure = {
      component: query.component,
      error: query.error
    };
    originalRequest = JSON.parse(query.request || '{}');
    context = JSON.parse(query.context || '{}');
  }
} else {
  failure = $json.body.failure;
  originalRequest = $json.body.originalRequest;
  context = $json.body.context;
}

const degradationManager = new GracefulDegradationManager(
  process.env.WEBHOOK_URL
);

// Attempt fallback recovery
const fallbackResult = await degradationManager.handleFailure(
  originalRequest,
  failure.component,
  failure.error
);

// Log degradation for monitoring
const monitoringParams = new URLSearchParams({
  event: 'fallback_executed',
  component: failure.component,
  level: fallbackResult.degradationLevel,
  strategy: fallbackResult.strategy,
  success: fallbackResult.result ? 'true' : 'false'
});

$http.request({
  method: 'GET',
  url: process.env.MONITORING_WEBHOOK + '?' + monitoringParams
}).catch(() => {});

// Notify if significant degradation
if (['minimal', 'emergency'].includes(fallbackResult.degradationLevel)) {
  const alertParams = new URLSearchParams({
    severity: 'high',
    component: failure.component,
    degradation: fallbackResult.degradationLevel
  });
  
  $http.request({
    method: 'GET',
    url: process.env.ALERT_WEBHOOK + '?' + alertParams
  }).catch(() => {});
}

return {
  json: {
    status: 'recovered',
    result: fallbackResult.result,
    metadata: {
      degradationLevel: fallbackResult.degradationLevel,
      strategy: fallbackResult.strategy,
      limitations: fallbackResult.limitations,
      originalFailure: failure.error
    }
  }
};
        `
      },
      "name": "Execute Fallback Strategy",
      "type": "n8n-nodes-base.function",
      "position": [450, 300]
    }
  ]
}
```

## Implementation Notes

- All patterns now support GET requests for Claude Projects compatibility  
- Use compression (LZ-String) for data over 500 bytes in GET requests  
- Implement proper error handling for GET request size limitations  
- Monitor GET request performance compared to POST  
- Use fire-and-forget GET requests for analytics to avoid blocking  
- Cache GET request results when appropriate  
- Test patterns under various load conditions with GET requests  
- Keep GET URLs under 2000 characters for maximum compatibility  
- Use session-based approaches for complex multi-step patterns  
- Document GET-specific limitations in your implementation

## Next Steps and Recommendations

After implementing AI patterns with GET support:

1. **Start with adaptive routing** \- Test GET-based routing first  
2. **Implement consensus building** \- Verify multi-agent GET coordination works  
3. **Deploy learning patterns** \- Ensure pattern updates work via GET  
4. **Test fallback strategies** \- Confirm GET-based degradation handling  
5. **Monitor performance** \- Compare GET vs POST performance metrics

## Next Steps

1️⃣ **Test adaptive routing with GET requests** in your Claude artifacts  
2️⃣ **Implement consensus building** using compressed GET parameters  
3️⃣ **Deploy context enhancement** with GET-compatible knowledge search  
4️⃣ **Configure graceful degradation** with GET-based monitoring  
5️⃣ **Monitor pattern effectiveness** using GET analytics endpoints

