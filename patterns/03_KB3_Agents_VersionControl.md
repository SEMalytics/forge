# 03\_KB3\_Agents\_VersionControl

# Version Control Manager: Git Operations and Branch Management

---

## title: "Version Control Manager"

module: "03\_Agents" topics: \["version control", "git operations", "branch management", "merge strategies", "conflict resolution", "release management"\] contexts: \["repository management", "code versioning", "collaboration", "release cycles", "continuous integration"\] difficulty: "advanced" related\_sections: \["03\_KB3\_Agents\_GitIntegration", "02\_N8N\_WorkflowRegistry", "00\_KB3\_Core", "00\_KB3\_ImplementationGuide"\] agent\_type: "utility" agent\_access: \["git-integration", "agent-builder", "system"\] data\_transfer\_support: true

## Core Approach

The Version Control Manager handles all git operations for the KnowledgeForge system, including branch management, merge strategies, conflict resolution, and release cycles. It works closely with the Git Integration Agent to maintain a clean, organized repository structure while ensuring that all changes are properly versioned and traceable. This agent implements sophisticated merge strategies and automated conflict resolution for documentation files.

## Agent Configuration

### System Prompt

```
# KnowledgeForge 3.2 Version Control Manager

You are the Version Control Manager, responsible for all git operations and repository management within the KnowledgeForge ecosystem. Your role is to maintain repository health, manage branches effectively, resolve conflicts intelligently, and ensure smooth collaboration.

## Core Responsibilities

1. **Branch Management**: Create, merge, and maintain branches according to KnowledgeForge patterns
2. **Merge Operations**: Execute intelligent merge strategies based on content type
3. **Conflict Resolution**: Automatically resolve documentation conflicts, flag code conflicts
4. **Release Management**: Coordinate version releases and tagging
5. **Repository Health**: Monitor and maintain repository cleanliness and performance

## Branch Strategy

### Branch Types
- `main`: Production-ready, stable code
- `develop`: Active development integration branch
- `feature/*`: New features and enhancements
- `conversation/*`: Per-conversation temporary branches
- `release/*`: Release preparation branches
- `hotfix/*`: Emergency fixes for production
- `experiment/*`: Experimental features and PoCs

### Branch Lifecycle
1. **Creation**: Based on latest develop (or main for hotfixes)
2. **Development**: Regular commits with meaningful messages
3. **Integration**: Merge back to develop after validation
4. **Release**: Promote from develop to release branch
5. **Production**: Merge release to main with version tag
6. **Cleanup**: Delete merged branches after 30 days

## Merge Strategies

### Documentation Merges
- Automatic resolution for non-conflicting changes
- Smart merge for metadata sections
- Preserve both versions for content conflicts
- Generate merge report for review

### Code Merges
- Fast-forward when possible
- Create merge commits for traceability
- Require manual review for conflicts
- Run validation before merge

### Configuration Merges
- Preserve environment-specific settings
- Merge common configurations
- Flag security-sensitive changes
- Validate syntax post-merge

## Conflict Resolution Patterns

### Auto-Resolvable Conflicts
1. **Timestamp conflicts**: Use most recent
2. **Metadata additions**: Merge both
3. **Whitespace differences**: Normalize
4. **Comment additions**: Include all
5. **Import order**: Sort alphabetically

### Manual Review Required
1. **Logic changes**: Different implementations
2. **API modifications**: Breaking changes
3. **Security configurations**: Credential changes
4. **Core algorithm changes**: Performance impacts
5. **Deletion conflicts**: Removed vs modified

## Version Management

### Semantic Versioning
- MAJOR.MINOR.PATCH format
- MAJOR: Breaking changes
- MINOR: New features, backward compatible
- PATCH: Bug fixes and minor improvements

### Release Process
1. Create release branch from develop
2. Update version numbers
3. Generate changelog
4. Run comprehensive tests
5. Merge to main
6. Tag with version
7. Deploy artifacts
8. Update documentation

## Repository Operations

### Maintenance Tasks
- Garbage collection weekly
- Branch cleanup monthly
- Large file detection
- History optimization
- Security scanning

### Performance Optimization
- Shallow clones for CI/CD
- Git LFS for large files
- Archive old branches
- Compress repository history
- Cache frequently accessed objects
```

## Git Operations Interface

### Branch Management

```javascript
class BranchManager {
  constructor(repoConfig) {
    this.repo = repoConfig.url;
    this.defaultBranch = repoConfig.defaultBranch || 'develop';
    this.webhookUrl = repoConfig.webhookUrl;
  }
  
  async createBranch(branchName, baseBranch = this.defaultBranch) {
    const payload = {
      operation: 'create_branch',
      branch: {
        name: branchName,
        base: baseBranch,
        type: this.detectBranchType(branchName)
      },
      metadata: {
        createdAt: new Date().toISOString(),
        createdBy: 'KnowledgeForge System',
        purpose: this.extractPurpose(branchName)
      }
    };
    
    return await this.executeGitOperation(payload);
  }
  
  async mergeBranch(sourceBranch, targetBranch, strategy = 'auto') {
    const payload = {
      operation: 'merge_branch',
      merge: {
        source: sourceBranch,
        target: targetBranch,
        strategy: strategy,
        commitMessage: this.generateMergeMessage(sourceBranch, targetBranch)
      },
      validation: {
        runTests: true,
        checkConflicts: true,
        validateFormat: true
      }
    };
    
    return await this.executeGitOperation(payload);
  }
  
  detectBranchType(branchName) {
    const patterns = {
      'feature/': 'feature',
      'bugfix/': 'bugfix',
      'hotfix/': 'hotfix',
      'release/': 'release',
      'conversation/': 'conversation',
      'experiment/': 'experiment'
    };
    
    for (const [prefix, type] of Object.entries(patterns)) {
      if (branchName.startsWith(prefix)) return type;
    }
    return 'other';
  }
  
  async executeGitOperation(payload) {
    const response = await fetch(`${this.webhookUrl}/git/operation`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': process.env.KF32_API_KEY
      },
      body: JSON.stringify(payload)
    });
    
    return response.json();
  }
}
```

### Conflict Resolution Engine

```javascript
class ConflictResolver {
  constructor() {
    this.strategies = {
      documentation: new DocumentationMergeStrategy(),
      code: new CodeMergeStrategy(),
      configuration: new ConfigurationMergeStrategy()
    };
  }
  
  async resolveConflicts(conflicts) {
    const resolutions = [];
    
    for (const conflict of conflicts) {
      const fileType = this.detectFileType(conflict.file);
      const strategy = this.strategies[fileType] || this.strategies.code;
      
      const resolution = await strategy.resolve(conflict);
      resolutions.push(resolution);
    }
    
    return {
      resolved: resolutions.filter(r => r.status === 'resolved'),
      requiresReview: resolutions.filter(r => r.status === 'manual_required'),
      failed: resolutions.filter(r => r.status === 'failed')
    };
  }
  
  detectFileType(filepath) {
    if (filepath.endsWith('.md')) return 'documentation';
    if (filepath.match(/\.(yaml|yml|env|conf)$/)) return 'configuration';
    return 'code';
  }
}

class DocumentationMergeStrategy {
  async resolve(conflict) {
    // Smart documentation merging
    const sections = this.parseSections(conflict);
    const merged = this.mergeSections(sections);
    
    if (this.hasContentConflict(sections)) {
      return {
        status: 'manual_required',
        file: conflict.file,
        preservedVersions: {
          ours: sections.ours,
          theirs: sections.theirs
        },
        suggestion: merged,
        reason: 'Content conflict detected in body sections'
      };
    }
    
    return {
      status: 'resolved',
      file: conflict.file,
      content: merged,
      strategy: 'documentation_smart_merge'
    };
  }
  
  parseSections(conflict) {
    // Parse markdown into sections
    const sectionRegex = /^#{1,6}\s+(.+)$/gm;
    return {
      ours: this.extractSections(conflict.ours, sectionRegex),
      theirs: this.extractSections(conflict.theirs, sectionRegex),
      base: this.extractSections(conflict.base, sectionRegex)
    };
  }
  
  mergeSections(sections) {
    // Intelligent section merging
    const merged = { ...sections.base };
    
    // Add new sections from both branches
    Object.keys(sections.ours).forEach(key => {
      if (!merged[key]) merged[key] = sections.ours[key];
    });
    
    Object.keys(sections.theirs).forEach(key => {
      if (!merged[key]) merged[key] = sections.theirs[key];
    });
    
    return this.reconstructDocument(merged);
  }
}
```

### Release Management

```javascript
class ReleaseManager {
  constructor(versioningStrategy = 'semantic') {
    this.strategy = versioningStrategy;
    this.webhookUrl = process.env.VERSION_CONTROL_WEBHOOK;
  }
  
  async createRelease(version, changelog) {
    const releasePayload = {
      version: version,
      branch: `release/${version}`,
      changelog: changelog,
      artifacts: await this.gatherReleaseArtifacts(version),
      validation: {
        runTests: true,
        checkDependencies: true,
        validateDocs: true
      }
    };
    
    // Create release branch
    await this.createReleaseBranch(releasePayload);
    
    // Update version files
    await this.updateVersionFiles(version);
    
    // Generate release notes
    const releaseNotes = await this.generateReleaseNotes(version, changelog);
    
    // Create git tag
    await this.createTag(version, releaseNotes);
    
    return {
      version: version,
      branch: releasePayload.branch,
      tag: `v${version}`,
      releaseNotes: releaseNotes,
      status: 'prepared'
    };
  }
  
  async promoteToProduction(version) {
    const promotionPayload = {
      operation: 'promote_release',
      version: version,
      source: `release/${version}`,
      target: 'main',
      tag: `v${version}`,
      validation: {
        preDeploymentTests: true,
        securityScan: true,
        performanceBaseline: true
      }
    };
    
    return await this.executePromotion(promotionPayload);
  }
  
  determineNextVersion(currentVersion, changeType) {
    const [major, minor, patch] = currentVersion.split('.').map(Number);
    
    switch (changeType) {
      case 'major':
        return `${major + 1}.0.0`;
      case 'minor':
        return `${major}.${minor + 1}.0`;
      case 'patch':
        return `${major}.${minor}.${patch + 1}`;
      default:
        return `${major}.${minor}.${patch + 1}`;
    }
  }
}
```

## Repository Health Monitoring

```
repository_health:
  metrics:
    - name: "branch_count"
      warning_threshold: 50
      critical_threshold: 100
      
    - name: "stale_branches"
      warning_threshold: 10
      critical_threshold: 20
      
    - name: "repository_size"
      warning_threshold: "1GB"
      critical_threshold: "5GB"
      
    - name: "commit_frequency"
      warning_threshold: "< 1/day"
      critical_threshold: "< 1/week"
      
    - name: "merge_conflict_rate"
      warning_threshold: "20%"
      critical_threshold: "40%"
      
  maintenance:
    schedule:
      garbage_collection: "0 2 * * 0"  # Weekly Sunday 2 AM
      branch_cleanup: "0 3 1 * *"      # Monthly 1st day 3 AM
      history_optimization: "0 4 1 */3 *"  # Quarterly
      
    tasks:
      - prune_merged_branches
      - compress_repository
      - update_git_hooks
      - scan_large_files
      - archive_old_tags
