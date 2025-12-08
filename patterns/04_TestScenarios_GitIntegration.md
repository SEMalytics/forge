# 04\_TestScenarios\_GitIntegration

# Git Integration Test Scenarios

---

## title: "Git Integration Test Scenarios"

module: "04\_Testing" topics: \["git integration testing", "artifact capture validation", "repository health", "automation testing", "version control validation"\] contexts: \["integration testing", "system validation", "continuous integration", "repository management", "artifact workflow"\] difficulty: "intermediate" related\_sections: \["03\_KB3\_Agents\_GitIntegration", "03\_KB3\_Agents\_VersionControl", "00\_KB3\_ImplementationGuide\_3.2\_GitIntegration", "04\_TestScenarios"\] testing\_type: "integration" test\_coverage: \["artifact capture", "git operations", "branch management", "documentation sync", "error handling"\] data\_transfer\_support: true

## Core Approach

These test scenarios validate the complete Git Integration system, including artifact capture, automatic commits, branch management, version control, and documentation synchronization. Each test includes setup, execution, validation, and cleanup procedures to ensure the system eliminates manual copy/paste workflows while maintaining repository integrity.

## Test Suite: Artifact Capture

### Test Scenario 1: Basic Artifact Capture

**Purpose**: Validate that artifacts are automatically captured and committed to git

**Setup**:

```shell
# Initialize test environment
export TEST_SESSION_ID="test_artifact_capture_$(date +%s)"
export TEST_BRANCH="test/artifact-capture-$TEST_SESSION_ID"
export GIT_TEST_REPO="test-knowledgeforge-artifacts"

# Create test branch
git checkout -b $TEST_BRANCH
git push origin $TEST_BRANCH
```

**Test Steps**:

```javascript
// Test artifact capture
const testArtifact = {
  artifact: {
    content: `# Test Agent Specification

## title: "Test Agent"
module: "03_Agents"
topics: ["testing", "validation", "git integration"]
contexts: ["test environment", "integration testing"]
difficulty: "intermediate"
related_sections: ["03_Agents_Catalog", "00_KB3_Core"]
agent_type: "test"
data_transfer_support: true

## Core Approach

This is a test agent created to validate the Git Integration system.`,
    type: 'markdown',
    filename: '03_KB3_Agents_TestAgent.md'
  },
  metadata: {
    conversationId: TEST_SESSION_ID,
    timestamp: new Date().toISOString(),
    context: 'Testing artifact capture',
    author: 'Test Suite',
    branch: TEST_BRANCH
  }
};

// Send artifact to capture webhook
const response = await fetch(`${WEBHOOK_URL}/kf32/artifact/capture`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.KF32_API_KEY
  },
  body: JSON.stringify(testArtifact)
});

const result = await response.json();
```

**Validation Criteria**:

- [ ] HTTP response status is 200  
- [ ] Response indicates success  
- [ ] File created in correct directory (`agents/specifications/`)  
- [ ] Commit created with proper message format  
- [ ] Commit pushed to test branch  
- [ ] Manifest updated with artifact entry

**Expected Git Commit**:

```
[DOC] Add: 03_KB3_Agents_TestAgent.md

- Type: KnowledgeForge Documentation
- Module: 03_Agents
- Context: Testing artifact capture

Auto-captured from KnowledgeForge conversation.

Conversation-ID: test_artifact_capture_1234567890
Timestamp: 2025-01-10T12:00:00.000Z
```

**Cleanup**:

```shell
# Delete test branch
git push origin --delete $TEST_BRANCH
```

### Test Scenario 2: Batch Artifact Capture

**Purpose**: Validate that multiple related artifacts are batched efficiently

**Test Steps**:

```javascript
// Create multiple artifacts within batch window
const artifacts = [
  {
    artifact: {
      content: '# Main Documentation\n\nPrimary content here.',
      type: 'markdown',
      filename: 'main_doc.md'
    },
    metadata: { conversationId: 'batch-test-001' }
  },
  {
    artifact: {
      content: '{"name": "Support Workflow", "nodes": []}',
      type: 'workflow',
      filename: 'support_workflow.json'
    },
    metadata: { conversationId: 'batch-test-001' }
  },
  {
    artifact: {
      content: 'export API_KEY="test-key"\nexport ENV="test"',
      type: 'config',
      filename: '.env.test'
    },
    metadata: { conversationId: 'batch-test-001' }
  }
];

// Send all artifacts within batch window (30 seconds)
const results = [];
for (const artifact of artifacts) {
  const response = await fetch(`${WEBHOOK_URL}/kf32/artifact/capture`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.KF32_API_KEY
    },
    body: JSON.stringify(artifact)
  });
  
  results.push(await response.json());
  
  // Small delay between requests
  await new Promise(resolve => setTimeout(resolve, 2000));
}
```

