# 00\_KB3\_Navigation

## title: "KnowledgeForge 3.2 Navigation Guide"

module: "00\_Framework" topics: \["navigation", "user guidance", "decision trees", "learning paths", "system exploration", "quick reference"\] contexts: \["getting started", "finding information", "system overview", "feature discovery", "workflow selection"\] difficulty: "beginner" related\_sections: \["00\_KB3\_Core", "00\_KB3\_ImplementationGuide", "03\_Agents\_Catalog", "02\_N8N\_WorkflowRegistry"\]

## Core Approach

This navigation guide helps you find the right resources in KnowledgeForge 3.2 based on your goals. Whether you're setting up the system, building agents, managing repositories, or exploring capabilities, follow the decision trees and quick links to reach your destination efficiently.

## 🗺️ System Map

```
KnowledgeForge 3.2
├── 🏗️ Core Framework
│   ├── System Architecture → 00_KB3_Core.md
│   ├── Implementation Guide → 00_KB3_ImplementationGuide.md
│   ├── Navigation (You are here) → 00_KB3_Navigation.md
│   └── Templates → 00_KB3_Templates.md
│
├── 🤖 Agent Ecosystem
│   ├── Agent Catalog → 03_Agents_Catalog.md
│   ├── Navigator Agent → 03_KB3_Agents_Navigator.md
│   ├── Agent-Building Agent → 03_KB3_Agents_AgentBuilder.md
│   ├── Git Integration Agent → 03_KB3_Agents_GitIntegration.md ⭐ NEW
│   ├── Version Control Manager → 03_KB3_Agents_VersionControl.md ⭐ NEW
│   └── Incantation Preserver → 03_KB3_Agents_IncantationPreserver.md ⭐ NEW
│
├── 🔄 Workflow Management
│   ├── Workflow Registry → 02_N8N_WorkflowRegistry.md
│   ├── Artifact Export → kf32_artifact_export_workflow.json ⭐ NEW
│   ├── Continuous Docs → kf32_continuous_docs_workflow.json ⭐ NEW
│   ├── Agent Git Integration → kf32_agent_building_git_integration.json ⭐ NEW
│   └── Monitoring Dashboard → kf32_monitoring_dashboard_workflow.json ⭐ NEW
│
├── 💾 Data Transfer System
│   └── Core Implementation → 01_Core_DataTransfer.md
│
├── 🧪 Testing & Validation
│   ├── Test Scenarios → 04_TestScenarios.md
│   └── Git Integration Tests → 04_TestScenarios_GitIntegration.md ⭐ NEW
│
└── 🔧 Tools & Utilities
    ├── Browser Exporter → claude_artifact_exporter.html ⭐ NEW
    └── Setup Scripts → setup_kf32.sh ⭐ NEW
```

## 🎯 Quick Start Paths

### "I want to..."

#### 🚀 Set up KnowledgeForge 3.2 from scratch

1. **Start here** → `00_KB3_ImplementationGuide.md`  
2. **Run setup script** → `setup_kf32.sh`  
3. **Configure Git** → `00_KB3_ImplementationGuide_3.2_GitIntegration.md`  
4. **Test system** → `04_TestScenarios.md`

#### 📤 Export artifacts automatically (eliminate copy/paste)

1. **Understand Git Integration** → `03_KB3_Agents_GitIntegration.md`  
2. **Deploy workflow** → `kf32_artifact_export_workflow.json`  
3. **Use browser tool** → Open `claude_artifact_exporter.html`  
4. **Configure repository** → `03_KB3_Agents_VersionControl.md`

#### 🤖 Build a new agent

1. **Use Agent Builder** → `03_KB3_Agents_AgentBuilder.md`  
2. **Check agent patterns** → `03_Agents_Catalog.md`  
3. **Auto-capture with Git** → Files automatically saved via integration  
4. **Test your agent** → `04_TestScenarios.md`

#### 📚 Understand the system architecture

1. **Core concepts** → `00_KB3_Core.md`  
2. **Integration patterns** → `00_KB3_Core.md#integration-patterns`  
3. **Layer architecture** → `00_KB3_Core.md#system-architecture`  
4. **Implementation details** → `00_KB3_ImplementationGuide.md`

#### 🔄 Create or modify workflows

1. **Browse existing** → `02_N8N_WorkflowRegistry.md`  
2. **Understand patterns** → `00_KB3_Templates.md`  
3. **Deploy workflow** → Import JSON to N8N  
4. **Test workflow** → `04_TestScenarios.md`

#### 💾 Transfer large datasets

1. **Data transfer guide** → `01_Core_DataTransfer.md`  
2. **Configure compression** → `01_Core_DataTransfer.md#compression`  
3. **Test with scenarios** → `04_TestScenarios.md#data-transfer`  
4. **Monitor performance** → Access monitoring dashboard

