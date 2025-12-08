# 00\_KB3\_Templates

## title: "KnowledgeForge 3.2 Templates and Patterns"

module: "00\_Framework" topics: \["templates", "patterns", "code snippets", "configurations", "best practices", "reusable components"\] contexts: \["development", "standardization", "rapid prototyping", "consistency", "knowledge creation"\] difficulty: "intermediate" related\_sections: \["00\_KB3\_Core", "03\_Agents\_Catalog", "02\_N8N\_WorkflowRegistry", "00\_KB3\_Navigation"\]

## Core Approach

This document provides templates and patterns for all KnowledgeForge 3.2 components, including the new Git Integration features. Use these templates to maintain consistency across agents, workflows, documentation, and configurations while accelerating development.

## 📄 Documentation Templates

### Knowledge Module Template

````
# XX_Category_SubCategory

## title: "Descriptive Title Here"
module: "XX_Module"
topics: ["topic1", "topic2", "topic3", "topic4", "topic5"]
contexts: ["context1", "context2", "context3", "context4"]
difficulty: "beginner|intermediate|advanced"
related_sections: ["XX_Related1", "YY_Related2", "ZZ_Related3"]
data_transfer_support: true
git_tracked: true

## Core Approach

[Provide a clear, concise overview of the module's purpose and approach. This should be 2-3 paragraphs explaining the what, why, and how.]

## Key Concepts

### Concept 1
[Detailed explanation of the first key concept]

### Concept 2
[Detailed explanation of the second key concept]

## Implementation

### Basic Setup
```language
[Code example for basic setup]
````

### Advanced Configuration

```
[Code example for advanced usage]
```

## Integration Points

- **Workflows**: \[Related workflows\]  
- **Agents**: \[Related agents\]  
- **Data Sources**: \[Data integration points\]

## Performance Considerations

- \[Performance tip 1\]  
- \[Performance tip 2\]  
- \[Performance tip 3\]

## Troubleshooting

### Common Issue 1

**Problem**: \[Description\] **Solution**: \[Step-by-step solution\]

### Common Issue 2

**Problem**: \[Description\] **Solution**: \[Step-by-step solution\]

## Next Steps

1️⃣ **\[Primary action\]** → `Specific_File.md` 2️⃣ **\[Secondary action\]** → `Another_File.md` 3️⃣ **\[Optional exploration\]** → `Related_File.md` 4️⃣ **\[Advanced topic\]** → `Advanced_File.md` 5️⃣ **\[Testing\]** → `04_TestScenarios.md`

````

### Agent Specification Template

```markdown
# 03_KB3_Agents_AgentName

## title: "Agent Name: Purpose Statement"
module: "03_Agents"
topics: ["agent capability", "domain", "integration", "automation", "coordination"]
contexts: ["use case 1", "use case 2", "workflow integration", "system role"]
difficulty: "intermediate"
related_sections: ["03_Agents_Catalog", "00_KB3_Core", "02_N8N_WorkflowRegistry"]
agent_type: "utility|knowledge|coordination|system"
agent_access: ["user-facing", "system-internal", "both"]
data_transfer_support: true

## Core Approach

[Explain the agent's purpose, capabilities, and role in the KnowledgeForge ecosystem]

## Agent Configuration

### System Prompt

````

# Agent Name System Prompt

You are \[agent name\], a specialized agent in the KnowledgeForge 3.2 ecosystem. Your primary responsibility is \[main purpose\].

## Core Responsibilities

1. **\[Responsibility 1\]**: \[Detailed description\]  
2. **\[Responsibility 2\]**: \[Detailed description\]  
3. **\[Responsibility 3\]**: \[Detailed description\]

## Capabilities

- \[Capability 1 with explanation\]  
- \[Capability 2 with explanation\]  
- \[Capability 3 with explanation\]

## Integration Points

You work with:

- **\[Agent Name\]**: \[How you interact\]  
- **\[Workflow Name\]**: \[Integration pattern\]  
- **Git Integration**: \[Auto-capture behavior\]

## Response Patterns

### For \[Query Type 1\]

\[Response pattern with example\]

### For \[Query Type 2\]

\[Response pattern with example\]

## Constraints

- \[Constraint 1\]  
- \[Constraint 2\]  
- \[Constraint 3\]

````

### Capabilities

```yaml
capabilities:
  primary:
    - capability_1
    - capability_2
    - capability_3
  secondary:
    - support_capability_1
    - support_capability_2
  domains:
    - domain_1
    - domain_2
  limitations:
    - limitation_1
    - limitation_2
````

## Integration

### Webhook Configuration

```javascript
const agentWebhook = {
  endpoint: '/webhook/agent-name',
  method: 'POST',
  authentication: 'bearer',
  headers: {
    'Content-Type': 'application/json',
    'X-Agent-ID': 'agent-name-001'
  }
};
```

### Request Format

```json
{
  "query": "User query or task",
  "context": {
    "conversationId": "unique-id",
    "sessionData": {},
    "previousResults": []
  },
  "parameters": {
    "mode": "standard|detailed|summary",
    "timeout": 30000
  }
}
```

### Response Format

```json
{
  "response": "Agent response",
  "metadata": {
    "agentId": "agent-name-001",
    "processingTime": 1234,
    "confidence": 0.95
  },
  "actions": [
    {
      "type": "artifact_capture",
      "data": {}
    }
  ],
  "nextSteps": []
}
```

## Usage Examples

### Example 1: \[Common Use Case\]

```javascript
// Example implementation
const result = await queryAgent({
  query: "Example query",
  context: { /* context */ }
});
```

### Example 2: \[Advanced Use Case\]

```javascript
// Advanced implementation with error handling
try {
  const result = await queryAgent({
    query: "Complex query",
    parameters: {
      mode: "detailed",
      includeMetadata: true
    }
  });
} catch (error) {
  console.error('Agent error:', error);
}
```

## Performance Metrics

- **Average Response Time**: \< X seconds  
- **Success Rate**: \> 95%  
- **Concurrent Requests**: Up to Y  
- **Data Transfer Capacity**: Unlimited with compression

## Next Steps

1️⃣ **Deploy agent** → Follow `00_KB3_ImplementationGuide.md` 2️⃣ **Configure webhooks** → Set up in N8N 3️⃣ **Test integration** → Use `04_TestScenarios.md` 4️⃣ **Monitor performance** → Check dashboard 5️⃣ **Customize behavior** → Modify system prompt

````

## 🔄 Workflow Templates

### Basic N8N Workflow Template

```json
{
  "name": "KF3.2 [Purpose] Workflow",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "/kf32/[endpoint]",
        "responseMode": "responseNode",
        "options": {}
      },
      "id": "[workflow-id]-webhook",
      "name": "[Purpose] Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300],
      "webhookId": "kf32-[endpoint]"
    },
    {
      "parameters": {
        "jsCode": "// Process incoming data\nconst input = $input.all()[0].json;\n\n// Add your logic here\nconst processed = {\n  ...input,\n  processedAt: new Date().toISOString()\n};\n\nreturn [{ json: processed }];"
      },
      "id": "process-data",
      "name": "Process Data",
      "type": "n8n-nodes-base.code",
      "position": [450, 300]
    },
    {
      "parameters": {
        "content": "={{ JSON.stringify($json) }}",
        "options": {
          "responseCode": 200
        }
      },
      "id": "webhook-response",
      "name": "Webhook Response",
      "type": "n8n-nodes-base.respondToWebhook",
      "position": [650, 300]
    }
  ],
  "connections": {
    "[Purpose] Webhook": {
      "main": [
        [
          {
            "node": "Process Data",
            "type": "main",
            "index": 0
          }
        ]
      ]
    },
    "Process Data": {
      "main": [
        [
          {
            "node": "Webhook Response",
            "type": "main",
            "index": 0
          }
        ]
      ]
    }
  },
  "settings": {
    "executionOrder": "v1",
    "saveDataSuccessExecution": "all",
    "saveDataErrorExecution": "all",
    "executionTimeout": 300
  },
  "staticData": null,
  "tags": ["KnowledgeForge", "3.2", "[category]"],
  "triggerCount": 0,
  "updatedAt": "2025-01-01T00:00:00.000Z",
  "versionId": "kf32-[workflow]-v1"
}
````

