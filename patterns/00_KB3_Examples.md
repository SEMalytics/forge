# 00\_KB3\_Examples

# KnowledgeForge 3.0: Implementation Examples

---

## title: "Implementation Examples"

module: "00\_Framework" topics: \["examples", "implementation", "use cases", "patterns", "solutions", "GET requests"\] contexts: \["development", "learning", "reference", "adaptation", "Claude Projects"\] difficulty: "intermediate" related\_sections: \["Core", "Templates", "Workflows", "Agents", "GET\_Implementation"\] workflow\_integration: \["all"\] agent\_access: \["all"\]

## Core Approach

This module provides concrete implementation examples for common KnowledgeForge 3.0 use cases. Each example includes complete code, configuration, and step-by-step instructions that can be adapted to your specific needs. All examples now support GET requests for Claude Projects compatibility while maintaining POST support for traditional integrations.

## Example 1: Customer Support System

### Overview

A complete customer support system that combines knowledge retrieval, ticket analysis, and automated response generation using N8N workflows and Claude agents. Fully compatible with GET requests for Claude artifact integration.

### System Architecture

```
Customer Query → Webhook (GET/POST) → Orchestrator → Decision Tree
                                              ↓
                              ┌─ Knowledge Search (Simple Query)
                              ├─ Agent Analysis (Complex Issue)
                              └─ Ticket Creation (New Issue)
```

### Implementation

#### 1\. Master Support Workflow (GET-Compatible)

```json
{
  "name": "Customer Support Master",
  "nodes": [
    {
      "parameters": {
        "path": "support/query",
        "responseMode": "responseNode",
        "options": {
          "responseHeaders": {
            "entries": [
              {
                "name": "Access-Control-Allow-Origin",
                "value": "*"
              },
              {
                "name": "Access-Control-Allow-Methods",
                "value": "GET, POST, OPTIONS"
              }
            ]
          }
        }
      },
      "name": "Support Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "functionCode": "// Handle both GET and POST requests\nconst method = $json.method || 'GET';\nlet query, customerId, context;\n\nif (method === 'GET') {\n  // Parse GET parameters\n  const params = $json.query || {};\n  query = params.query || '';\n  customerId = params.customerId || 'anonymous';\n  context = params.context ? JSON.parse(params.context) : {};\n} else {\n  // Handle POST body\n  query = $json.body.query;\n  customerId = $json.body.customerId;\n  context = $json.body.context || {};\n}\n\n// Classify query type\nconst classification = classifyQuery(query);\n\nfunction classifyQuery(text) {\n  const lower = text.toLowerCase();\n  \n  if (lower.includes('how do i') || lower.includes('how to')) {\n    return 'howto';\n  } else if (lower.includes('error') || lower.includes('problem')) {\n    return 'troubleshooting';\n  } else if (lower.includes('billing') || lower.includes('payment')) {\n    return 'billing';\n  } else if (lower.includes('cancel') || lower.includes('refund')) {\n    return 'account';\n  }\n  \n  return 'general';\n}\n\n// Determine complexity\nconst complexity = assessComplexity(query);\n\nfunction assessComplexity(text) {\n  const factors = {\n    length: text.length > 200 ? 1 : 0,\n    technical: /API|integration|error code/i.test(text) ? 1 : 0,\n    emotional: /angry|frustrated|urgent/i.test(text) ? 1 : 0,\n    multiple: text.split('?').length > 2 ? 1 : 0\n  };\n  \n  const score = Object.values(factors).reduce((a, b) => a + b, 0);\n  return score >= 2 ? 'complex' : 'simple';\n}\n\n// Log the query via GET for analytics\nconst analyticsParams = new URLSearchParams({\n  event: 'support_query',\n  type: classification,\n  complexity: complexity,\n  customerId: customerId,\n  timestamp: Date.now()\n});\n\n// Fire and forget analytics\n$http.request({\n  method: 'GET',\n  url: process.env.ANALYTICS_WEBHOOK + '?' + analyticsParams\n}).catch(() => {});\n\nreturn {\n  json: {\n    query: query,\n    customerId: customerId,\n    classification: classification,\n    complexity: complexity,\n    context: context,\n    method: method\n  }\n};"
      },
      "name": "Analyze Query",
      "type": "n8n-nodes-base.function",
      "position": [450, 300]
    }
  ]
}
```