**Validation Criteria**:

- [ ] All artifacts captured successfully  
- [ ] Artifacts grouped in single commit (if within batch window)  
- [ ] Commit message references all files  
- [ ] Files placed in correct directories  
- [ ] Manifest updated with all entries

### Test Scenario 3: Large Artifact Handling

**Purpose**: Validate handling of large artifacts and compression

**Test Steps**:

```javascript
// Generate large artifact (5MB)
const largeContent = 'x'.repeat(5 * 1024 * 1024);
const largeArtifact = {
  artifact: {
    content: `# Large Dataset\n\n\`\`\`\n${largeContent}\n\`\`\``,
    type: 'markdown',
    filename: 'large_dataset.md'
  },
  metadata: {
    conversationId: 'large-test-001',
    context: 'Testing large file handling'
  }
};

// Test compression and chunking
const response = await fetch(`${WEBHOOK_URL}/kf32/artifact/capture`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.KF32_API_KEY
  },
  body: JSON.stringify(largeArtifact)
});
```

**Validation Criteria**:

- [ ] Large file handled without timeout  
- [ ] Git LFS used if configured  
- [ ] Compression applied effectively  
- [ ] No memory overflow errors  
- [ ] Reasonable commit time (\<30 seconds)

## Test Suite: Git Operations

### Test Scenario 4: Branch Management

**Purpose**: Validate automatic branch creation and management

**Test Steps**:

```javascript
// Test branch creation for different types
const branchTests = [
  {
    type: 'feature',
    name: 'feature/test-auto-routing',
    base: 'develop'
  },
  {
    type: 'conversation',
    name: `conversation/session-${Date.now()}`,
    base: 'develop'
  },
  {
    type: 'hotfix',
    name: 'hotfix/critical-fix-test',
    base: 'main'
  }
];

for (const test of branchTests) {
  const response = await fetch(`${WEBHOOK_URL}/kf32/git/branch/create`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.KF32_API_KEY
    },
    body: JSON.stringify({
      branchName: test.name,
      baseBranch: test.base,
      purpose: 'Integration testing'
    })
  });
  
  const result = await response.json();
  console.log(`Branch ${test.name}: ${result.success ? 'Created' : 'Failed'}`);
}
```

**Validation Criteria**:

- [ ] Branches created from correct base  
- [ ] Branch protection rules applied  
- [ ] Naming conventions enforced  
- [ ] Metadata stored correctly  
- [ ] Branches visible in repository

### Test Scenario 5: Merge Operations

**Purpose**: Validate automatic merge strategies

**Test Steps**:

```javascript
// Create test branches with different content
const testMerge = async () => {
  // Create feature branch
  await createBranch('feature/merge-test');
  
  // Add documentation change
  await captureArtifact({
    artifact: {
      content: '# Updated Documentation\n\nNew section added.',
      type: 'markdown',
      filename: 'merge_test.md'
    },
    metadata: {
      branch: 'feature/merge-test'
    }
  });
  
  // Test merge
  const mergeResponse = await fetch(`${WEBHOOK_URL}/kf32/git/merge`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.KF32_API_KEY
    },
    body: JSON.stringify({
      sourceBranch: 'feature/merge-test',
      targetBranch: 'develop',
      strategy: 'auto',
      deleteSourceBranch: true
    })
  });
  
  return await mergeResponse.json();
};
```

**Validation Criteria**:

- [ ] Documentation merges automatically  
- [ ] Merge commit created with proper message  
- [ ] Source branch deleted if specified  
- [ ] No conflicts for non-overlapping changes  
- [ ] Merge recorded in repository history

### Test Scenario 6: Conflict Resolution

**Purpose**: Validate conflict detection and resolution

**Test Steps**:

```javascript
// Create conflicting changes
const testConflictResolution = async () => {
  // Create two branches
  await createBranch('feature/conflict-1');
  await createBranch('feature/conflict-2');
  
  // Same file, different changes
  const file = 'conflict_test.md';
  
  // Branch 1 change
  await captureArtifact({
    artifact: {
      content: '# Header\n\nBranch 1 content.',
      filename: file
    },
    metadata: { branch: 'feature/conflict-1' }
  });
  
  // Branch 2 change
  await captureArtifact({
    artifact: {
      content: '# Header\n\nBranch 2 content.',
      filename: file
    },
    metadata: { branch: 'feature/conflict-2' }
  });
  
  // Merge branch 1 to develop
  await mergeBranch('feature/conflict-1', 'develop');
  
  // Attempt to merge branch 2 (should detect conflict)
  const conflictResponse = await mergeBranch('feature/conflict-2', 'develop');
  
  return conflictResponse;
};
```

**Validation Criteria**:

- [ ] Conflict detected correctly  
- [ ] Conflict report generated  
- [ ] Both versions preserved  
- [ ] Manual review flag set  
- [ ] Notification sent

## Test Suite: Documentation Synchronization

### Test Scenario 7: Cross-Reference Validation

**Purpose**: Validate documentation cross-reference checking

**Test Steps**:

```javascript
// Create document with references
const docWithRefs = {
  artifact: {
    content: `# Test Document

See implementation details in 00_KB3_Core.md and workflow patterns in 02_N8N_WorkflowRegistry.md.

Invalid reference: 99_NonExistent_File.md`,
    type: 'markdown',
    filename: 'test_references.md'
  }
};