## 🌳 Decision Trees

### Setup Decision Tree

```
START: What's your deployment goal?
│
├── 🏃 Quick Development Setup
│   ├── Have Docker? → Run docker-compose up
│   ├── Need Git integration? → Run setup_kf32.sh
│   └── Ready to test → 04_TestScenarios.md
│
├── 🏭 Production Deployment
│   ├── Review requirements → 00_KB3_ImplementationGuide.md#requirements
│   ├── Configure SSL → 00_KB3_ImplementationGuide.md#ssl-configuration
│   ├── Set up monitoring → kf32_monitoring_dashboard_workflow.json
│   └── Enable backups → 00_KB3_ImplementationGuide.md#backup-strategy
│
└── 🧪 Testing Existing System
    ├── Run health check → 00_KB3_ImplementationGuide.md#health-check
    ├── Test integrations → 04_TestScenarios_GitIntegration.md
    └── Validate workflows → 02_N8N_WorkflowRegistry.md
```

### Agent Selection Tree

```
START: What kind of agent do you need?
│
├── 🧭 Help me navigate KnowledgeForge
│   └── Navigator Agent → 03_KB3_Agents_Navigator.md
│
├── 🏗️ Build a new agent
│   └── Agent-Building Agent → 03_KB3_Agents_AgentBuilder.md
│
├── 📤 Capture and version artifacts
│   └── Git Integration Agent → 03_KB3_Agents_GitIntegration.md
│
├── 🔀 Manage branches and releases
│   └── Version Control Manager → 03_KB3_Agents_VersionControl.md
│
└── 🔮 Protect system prompts
    └── Incantation Preserver → 03_KB3_Agents_IncantationPreserver.md
```

### Problem Resolution Tree

```
START: What issue are you facing?
│
├── 📤 Artifacts not capturing
│   ├── Check webhook → Test with curl command
│   ├── Verify API key → Check environment variables
│   ├── Review workflow → kf32_artifact_export_workflow.json
│   └── Check logs → docker logs kf32_n8n
│
├── 🔀 Git operations failing
│   ├── Test token → 00_KB3_ImplementationGuide_3.2_GitIntegration.md#troubleshooting
│   ├── Check permissions → Verify repo access
│   ├── Review branch protection → 03_KB3_Agents_VersionControl.md
│   └── Examine commit history → git log --oneline
│
├── 💾 Large data transfer issues
│   ├── Check compression → 01_Core_DataTransfer.md#compression
│   ├── Adjust chunk size → Modify MAX_CHUNK_SIZE
│   ├── Monitor memory → docker stats
│   └── Test smaller dataset → 04_TestScenarios.md
│
└── 🤖 Agent not responding
    ├── Verify endpoint → Check webhook URL
    ├── Test connection → Use health check endpoint
    ├── Review configuration → 03_Agents_Catalog.md
    └── Check integration → Test with simple request
```

## 📍 Feature Navigation

### Git Integration Features (New in 3.2)

- **Automatic Artifact Capture** → `03_KB3_Agents_GitIntegration.md`  
- **Branch Management** → `03_KB3_Agents_VersionControl.md#branch-management`  
- **Continuous Documentation** → `kf32_continuous_docs_workflow.json`  
- **Incantation Preservation** → `03_KB3_Agents_IncantationPreserver.md`  
- **Browser Export Tool** → `claude_artifact_exporter.html`  
- **Monitoring Dashboard** → `http://localhost:5678/webhook/kf32/monitoring/dashboard`

### Core Features

- **System Architecture** → `00_KB3_Core.md`  
- **Agent Coordination** → `03_Agents_Catalog.md`  
- **Workflow Automation** → `02_N8N_WorkflowRegistry.md`  
- **Data Transfer** → `01_Core_DataTransfer.md`  
- **Testing Framework** → `04_TestScenarios.md`

### Configuration & Setup

- **Complete Setup Guide** → `00_KB3_ImplementationGuide.md`  
- **Git Integration Setup** → `00_KB3_ImplementationGuide_3.2_GitIntegration.md`  
- **Environment Variables** → `00_KB3_ImplementationGuide.md#configuration`  
- **Docker Deployment** → `00_KB3_ImplementationGuide.md#docker`

## 🔍 Search Helpers

### By Topic

- **Git/Version Control**: `GitIntegration`, `VersionControl`, `IncantationPreserver`  
- **Agents**: `Navigator`, `AgentBuilder`, `Catalog`  
- **Workflows**: `WorkflowRegistry`, `artifact_export`, `continuous_docs`  
- **Data**: `DataTransfer`, `compression`, `chunking`  
- **Testing**: `TestScenarios`, `GitIntegration tests`

### By File Pattern