#### 2\. Knowledge Search Workflow (GET-Enabled)

```javascript
// Claude Artifact: Knowledge Search Interface
class KnowledgeSupportSearch {
  constructor(webhookUrl) {
    this.webhookUrl = webhookUrl;
  }
  
  async searchKnowledge(query, filters = {}) {
    // Prepare search parameters
    const searchParams = new URLSearchParams({
      q: query,
      type: filters.type || 'all',
      limit: filters.limit || '5',
      relevance: filters.relevance || '0.7'
    });
    
    // Add optional filters
    if (filters.category) {
      searchParams.append('category', filters.category);
    }
    if (filters.dateRange) {
      searchParams.append('dateRange', filters.dateRange);
    }
    
    try {
      // Use GET request (Claude-compatible)
      const response = await fetch(`${this.webhookUrl}?${searchParams}`);
      const results = await response.json();
      
      return this.formatResults(results);
    } catch (error) {
      console.error('Search failed:', error);
      return this.fallbackResponse(query);
    }
  }
  
  formatResults(results) {
    if (!results.found || results.articles.length === 0) {
      return {
        found: false,
        message: "I couldn't find specific information about that. Let me connect you with a specialist.",
        escalate: true
      };
    }
    
    return {
      found: true,
      message: "I found some helpful information:",
      articles: results.articles.map(article => ({
        title: article.title,
        summary: article.summary,
        link: article.link,
        relevance: article.relevance
      })),
      additionalHelp: "Was this helpful? Reply 'yes' or 'no'"
    };
  }
  
  fallbackResponse(query) {
    return {
      found: false,
      message: "I'm having trouble searching right now, but I'd be happy to help directly. Can you tell me more about your issue?",
      fallback: true
    };
  }
}

// Usage in Claude artifact
const search = new KnowledgeSupportSearch('https://n8n.example.com/webhook/support/search');

// HTML Interface for Claude
document.getElementById('searchForm').addEventListener('submit', async (e) => {
  e.preventDefault();
  
  const query = document.getElementById('query').value;
  const category = document.getElementById('category').value;
  
  const results = await search.searchKnowledge(query, { category });
  
  // Display results
  const resultsDiv = document.getElementById('results');
  if (results.found) {
    resultsDiv.innerHTML = `
      <h3>${results.message}</h3>
      ${results.articles.map(article => `
        <div class="article">
          <h4>${article.title}</h4>
          <p>${article.summary}</p>
          <a href="${article.link}" target="_blank">Read more</a>
        </div>
      `).join('')}
      <p>${results.additionalHelp}</p>
    `;
  } else {
    resultsDiv.innerHTML = `<p>${results.message}</p>`;
  }
});
```

#### 3\. Claude Support Agent Configuration (GET-Compatible)

````
# Customer Support Specialist Agent

You are a KnowledgeForge 3.0 Customer Support Specialist with expertise in handling complex customer inquiries via GET request integration.

## Your Capabilities
1. Analyze customer issues comprehensively
2. Provide empathetic and solution-focused responses
3. Access information via GET requests to N8N workflows
4. Escalate appropriately when needed
5. Generate GET-compatible artifacts for customer self-service

## GET Request Integration

When you need to access external data or trigger workflows, use GET requests:

```javascript
// Fetch customer history
const historyUrl = `https://n8n.example.com/webhook/customer/history?customerId=${customerId}`;
const history = await fetch(historyUrl).then(r => r.json());

// Search knowledge base
const searchUrl = `https://n8n.example.com/webhook/kb/search?q=${encodeURIComponent(query)}`;
const results = await fetch(searchUrl).then(r => r.json());

// Create ticket (using GET with action parameter)
const ticketUrl = `https://n8n.example.com/webhook/ticket/create?action=new&customerId=${customerId}&issue=${encodeURIComponent(issue)}`;
const ticket = await fetch(ticketUrl).then(r => r.json());
````

## Response Framework

When handling a customer query:

1. **Acknowledge** \- Show you understand their concern  
2. **Analyze** \- Identify the core issue(s)  
3. **Solution** \- Provide clear, actionable steps  
4. **Follow-up** \- Ensure satisfaction and offer next steps

