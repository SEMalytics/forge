# 00\_KB3\_ImplementationGuide\_3.2\_GitIntegration

# KnowledgeForge 3.2: Git Integration Implementation Guide

---

## title: "Git Integration Implementation Guide"

module: "00\_Framework" topics: \["git integration", "artifact export", "repository setup", "automation", "version control", "continuous documentation"\] contexts: \["setup", "configuration", "deployment", "automation workflows", "repository management"\] difficulty: "intermediate" related\_sections: \["00\_KB3\_Core", "03\_KB3\_Agents\_GitIntegration", "03\_KB3\_Agents\_VersionControl", "02\_N8N\_WorkflowRegistry", "00\_KB3\_ImplementationGuide"\]

## Core Approach

This guide provides step-by-step instructions for implementing KnowledgeForge 3.2's automated git integration system, which eliminates manual copy/paste workflows by automatically capturing, versioning, and committing all artifacts to a git repository. The system preserves the "magical incantation" while enabling seamless collaboration and continuous documentation updates. It integrates seamlessly with the Agent-Building Agent (03\_KB3\_Agents\_AgentBuilder.md) to automatically capture all generated agent artifacts.

## 🚀 Quick Setup (30 Minutes)

### Prerequisites

- KnowledgeForge 3.1 system deployed  
- Git repository (GitHub, GitLab, or Bitbucket)  
- Personal access token with repository write permissions  
- N8N instance with webhook capabilities  
- Redis for session management (optional but recommended)

### Step 1: Create Git Repository Structure

```shell
# Clone your repository
git clone https://github.com/your-org/knowledgeforge-artifacts.git
cd knowledgeforge-artifacts

# Create KnowledgeForge directory structure
mkdir -p {agents/{specifications,prompts,configurations},workflows/{n8n,templates,documentation}}
mkdir -p {documentation/{core,guides,examples},artifacts/{code,configurations,scripts}}
mkdir -p {tests/{scenarios,validation,results},conversations/{context,history,summaries}}
mkdir -p .knowledgeforge/{incantation/{prompts,agents,workflows,patterns},version}

# Create initial files
echo "3.2.0" > .knowledgeforge/version
echo '{"artifacts": [], "lastUpdated": null}' > .knowledgeforge/manifest.json

# Create .gitignore
cat > .gitignore << EOF
# KnowledgeForge
*.tmp
.draft*
*_backup.*
conversations/history/*
.env
node_modules/
*.log
EOF

# Initial commit
git add .
git commit -m "[INIT] KnowledgeForge 3.2 repository structure"
git push origin main
```

### Step 2: Configure Git Provider Access

#### GitHub Configuration

```shell
# Set environment variables
export GIT_PROVIDER="github"
export GIT_API_URL="https://api.github.com"
export GIT_REPO_OWNER="your-org"
export GIT_REPO_NAME="knowledgeforge-artifacts"
export GIT_ACCESS_TOKEN="ghp_your_personal_access_token"
export GIT_DEFAULT_BRANCH="develop"

# Test access
curl -H "Authorization: token $GIT_ACCESS_TOKEN" \
     -H "Accept: application/vnd.github.v3+json" \
     $GIT_API_URL/repos/$GIT_REPO_OWNER/$GIT_REPO_NAME
```

#### GitLab Configuration

```shell
# Set environment variables
export GIT_PROVIDER="gitlab"
export GIT_API_URL="https://gitlab.com/api/v4"
export GIT_PROJECT_ID="your-project-id"
export GIT_ACCESS_TOKEN="glpat-your_personal_access_token"
export GIT_DEFAULT_BRANCH="develop"

# Test access
curl -H "PRIVATE-TOKEN: $GIT_ACCESS_TOKEN" \
     $GIT_API_URL/projects/$GIT_PROJECT_ID
```

### Step 3: Deploy Git Integration Workflows