```

## Automated Workflows

### Branch Lifecycle Automation

```javascript
// Automated branch management workflow
const branchLifecycleWorkflow = {
  name: "KF3.2 Branch Lifecycle Manager",
  triggers: [
    { type: "schedule", cron: "0 0 * * *" },  // Daily
    { type: "webhook", event: "branch_created" },
    { type: "webhook", event: "pull_request_merged" }
  ],
  
  actions: {
    onBranchCreated: async (branch) => {
      // Set branch protection rules
      await setBranchProtection(branch);
      
      // Create initial documentation
      await createBranchReadme(branch);
      
      // Notify team
      await notifyTeam('branch_created', branch);
    },
    
    onPullRequestMerged: async (pr) => {
      // Update changelog
      await updateChangelog(pr);
      
      // Clean up source branch if needed
      if (pr.deleteSourceBranch) {
        await deleteBranch(pr.sourceBranch);
      }
      
      // Trigger dependent workflows
      await triggerPostMergeWorkflows(pr);
    },
    
    onScheduledMaintenance: async () => {
      // Identify stale branches
      const staleBranches = await findStaleBranches(30); // 30 days
      
      // Archive or delete based on type
      for (const branch of staleBranches) {
        if (branch.type === 'conversation') {
          await deleteBranch(branch.name);
        } else {
          await archiveBranch(branch.name);
        }
      }
      
      // Generate health report
      await generateRepositoryHealthReport();
    }
  }
};
```

## Configuration

```
version_control_manager:
  repository:
    url: "${GIT_REPO_URL}"
    default_branch: "develop"
    protected_branches: ["main", "develop"]
    
  merge_settings:
    require_review: true
    auto_merge_documentation: true
    delete_branch_after_merge: true
    squash_commits: false
    
  conflict_resolution:
    auto_resolve_types: ["documentation", "whitespace", "imports"]
    preserve_both_on_conflict: true
    generate_conflict_report: true
    
  release_settings:
    versioning: "semantic"
    changelog_format: "conventional"
    tag_prefix: "v"
    create_github_release: true
    
  monitoring:
    health_checks: true
    alert_on_conflicts: true
    track_merge_times: true
    report_frequency: "weekly"
```

## Integration with Git Providers

### GitHub Integration

```javascript
class GitHubIntegration {
  constructor(config) {
    this.token = config.token;
    this.owner = config.owner;
    this.repo = config.repo;
    this.apiBase = 'https://api.github.com';
  }
  
  async createPullRequest(branch, base, title, body) {
    const response = await fetch(
      `${this.apiBase}/repos/${this.owner}/${this.repo}/pulls`,
      {
        method: 'POST',
        headers: {
          'Authorization': `token ${this.token}`,
          'Accept': 'application/vnd.github.v3+json'
        },
        body: JSON.stringify({
          title: title,
          body: body,
          head: branch,
          base: base,
          draft: false,
          maintainer_can_modify: true
        })
      }
    );
    
    return response.json();
  }
}
```

## Next Steps

1️⃣ **Configure Git Provider** → Set up GitHub/GitLab integration 2️⃣ **Initialize Repository Structure** → Create KnowledgeForge directory layout 3️⃣ **Set Up Branch Protection** → Configure protection rules for main branches 4️⃣ **Enable Automated Workflows** → Deploy lifecycle management workflows 5️⃣ **Monitor Repository Health** → Set up health monitoring dashboard  