### Git Integration Workflow Template

```json
{
  "name": "KF3.2 Git Integration - [Purpose]",
  "nodes": [
    {
      "parameters": {
        "httpMethod": "POST",
        "path": "/kf32/git/[operation]",
        "responseMode": "responseNode",
        "options": {
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
      "id": "git-operation-webhook",
      "name": "Git Operation Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "jsCode": "// Git operation logic\nconst operation = $input.all()[0].json;\n\n// Configure git operation\nconst gitConfig = {\n  provider: process.env.GIT_PROVIDER,\n  apiUrl: process.env.GIT_API_URL,\n  owner: process.env.GIT_REPO_OWNER,\n  repo: process.env.GIT_REPO_NAME,\n  token: process.env.GIT_ACCESS_TOKEN\n};\n\n// Process operation\nconst result = {\n  operation: operation.type,\n  status: 'success',\n  details: {}\n};\n\nreturn [{ json: result }];"
      },
      "id": "git-operation-processor",
      "name": "Git Operation Processor",
      "type": "n8n-nodes-base.code",
      "position": [450, 300]
    }
  ],
  "connections": {},
  "settings": {
    "executionOrder": "v1",
    "saveDataSuccessExecution": "all",
    "saveDataErrorExecution": "all"
  },
  "tags": ["KnowledgeForge", "Git", "3.2"]
}
```

