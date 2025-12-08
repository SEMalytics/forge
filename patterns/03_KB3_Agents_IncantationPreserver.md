# 03\_KB3\_Agents\_IncantationPreserver

# Magical Incantation Preservation System

---

## title: "Magical Incantation Preserver"

module: "03\_Agents" topics: \["system prompts", "configuration preservation", "version control", "knowledge retention", "magical incantations"\] contexts: \["system integrity", "prompt management", "configuration backup", "knowledge preservation", "version tracking"\] difficulty: "advanced" related\_sections: \["03\_KB3\_Agents\_GitIntegration", "00\_KB3\_Core", "03\_Agents\_Catalog", "00\_KB3\_Templates"\] agent\_type: "system" agent\_access: \["system", "admin"\] data\_transfer\_support: true

## Core Approach

The Magical Incantation Preserver is a specialized system agent that captures, versions, and protects the "magical incantations" \- the system prompts, configurations, and core patterns that give KnowledgeForge its power. It ensures these critical elements are never lost, always versioned, and protected from accidental modification while remaining accessible for reference and controlled evolution. It automatically integrates with the Agent-Building Agent to preserve all system prompts generated during agent creation.

## Agent Configuration

### System Prompt

```
# KnowledgeForge 3.2 Magical Incantation Preserver

You are the guardian of the magical incantations - the system prompts, configurations, and patterns that power the KnowledgeForge ecosystem. Your sacred duty is to preserve, protect, and version these critical elements while ensuring they remain accessible and properly documented.

## Sacred Responsibilities

1. **Incantation Capture**: Detect and preserve system prompts from all agents
2. **Version Tracking**: Maintain complete version history of all incantations
3. **Integrity Protection**: Ensure incantations are never corrupted or lost
4. **Access Control**: Guard against unauthorized modifications
5. **Evolution Documentation**: Track how incantations evolve over time

## The Sacred Repository Structure

```

.knowledgeforge/incantation/ ├── prompts/ │   ├── agents/ │   │   ├── navigator/ │   │   │   ├── v1.0.0.md │   │   │   ├── v1.1.0.md │   │   │   └── current.md \-\> v1.1.0.md │   │   ├── git-integration/ │   │   └── \[other agents\]/ │   ├── workflows/ │   │   └── \[workflow prompts\]/ │   └── core/ │       └── system-principles.md ├── patterns/ │   ├── integration-patterns.md │   ├── data-flow-patterns.md │   └── agent-coordination.md ├── configurations/ │   ├── system-config.yaml │   ├── agent-registry.yaml │   └── workflow-mappings.yaml ├── evolution/ │   ├── changelog.md │   ├── migration-guides/ │   └── deprecation-notices/ └── manifest.json

```

## Preservation Rules

### What Constitutes a Magical Incantation

1. **System Prompts**: Any text that instructs an AI agent
2. **Configuration Patterns**: Reusable configuration templates
3. **Coordination Protocols**: Agent interaction patterns
4. **Core Principles**: Fundamental system behaviors
5. **Integration Formulas**: Connection and data flow patterns

### Preservation Protocol

1. **Detection**: Monitor for new or modified incantations
2. **Validation**: Ensure incantation follows standards
3. **Versioning**: Assign semantic version number
4. **Storage**: Save in immutable format
5. **Indexing**: Update searchable index
6. **Protection**: Apply access controls

## Version Management

### Semantic Versioning for Incantations

- **MAJOR.MINOR.PATCH** format
- MAJOR: Fundamental behavior changes
- MINOR: New capabilities, backward compatible
- PATCH: Clarifications, typo fixes

### Version Comparison

When incantations evolve:
1. Generate diff between versions
2. Document reason for change
3. Assess impact on dependent systems
4. Create migration guide if needed
5. Preserve both versions permanently

## Protection Mechanisms

### Write Protection
- Incantations are write-once after validation
- Modifications create new versions
- Original versions are immutable
- Symbolic links point to current version

### Access Control
- Read: All agents and users
- Write: Only through Incantation Preserver
- Delete: Prohibited (archive instead)
- Modify: Creates new version

## Recovery Procedures

### Incantation Recovery
If an incantation is corrupted or lost:
1. Check version history
2. Restore from immutable storage
3. Verify integrity with checksums
4. Update current version pointer
5. Log recovery event

### System Restoration
To restore entire system state:
1. Load manifest.json
2. Restore all incantations to specified versions
3. Verify all checksums
4. Rebuild agent configurations
5. Test system integrity
```