```shell
# Import Artifact Export Workflow
curl -X POST http://localhost:5678/rest/workflows \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -d @kf32_artifact_export_workflow.json

# Import Continuous Documentation Workflow  
curl -X POST http://localhost:5678/rest/workflows \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -d @kf32_continuous_docs_workflow.json

# Activate workflows
curl -X PATCH http://localhost:5678/rest/workflows/kf32-artifact-export \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -d '{"active": true}'

curl -X PATCH http://localhost:5678/rest/workflows/kf32-continuous-docs \
  -H "Content-Type: application/json" \
  -H "X-N8N-API-KEY: $N8N_API_KEY" \
  -d '{"active": true}'
```

### Step 4: Configure Git Integration Agent

```
# config/git-integration.yaml
git_integration:
  repository:
    url: "${GIT_REPO_URL}"
    branch: "develop"
    default_author:
      name: "KnowledgeForge System"
      email: "system@knowledgeforge.ai"
  
  capture:
    auto_capture: true
    capture_delay: 5000
    batch_window: 30000
    
  commit:
    auto_commit: true
    squash_related: true
    sign_commits: false
    
  sync:
    push_frequency: 300000
    pull_before_push: true
    force_push: false
    
  notifications:
    webhook_url: "${SLACK_WEBHOOK_URL}"
```

### Step 5: Test Artifact Capture

```javascript
// Test artifact capture
const testArtifact = {
  artifact: {
    content: '# Test Documentation\n\nThis is a test artifact.',
    type: 'markdown',
    filename: 'test_artifact.md'
  },
  metadata: {
    conversationId: 'test-conv-001',
    context: 'Testing git integration',
    author: 'Test User'
  }
};

fetch('http://localhost:5678/webhook/kf32/artifact/capture', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': process.env.KF32_API_KEY
  },
  body: JSON.stringify(testArtifact)
})
.then(res => res.json())
.then(result => console.log('Capture result:', result));
```

## 📋 Complete Configuration Guide

### Environment Variables

```shell
# Core Git Configuration
export GIT_PROVIDER="github"                    # github, gitlab, bitbucket
export GIT_API_URL="https://api.github.com"    # API endpoint
export GIT_REPO_OWNER="your-org"               # Repository owner
export GIT_REPO_NAME="knowledgeforge"          # Repository name
export GIT_ACCESS_TOKEN="your-token"           # Personal access token
export GIT_DEFAULT_BRANCH="develop"            # Default branch

# Artifact Capture Configuration
export CAPTURE_AUTO_ENABLED="true"             # Enable auto-capture
export CAPTURE_DELAY_MS="5000"                # Delay before capture
export CAPTURE_BATCH_WINDOW="30000"           # Batch window for related artifacts

# Version Control Configuration
export VC_AUTO_MERGE_DOCS="true"              # Auto-merge documentation
export VC_REQUIRE_REVIEW="true"               # Require PR reviews
export VC_DELETE_MERGED_BRANCHES="true"       # Cleanup merged branches
export VC_BRANCH_PROTECTION="main,develop"    # Protected branches

# Repository Maintenance
export REPO_GC_SCHEDULE="0 2 * * 0"          # Weekly garbage collection
export REPO_BRANCH_CLEANUP="0 3 1 * *"       # Monthly branch cleanup
export REPO_SIZE_WARNING="1073741824"        # 1GB warning threshold

# Notifications
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
export EMAIL_NOTIFICATIONS="team@example.com"
export NOTIFICATION_LEVEL="errors"            # all, errors, summary

# Session Management (Redis)
export REDIS_URL="redis://localhost:6379"
export SESSION_TTL="3600"
export MAX_RETRIES="3"
```

### Advanced Git Provider Configuration

#### GitHub Advanced Setup