- Core docs: `00_KB3_*.md`  
- Agents: `03_KB3_Agents_*.md`  
- Workflows: `kf32_*_workflow.json`  
- Tests: `04_TestScenarios*.md`

### By Difficulty

- **Beginner**: Start with Navigation, Core, Agent Catalog  
- **Intermediate**: Implementation Guide, Workflow Registry, Data Transfer  
- **Advanced**: Agent Building, Version Control, Custom Integrations

## 🚦 Status Indicators

### System Components

- ✅ **Core Framework**: Stable, production-ready  
- ✅ **Agent System**: Fully functional with 5 specialized agents  
- ✅ **Git Integration**: NEW \- Automated capture and versioning  
- ✅ **Data Transfer**: Unlimited size support with compression  
- ✅ **Workflow Engine**: N8N-based, highly customizable  
- 🚧 **Advanced Analytics**: Coming in 3.3

### Quick Health Checks

```shell
# Check if system is running
curl http://localhost:5678/healthz

# Verify Git integration
curl -H "X-API-Key: $KF32_API_KEY" \
  http://localhost:5678/webhook/kf32/git/status

# Test artifact capture
curl -X POST http://localhost:5678/webhook/kf32/artifact/capture \
  -H "X-API-Key: $KF32_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"artifact": {"content": "test", "type": "text"}}'
```

## 📚 Learning Paths

### Path 1: System Administrator

1. `00_KB3_Core.md` \- Understand architecture  
2. `00_KB3_ImplementationGuide.md` \- Deploy system  
3. `00_KB3_ImplementationGuide_3.2_GitIntegration.md` \- Configure Git  
4. `04_TestScenarios.md` \- Validate deployment  
5. `03_KB3_Agents_VersionControl.md` \- Manage repositories

### Path 2: Agent Developer

1. `03_Agents_Catalog.md` \- Explore existing agents  
2. `03_KB3_Agents_AgentBuilder.md` \- Create new agents  
3. `00_KB3_Templates.md` \- Use templates  
4. `03_KB3_Agents_GitIntegration.md` \- Auto-save work  
5. `04_TestScenarios.md` \- Test agents

### Path 3: Workflow Designer

1. `02_N8N_WorkflowRegistry.md` \- Understand workflows  
2. `00_KB3_Templates.md` \- Workflow patterns  
3. `01_Core_DataTransfer.md` \- Handle data  
4. `kf32_*_workflow.json` \- Study examples  
5. `04_TestScenarios.md` \- Test workflows

### Path 4: Knowledge Curator

1. `00_KB3_Navigation.md` \- System overview  
2. `03_KB3_Agents_Navigator.md` \- Use navigation  
3. `kf32_continuous_docs_workflow.json` \- Auto-sync docs  
4. `03_KB3_Agents_IncantationPreserver.md` \- Preserve knowledge  
5. `00_KB3_Core.md` \- Understand structure

## 🎯 Common Tasks Quick Reference

### Export an Artifact

```javascript
// Use the browser tool or:
fetch('http://localhost:5678/webhook/kf32/artifact/capture', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
    'X-API-Key': 'your-api-key'
  },
  body: JSON.stringify({
    artifact: { content, type, filename },
    metadata: { conversationId, context }
  })
});
```

### Check System Status

```shell
# Run monitoring script
./monitor-status.sh

# Or access dashboard
open http://localhost:5678/webhook/kf32/monitoring/dashboard
```

### Create New Agent

1. Start conversation with Agent-Building Agent  
2. Follow the PDIA cycle  
3. Artifacts auto-captured to Git  
4. Find in `agents/specifications/`

### Run Tests

```shell
# All tests
npm test

# Specific suite
npm test -- --suite=git-integration
```

## 🆘 Getting Help

### Documentation Issues

- Can't find something? Start with this Navigation guide  
- Broken links? Check `00_KB3_Core.md` for correct references  
- Need examples? See `00_KB3_Templates.md`

### Technical Support

- Implementation problems? → `00_KB3_ImplementationGuide.md#troubleshooting`  
- Git issues? → `00_KB3_ImplementationGuide_3.2_GitIntegration.md#troubleshooting`  
- Agent problems? → `03_Agents_Catalog.md` for specifications

### Community Resources

- GitHub Issues: Report bugs and request features  
- Documentation: Always check latest in repository  
- Monitoring: Use dashboard for system insights

## Next Steps

Based on your role:

1️⃣ **New Users** → Start with `00_KB3_Core.md` to understand the system 2️⃣ **Developers** → Jump to `03_KB3_Agents_AgentBuilder.md` to create agents 3️⃣ **Administrators** → Follow `00_KB3_ImplementationGuide.md` for deployment 4️⃣ **Researchers** → Explore `01_Core_DataTransfer.md` for data capabilities 5️⃣ **Teams** → Configure `03_KB3_Agents_GitIntegration.md` for collaboration  