## Artifact Generation

Create interactive artifacts that work with GET requests:

```html
<!DOCTYPE html>
<html>
<head>
    <title>Support Assistant</title>
    <script src="https://cdn.jsdelivr.net/npm/lz-string@1.5.0/libs/lz-string.min.js"></script>
</head>
<body>
    <div id="supportChat">
        <h2>How can I help you today?</h2>
        <textarea id="issue" placeholder="Describe your issue..."></textarea>
        <button onclick="submitIssue()">Get Help</button>
        <div id="response"></div>
    </div>
    
    <script>
    async function submitIssue() {
        const issue = document.getElementById('issue').value;
        const webhookUrl = 'https://n8n.example.com/webhook/support/analyze';
        
        // Prepare GET request
        const params = new URLSearchParams({
            query: issue,
            timestamp: Date.now()
        });
        
        // Compress if needed
        if (issue.length > 200) {
            params.set('compressed', 'true');
            params.set('query', LZString.compressToEncodedURIComponent(issue));
        }
        
        try {
            const response = await fetch(`${webhookUrl}?${params}`);
            const result = await response.json();
            
            document.getElementById('response').innerHTML = `
                <h3>Solution:</h3>
                <p>${result.solution}</p>
                ${result.articles ? `
                    <h4>Helpful Articles:</h4>
                    <ul>${result.articles.map(a => 
                        `<li><a href="${a.link}">${a.title}</a></li>`
                    ).join('')}</ul>
                ` : ''}
            `;
        } catch (error) {
            document.getElementById('response').innerHTML = 
                '<p>Sorry, I encountered an error. Please try again.</p>';
        }
    }
    </script>
</body>
</html>
```

````

### Usage Example (GET Requests)

```bash
# Customer query via GET
curl "https://your-n8n.com/webhook/support/query?customerId=cust_123&query=I%27m%20having%20trouble%20connecting%20my%20API.%20I%20keep%20getting%20a%20401%20error%20even%20though%20my%20API%20key%20is%20correct.&context=%7B%22previousTickets%22%3A2%2C%22accountType%22%3A%22premium%22%7D"

# Or using a browser/fetch
const supportUrl = new URL('https://your-n8n.com/webhook/support/query');
supportUrl.searchParams.append('customerId', 'cust_123');
supportUrl.searchParams.append('query', "I'm having trouble connecting my API. I keep getting a 401 error even though my API key is correct.");
supportUrl.searchParams.append('context', JSON.stringify({
  previousTickets: 2,
  accountType: 'premium'
}));

const response = await fetch(supportUrl);
const result = await response.json();

// Response
{
  "status": "success",
  "response": {
    "message": "I understand you're experiencing authentication issues with your API connection. A 401 error typically indicates an authentication problem. Let me help you resolve this:\n\n1. **Verify API Key Format**: Ensure your API key includes the 'Bearer' prefix if required\n2. **Check Key Permissions**: Confirm your API key has the necessary permissions for the endpoint\n3. **Validate Encoding**: Make sure the key isn't being modified during transmission\n\nHere's a quick test you can run:\n```curl -H \"Authorization: Bearer YOUR_API_KEY\" https://api.example.com/test```\n\nIf this doesn't resolve the issue, I can help you debug further.",
    "articles": [
      {
        "title": "API Authentication Guide",
        "link": "https://support.example.com/kb/api-auth"
      }
    ],
    "resolved": false,
    "nextSteps": [
      "Try the curl test command",
      "Check API key permissions",
      "Reply with results"
    ]
  }
}
````

## Example 2: Code Review Assistant

### Overview

An intelligent code review system that analyzes pull requests, identifies issues, and suggests improvements using multiple specialized agents. Now with GET request support for browser-based integrations.

### Implementation

#### 1\. Code Review Orchestrator (GET-Compatible)