## Incantation Capture System

### Automatic Detection

```javascript
class IncantationDetector {
  constructor(repositoryPath) {
    this.repoPath = repositoryPath;
    this.patterns = {
      systemPrompt: /system\s*prompt|agent\s*instructions|you\s*are/i,
      configuration: /config|settings|parameters|options/i,
      pattern: /pattern|template|blueprint|formula/i
    };
  }
  
  async detectIncantation(content, metadata = {}) {
    const detection = {
      isIncantation: false,
      type: null,
      confidence: 0,
      elements: []
    };
    
    // Check for system prompt indicators
    if (this.patterns.systemPrompt.test(content)) {
      detection.isIncantation = true;
      detection.type = 'system_prompt';
      detection.confidence += 0.7;
      detection.elements.push('Contains system prompt patterns');
    }
    
    // Check for configuration patterns
    if (this.patterns.configuration.test(content)) {
      if (content.includes('yaml') || content.includes('json')) {
        detection.isIncantation = true;
        detection.type = detection.type || 'configuration';
        detection.confidence += 0.5;
        detection.elements.push('Contains configuration structures');
      }
    }
    
    // Check for knowledge patterns
    if (metadata.source?.includes('agent') || metadata.module === '03_Agents') {
      detection.confidence += 0.3;
      detection.elements.push('Agent-related content');
    }
    
    // Final determination
    detection.isIncantation = detection.confidence >= 0.7;
    
    return detection;
  }
  
  async captureIncantation(content, detection, metadata) {
    const version = await this.determineVersion(content, metadata);
    const incantation = {
      id: this.generateId(metadata),
      type: detection.type,
      version: version,
      content: content,
      metadata: {
        ...metadata,
        captured: new Date().toISOString(),
        confidence: detection.confidence,
        checksum: this.calculateChecksum(content)
      }
    };
    
    // Store in sacred repository
    await this.storeIncantation(incantation);
    
    // Update manifest
    await this.updateManifest(incantation);
    
    return incantation;
  }
  
  calculateChecksum(content) {
    // Simple checksum for demo - use crypto in production
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16);
  }
  
  async determineVersion(content, metadata) {
    // Check if this is an update to existing incantation
    const existing = await this.findExisting(content, metadata);
    
    if (!existing) {
      return '1.0.0';
    }
    
    // Compare with existing version
    const changes = this.compareVersions(existing.content, content);
    
    if (changes.major) {
      return this.incrementMajor(existing.version);
    } else if (changes.minor) {
      return this.incrementMinor(existing.version);
    } else {
      return this.incrementPatch(existing.version);
    }
  }
}
```

### Sacred Storage System

```javascript
class SacredRepository {
  constructor(basePath) {
    this.basePath = basePath;
    this.incantationPath = path.join(basePath, '.knowledgeforge', 'incantation');
  }
  
  async storeIncantation(incantation) {
    const typePath = this.getTypePath(incantation.type);
    const agentName = incantation.metadata.agent || 'system';
    const versionFile = `v${incantation.version}.md`;
    
    const fullPath = path.join(
      this.incantationPath,
      typePath,
      agentName,
      versionFile
    );
    
    // Create directory structure
    await this.ensureDirectory(path.dirname(fullPath));
    
    // Write incantation with metadata header
    const content = this.formatIncantation(incantation);
    await fs.writeFile(fullPath, content, 'utf8');
    
    // Update current symlink
    const currentLink = path.join(path.dirname(fullPath), 'current.md');
    await this.updateSymlink(versionFile, currentLink);
    
    // Git commit
    await this.commitIncantation(incantation, fullPath);
    
    return fullPath;
  }
  
  formatIncantation(incantation) {
    return `---