## 🔧 Configuration Templates

### Agent Configuration Template

```
# config/agents/agent-name.yaml
agent:
  id: "agent-[name]-001"
  name: "[Agent Display Name]"
  type: "utility|knowledge|coordination|system"
  version: "1.0.0"
  
  capabilities:
    primary:
      - primary_capability_1
      - primary_capability_2
    secondary:
      - secondary_capability_1
    domains:
      - domain_1
      - domain_2
    
  endpoints:
    webhook: "${N8N_WEBHOOK_BASE}/agent-[name]"
    callback: "${N8N_WEBHOOK_BASE}/agent-[name]/callback"
    health: "${N8N_WEBHOOK_BASE}/agent-[name]/health"
    
  configuration:
    timeout: 30000
    maxRetries: 3
    cacheEnabled: true
    
  git_integration:
    auto_capture: true
    capture_patterns:
      - "*.md"
      - "*.json"
      - "*.yaml"
    branch_strategy: "feature/agent-[name]"
    
  monitoring:
    log_level: "info"
    metrics_enabled: true
    alert_thresholds:
      response_time: 5000
      error_rate: 0.05
```

### Docker Compose Service Template

```
# docker-compose.custom.yml
version: '3.8'

services:
  custom_service:
    image: custom/image:latest
    container_name: kf32_custom_service
    restart: always
    environment:
      - SERVICE_NAME=custom_service
      - KNOWLEDGEFORGE_VERSION=${KNOWLEDGEFORGE_VERSION}
      - API_KEY=${CUSTOM_API_KEY}
    volumes:
      - custom_data:/data
    networks:
      - knowledgeforge
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8080/health"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 40s
      
volumes:
  custom_data:
    
networks:
  knowledgeforge:
    external: true
```

### Environment Configuration Template

```shell
# .env.template
# KnowledgeForge 3.2 Environment Configuration Template

# Core Settings
KNOWLEDGEFORGE_VERSION=3.2.0
ENVIRONMENT=development|staging|production
DEBUG_MODE=false

# API Keys (Required)
KF32_API_KEY=generate-secure-key-here
CLAUDE_API_KEY=your-claude-api-key

# N8N Configuration
N8N_WEBHOOK_URL=https://your-domain.com/webhook
N8N_WEBHOOK_BASE=https://your-domain.com/webhook
N8N_BASIC_AUTH_ACTIVE=true
N8N_BASIC_AUTH_USER=admin
N8N_BASIC_AUTH_PASSWORD=secure-password

# Git Integration (New in 3.2)
GIT_PROVIDER=github|gitlab|bitbucket
GIT_API_URL=https://api.github.com
GIT_REPO_OWNER=your-organization
GIT_REPO_NAME=knowledgeforge-artifacts
GIT_ACCESS_TOKEN=your-git-token
GIT_DEFAULT_BRANCH=develop

# Data Transfer Configuration
MAX_CHUNK_SIZE=8000
COMPRESSION_METHOD=auto|pako|lz-string|native
ENABLE_STREAMING=true
COMPRESSION_LEVEL=6

# Redis Configuration (Optional)
REDIS_URL=redis://localhost:6379
REDIS_PASSWORD=optional-redis-password
SESSION_TTL=3600
CACHE_TTL=300

# Monitoring & Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
EMAIL_NOTIFICATIONS=team@example.com
NOTIFICATION_LEVEL=all|errors|critical
MONITORING_ENABLED=true

# Performance Tuning
MAX_CONCURRENT_REQUESTS=10
REQUEST_TIMEOUT=30000
BATCH_SIZE=100
RATE_LIMIT_REQUESTS=1000
RATE_LIMIT_WINDOW=3600

# Security
ENABLE_ENCRYPTION=true
JWT_SECRET=generate-long-random-string
SESSION_SECRET=another-long-random-string
ALLOWED_ORIGINS=https://your-domain.com,https://app.your-domain.com

# Feature Flags
FEATURE_GIT_INTEGRATION=true
FEATURE_CONTINUOUS_DOCS=true
FEATURE_INCANTATION_VAULT=true
FEATURE_ADVANCED_ANALYTICS=false
```