```json
{
  "name": "Code Review Orchestrator",
  "nodes": [
    {
      "parameters": {
        "path": "code-review/analyze",
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
      "name": "Review Webhook",
      "type": "n8n-nodes-base.webhook",
      "position": [250, 300]
    },
    {
      "parameters": {
        "functionCode": "// Handle GET and POST requests\nconst method = $json.method || 'GET';\nlet pr;\n\nif (method === 'GET') {\n  // Parse GET parameters\n  const params = $json.query || {};\n  \n  // For GET, expect PR data as compressed parameter\n  if (params.compressed === 'true') {\n    pr = JSON.parse(LZString.decompressFromEncodedURIComponent(params.pr));\n  } else {\n    pr = {\n      repo: params.repo,\n      prNumber: params.prNumber,\n      files: params.files ? JSON.parse(params.files) : [],\n      diff: params.diff || ''\n    };\n  }\n} else {\n  pr = $json.body;\n}\n\n// Analyze code characteristics\nconst analysis = {\n  language: detectLanguage(pr.files || []),\n  complexity: assessComplexity(pr.diff || ''),\n  changeSize: (pr.additions || 0) + (pr.deletions || 0),\n  riskLevel: assessRisk(pr),\n  requiredChecks: determineChecks(pr)\n};\n\n// Log analysis via GET\nconst logParams = new URLSearchParams({\n  event: 'code_review_started',\n  repo: pr.repo || 'unknown',\n  language: analysis.language,\n  complexity: analysis.complexity,\n  timestamp: Date.now()\n});\n\n$http.request({\n  method: 'GET',\n  url: process.env.ANALYTICS_WEBHOOK + '?' + logParams\n}).catch(() => {});\n\nfunction detectLanguage(files) {\n  if (!files || files.length === 0) return 'unknown';\n  \n  const extensions = files.map(f => {\n    if (typeof f === 'string') {\n      return f.split('.').pop();\n    }\n    return f.filename ? f.filename.split('.').pop() : '';\n  });\n  \n  const langMap = {\n    'js': 'javascript',\n    'ts': 'typescript',\n    'py': 'python',\n    'java': 'java',\n    'rb': 'ruby',\n    'go': 'go'\n  };\n  \n  const mostCommon = extensions\n    .filter(ext => langMap[ext])\n    .reduce((acc, ext) => {\n      acc[ext] = (acc[ext] || 0) + 1;\n      return acc;\n    }, {});\n  \n  const sorted = Object.entries(mostCommon)\n    .sort((a, b) => b[1] - a[1]);\n  \n  return sorted.length > 0 ? langMap[sorted[0][0]] : 'mixed';\n}\n\nfunction assessComplexity(diff) {\n  if (!diff) return 'low';\n  \n  const lines = diff.split('\\n').length;\n  const functions = (diff.match(/function|def|class/g) || []).length;\n  const conditions = (diff.match(/if|else|switch|case/g) || []).length;\n  \n  const score = (lines / 100) + (functions * 2) + (conditions * 1.5);\n  \n  if (score > 20) return 'high';\n  if (score > 10) return 'medium';\n  return 'low';\n}\n\nfunction assessRisk(pr) {\n  const risks = [];\n  \n  if (pr.changeSize > 500) risks.push('large_change');\n  if (pr.files && pr.files.some(f => f.includes('config'))) risks.push('config_change');\n  if (pr.files && pr.files.some(f => f.includes('security'))) risks.push('security_related');\n  if (pr.diff && pr.diff.includes('DELETE')) risks.push('deletion');\n  \n  if (risks.length >= 3) return 'high';\n  if (risks.length >= 1) return 'medium';\n  return 'low';\n}\n\nfunction determineChecks(pr) {\n  const checks = ['syntax', 'style'];\n  \n  if (assessRisk(pr) !== 'low') {\n    checks.push('security', 'performance');\n  }\n  \n  if (pr.files && pr.files.some(f => f.includes('test'))) {\n    checks.push('test_coverage');\n  }\n  \n  return checks;\n}\n\nreturn { json: analysis };"
      },
      "name": "Analyze PR",
      "type": "n8n-nodes-base.function",
      "position": [450, 300]
    }
  ]
}
```

#### 2\. Browser-Based Code Review Interface