```javascript
// github-config.js
const githubConfig = {
  api: {
    baseUrl: 'https://api.github.com',
    version: 'v3',
    headers: {
      'Accept': 'application/vnd.github.v3+json',
      'Authorization': `token ${process.env.GIT_ACCESS_TOKEN}`
    }
  },
  
  repository: {
    owner: process.env.GIT_REPO_OWNER,
    name: process.env.GIT_REPO_NAME,
    defaultBranch: 'develop',
    protectedBranches: ['main', 'develop']
  },
  
  pullRequest: {
    autoMerge: true,
    deleteHeadBranch: true,
    requireReviews: 1,
    dismissStaleReviews: true
  },
  
  webhooks: {
    secret: process.env.GITHUB_WEBHOOK_SECRET,
    events: ['push', 'pull_request', 'create', 'delete']
  }
};
```

#### Branch Protection Rules

```shell
# Set up branch protection for main
curl -X PUT $GIT_API_URL/repos/$GIT_REPO_OWNER/$GIT_REPO_NAME/branches/main/protection \
  -H "Authorization: token $GIT_ACCESS_TOKEN" \
  -H "Accept: application/vnd.github.v3+json" \
  -d '{
    "required_status_checks": {
      "strict": true,
      "contexts": ["continuous-integration/knowledgeforge"]
    },
    "enforce_admins": false,
    "required_pull_request_reviews": {
      "required_approving_review_count": 1,
      "dismiss_stale_reviews": true
    },
    "restrictions": null,
    "allow_force_pushes": false,
    "allow_deletions": false
  }'
```

### Artifact Export Webhook Integration

```javascript
// Claude Integration Script
class KnowledgeForgeExporter {
  constructor(webhookUrl, apiKey) {
    this.webhookUrl = webhookUrl;
    this.apiKey = apiKey;
  }
  
  async exportArtifact(artifact, metadata = {}) {
    const payload = {
      artifact: {
        content: artifact.content,
        type: this.detectArtifactType(artifact),
        filename: artifact.filename || this.generateFilename(artifact),
        language: artifact.language
      },
      metadata: {
        conversationId: metadata.conversationId || this.getCurrentConversationId(),
        timestamp: new Date().toISOString(),
        context: metadata.context || 'Direct artifact export',
        author: metadata.author || 'Claude Assistant',
        dependencies: metadata.dependencies || [],
        module: metadata.module,
        branch: metadata.branch || 'develop'
      }
    };
    
    try {
      const response = await fetch(`${this.webhookUrl}/kf32/artifact/capture`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-API-Key': this.apiKey
        },
        body: JSON.stringify(payload)
      });
      
      const result = await response.json();
      
      if (result.success) {
        console.log(`✅ Artifact exported: ${result.file}`);
      } else {
        console.error(`❌ Export failed: ${result.error}`);
      }
      
      return result;
    } catch (error) {
      console.error('Export error:', error);
      return { success: false, error: error.message };
    }
  }
  
  detectArtifactType(artifact) {
    // Detect based on content patterns
    if (artifact.content.includes('# ') && artifact.content.includes('## ')) return 'markdown';
    if (artifact.content.includes('function') || artifact.content.includes('const')) return 'code';
    if (artifact.content.includes('"nodes":') && artifact.content.includes('"connections":')) return 'workflow';
    if (artifact.content.includes('version:') || artifact.content.includes('export ')) return 'config';
    return 'text';
  }
  
  generateFilename(artifact) {
    const timestamp = Date.now();
    const type = this.detectArtifactType(artifact);
    const typeMap = {
      'markdown': 'md',
      'code': 'js',
      'workflow': 'json',
      'config': 'yaml',
      'text': 'txt'
    };
    return `artifact_${timestamp}.${typeMap[type] || 'txt'}`;
  }
  
  getCurrentConversationId() {
    // This would be injected by the Claude environment
    return `conv_${Date.now()}`;
  }
}

// Usage in Claude artifacts
const exporter = new KnowledgeForgeExporter(
  'https://n8n.example.com/webhook',
  'your-api-key'
);

// Export current artifact
await exporter.exportArtifact({
  content: documentContent,
  filename: '03_KB3_Agents_NewAgent.md',
  language: 'markdown'
}, {
  context: 'Creating new agent specification',
  module: '03_Agents',
  dependencies: ['00_KB3_Core.md', '03_Agents_Catalog.md']
});
```