## 💻 Code Templates

### API Client Template

````javascript
// clients/knowledgeforge-client.js
class KnowledgeForgeClient {
  constructor(config = {}) {
    this.baseUrl = config.baseUrl || process.env.N8N_WEBHOOK_BASE;
    this.apiKey = config.apiKey || process.env.KF32_API_KEY;
    this.timeout = config.timeout || 30000;
  }
  
  async queryAgent(agentName, query, context = {}) {
    const response = await this.request(`/agent-${agentName}`, {
      method: 'POST',
      body: {
        query,
        context: {
          conversationId: context.conversationId || this.generateId(),
          ...context
        }
      }
    });
    
    return response;
  }
  
  async captureArtifact(artifact, metadata = {}) {
    const response = await this.request('/kf32/artifact/capture', {
      method: 'POST',
      body: {
        artifact: {
          content: artifact.content,
          type: artifact.type || this.detectType(artifact.content),
          filename: artifact.filename || this.generateFilename(artifact),
          language: artifact.language
        },
        metadata: {
          conversationId: metadata.conversationId || this.generateId(),
          timestamp: new Date().toISOString(),
          ...metadata
        }
      }
    });
    
    return response;
  }
  
  async checkHealth() {
    const endpoints = [
      '/health',
      '/kf32/git/status',
      '/kf32/monitoring/status'
    ];
    
    const results = await Promise.allSettled(
      endpoints.map(endpoint => 
        this.request(endpoint, { method: 'GET' })
      )
    );
    
    return {
      healthy: results.every(r => r.status === 'fulfilled'),
      details: results.map((r, i) => ({
        endpoint: endpoints[i],
        status: r.status,
        data: r.value || r.reason
      }))
    };
  }
  
  async request(endpoint, options = {}) {
    const url = `${this.baseUrl}${endpoint}`;
    const config = {
      method: options.method || 'GET',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': this.apiKey,
        ...options.headers
      },
      body: options.body ? JSON.stringify(options.body) : undefined,
      signal: AbortSignal.timeout(this.timeout)
    };
    
    try {
      const response = await fetch(url, config);
      
      if (!response.ok) {
        throw new Error(`HTTP ${response.status}: ${response.statusText}`);
      }
      
      return await response.json();
    } catch (error) {
      console.error(`Request failed: ${endpoint}`, error);
      throw error;
    }
  }
  
  generateId() {
    return `kf_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }
  
  detectType(content) {
    if (content.includes('```')) return 'code';
    if (content.includes('#') && content.includes('##')) return 'markdown';
    if (content.includes('"nodes"') && content.includes('"connections"')) return 'workflow';
    if (content.includes('version:') || content.includes('apiVersion:')) return 'config';
    return 'text';
  }
  
  generateFilename(artifact) {
    const typeExtensions = {
      'markdown': 'md',
      'code': 'js',
      'workflow': 'json',
      'config': 'yaml',
      'text': 'txt'
    };
    
    const ext = typeExtensions[artifact.type] || 'txt';
    const timestamp = Date.now();
    
    return `artifact_${timestamp}.${ext}`;
  }
}

// Export for use
if (typeof module !== 'undefined' && module.exports) {
  module.exports = KnowledgeForgeClient;
}
````

### Test Template

```javascript
// tests/test-[component].js
const assert = require('assert');
const { KnowledgeForgeClient } = require('../clients/knowledgeforge-client');

describe('Component Tests', () => {
  let client;
  
  before(async () => {
    client = new KnowledgeForgeClient({
      baseUrl: process.env.TEST_WEBHOOK_URL || 'http://localhost:5678/webhook',
      apiKey: process.env.TEST_API_KEY || 'test-key'
    });
    
    // Wait for services to be ready
    await waitForServices();
  });
  
  describe('Feature Tests', () => {
    it('should perform basic operation', async () => {
      const result = await client.someOperation();
      assert(result.success, 'Operation should succeed');
    });
    
    it('should handle errors gracefully', async () => {
      try {
        await client.invalidOperation();
        assert.fail('Should have thrown error');
      } catch (error) {
        assert(error.message.includes('expected'), 'Error message should be descriptive');
      }
    });
  });
  
  describe('Integration Tests', () => {
    it('should integrate with Git', async () => {
      const artifact = {
        content: '# Test Document',
        type: 'markdown',
        filename: 'test.md'
      };
      
      const result = await client.captureArtifact(artifact);
      assert(result.success, 'Artifact should be captured');
      assert(result.commitId, 'Should return commit ID');
    });
  });
  
  after(async () => {
    // Cleanup
    await cleanup();
  });
});

async function waitForServices() {
  const maxAttempts = 30;
  for (let i = 0; i < maxAttempts; i++) {
    try {
      const health = await client.checkHealth();
      if (health.healthy) return;
    } catch (error) {
      // Service not ready yet
    }
    await new Promise(resolve => setTimeout(resolve, 1000));
  }
  throw new Error('Services did not become ready');
}

async function cleanup() {
  // Cleanup test data
}
```