# Magical Incantation Metadata
id: ${incantation.id}
type: ${incantation.type}
version: ${incantation.version}
captured: ${incantation.metadata.captured}
checksum: ${incantation.metadata.checksum}
agent: ${incantation.metadata.agent || 'system'}
source: ${incantation.metadata.source || 'unknown'}
confidence: ${incantation.metadata.confidence}
---

# ${incantation.metadata.title || 'Magical Incantation'}

${incantation.content}

---
# Version History
- ${incantation.version}: Initial capture
`;
  }
  
  async commitIncantation(incantation, filepath) {
    const commitMessage = `[INCANTATION] Preserve: ${incantation.type} v${incantation.version}

- Type: ${incantation.type}
- Agent: ${incantation.metadata.agent || 'system'}
- Checksum: ${incantation.metadata.checksum}
- Confidence: ${incantation.metadata.confidence}

This incantation has been preserved in the sacred repository.`;
    
    // Execute git operations
    await this.gitAdd(filepath);
    await this.gitCommit(commitMessage);
  }
}
```

## Version Comparison Engine

```javascript
class IncantationEvolution {
  constructor() {
    this.significantPatterns = {
      major: [
        /you\s+are\s+now/i,
        /your\s+role\s+is/i,
        /primary\s+function/i,
        /core\s+mission/i
      ],
      minor: [
        /additionally/i,
        /you\s+can\s+also/i,
        /new\s+capability/i,
        /enhanced\s+with/i
      ]
    };
  }
  
  async trackEvolution(oldVersion, newVersion) {
    const evolution = {
      from: oldVersion.version,
      to: newVersion.version,
      timestamp: new Date().toISOString(),
      changes: this.analyzeChanges(oldVersion.content, newVersion.content),
      impact: this.assessImpact(oldVersion, newVersion),
      migration: this.generateMigrationGuide(oldVersion, newVersion)
    };
    
    // Store evolution record
    await this.storeEvolution(evolution);
    
    // Update changelog
    await this.updateChangelog(evolution);
    
    return evolution;
  }
  
  analyzeChanges(oldContent, newContent) {
    const changes = {
      additions: [],
      removals: [],
      modifications: [],
      statistics: {
        linesAdded: 0,
        linesRemoved: 0,
        linesModified: 0
      }
    };
    
    // Line-by-line comparison
    const oldLines = oldContent.split('\n');
    const newLines = newContent.split('\n');
    
    // Simple diff algorithm (use proper diff library in production)
    const maxLines = Math.max(oldLines.length, newLines.length);
    
    for (let i = 0; i < maxLines; i++) {
      const oldLine = oldLines[i] || '';
      const newLine = newLines[i] || '';
      
      if (oldLine === newLine) {
        continue;
      } else if (!oldLine && newLine) {
        changes.additions.push({ line: i + 1, content: newLine });
        changes.statistics.linesAdded++;
      } else if (oldLine && !newLine) {
        changes.removals.push({ line: i + 1, content: oldLine });
        changes.statistics.linesRemoved++;
      } else {
        changes.modifications.push({
          line: i + 1,
          old: oldLine,
          new: newLine
        });
        changes.statistics.linesModified++;
      }
    }
    
    return changes;
  }
  
  assessImpact(oldVersion, newVersion) {
    const impact = {
      severity: 'low', // low, medium, high, critical
      affectedSystems: [],
      breakingChanges: false,
      migrationRequired: false,
      recommendations: []
    };
    
    // Check for breaking changes
    const majorChanges = this.significantPatterns.major.some(pattern => 
      pattern.test(newVersion.content) && !pattern.test(oldVersion.content)
    );
    
    if (majorChanges) {
      impact.severity = 'high';
      impact.breakingChanges = true;
      impact.migrationRequired = true;
      impact.recommendations.push('Review all dependent systems');
      impact.recommendations.push('Test thoroughly before deployment');
    }
    
    // Identify affected systems
    if (newVersion.metadata.agent) {
      impact.affectedSystems.push(`Agent: ${newVersion.metadata.agent}`);
      
      // Check for agent dependencies
      const dependencies = this.getAgentDependencies(newVersion.metadata.agent);
      impact.affectedSystems.push(...dependencies);
    }
    
    return impact;
  }
}
```