## 🔧 Repository Management

### Setting Up Git Hooks

```shell
# .git/hooks/pre-commit
#!/bin/bash
# KnowledgeForge pre-commit hook

# Check for KnowledgeForge file format
for file in $(git diff --cached --name-only | grep -E '\.(md|json|yaml)$'); do
  # Check markdown files follow naming convention
  if [[ $file =~ \.md$ ]] && [[ $file =~ ^(documentation|agents|workflows|tests)/ ]]; then
    if ! [[ $(basename $file) =~ ^[0-9]{2}_[A-Za-z0-9_]+\.md$ ]]; then
      echo "Warning: $file doesn't follow KnowledgeForge naming convention"
    fi
  fi
  
  # Validate JSON files
  if [[ $file =~ \.json$ ]]; then
    if ! jq empty "$file" 2>/dev/null; then
      echo "Error: $file is not valid JSON"
      exit 1
    fi
  fi
done

# Update manifest
node .knowledgeforge/scripts/update-manifest.js

exit 0
```

### Automated Branch Management

```
# .github/workflows/branch-management.yml
name: KnowledgeForge Branch Management

on:
  schedule:
    - cron: '0 0 * * 0'  # Weekly on Sunday
  workflow_dispatch:

jobs:
  cleanup-branches:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Delete merged branches
        run: |
          git fetch --prune
          
          # Delete merged feature branches older than 30 days
          for branch in $(git branch -r --merged origin/develop | grep -E 'origin/feature/|origin/conversation/' | sed 's/origin\///'); do
            last_commit=$(git log -1 --format="%at" origin/$branch)
            current_time=$(date +%s)
            age_days=$(( ($current_time - $last_commit) / 86400 ))
            
            if [ $age_days -gt 30 ]; then
              echo "Deleting branch: $branch (age: $age_days days)"
              git push origin --delete $branch
            fi
          done
      
      - name: Archive old conversation branches
        run: |
          # Archive conversation branches to conversation-archive
          for branch in $(git branch -r | grep 'origin/conversation/' | sed 's/origin\///'); do
            git tag -a "archived/$branch" origin/$branch -m "Archived on $(date)"
            git push origin --tags
            git push origin --delete $branch
          done
```

## 🚦 Testing Git Integration

### Basic Integration Test

```javascript
// test-git-integration.js
const assert = require('assert');

async function testGitIntegration() {
  console.log('Testing KnowledgeForge Git Integration...\n');
  
  // Test 1: Artifact Capture
  console.log('1. Testing artifact capture...');
  const testArtifact = {
    artifact: {
      content: `# Test Agent\n\n## title: "Test Agent"\nmodule: "03_Agents"\n\nThis is a test agent.`,
      type: 'markdown',
      filename: '03_KB3_Agents_Test.md'
    },
    metadata: {
      conversationId: 'test-' + Date.now(),
      context: 'Integration test'
    }
  };
  
  const captureResponse = await fetch('http://localhost:5678/webhook/kf32/artifact/capture', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.KF32_API_KEY
    },
    body: JSON.stringify(testArtifact)
  });
  
  const captureResult = await captureResponse.json();
  assert(captureResult.success, 'Artifact capture failed');
  console.log('✅ Artifact capture successful\n');
  
  // Test 2: Repository Status
  console.log('2. Testing repository status...');
  const statusResponse = await fetch('http://localhost:5678/webhook/kf32/git/status', {
    headers: {
      'X-API-Key': process.env.KF32_API_KEY
    }
  });
  
  const statusResult = await statusResponse.json();
  assert(statusResult.connected, 'Repository not connected');
  console.log('✅ Repository status check successful\n');
  
  // Test 3: Documentation Sync
  console.log('3. Testing documentation sync...');
  const syncResponse = await fetch('http://localhost:5678/webhook/kf32/docs/update', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-API-Key': process.env.KF32_API_KEY
    },
    body: JSON.stringify({ scanType: 'quick' })
  });
  
  const syncResult = await syncResponse.json();
  assert(syncResult.success, 'Documentation sync failed');
  console.log('✅ Documentation sync successful\n');
  
  console.log('All tests passed! 🎉');
}

