02\_Workflows\_Knowledge

# KnowledgeForge 3.0: Knowledge Workflows

---

title: "Knowledge Workflows" module: "02\_Workflows" topics: \["knowledge retrieval", "search", "processing", "caching", "optimization"\] contexts: \["knowledge management", "information retrieval", "content processing"\] difficulty: "intermediate" related\_sections: \["Orchestration", "Agents", "Core", "Templates"\] workflow\_integration: \["knowledge\_retrieval", "search\_optimization"\] agent\_access: \["navigator", "knowledge-expert"\]

## Core Approach

This module defines specialized workflows for knowledge operations in KnowledgeForge 3.0. These workflows handle knowledge retrieval, search optimization, content processing, and intelligent caching to provide fast, accurate, and contextually relevant information access. They integrate seamlessly with agents and the orchestration system to create a comprehensive knowledge management environment.

## Knowledge Retrieval Workflows

### Simple Knowledge Retrieval

```json
{
  "name": "Simple Knowledge Retrieval",
  "description": "Fast, cached knowledge module retrieval",
  "trigger": "webhook",
  "nodes": [
    {
      "parameters": {
        "functionCode": "// Simple, fast knowledge retrieval\nconst moduleId = $json.payload.moduleId;\nconst context = $json.context || {};\nconst options = $json.options || {};\n\n// Validate module ID\nif (!moduleId) {\n  throw new Error('Module ID is required');\n}\n\n// Generate cache key\nconst cacheKey = `knowledge:module:${moduleId}:${JSON.stringify(context).slice(0, 100)}`;\n\nreturn {\n  json: {\n    moduleId,\n    cacheKey,\n    context,\n    options,\n    timestamp: new Date().toISOString()\n  }\n};"
      },
      "id": "prepare_retrieval",
      "name": "Prepare Retrieval",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    },
    {
      "parameters": {
        "operation": "get",
        "key": "={{$json.cacheKey}}"
      },
      "id": "check_cache",
      "name": "Check Cache",
      "type": "n8n-nodes-base.redis",
      "position": [430, 300],
      "continueOnFail": true
    },
    {
      "parameters": {
        "conditions": {
          "boolean": [
            {
              "value1": "={{$node['Check Cache'].json.value !== null}}",
              "value2": true
            }
          ]
        }
      },
      "id": "cache_check",
      "name": "Cache Hit?",
      "type": "n8n-nodes-base.if",
      "position": [610, 300]
    },
    {
      "parameters": {
        "functionCode": "// Return cached content with freshness check\nconst cached = JSON.parse($node['Check Cache'].json.value);\nconst cacheAge = Date.now() - new Date(cached.cachedAt).getTime();\nconst maxAge = 3600000; // 1 hour\n\nif (cacheAge > maxAge) {\n  return {\n    json: {\n      cacheStatus: 'stale',\n      shouldRefresh: true,\n      cached: cached\n    }\n  };\n}\n\nreturn {\n  json: {\n    status: 'success',\n    result: {\n      module: cached.module,\n      source: 'cache',\n      cacheAge: Math.round(cacheAge / 1000),\n      retrievedAt: new Date().toISOString()\n    },\n    cacheHit: true\n  }\n};"
      },
      "id": "return_cached",
      "name": "Return Cached",
      "type": "n8n-nodes-base.function",
      "position": [790, 200]
    },
    {
      "parameters": {
        "url": "={{$env.KNOWLEDGEFORGE_API_URL}}/knowledge/modules/{{$json.moduleId}}",
        "authentication": "genericCredentialType",
        "genericAuthType": "httpHeaderAuth",
        "sendHeaders": true,
        "headerParameters": {
          "parameters": [
            {
              "name": "X-API-Key",
              "value": "={{$env.KNOWLEDGEFORGE_API_KEY}}"
            },
            {
              "name": "X-Context",
              "value": "={{JSON.stringify($json.context)}}"
            }
          ]
        },
        "options": {
          "timeout": 10000,
          "retry": {
            "maxTries": 3,
            "waitBetweenTries": 1000
          }
        }
      },
      "id": "fetch_knowledge",
      "name": "Fetch Knowledge",
      "type": "n8n-nodes-base.httpRequest",
      "position": [790, 400]
    },
    {
      "parameters": {
        "functionCode": "// Process and enhance knowledge module\nconst knowledge = $json.data || $json;\nconst originalRequest = $node['Prepare Retrieval'].json;\n\n// Enhance with navigation context\nconst enhanced = {\n  ...knowledge,\n  navigation: {\n    currentModule: knowledge.id,\n    breadcrumb: generateBreadcrumb(knowledge),\n    relatedModules: knowledge.metadata?.relatedSections || [],\n    nextSteps: generateNextSteps(knowledge, originalRequest.context)\n  },\n  retrieval: {\n    retrievedAt: new Date().toISOString(),\n    source: 'api',\n    requestContext: originalRequest.context,\n    processingTime: Date.now() - new Date(originalRequest.timestamp).getTime()\n  }\n};\n\nfunction generateBreadcrumb(module) {\n  const parts = (module.id || '').split('_');\n  return parts.map((part, index) => ({\n    level: index,\n    name: part,\n    path: parts.slice(0, index + 1).join('_')\n  }));\n}\n\nfunction generateNextSteps(module, context) {\n  const steps = [];\n  \n  if (context.userIntent === 'learning') {\n    steps.push('Continue to practical examples');\n    steps.push('Test your understanding');\n  } else if (context.userIntent === 'implementation') {\n    steps.push('See implementation guide');\n    steps.push('Download code examples');\n  } else {\n    steps.push('Explore related topics');\n    steps.push('Find practical applications');\n  }\n  \n  steps.push('Ask follow-up questions');\n  steps.push('Save for later reference');\n  steps.push('Share with team');\n  \n  return steps;\n}\n\nreturn {\n  json: {\n    status: 'success',\n    result: {\n      module: enhanced\n    },\n    cacheHit: false\n  }\n};"
      },
      "id": "enhance_knowledge",
      "name": "Enhance Knowledge",
      "type": "n8n-nodes-base.function",
      "position": [970, 400]
    },
    {
      "parameters": {
        "operation": "set",
        "key": "={{$node['Prepare Retrieval'].json.cacheKey}}",
        "value": "={{JSON.stringify({\n  module: $json.result.module,\n  cachedAt: new Date().toISOString()\n})}}",
        "expire": true,
        "ttl": 3600
      },
      "id": "cache_result",
      "name": "Cache Result",
      "type": "n8n-nodes-base.redis",
      "position": [1150, 400]
    }
  ],
  "connections": {
    "Prepare Retrieval": {
      "main": [
        [
          {
            "node": "Check Cache",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Check Cache": {
      "main": [
        [
          {
            "node": "Cache Hit?",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Cache Hit?": {
      "main": [
        [
          {
            "node": "Return Cached",
            "type": "main",
            "index": 0
          }
        ],
        [
          {
            "node": "Fetch Knowledge",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Fetch Knowledge": {
      "main": [
        [
          {
            "node": "Enhance Knowledge",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Enhance Knowledge": {
      "main": [
        [
          {
            "node": "Cache Result",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  }
}
```