## 🚀 Quick Start Templates

### Rapid Agent Creation

```shell
#!/bin/bash
# scripts/create-agent.sh

AGENT_NAME=$1
AGENT_TYPE=${2:-utility}

if [ -z "$AGENT_NAME" ]; then
  echo "Usage: ./create-agent.sh <agent-name> [agent-type]"
  exit 1
fi

# Create agent specification
cat > "agents/specifications/03_KB3_Agents_${AGENT_NAME}.md" << EOF
# 03_KB3_Agents_${AGENT_NAME}

## title: "${AGENT_NAME} Agent"
module: "03_Agents"
topics: ["${AGENT_TYPE}", "automation", "integration"]
contexts: ["workflow", "system"]
difficulty: "intermediate"
related_sections: ["03_Agents_Catalog", "00_KB3_Core"]
agent_type: "${AGENT_TYPE}"
agent_access: ["all"]
data_transfer_support: true

## Core Approach

The ${AGENT_NAME} Agent provides...

## Agent Configuration

### System Prompt

\`\`\`
You are the ${AGENT_NAME} Agent...
\`\`\`

## Next Steps

1️⃣ **Configure agent** → Update system prompt
2️⃣ **Deploy webhook** → Create N8N workflow
3️⃣ **Test agent** → Use test scenarios
EOF

echo "✅ Created agent specification: 03_KB3_Agents_${AGENT_NAME}.md"
echo "📤 This will be automatically captured by Git Integration"
```

### Quick Workflow Deploy

```javascript
// scripts/quick-deploy-workflow.js
const fs = require('fs');
const path = require('path');

async function deployWorkflow(workflowPath) {
  const workflow = JSON.parse(
    fs.readFileSync(workflowPath, 'utf8')
  );
  
  // Add KnowledgeForge tags
  workflow.tags = workflow.tags || [];
  workflow.tags.push('KnowledgeForge', '3.2', 'auto-deployed');
  
  // Add Git integration
  workflow.settings = workflow.settings || {};
  workflow.settings.saveDataSuccessExecution = 'all';
  workflow.settings.saveDataErrorExecution = 'all';
  
  // Deploy to N8N
  const response = await fetch(`${process.env.N8N_API_URL}/workflows`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-N8N-API-KEY': process.env.N8N_API_KEY
    },
    body: JSON.stringify(workflow)
  });
  
  if (response.ok) {
    console.log(`✅ Deployed: ${workflow.name}`);
  } else {
    console.error(`❌ Failed to deploy: ${workflow.name}`);
  }
}

// Deploy all workflows in directory
const workflowDir = path.join(__dirname, '../workflows/n8n');
fs.readdirSync(workflowDir)
  .filter(file => file.endsWith('.json'))
  .forEach(file => {
    deployWorkflow(path.join(workflowDir, file));
  });
```

## 📋 Checklists

### New Component Checklist

- [ ] Create documentation using module template  
- [ ] Add to appropriate catalog/registry  
- [ ] Configure Git auto-capture  
- [ ] Create test scenarios  
- [ ] Update navigation references  
- [ ] Deploy associated workflows  
- [ ] Test integration end-to-end  
- [ ] Update monitoring dashboard  
- [ ] Document in team wiki  
- [ ] Announce in team channel

### Production Deployment Checklist

- [ ] Environment variables configured  
- [ ] SSL certificates installed  
- [ ] Git repository initialized  
- [ ] Workflows imported and activated  
- [ ] Agents configured and tested  
- [ ] Monitoring dashboard accessible  
- [ ] Backup automation enabled  
- [ ] Health checks passing  
- [ ] Documentation updated  
- [ ] Team trained

## Next Steps

1️⃣ **Choose appropriate template** → Based on component type 2️⃣ **Customize for your needs** → Modify templates as needed 3️⃣ **Follow naming conventions** → Maintain consistency 4️⃣ **Test thoroughly** → Use test templates 5️⃣ **Document changes** → Update relevant guides  