// Capture and trigger validation
await captureArtifact(docWithRefs);

// Trigger documentation sync
const syncResponse = await fetch(`${WEBHOOK_URL}/kf32/docs/update`, {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.KF32_API_KEY
  },
  body: JSON.stringify({ validateReferences: true })
});

const validation = await syncResponse.json();
```

**Validation Criteria**:

- [ ] Valid references confirmed  
- [ ] Invalid references detected  
- [ ] Warning generated for invalid refs  
- [ ] Suggestions provided for fixes  
- [ ] Validation report accurate

### Test Scenario 8: Index Generation

**Purpose**: Validate automatic documentation index generation

**Test Steps**:

```javascript
// Add multiple documents
const testDocs = [
  '00_TestCore.md',
  '02_TestWorkflow.md',
  '03_TestAgent.md'
];

for (const doc of testDocs) {
  await captureArtifact({
    artifact: {
      content: `# ${doc}\n\nTest content.`,
      filename: doc
    }
  });
}

// Trigger index generation
const indexResponse = await fetch(`${WEBHOOK_URL}/kf32/docs/index/generate`, {
  method: 'POST',
  headers: {
    'X-API-Key': process.env.KF32_API_KEY
  }
});
```

**Validation Criteria**:

- [ ] Index includes all documents  
- [ ] Categories correctly assigned  
- [ ] Navigation links valid  
- [ ] Statistics accurate  
- [ ] Index committed to repository

## Test Suite: Repository Health

### Test Scenario 9: Branch Cleanup

**Purpose**: Validate automatic branch cleanup

**Test Steps**:

```javascript
// Create old conversation branches
const oldDate = new Date();
oldDate.setDate(oldDate.getDate() - 35); // 35 days old

const oldBranches = [];
for (let i = 0; i < 5; i++) {
  const branchName = `conversation/old-session-${i}`;
  await createBranch(branchName);
  
  // Simulate old commits (would need git command)
  // git commit --date="35 days ago"
  
  oldBranches.push(branchName);
}