```html
<!DOCTYPE html>
<html>
<head>
    <title>Code Review Assistant</title>
    <script src="https://cdn.jsdelivr.net/npm/lz-string@1.5.0/libs/lz-string.min.js"></script>
    <style>
        .container { max-width: 800px; margin: 0 auto; padding: 20px; }
        .file-input { margin: 10px 0; }
        .results { margin-top: 20px; padding: 15px; background: #f5f5f5; }
        .issue { margin: 10px 0; padding: 10px; background: white; border-left: 3px solid #ff6b6b; }
        .suggestion { margin: 10px 0; padding: 10px; background: white; border-left: 3px solid #51cf66; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Code Review Assistant</h1>
        
        <div class="file-input">
            <label>Repository: <input type="text" id="repo" placeholder="owner/repo"></label>
        </div>
        
        <div class="file-input">
            <label>PR Number: <input type="number" id="prNumber" placeholder="123"></label>
        </div>
        
        <div class="file-input">
            <label>Code Diff: <textarea id="diff" rows="10" cols="80" placeholder="Paste your diff here..."></textarea></label>
        </div>
        
        <button onclick="analyzeCode()">Analyze Code</button>
        
        <div id="results" class="results" style="display: none;"></div>
    </div>
    
    <script>
    async function analyzeCode() {
        const repo = document.getElementById('repo').value;
        const prNumber = document.getElementById('prNumber').value;
        const diff = document.getElementById('diff').value;
        
        if (!repo || !diff) {
            alert('Please provide repository and diff');
            return;
        }
        
        // Prepare PR data
        const prData = {
            repo: repo,
            prNumber: prNumber,
            diff: diff,
            files: extractFilesFromDiff(diff),
            additions: countAdditions(diff),
            deletions: countDeletions(diff)
        };
        
        // Compress for GET request
        const compressed = LZString.compressToEncodedURIComponent(JSON.stringify(prData));
        
        // Check size and use appropriate method
        const webhookUrl = 'https://n8n.example.com/webhook/code-review/analyze';
        let url;
        
        if (compressed.length < 1500) {
            // Use GET with compressed data
            url = `${webhookUrl}?compressed=true&pr=${compressed}`;
        } else {
            // For very large diffs, use session-based approach
            url = await initLargeReviewSession(prData);
        }
        
        try {
            const response = await fetch(url);
            const analysis = await response.json();
            
            displayResults(analysis);
        } catch (error) {
            console.error('Analysis failed:', error);
            alert('Failed to analyze code. Please try again.');
        }
    }
    
    function extractFilesFromDiff(diff) {
        const filePattern = /\+\+\+ b\/(.+)/g;
        const files = [];
        let match;
        
        while ((match = filePattern.exec(diff)) !== null) {
            files.push(match[1]);
        }
        
        return files;
    }
    
    function countAdditions(diff) {
        return (diff.match(/^\+[^+]/gm) || []).length;
    }
    
    function countDeletions(diff) {
        return (diff.match(/^-[^-]/gm) || []).length;
    }
    
    async function initLargeReviewSession(prData) {
        // For very large PRs, use session-based transfer
        const initUrl = 'https://n8n.example.com/webhook/code-review/init-session';
        const sessionResponse = await fetch(initUrl);
        const session = await sessionResponse.json();
        
        // Send chunks
        const chunks = chunkData(JSON.stringify(prData), 1000);
        for (let i = 0; i < chunks.length; i++) {
            const chunkUrl = `https://n8n.example.com/webhook/code-review/add-chunk?sessionId=${session.id}&index=${i}&chunk=${encodeURIComponent(chunks[i])}`;
            await fetch(chunkUrl);
        }
        
        // Finalize and analyze
        return `https://n8n.example.com/webhook/code-review/analyze-session?sessionId=${session.id}`;
    }
    
    function chunkData(data, size) {
        const chunks = [];
        for (let i = 0; i < data.length; i += size) {
            chunks.push(data.substr(i, size));
        }
        return chunks;
    }
    
    function displayResults(analysis) {
        const resultsDiv = document.getElementById('results');
        resultsDiv.style.display = 'block';
        
        resultsDiv.innerHTML = `
            <h2>Code Review Results</h2>
            <p><strong>Language:</strong> ${analysis.language}</p>
            <p><strong>Complexity:</strong> ${analysis.complexity}</p>
            <p><strong>Risk Level:</strong> ${analysis.riskLevel}</p>
            <p><strong>Change Size:</strong> ${analysis.changeSize} lines</p>
            
            <h3>Required Checks:</h3>
            <ul>
                ${analysis.requiredChecks.map(check => `<li>${check}</li>`).join('')}
            </ul>
            
            ${analysis.issues ? `
                <h3>Issues Found:</h3>
                ${analysis.issues.map(issue => `
                    <div class="issue">
                        <strong>${issue.type}:</strong> ${issue.message}
                        <br><small>Line ${issue.line || 'N/A'}</small>
                    </div>
                `).join('')}
            ` : ''}
            
            ${analysis.suggestions ? `
                <h3>Suggestions:</h3>
                ${analysis.suggestions.map(suggestion => `
                    <div class="suggestion">
                        ${suggestion}
                    </div>
                `).join('')}
            ` : ''}
        `;
    }
    </script>