### Intelligent Search Workflow

```json
{
  "name": "Intelligent Knowledge Search",
  "description": "Semantic search with context awareness",
  "trigger": "webhook",
  "nodes": [
    {
      "parameters": {
        "functionCode": "// Enhanced search preprocessing\nconst query = $json.payload.query;\nconst filters = $json.payload.filters || {};\nconst options = $json.payload.options || {};\nconst context = $json.context || {};\n\nconst processed = {\n  originalQuery: query,\n  processedQuery: preprocessQuery(query),\n  searchTerms: extractSearchTerms(query),\n  filters: enhanceFilters(filters, context),\n  semanticQuery: generateSemanticQuery(query, context),\n  searchStrategy: determineSearchStrategy(query, filters, options)\n};\n\nfunction preprocessQuery(q) {\n  if (typeof q !== 'string') return q;\n  \n  let processed = q.toLowerCase().trim();\n  const stopWords = ['the', 'is', 'at', 'which', 'on', 'a', 'an'];\n  stopWords.forEach(word => {\n    processed = processed.replace(new RegExp(`\\\\b${word}\\\\b`, 'g'), ' ');\n  });\n  \n  return processed.replace(/\\s+/g, ' ').trim();\n}\n\nfunction extractSearchTerms(q) {\n  if (typeof q !== 'string') return [];\n  \n  const terms = [];\n  \n  // Extract quoted phrases\n  const quotedPhrases = q.match(/\"([^\"]+)\"/g) || [];\n  quotedPhrases.forEach(phrase => {\n    terms.push({\n      type: 'phrase',\n      value: phrase.replace(/\"/g, ''),\n      weight: 2.0\n    });\n  });\n  \n  // Extract individual words\n  const words = q.replace(/\"[^\"]+\"/g, '').split(/\\s+/).filter(w => w.length > 2);\n  words.forEach(word => {\n    terms.push({\n      type: 'word',\n      value: word,\n      weight: 1.0\n    });\n  });\n  \n  return terms;\n}\n\nfunction enhanceFilters(filters, context) {\n  const enhanced = { ...filters };\n  \n  // Add context-based filters\n  if (context.userRole) {\n    enhanced.difficulty = getDifficultyForRole(context.userRole);\n  }\n  \n  if (context.domain) {\n    enhanced.modules = [`${context.domain}_*`];\n  }\n  \n  return enhanced;\n}\n\nfunction getDifficultyForRole(role) {\n  const mapping = {\n    'beginner': ['beginner'],\n    'intermediate': ['beginner', 'intermediate'],\n    'expert': ['intermediate', 'advanced'],\n    'admin': ['beginner', 'intermediate', 'advanced']\n  };\n  return mapping[role] || ['beginner', 'intermediate'];\n}\n\nfunction generateSemanticQuery(query, context) {\n  return {\n    text: query,\n    intent: classifyIntent(query),\n    context: context,\n    embeddings: null // Would be populated by embedding service\n  };\n}\n\nfunction classifyIntent(q) {\n  if (typeof q !== 'string') return 'unknown';\n  \n  const lower = q.toLowerCase();\n  if (lower.includes('how to')) return 'tutorial';\n  if (lower.includes('example')) return 'examples';\n  if (lower.includes('troubleshoot')) return 'problem_solving';\n  if (lower.includes('best practice')) return 'guidance';\n  return 'information_seeking';\n}\n\nfunction determineSearchStrategy(query, filters, options) {\n  if (options.semantic === true) return 'semantic';\n  if (Object.keys(filters).length > 2) return 'filtered';\n  if (typeof query === 'string' && query.length > 50) return 'complex';\n  return 'simple';\n}\n\nreturn { json: processed };"
      },
      "id": "preprocess_search",
      "name": "Preprocess Search",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    },
    {
      "parameters": {
        "rules": {
          "values": [
            {
              "conditions": {
                "conditions": [
                  {
                    "leftValue": "={{$json.searchStrategy}}",
                    "rightValue": "semantic",
                    "operation": "equals"
                  }
                ]
              },
              "renameOutput": true,
              "outputKey": "semantic"
            },
            {
              "conditions": {
                "conditions": [
                  {
                    "leftValue": "={{$json.searchStrategy}}",
                    "rightValue": "filtered",
                    "operation": "equals"
                  }
                ]
              },
              "renameOutput": true,
              "outputKey": "filtered"
            },
            {
              "conditions": {
                "conditions": [
                  {
                    "leftValue": "={{$json.searchStrategy}}",
                    "rightValue": "complex",
                    "operation": "equals"
                  }
                ]
              },
              "renameOutput": true,
              "outputKey": "complex"
            }
          ]
        },
        "fallbackOutput": "simple"
      },
      "id": "search_strategy_router",
      "name": "Search Strategy Router",
      "type": "n8n-nodes-base.switch",
      "position": [430, 300]
    },
    {
      "parameters": {
        "url": "={{$env.KNOWLEDGEFORGE_API_URL}}/search/simple",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "query",
              "value": "={{$json.processedQuery}}"
            },
            {
              "name": "terms",
              "value": "={{JSON.stringify($json.searchTerms)}}"
            }
          ]
        }
      },
      "id": "simple_search",
      "name": "Simple Search",
      "type": "n8n-nodes-base.httpRequest",
      "position": [610, 200]
    },
    {
      "parameters": {
        "url": "={{$env.KNOWLEDGEFORGE_API_URL}}/search/semantic",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "semanticQuery",
              "value": "={{JSON.stringify($json.semanticQuery)}}"
            }
          ]
        }
      },
      "id": "semantic_search",
      "name": "Semantic Search",
      "type": "n8n-nodes-base.httpRequest",
      "position": [610, 300]
    },
    {
      "parameters": {
        "url": "={{$env.KNOWLEDGEFORGE_API_URL}}/search/filtered",
        "sendBody": true,
        "bodyParameters": {
          "parameters": [
            {
              "name": "query",
              "value": "={{$json.processedQuery}}"
            },
            {
              "name": "filters",
              "value": "={{JSON.stringify($json.filters)}}"
            }
          ]
        }
      },
      "id": "filtered_search",
      "name": "Filtered Search",
      "type": "n8n-nodes-base.httpRequest",
      "position": [610, 400]
    },
    {
      "parameters": {
        "functionCode": "// Process and rank search results\nconst results = $json.results || [];\nconst originalQuery = $node['Preprocess Search'].json;\n\n// Enhance results with relevance scoring\nconst enhanced = results.map(result => ({\n  ...result,\n  relevanceScore: calculateRelevance(result, originalQuery),\n  contextMatch: assessContextMatch(result, originalQuery),\n  accessibilityLevel: determineAccessibility(result, originalQuery)\n}));\n\n// Sort by relevance\nenhanced.sort((a, b) => b.relevanceScore - a.relevanceScore);\n\nfunction calculateRelevance(result, query) {\n  let score = result.baseScore || 0.5;\n  \n  // Boost for exact matches\n  query.searchTerms.forEach(term => {\n    if (result.title?.toLowerCase().includes(term.value.toLowerCase())) {\n      score += term.weight * 0.3;\n    }\n    if (result.content?.toLowerCase().includes(term.value.toLowerCase())) {\n      score += term.weight * 0.1;\n    }\n  });\n  \n  // Context relevance\n  if (result.module && query.filters.modules?.some(m => \n    m.includes('*') ? result.module.startsWith(m.replace('*', '')) : result.module === m\n  )) {\n    score += 0.2;\n  }\n  \n  return Math.min(score, 1.0);\n}\n\nfunction assessContextMatch(result, query) {\n  const context = query.semanticQuery?.context || {};\n  let match = 'medium';\n  \n  if (context.userRole && result.difficulty) {\n    const appropriateDifficulties = {\n      'beginner': ['beginner'],\n      'intermediate': ['beginner', 'intermediate'],\n      'expert': ['intermediate', 'advanced']\n    };\n    \n    if (appropriateDifficulties[context.userRole]?.includes(result.difficulty)) {\n      match = 'high';\n    } else {\n      match = 'low';\n    }\n  }\n  \n  return match;\n}\n\nfunction determineAccessibility(result, query) {\n  const intent = query.semanticQuery?.intent || 'unknown';\n  \n  if (intent === 'tutorial' && result.type === 'guide') return 'high';\n  if (intent === 'examples' && result.type === 'example') return 'high';\n  if (intent === 'problem_solving' && result.type === 'troubleshooting') return 'high';\n  \n  return 'medium';\n}\n\nreturn {\n  json: {\n    status: 'success',\n    results: enhanced.slice(0, 20), // Limit to top 20\n    searchMeta: {\n      totalResults: enhanced.length,\n      strategy: originalQuery.searchStrategy,\n      processingTime: Date.now() - new Date().getTime(),\n      query: originalQuery.originalQuery\n    }\n  }\n};"
      },
      "id": "process_results",
      "name": "Process Results",
      "type": "n8n-nodes-base.function",
      "position": [790, 300]
    }
  ]
}
```