// Trigger cleanup
const cleanupResponse = await fetch(`${WEBHOOK_URL}/kf32/git/maintenance/cleanup`, {
  method: 'POST',
  headers: {
    'X-API-Key': process.env.KF32_API_KEY
  },
  body: JSON.stringify({
    cleanupType: 'branches',
    olderThanDays: 30
  })
});
```

**Validation Criteria**:

- [ ] Old conversation branches deleted  
- [ ] Recent branches preserved  
- [ ] Protected branches untouched  
- [ ] Cleanup report generated  
- [ ] Repository size reduced

### Test Scenario 10: Performance Monitoring

**Purpose**: Validate git operation performance metrics

**Test Steps**:

```javascript
// Performance test suite
const performanceTest = async () => {
  const metrics = {
    captureTime: [],
    commitTime: [],
    pushTime: [],
    totalTime: []
  };
  
  // Run 10 iterations
  for (let i = 0; i < 10; i++) {
    const start = Date.now();
    
    const artifact = {
      artifact: {
        content: `# Performance Test ${i}\n\nTest content.`,
        filename: `perf_test_${i}.md`
      }
    };
    
    const captureStart = Date.now();
    const response = await captureArtifact(artifact);
    const captureEnd = Date.now();
    
    metrics.captureTime.push(captureEnd - captureStart);
    metrics.totalTime.push(captureEnd - start);
  }
  
  // Calculate averages
  const avg = arr => arr.reduce((a, b) => a + b, 0) / arr.length;
  
  return {
    avgCaptureTime: avg(metrics.captureTime),
    avgTotalTime: avg(metrics.totalTime),
    maxTime: Math.max(...metrics.totalTime),
    minTime: Math.min(...metrics.totalTime)
  };
};
```

**Validation Criteria**:

- [ ] Average capture time \< 2 seconds  
- [ ] Average total time \< 5 seconds  
- [ ] No timeouts  
- [ ] Consistent performance  
- [ ] Metrics properly recorded

## Test Suite: Error Handling

### Test Scenario 11: Network Failure Recovery

**Purpose**: Validate system behavior during network failures

**Test Steps**:

```javascript
// Simulate network failure
const testNetworkFailure = async () => {
  // Temporarily block git API endpoint
  // This would be done at network level
  
  const artifact = {
    artifact: {
      content: '# Test During Network Failure',
      filename: 'network_failure_test.md'
    }
  };
  
  try {
    const response = await captureArtifact(artifact);
    return response;
  } catch (error) {
    // Check if queued for retry
    const queueStatus = await fetch(`${WEBHOOK_URL}/kf32/queue/status`, {
      headers: { 'X-API-Key': process.env.KF32_API_KEY }
    });
    
    return await queueStatus.json();
  }
};
```

**Validation Criteria**:

- [ ] Artifact queued for retry  
- [ ] No data loss  
- [ ] Appropriate error message  
- [ ] Retry mechanism activated  
- [ ] Recovery after network restoration

### Test Scenario 12: Authentication Failure

**Purpose**: Validate handling of authentication failures

**Test Steps**:

```javascript
// Test with invalid token
const testAuthFailure = async () => {
  const originalToken = process.env.GIT_ACCESS_TOKEN;
  process.env.GIT_ACCESS_TOKEN = 'invalid-token';
  
  try {
    const response = await captureArtifact({
      artifact: {
        content: '# Auth Test',
        filename: 'auth_test.md'
      }
    });
    
    return response;
  } finally {
    // Restore valid token
    process.env.GIT_ACCESS_TOKEN = originalToken;
  }
};
```

**Validation Criteria**:

- [ ] Auth failure detected  
- [ ] Appropriate error message  
- [ ] No partial commits  
- [ ] Alert sent to admin  
- [ ] System remains stable

## Test Automation

### Continuous Integration Tests

```
# .github/workflows/git-integration-tests.yml
name: Git Integration Tests

on:
  push:
    branches: [develop, main]
  pull_request:
    branches: [develop]
  schedule:
    - cron: '0 */6 * * *'  # Every 6 hours

jobs:
  integration-tests:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v3
    
    - name: Setup Test Environment
      run: |
        docker-compose -f docker-compose.test.yml up -d
        sleep 30
        
    - name: Run Artifact Capture Tests
      run: npm test -- --suite=artifact-capture
      
    - name: Run Git Operations Tests
      run: npm test -- --suite=git-operations
      
    - name: Run Documentation Sync Tests
      run: npm test -- --suite=doc-sync
      
    - name: Run Repository Health Tests
      run: npm test -- --suite=repo-health
      
    - name: Run Error Handling Tests
      run: npm test -- --suite=error-handling
      
    - name: Generate Test Report
      if: always()
      run: npm run test:report
      
    - name: Upload Test Results
      if: always()
      uses: actions/upload-artifact@v3
      with:
        name: test-results
        path: test-results/
```

### Test Runner Script

```javascript
// test-runner.js
const { execSync } = require('child_process');
const fs = require('fs');

class GitIntegrationTestRunner {
  constructor() {
    this.results = {
      passed: 0,
      failed: 0,
      skipped: 0,
      suites: {}
    };
  }
  
  async runAllTests() {
    console.log('🧪 KnowledgeForge Git Integration Test Suite\n');
    
    const suites = [
      { name: 'Artifact Capture', tests: [1, 2, 3] },
      { name: 'Git Operations', tests: [4, 5, 6] },
      { name: 'Documentation Sync', tests: [7, 8] },
      { name: 'Repository Health', tests: [9, 10] },
      { name: 'Error Handling', tests: [11, 12] }
    ];
    
    for (const suite of suites) {
      console.log(`\n📁 ${suite.name}`);
      console.log('─'.repeat(50));
      
      this.results.suites[suite.name] = {
        tests: [],
        passed: 0,
        failed: 0
      };
      
      for (const testNum of suite.tests) {
        await this.runTest(suite.name, testNum);
      }
    }
    
    this.generateReport();
  }
  