</body>
</html>
```

#### 3\. Multi-Agent Code Review (GET-Based)

```javascript
// Code Review Agent Coordinator with GET support
class CodeReviewCoordinator {
  constructor(webhookBaseUrl) {
    this.webhookBaseUrl = webhookBaseUrl;
    this.agents = {
      syntax: '/agent/syntax-checker',
      security: '/agent/security-analyzer',
      performance: '/agent/performance-reviewer',
      style: '/agent/style-checker'
    };
  }
  
  async performComprehensiveReview(prData) {
    const reviews = [];
    
    // Run checks in parallel using GET requests
    const checkPromises = Object.entries(this.agents).map(async ([type, endpoint]) => {
      try {
        // Prepare data for GET
        const params = new URLSearchParams({
          repo: prData.repo,
          language: prData.language || 'unknown',
          checkType: type
        });
        
        // Add compressed diff if not too large
        if (prData.diff && prData.diff.length < 5000) {
          params.append('diff', LZString.compressToEncodedURIComponent(prData.diff));
          params.append('compressed', 'true');
        } else if (prData.sessionId) {
          params.append('sessionId', prData.sessionId);
        }
        
        const response = await fetch(`${this.webhookBaseUrl}${endpoint}?${params}`);
        const result = await response.json();
        
        return {
          type: type,
          status: 'completed',
          findings: result
        };
      } catch (error) {
        return {
          type: type,
          status: 'failed',
          error: error.message
        };
      }
    });
    
    const results = await Promise.all(checkPromises);
    
    // Aggregate results
    return this.aggregateReviews(results);
  }
  
  aggregateReviews(reviews) {
    const aggregated = {
      overallStatus: 'pass',
      totalIssues: 0,
      criticalIssues: 0,
      suggestions: [],
      detailedFindings: {}
    };
    
    reviews.forEach(review => {
      if (review.status === 'completed') {
        aggregated.detailedFindings[review.type] = review.findings;
        
        if (review.findings.issues) {
          aggregated.totalIssues += review.findings.issues.length;
          aggregated.criticalIssues += review.findings.issues.filter(i => i.severity === 'critical').length;
        }
        
        if (review.findings.suggestions) {
          aggregated.suggestions.push(...review.findings.suggestions);
        }
      }
    });
    
    if (aggregated.criticalIssues > 0) {
      aggregated.overallStatus = 'fail';
    } else if (aggregated.totalIssues > 5) {
      aggregated.overallStatus = 'warning';
    }
    
    return aggregated;
  }
}

// Usage in Claude artifact
const reviewer = new CodeReviewCoordinator('https://n8n.example.com/webhook/code-review');

async function reviewPullRequest(prUrl) {
  // Extract PR info from URL
  const prInfo = parsePRUrl(prUrl);
  
  // Fetch PR data (mock for demo)
  const prData = {
    repo: prInfo.repo,
    prNumber: prInfo.number,
    diff: await fetchPRDiff(prInfo), // This would fetch actual diff
    language: 'javascript'
  };
  
  // Perform review
  const review = await reviewer.performComprehensiveReview(prData);
  
  // Display results
  displayReviewResults(review);
}
```

## Example 3: Learning Path Generator

### Overview

An intelligent system that creates personalized learning paths based on user skills, goals, and available resources. Uses GET requests for all integrations.

### Implementation

```javascript
// Learning Path Generator with GET API
class LearningPathGenerator {
  constructor(apiBaseUrl) {
    this.apiBaseUrl = apiBaseUrl;
  }
  