## Multi-Module Synthesis Workflow

```javascript
// Multi-module knowledge synthesis for complex queries
{
  "name": "Multi Module Synthesis",
  "description": "Synthesize knowledge from multiple modules",
  "nodes": [
    {
      "parameters": {
        "functionCode": `
// Identify and fetch required modules
const analysis = $json.analysis;
const requiredModules = analysis.requiredModules || [];

// Create parallel fetch requests
const fetchTasks = requiredModules.map(modulePattern => ({
  modulePattern,
  cacheKey: \`synthesis:\${modulePattern}:\${Date.now()}\`,
  priority: calculatePriority(modulePattern, analysis)
}));

function calculatePriority(pattern, analysis) {
  // Core modules get highest priority
  if (pattern.startsWith('01_Core')) return 1;
  
  // Modules matching user intent get high priority
  const intent = analysis.intent?.primary || '';
  if (intent === 'implementation' && pattern.includes('Implementation')) return 2;
  if (intent === 'examples' && pattern.includes('Examples')) return 2;
  
  return 3; // Default priority
}

return {
  json: {
    fetchTasks,
    synthesisStrategy: determineSynthesisStrategy(analysis),
    originalAnalysis: analysis
  }
};

function determineSynthesisStrategy(analysis) {
  const complexity = analysis.complexity;
  const intent = analysis.intent?.primary;
  
  if (complexity === 'high' && intent === 'learning') {
    return 'guided_progression';
  } else if (intent === 'implementation') {
    return 'implementation_focused';
  } else if (intent === 'problem_solving') {
    return 'solution_oriented';
  }
  
  return 'comprehensive_overview';
}
`
      },
      "id": "plan_synthesis",
      "name": "Plan Synthesis",
      "type": "n8n-nodes-base.function",
      "position": [250, 300]
    },
    {
      "parameters": {
        "batchSize": 3,
        "options": {
          "continueOnFail": true
        }
      },
      "id": "parallel_fetch",
      "name": "Parallel Module Fetch",
      "type": "n8n-nodes-base.splitInBatches",
      "position": [430, 300]
    },
    {
      "parameters": {
        "workflowId": "simple_knowledge_retrieval",
        "source": "parameter",
        "parameters": {
          "parameters": [
            {
              "name": "moduleId",
              "value": "={{$json.modulePattern}}"
            },
            {
              "name": "context",
              "value": "={{$node['Plan Synthesis'].json.originalAnalysis.context}}"
            }
          ]
        }
      },
      "id": "fetch_module",
      "name": "Fetch Module",
      "type": "n8n-nodes-base.executeWorkflow",
      "position": [610, 300]
    },
    {
      "parameters": {
        "functionCode": `
// Synthesize fetched modules into coherent response
const modules = $input.all();
const synthesis = $node['Plan Synthesis'].json;
const strategy = synthesis.synthesisStrategy;

const synthesized = {
  strategy,
  modules: modules.map(m => m.json),
  content: synthesizeContent(modules, strategy),
  navigation: createSynthesisNavigation(modules, strategy),
  metadata: {
    sourceModules: modules.length,
    synthesisTime: new Date().toISOString(),
    strategy: strategy
  }
};

function synthesizeContent(modules, strategy) {
  const content = {
    summary: generateSummary(modules),
    sections: [],
    implementation: null,
    examples: [],
    nextSteps: []
  };
  
  switch (strategy) {
    case 'guided_progression':
      content.sections = createProgressionSections(modules);
      break;
    case 'implementation_focused':
      content.implementation = extractImplementationGuidance(modules);
      content.examples = extractCodeExamples(modules);
      break;
    case 'solution_oriented':
      content.sections = createSolutionSections(modules);
      break;
    default:
      content.sections = createOverviewSections(modules);
  }
  
  content.nextSteps = generateSynthesisNextSteps(modules, strategy);
  return content;
}

function generateSummary(modules) {
  const titles = modules.map(m => m.json?.result?.module?.title || 'Unknown');
  return \`This synthesis combines knowledge from \${modules.length} modules: \${titles.join(', ')}. \`;
}

function createProgressionSections(modules) {
  // Sort modules by logical progression
  const sorted = modules.sort((a, b) => {
    const aDiff = getDifficultyOrder(a.json?.result?.module?.difficulty);
    const bDiff = getDifficultyOrder(b.json?.result?.module?.difficulty);
    return aDiff - bDiff;
  });
  
  return sorted.map((module, index) => ({
    order: index + 1,
    title: module.json?.result?.module?.title || \`Section \${index + 1}\`,
    content: module.json?.result?.module?.content || '',
    difficulty: module.json?.result?.module?.difficulty || 'intermediate'
  }));
}

function getDifficultyOrder(difficulty) {
  const order = { 'beginner': 1, 'intermediate': 2, 'advanced': 3 };
  return order[difficulty] || 2;
}

function extractImplementationGuidance(modules) {
  const implementationSections = [];
  
  modules.forEach(module => {
    const content = module.json?.result?.module?.content || '';
    const implementationMatch = content.match(/## Implementation.*?(?=##|$)/s);
    if (implementationMatch) {
      implementationSections.push({
        source: module.json?.result?.module?.title,
        content: implementationMatch[0]
      });
    }
  });
  
  return implementationSections;
}

function extractCodeExamples(modules) {
  const examples = [];
  
  modules.forEach(module => {
    const content = module.json?.result?.module?.content || '';
    const codeBlocks = content.match(/\`\`\`[\\s\\S]*?\`\`\`/g) || [];
    
    codeBlocks.forEach(block => {
      examples.push({
        source: module.json?.result?.module?.title,
        code: block
      });
    });
  });
  
  return examples;
}

function createSolutionSections(modules) {
  return modules.map(module => ({
    title: module.json?.result?.module?.title || 'Solution Component',
    type: 'solution',
    content: module.json?.result?.module?.content || '',
    relevance: calculateRelevance(module)
  })).sort((a, b) => b.relevance - a.relevance);
}

function calculateRelevance(module) {
  const content = module.json?.result?.module?.content || '';
  const keywords = ['solution', 'solve', 'fix', 'troubleshoot', 'resolve'];
  return keywords.reduce((score, keyword) => {
    return score + (content.toLowerCase().includes(keyword) ? 1 : 0);
  }, 0);
}

function createOverviewSections(modules) {
  return modules.map((module, index) => ({
    order: index + 1,
    title: module.json?.result?.module?.title || \`Overview \${index + 1}\`,
    content: module.json?.result?.module?.content || '',
    module: module.json?.result?.module?.id
  }));
}

function createSynthesisNavigation(modules, strategy) {
  const allRelated = modules.flatMap(m => 
    m.json?.result?.module?.navigation?.relatedModules || []
  );
  
  const uniqueRelated = [...new Set(allRelated)];
  
  return {
    strategy,
    sourceModules: modules.map(m => m.json?.result?.module?.id),
    relatedModules: uniqueRelated,
    nextSteps: generateSynthesisNextSteps(modules, strategy)
  };
}

function generateSynthesisNextSteps(modules, strategy) {
  const steps = [];
  
  switch (strategy) {
    case 'guided_progression':
      steps.push('Continue with advanced concepts');
      steps.push('Practice with hands-on exercises');
      break;
    case 'implementation_focused':
      steps.push('Begin implementation');
      steps.push('Test with sample data');
      break;
    case 'solution_oriented':
      steps.push('Apply the solution');
      steps.push('Monitor results');
      break;
    default:
      steps.push('Explore related topics');
      steps.push('Dive deeper into specific areas');
  }
  
  steps.push('Ask clarifying questions');
  steps.push('Save this synthesis for reference');
  steps.push('Share with your team');
  
  return steps;
}

return { json: synthesized };
`
      },
      "id": "synthesize_knowledge",
      "name": "Synthesize Knowledge",
      "type": "n8n-nodes-base.function",
      "position": [790, 300]
    }
  ]
}
```

## Knowledge Caching and Optimization

### Intelligent Caching Strategy

- **L1 Cache**: In-memory for frequently accessed modules (Redis)  
- **L2 Cache**: Processed content cache for complex syntheses  
- **L3 Cache**: Search result cache with TTL based on content volatility

### Cache Invalidation Patterns

```javascript
// Cache invalidation workflow
{
  "name": "Cache Invalidation",
  "trigger": "webhook",
  "nodes": [
    {
      "parameters": {
        "functionCode": `
// Intelligent cache invalidation
const event = $json.event;
const affectedModules = $json.affectedModules || [];

const invalidationPlan = {
  event,
  affectedModules,
  cascadeRules: determineCascadeRules(event, affectedModules),
  priority: calculateInvalidationPriority(event),
  strategy: selectInvalidationStrategy(event, affectedModules)
};

function determineCascadeRules(event, modules) {
  const rules = [];
  
  // If core module changes, invalidate all dependent caches
  if (modules.some(m => m.startsWith('01_Core'))) {
    rules.push('invalidate_all_dependent');
  }
  
  // If framework changes, invalidate framework-related caches
  if (modules.some(m => m.startsWith('00_KB3'))) {
    rules.push('invalidate_framework_dependent');
  }
  
  // If workflow changes, invalidate orchestration caches
  if (modules.some(m => m.startsWith('02_Workflows'))) {
    rules.push('invalidate_orchestration_cache');
  }
  
  return rules;
}

function calculateInvalidationPriority(event) {
  const priorities = {
    'content_update': 'medium',
    'structure_change': 'high',
    'security_update': 'critical',
    'performance_optimization': 'low'
  };
  
  return priorities[event.type] || 'medium';
}

function selectInvalidationStrategy(event, modules) {
  if (modules.length > 10) return 'bulk_invalidation';
  if (event.type === 'security_update') return 'immediate_purge';
  return 'selective_invalidation';
}

return { json: invalidationPlan };
`
      },
      "id": "plan_invalidation",
      "name": "Plan Invalidation"
    }
  ]
}
```

## Performance Monitoring and Analytics

### Knowledge Access Analytics

```javascript
// Analytics workflow for knowledge usage patterns
{
  "name": "Knowledge Analytics",
  "nodes": [
    {
      "parameters": {
        "functionCode": `
// Collect and analyze knowledge usage metrics
const metrics = $json.metrics || {};

const analysis = {
  accessPatterns: analyzeAccessPatterns(metrics),
  popularModules: identifyPopularModules(metrics),
  searchTrends: analyzeSearchTrends(metrics),
  performanceMetrics: calculatePerformanceMetrics(metrics),
  recommendations: generateRecommendations(metrics)
};

function analyzeAccessPatterns(metrics) {
  // Implementation for access pattern analysis
  return {
    peakHours: metrics.hourlyAccess || {},
    userJourneys: metrics.navigationPaths || [],
    commonQueries: metrics.frequentQueries || []
  };
}

function identifyPopularModules(metrics) {
  const moduleAccess = metrics.moduleAccess || {};
  return Object.entries(moduleAccess)
    .sort(([,a], [,b]) => b - a)
    .slice(0, 10)
    .map(([module, count]) => ({ module, accessCount: count }));
}

function analyzeSearchTrends(metrics) {
  return {
    trendingQueries: metrics.searchQueries || [],
    searchSuccessRate: metrics.searchSuccessRate || 0.85,
    avgSearchTime: metrics.avgSearchTime || 150
  };
}

function calculatePerformanceMetrics(metrics) {
  return {
    avgResponseTime: metrics.avgResponseTime || 200,
    cacheHitRate: metrics.cacheHitRate || 0.75,
    errorRate: metrics.errorRate || 0.02,
    throughput: metrics.requestsPerSecond || 45
  };
}

function generateRecommendations(metrics) {
  const recommendations = [];
  
  if (metrics.cacheHitRate < 0.7) {
    recommendations.push('Improve caching strategy for frequently accessed modules');
  }
  
  if (metrics.avgResponseTime > 300) {
    recommendations.push('Optimize slow-performing knowledge retrieval workflows');
  }
  
  if (metrics.searchSuccessRate < 0.8) {
    recommendations.push('Enhance search algorithm and content tagging');
  }
  
  return recommendations;
}

return { json: analysis };
`
      }
    }
  ]
}
```

## Implementation Notes

- Knowledge workflows integrate seamlessly with the agent system through standardized interfaces  
- Caching strategies are tuned for optimal performance while maintaining content freshness  
- Search workflows support both exact match and semantic search capabilities  
- Multi-module synthesis enables complex knowledge assembly for comprehensive responses  
- All workflows include comprehensive error handling and fallback mechanisms  
- Performance monitoring provides insights for continuous optimization  
- Workflows are designed to scale horizontally with increased load

## Next Steps and Recommendations

After reviewing this knowledge workflows module, consider these recommended next actions:

1. **Implement basic knowledge retrieval** \- Start with simple caching and retrieval workflows  
2. **Set up search infrastructure** \- Deploy search indexing and semantic capabilities  
3. **Configure caching layers** \- Implement Redis-based caching with appropriate TTL strategies

## Next Steps

1️⃣ Continue with 02\_Workflows\_Agents.md to understand agent-workflow integration   
2️⃣ Review 02\_Workflows\_Orchestration.md for workflow coordination patterns   
3️⃣ Explore 01\_Core\_ProcessModel.md for underlying process architecture   
4️⃣ See 00\_KB3\_Implementation.md for deployment guidance   
5️⃣ Check 00\_KB3\_API\_Definitions.md for integration specifications  