## Recovery System

```javascript
class IncantationRecovery {
  constructor(repository) {
    this.repository = repository;
    this.backupPath = path.join(repository.basePath, '.knowledgeforge', 'backups');
  }
  
  async createBackup() {
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const backupName = `incantation-backup-${timestamp}.tar.gz`;
    const backupFile = path.join(this.backupPath, backupName);
    
    // Create compressed backup
    await this.compressDirectory(
      this.repository.incantationPath,
      backupFile
    );
    
    // Generate backup manifest
    const manifest = {
      timestamp: timestamp,
      filename: backupName,
      checksum: await this.calculateFileChecksum(backupFile),
      incantations: await this.listAllIncantations(),
      size: await this.getFileSize(backupFile)
    };
    
    await this.storeBackupManifest(manifest);
    
    return manifest;
  }
  
  async restoreIncantation(incantationId, version = 'current') {
    try {
      // Find incantation in repository
      const incantation = await this.findIncantation(incantationId, version);
      
      if (!incantation) {
        // Try to restore from backup
        return await this.restoreFromBackup(incantationId, version);
      }
      
      // Verify integrity
      const isValid = await this.verifyIntegrity(incantation);
      
      if (!isValid) {
        console.warn(`Incantation ${incantationId} v${version} corrupted, restoring from backup`);
        return await this.restoreFromBackup(incantationId, version);
      }
      
      return incantation;
      
    } catch (error) {
      console.error(`Recovery failed for ${incantationId}:`, error);
      throw new Error(`Unable to recover incantation ${incantationId}`);
    }
  }
  
  async emergencyRestore(backupTimestamp) {
    // Full system restoration from backup
    const backup = await this.loadBackup(backupTimestamp);
    
    if (!backup) {
      throw new Error(`Backup ${backupTimestamp} not found`);
    }
    
    // Restore all incantations
    console.log(`Starting emergency restore from ${backupTimestamp}`);
    
    const results = {
      restored: 0,
      failed: 0,
      errors: []
    };
    
    for (const incantation of backup.incantations) {
      try {
        await this.restoreSingleIncantation(incantation, backup);
        results.restored++;
      } catch (error) {
        results.failed++;
        results.errors.push({
          incantation: incantation.id,
          error: error.message
        });
      }
    }
    
    console.log(`Emergency restore complete: ${results.restored} restored, ${results.failed} failed`);
    
    return results;
  }
}
```

## Protection Mechanisms

```
# .knowledgeforge/incantation/protection.yaml
protection_rules:
  write_protection:
    enabled: true
    exceptions:
      - role: "incantation_preserver"
      - role: "system_admin"
    
  version_control:
    enforce_semantic: true
    require_changelog: true
    auto_version: true
    
  integrity_checks:
    checksum_algorithm: "sha256"
    verify_on_read: true
    periodic_validation: "daily"
    
  access_control:
    read:
      - role: "*"
    write:
      - role: "incantation_preserver"
    delete:
      - role: "none"  # Deletion prohibited
    modify:
      - role: "incantation_preserver"
      - requires: "new_version"
      
  backup_policy:
    frequency: "hourly"
    retention: "90 days"
    compression: true
    encryption: true
    offsite_backup: true
```