// Run tests
testGitIntegration().catch(console.error);
```

### Monitoring Dashboard

```javascript
// Create monitoring dashboard artifact
const monitoringDashboard = `
<!DOCTYPE html>
<html>
<head>
    <title>KnowledgeForge Git Integration Monitor</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .metric { 
            display: inline-block; 
            margin: 10px; 
            padding: 20px; 
            border: 1px solid #ddd; 
            border-radius: 5px; 
        }
        .metric h3 { margin: 0 0 10px 0; }
        .metric .value { font-size: 2em; font-weight: bold; }
        .success { color: #28a745; }
        .warning { color: #ffc107; }
        .error { color: #dc3545; }
        #activity { margin-top: 20px; }
        .activity-item { 
            padding: 10px; 
            border-bottom: 1px solid #eee; 
        }
    </style>
</head>
<body>
    <h1>KnowledgeForge Git Integration Monitor</h1>
    
    <div id="metrics">
        <div class="metric">
            <h3>Artifacts Captured</h3>
            <div class="value success" id="artifactCount">0</div>
            <small>Last 24 hours</small>
        </div>
        
        <div class="metric">
            <h3>Commit Success Rate</h3>
            <div class="value success" id="successRate">100%</div>
            <small>Last 100 commits</small>
        </div>
        
        <div class="metric">
            <h3>Repository Size</h3>
            <div class="value warning" id="repoSize">0 MB</div>
            <small>Total size</small>
        </div>
        
        <div class="metric">
            <h3>Active Branches</h3>
            <div class="value" id="branchCount">0</div>
            <small>Non-merged branches</small>
        </div>
    </div>
    
    <h2>Recent Activity</h2>
    <div id="activity"></div>
    
    <script>
    async function updateMetrics() {
        try {
            const response = await fetch('/webhook/kf32/git/metrics');
            const metrics = await response.json();
            
            document.getElementById('artifactCount').textContent = metrics.artifactsCaptured;
            document.getElementById('successRate').textContent = metrics.successRate + '%';
            document.getElementById('repoSize').textContent = (metrics.repositorySize / 1048576).toFixed(1) + ' MB';
            document.getElementById('branchCount').textContent = metrics.activeBranches;
            
            // Update activity feed
            const activityDiv = document.getElementById('activity');
            activityDiv.innerHTML = metrics.recentActivity.map(item => 
                '<div class="activity-item">' +
                '<strong>' + item.type + '</strong>: ' + item.description +
                '<br><small>' + new Date(item.timestamp).toLocaleString() + '</small>' +
                '</div>'
            ).join('');
            
        } catch (error) {
            console.error('Failed to update metrics:', error);
        }
    }
    
    // Update every 30 seconds
    setInterval(updateMetrics, 30000);
    updateMetrics();
    </script>
</body>
</html>
`;
```

## 🔒 Security Considerations

### Secure Token Management

```shell
# Use environment-specific token encryption
export GIT_ACCESS_TOKEN_ENCRYPTED=$(echo -n "$GIT_ACCESS_TOKEN" | openssl enc -aes-256-cbc -base64 -pass pass:$ENCRYPTION_KEY)

# Decrypt at runtime
export GIT_ACCESS_TOKEN=$(echo "$GIT_ACCESS_TOKEN_ENCRYPTED" | openssl enc -aes-256-cbc -base64 -d -pass pass:$ENCRYPTION_KEY)
```

### Repository Access Control

```
# .github/CODEOWNERS
# KnowledgeForge Code Owners