  async runTest(suiteName, testNumber) {
    const testName = `Test Scenario ${testNumber}`;
    
    try {
      // Run specific test
      const result = await require(`./tests/scenario-${testNumber}.js`).run();
      
      if (result.success) {
        console.log(`  ✅ ${testName}: PASSED`);
        this.results.passed++;
        this.results.suites[suiteName].passed++;
      } else {
        console.log(`  ❌ ${testName}: FAILED`);
        console.log(`     ${result.error}`);
        this.results.failed++;
        this.results.suites[suiteName].failed++;
      }
      
      this.results.suites[suiteName].tests.push({
        name: testName,
        success: result.success,
        duration: result.duration,
        error: result.error
      });
      
    } catch (error) {
      console.log(`  ⚠️  ${testName}: ERROR`);
      console.log(`     ${error.message}`);
      this.results.failed++;
      this.results.suites[suiteName].failed++;
    }
  }
  
  generateReport() {
    console.log('\n\n📊 Test Results Summary');
    console.log('═'.repeat(50));
    console.log(`Total Tests: ${this.results.passed + this.results.failed}`);
    console.log(`Passed: ${this.results.passed} ✅`);
    console.log(`Failed: ${this.results.failed} ❌`);
    console.log(`Success Rate: ${(this.results.passed / (this.results.passed + this.results.failed) * 100).toFixed(1)}%`);
    
    // Generate detailed report
    const report = {
      timestamp: new Date().toISOString(),
      summary: this.results,
      environment: {
        node: process.version,
        platform: process.platform,
        git_provider: process.env.GIT_PROVIDER
      }
    };
    
    fs.writeFileSync('test-results/git-integration-report.json', JSON.stringify(report, null, 2));
    console.log('\n📄 Detailed report saved to test-results/git-integration-report.json');
  }
}

// Run tests
const runner = new GitIntegrationTestRunner();
runner.runAllTests().catch(console.error);
```

## Test Data Management

### Test Data Setup

```shell
#!/bin/bash
# setup-test-data.sh

echo "Setting up Git Integration test data..."

# Create test repository
git init test-repo
cd test-repo

# Add test files
mkdir -p documentation/core agents/specifications workflows/n8n

# Create sample files
echo "# Test Core Documentation" > documentation/core/00_Test_Core.md
echo '{"name": "Test Workflow"}' > workflows/n8n/test_workflow.json
echo "# Test Agent" > agents/specifications/03_Test_Agent.md

# Initial commit
git add .
git commit -m "[TEST] Initial test data"

# Create test branches
git branch feature/test-feature
git branch conversation/test-session

echo "Test data setup complete!"
```

### Test Data Cleanup

```shell
#!/bin/bash
# cleanup-test-data.sh

echo "Cleaning up test data..."

# Remove test branches
git branch -D feature/test-* 2>/dev/null
git branch -D conversation/test-* 2>/dev/null
git push origin --delete feature/test-* 2>/dev/null
git push origin --delete conversation/test-* 2>/dev/null

# Remove test files
find . -name "*test*" -type f -delete

# Clean git history
git gc --aggressive --prune=now

echo "Test data cleanup complete!"
```

## Performance Benchmarks

### Expected Performance Metrics

```
performance_benchmarks:
  artifact_capture:
    small_file: "< 500ms"      # Files under 100KB
    medium_file: "< 2s"        # Files 100KB-1MB
    large_file: "< 10s"        # Files 1MB-10MB
    
  git_operations:
    branch_create: "< 1s"
    commit_push: "< 3s"
    merge_simple: "< 2s"
    merge_complex: "< 10s"
    
  documentation_sync:
    quick_scan: "< 5s"
    full_scan: "< 30s"
    index_generation: "< 10s"
    
  repository_health:
    status_check: "< 500ms"
    branch_cleanup: "< 60s"
    garbage_collection: "< 5m"
```

## Next Steps

1️⃣ **Run basic integration tests** → Validate core functionality 2️⃣ **Set up CI/CD pipeline** → Automate test execution 3️⃣ **Configure performance monitoring** → Track metrics over time 4️⃣ **Create test documentation** → Document test procedures 5️⃣ **Establish baselines** → Set performance benchmarks 6️⃣ **Schedule regular testing** → Ensure ongoing system health  