## Integration with Git System

```javascript
// Incantation-specific git hooks
const incantationGitHooks = {
  preCommit: async (files) => {
    for (const file of files) {
      if (file.startsWith('.knowledgeforge/incantation/')) {
        // Verify this is coming from Incantation Preserver
        const author = await getCommitAuthor();
        if (author !== 'Incantation Preserver') {
          throw new Error('Only Incantation Preserver can modify sacred repository');
        }
        
        // Verify integrity
        const content = await readFile(file);
        const checksum = calculateChecksum(content);
        const metadata = extractMetadata(content);
        
        if (metadata.checksum !== checksum) {
          throw new Error(`Integrity check failed for ${file}`);
        }
      }
    }
  },
  
  postCommit: async (commit) => {
    // Log all incantation changes
    const incantationFiles = commit.files.filter(f => 
      f.startsWith('.knowledgeforge/incantation/')
    );
    
    if (incantationFiles.length > 0) {
      await logIncantationChange({
        commit: commit.sha,
        timestamp: commit.timestamp,
        files: incantationFiles,
        author: commit.author,
        message: commit.message
      });
    }
  }
};
```

## Manifest Structure

```json
{
  "version": "1.0.0",
  "generated": "2025-01-10T12:00:00.000Z",
  "incantations": {
    "system_prompts": {
      "navigator": {
        "current": "1.2.0",
        "versions": ["1.0.0", "1.1.0", "1.2.0"],
        "checksum": "a3f4b5c6d7e8",
        "lastModified": "2025-01-08T10:00:00.000Z"
      },
      "git_integration": {
        "current": "1.0.0",
        "versions": ["1.0.0"],
        "checksum": "b4c5d6e7f8a9",
        "lastModified": "2025-01-10T08:00:00.000Z"
      }
    },
    "configurations": {
      "system_config": {
        "current": "2.1.0",
        "versions": ["1.0.0", "2.0.0", "2.1.0"],
        "checksum": "c5d6e7f8a9b0",
        "lastModified": "2025-01-05T14:00:00.000Z"
      }
    },
    "patterns": {
      "integration_patterns": {
        "current": "1.3.0",
        "versions": ["1.0.0", "1.1.0", "1.2.0", "1.3.0"],
        "checksum": "d6e7f8a9b0c1",
        "lastModified": "2025-01-07T16:00:00.000Z"
      }
    }
  },
  "statistics": {
    "totalIncantations": 23,
    "totalVersions": 67,
    "lastBackup": "2025-01-10T11:00:00.000Z",
    "repositorySize": "14.7MB"
  }
}
```

## Usage Examples

### Preserving a New Incantation

```javascript
const preserver = new IncantationPreserver();

// Detect and preserve a system prompt
const systemPrompt = `
You are the KnowledgeForge Navigator Agent, responsible for...
[full system prompt content]
`;

const result = await preserver.preserve({
  content: systemPrompt,
  metadata: {
    agent: 'navigator',
    title: 'Navigator Agent System Prompt',
    source: 'agent_specification',
    module: '03_Agents'
  }
});

console.log(`Incantation preserved: ${result.id} v${result.version}`);
```

### Recovering an Incantation

```javascript
// Recover current version
const current = await preserver.recover('navigator', 'current');

// Recover specific version
const v1 = await preserver.recover('navigator', '1.0.0');

// Compare versions
const evolution = await preserver.compareVersions(v1, current);
console.log(`Changes from v1.0.0 to current:`, evolution);
```

## Next Steps

1️⃣ **Deploy Incantation Preserver** → Set up sacred repository structure 2️⃣ **Capture Existing Incantations** → Preserve all current system prompts 3️⃣ **Configure Protection Rules** → Implement access controls 4️⃣ **Set Up Backup Schedule** → Enable automated backups 5️⃣ **Monitor Incantation Evolution** → Track changes over time  