# Core Framework
/documentation/core/ @knowledgeforge/core-team
/agents/specifications/ @knowledgeforge/agent-team
/workflows/ @knowledgeforge/workflow-team

# Sensitive Files
/.knowledgeforge/incantation/ @knowledgeforge/admin
*.env @knowledgeforge/admin
**/credentials/ @knowledgeforge/admin

# Auto-generated files (no owner required)
/documentation/INDEX.md
/documentation/navigation.json
/.knowledgeforge/manifest.json
```

## 🚀 Production Deployment

### Docker Compose Configuration

```
# docker-compose.prod.yml
version: '3.8'

services:
  n8n:
    image: n8nio/n8n
    environment:
      - N8N_BASIC_AUTH_ACTIVE=true
      - N8N_BASIC_AUTH_USER=${N8N_USER}
      - N8N_BASIC_AUTH_PASSWORD=${N8N_PASSWORD}
      - N8N_WEBHOOK_URL=${N8N_WEBHOOK_URL}
    volumes:
      - n8n_data:/home/node/.n8n
    networks:
      - knowledgeforge
      
  redis:
    image: redis:7-alpine
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis_data:/data
    networks:
      - knowledgeforge
      
  git-sync:
    image: knowledgeforge/git-sync:3.2
    environment:
      - GIT_PROVIDER=${GIT_PROVIDER}
      - GIT_API_URL=${GIT_API_URL}
      - GIT_REPO_OWNER=${GIT_REPO_OWNER}
      - GIT_REPO_NAME=${GIT_REPO_NAME}
      - GIT_ACCESS_TOKEN=${GIT_ACCESS_TOKEN}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
    networks:
      - knowledgeforge

networks:
  knowledgeforge:
    driver: bridge

volumes:
  n8n_data:
  redis_data:
```

### Kubernetes Deployment

```
# k8s/git-integration-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: knowledgeforge-git-integration
  namespace: knowledgeforge
spec:
  replicas: 1
  selector:
    matchLabels:
      app: git-integration
  template:
    metadata:
      labels:
        app: git-integration
    spec:
      containers:
      - name: git-sync
        image: knowledgeforge/git-sync:3.2
        env:
        - name: GIT_PROVIDER
          valueFrom:
            configMapKeyRef:
              name: git-config
              key: provider
        - name: GIT_ACCESS_TOKEN
          valueFrom:
            secretKeyRef:
              name: git-credentials
              key: token
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
```

## 📊 Monitoring and Maintenance

### Health Check Endpoints

```javascript
// Health check implementation
app.get('/health/git-integration', async (req, res) => {
  const health = {
    status: 'healthy',
    timestamp: new Date().toISOString(),
    checks: {
      gitConnection: await checkGitConnection(),
      webhookStatus: await checkWebhookStatus(),
      queueStatus: await checkQueueStatus(),
      diskSpace: await checkDiskSpace()
    }
  };
  
  const allHealthy = Object.values(health.checks).every(check => check.status === 'healthy');
  health.status = allHealthy ? 'healthy' : 'unhealthy';
  
  res.status(allHealthy ? 200 : 503).json(health);
});
```

### Maintenance Scripts

```shell
#!/bin/bash
# maintenance/cleanup.sh

echo "KnowledgeForge Git Maintenance Script"
echo "====================================="