  async generatePath(userProfile, goal) {
    // Assess current skills via GET
    const skillsParams = new URLSearchParams({
      userId: userProfile.id,
      domain: goal.domain
    });
    
    const currentSkills = await fetch(
      `${this.apiBaseUrl}/skills/assess?${skillsParams}`
    ).then(r => r.json());
    
    // Get learning resources via GET
    const resourceParams = new URLSearchParams({
      domain: goal.domain,
      level: currentSkills.level,
      targetLevel: goal.targetLevel,
      format: userProfile.preferredFormat || 'mixed'
    });
    
    const resources = await fetch(
      `${this.apiBaseUrl}/resources/search?${resourceParams}`
    ).then(r => r.json());
    
    // Generate personalized path
    const pathData = {
      user: userProfile,
      currentSkills: currentSkills,
      targetGoal: goal,
      resources: resources
    };
    
    // Use compressed GET for path generation
    const compressed = LZString.compressToEncodedURIComponent(JSON.stringify(pathData));
    const pathParams = new URLSearchParams({
      compressed: 'true',
      data: compressed
    });
    
    const path = await fetch(
      `${this.apiBaseUrl}/path/generate?${pathParams}`
    ).then(r => r.json());
    
    return this.formatLearningPath(path);
  }
  
  formatLearningPath(path) {
    return {
      title: path.title,
      duration: path.estimatedDuration,
      milestones: path.milestones.map(m => ({
        name: m.name,
        skills: m.skills,
        resources: m.resources,
        assessment: m.assessment,
        estimatedTime: m.estimatedTime
      })),
      totalResources: path.resources.length,
      difficulty: path.difficulty,
      prerequisites: path.prerequisites
    };
  }
}