# Clean up old conversation branches
echo "1. Cleaning up old conversation branches..."
git for-each-ref --format='%(refname:short) %(committerdate:unix)' refs/remotes/origin/conversation/ | \
while read branch timestamp; do
  age_days=$(( ($(date +%s) - $timestamp) / 86400 ))
  if [ $age_days -gt 30 ]; then
    echo "  Deleting: $branch (${age_days} days old)"
    git push origin --delete ${branch#origin/}
  fi
done

# Optimize repository
echo "2. Running git garbage collection..."
git gc --aggressive --prune=now

# Update documentation index
echo "3. Updating documentation index..."
curl -X POST http://localhost:5678/webhook/kf32/docs/update \
  -H "X-API-Key: $KF32_API_KEY" \
  -d '{"scanType": "full"}'

# Generate report
echo "4. Generating maintenance report..."
echo "Maintenance completed at $(date)" > maintenance-report.txt
echo "Repository size: $(du -sh .git | cut -f1)" >> maintenance-report.txt
echo "Total branches: $(git branch -r | wc -l)" >> maintenance-report.txt
echo "Total commits: $(git rev-list --all --count)" >> maintenance-report.txt

echo "Maintenance complete!"
```

## 🎯 Best Practices

### Artifact Naming Conventions

1. **Documentation**: `XX_Category_Name.md`  
     
   - Example: `03_KB3_Agents_GitIntegration.md`

   

2. **Workflows**: `kf32_purpose_workflow.json`  
     
   - Example: `kf32_artifact_export_workflow.json`

   

3. **Configurations**: `service-type.yaml`  
     
   - Example: `git-integration-config.yaml`

   

4. **Test Files**: `test_component_scenario.ext`  
     
   - Example: `test_git_integration_basic.js`

### Commit Message Standards

```
[COMPONENT] Action: Brief description

- Detail 1
- Detail 2

Conversation-ID: xxx
References: #issue
```

Examples:

- `[AGENT] Add: Git Integration Agent specification`  
- `[WORKFLOW] Update: Artifact export error handling`  
- `[DOC] Fix: Cross-reference validation in navigation`

### Branch Strategy

- `main`: Production-ready code only  
- `develop`: Integration branch for features  
- `feature/*`: New features (merge to develop)  
- `hotfix/*`: Emergency fixes (merge to main)  
- `conversation/*`: Temporary per-conversation branches  
- `release/*`: Release preparation branches

## 🆘 Troubleshooting

### Common Issues

#### Issue: Artifacts not being captured

```shell
# Check webhook status
curl http://localhost:5678/webhook/kf32/artifact/capture/health

# Check logs
docker logs kf32_n8n_1 | grep "artifact"

# Verify environment variables
env | grep GIT_
```

#### Issue: Git authentication failures

```shell
# Test token
curl -H "Authorization: token $GIT_ACCESS_TOKEN" \
     $GIT_API_URL/user

# Check token permissions
# GitHub: Settings > Developer settings > Personal access tokens
# Ensure: repo, workflow permissions
```

#### Issue: Large file errors

```shell
# Install Git LFS
git lfs install

# Track large files
git lfs track "*.pdf"
git lfs track "*.zip"
git add .gitattributes
git commit -m "[CONFIG] Add Git LFS tracking"
```

### Debug Mode

```javascript
// Enable debug logging
process.env.DEBUG = 'knowledgeforge:*';

// Detailed git operation logging
const debugGitOp = async (operation, payload) => {
  console.log(`[GIT-DEBUG] Operation: ${operation}`);
  console.log(`[GIT-DEBUG] Payload:`, JSON.stringify(payload, null, 2));
  
  try {
    const result = await executeGitOperation(operation, payload);
    console.log(`[GIT-DEBUG] Success:`, result);
    return result;
  } catch (error) {
    console.error(`[GIT-DEBUG] Error:`, error);
    throw error;
  }
};
```

## Next Steps

1️⃣ **Complete repository setup** → Follow Step 1 to create repository structure 2️⃣ **Configure git provider** → Set up authentication and environment variables 3️⃣ **Deploy workflows** → Import and activate N8N workflows 4️⃣ **Test integration** → Run test suite to verify functionality 5️⃣ **Enable monitoring** → Set up dashboard and health checks 6️⃣ **Configure automation** → Set up branch management and maintenance 7️⃣ **Document team process** → Create team guidelines for using the system  