// Interactive Learning Path UI
const learningUI = `
<!DOCTYPE html>
<html>
<head>
    <title>Learning Path Generator</title>
    <script src="https://cdn.jsdelivr.net/npm/lz-string@1.5.0/libs/lz-string.min.js"></script>
    <style>
        .milestone { 
            margin: 20px 0; 
            padding: 15px; 
            border: 1px solid #ddd; 
            border-radius: 8px; 
        }
        .resource { 
            margin: 5px 0; 
            padding: 5px 10px; 
            background: #f0f0f0; 
            border-radius: 4px; 
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>Personalized Learning Path Generator</h1>
        
        <form id="pathForm">
            <div>
                <label>Your Name: <input type="text" id="userName" required></label>
            </div>
            <div>
                <label>Current Level: 
                    <select id="currentLevel">
                        <option value="beginner">Beginner</option>
                        <option value="intermediate">Intermediate</option>
                        <option value="advanced">Advanced</option>
                    </select>
                </label>
            </div>
            <div>
                <label>Learning Goal: <input type="text" id="goal" placeholder="e.g., Master React Development" required></label>
            </div>
            <div>
                <label>Preferred Format: 
                    <select id="format">
                        <option value="mixed">Mixed</option>
                        <option value="video">Video</option>
                        <option value="text">Text</option>
                        <option value="interactive">Interactive</option>
                    </select>
                </label>
            </div>
            <button type="submit">Generate Learning Path</button>
        </form>
        
        <div id="learningPath" style="display: none;"></div>
    </div>
    
    <script>
    const generator = new LearningPathGenerator('https://n8n.example.com/webhook/learning');
    
    document.getElementById('pathForm').addEventListener('submit', async (e) => {
        e.preventDefault();
        
        const userProfile = {
            id: 'user_' + Date.now(),
            name: document.getElementById('userName').value,
            currentLevel: document.getElementById('currentLevel').value,
            preferredFormat: document.getElementById('format').value
        };
        
        const goal = {
            domain: extractDomain(document.getElementById('goal').value),
            targetLevel: 'expert',
            description: document.getElementById('goal').value
        };
        
        try {
            const path = await generator.generatePath(userProfile, goal);
            displayPath(path);
        } catch (error) {
            alert('Failed to generate learning path. Please try again.');
        }
    });
    
    function extractDomain(goal) {
        // Simple domain extraction
        const domains = ['react', 'python', 'machine learning', 'data science', 'web development'];
        const lower = goal.toLowerCase();
        
        for (const domain of domains) {
            if (lower.includes(domain)) {
                return domain;
            }
        }
        
        return 'general';
    }
    
    function displayPath(path) {
        const pathDiv = document.getElementById('learningPath');
        pathDiv.style.display = 'block';
        
        pathDiv.innerHTML = \`
            <h2>\${path.title}</h2>
            <p><strong>Duration:</strong> \${path.duration}</p>
            <p><strong>Difficulty:</strong> \${path.difficulty}</p>
            
            <h3>Learning Milestones:</h3>
            \${path.milestones.map((milestone, index) => \`
                <div class="milestone">
                    <h4>Milestone \${index + 1}: \${milestone.name}</h4>
                    <p><strong>Time:</strong> \${milestone.estimatedTime}</p>
                    <p><strong>Skills:</strong> \${milestone.skills.join(', ')}</p>
                    
                    <h5>Resources:</h5>
                    \${milestone.resources.map(resource => \`
                        <div class="resource">
                            <a href="\${resource.url}" target="_blank">\${resource.title}</a>
                            <span>(\${resource.type})</span>
                        </div>
                    \`).join('')}
                    
                    <p><strong>Assessment:</strong> \${milestone.assessment.type}</p>
                </div>
            \`).join('')}
        \`;
    }
    </script>
</body>
</html>
`;
```

## Best Practices for GET-Based Examples

### 1\. Data Size Management

Always check data size before sending via GET:

```javascript
function prepareGetRequest(url, data) {
  const jsonData = JSON.stringify(data);
  
  if (jsonData.length < 500) {
    // Small data - send as is
    return `${url}?data=${encodeURIComponent(jsonData)}`;
  } else if (jsonData.length < 2000) {
    // Medium data - compress
    const compressed = LZString.compressToEncodedURIComponent(jsonData);
    return `${url}?compressed=true&data=${compressed}`;
  } else {
    // Large data - use session-based transfer
    return initializeSession(url, data);
  }
}
```

### 2\. Error Handling

Implement proper error handling for GET requests:

```javascript
async function safeGetRequest(url, params) {
  try {
    const urlWithParams = new URL(url);
    Object.entries(params).forEach(([key, value]) => {
      urlWithParams.searchParams.append(key, value);
    });
    
    const response = await fetch(urlWithParams);
    
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('GET request failed:', error);
    
    // Fallback handling
    if (error.message.includes('414')) {
      // URI too long - retry with compression
      return retryWithCompression(url, params);
    }
    
    throw error;
  }
}
```

### 3\. Analytics and Monitoring

Track GET request performance:

```javascript
function trackGetRequest(endpoint, dataSize, compressed) {
  const metrics = {
    endpoint: endpoint,
    method: 'GET',
    dataSize: dataSize,
    compressed: compressed,
    timestamp: Date.now()
  };
  
  // Send metrics asynchronously
  navigator.sendBeacon(
    'https://analytics.example.com/track',
    JSON.stringify(metrics)
  );
}
```

## Implementation Notes

- All examples now support GET requests for Claude Projects compatibility  
- Use compression for data over 500 bytes  
- Implement session-based transfers for very large data  
- Monitor URL length to stay under 2000 characters  
- Test GET endpoints with various data sizes  
- Cache GET responses when appropriate  
- Provide fallback mechanisms for GET failures  
- Document GET-specific limitations for users  
- Use browser developer tools to debug GET requests  
- Consider security implications of data in URLs

## Next Steps and Recommendations

After implementing these GET-based examples:

1. **Test with real Claude artifacts** \- Verify GET requests work from Claude  
2. **Monitor URL lengths** \- Track typical request sizes  
3. **Optimize compression** \- Find the best compression settings  
4. **Implement caching** \- Cache frequent GET responses  
5. **Create more examples** \- Build domain-specific implementations

## Next Steps

1️⃣ **Deploy the customer support system** with GET webhook endpoints  
2️⃣ **Test code review from Claude artifacts** using compressed GET  
3️⃣ **Create learning paths** with GET-based resource fetching  
4️⃣ **Build your own GET-compatible example** for your use case  
5️⃣ **Share successful GET implementations** with the community

