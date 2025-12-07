"""
Commit strategies and conventional commit formatting

Provides:
- Conventional commit format
- Task-based commits
- Fix commits
- Auto-generated commit messages
"""

import re
from typing import List, Optional, Dict
from dataclasses import dataclass
from enum import Enum

from forge.utils.logger import logger


class CommitType(Enum):
    """Conventional commit types"""
    FEAT = "feat"           # New feature
    FIX = "fix"             # Bug fix
    DOCS = "docs"           # Documentation
    STYLE = "style"         # Formatting
    REFACTOR = "refactor"   # Code restructuring
    PERF = "perf"           # Performance
    TEST = "test"           # Tests
    BUILD = "build"         # Build system
    CI = "ci"               # CI/CD
    CHORE = "chore"         # Maintenance
    REVERT = "revert"       # Revert commit


@dataclass
class ConventionalCommit:
    """
    Conventional commit message.

    Format: <type>[optional scope]: <description>

    [optional body]

    [optional footer(s)]
    """
    type: CommitType
    description: str
    scope: Optional[str] = None
    body: Optional[str] = None
    breaking: bool = False
    issues: List[str] = None
    footers: Dict[str, str] = None

    def __post_init__(self):
        if self.issues is None:
            self.issues = []
        if self.footers is None:
            self.footers = {}

    def format(self) -> str:
        """
        Format as conventional commit message.

        Returns:
            Formatted commit message
        """
        # Build header
        header_parts = [self.type.value]

        if self.scope:
            header_parts.append(f"({self.scope})")

        if self.breaking:
            header_parts.append("!")

        header = "".join(header_parts) + f": {self.description}"

        # Build message parts
        parts = [header]

        if self.body:
            parts.append("")
            parts.append(self.body)

        # Add footers
        if self.breaking:
            parts.append("")
            parts.append("BREAKING CHANGE: " + (
                self.footers.get("BREAKING CHANGE", "Breaking API change")
            ))

        # Add issue references
        if self.issues:
            parts.append("")
            for issue in self.issues:
                if issue.startswith("#"):
                    parts.append(f"Closes {issue}")
                else:
                    parts.append(f"Closes #{issue}")

        # Add custom footers
        for key, value in self.footers.items():
            if key != "BREAKING CHANGE":
                parts.append("")
                parts.append(f"{key}: {value}")

        return "\n".join(parts)

    @classmethod
    def parse(cls, message: str) -> Optional['ConventionalCommit']:
        """
        Parse conventional commit message.

        Args:
            message: Commit message to parse

        Returns:
            ConventionalCommit or None if invalid
        """
        lines = message.strip().split("\n")
        if not lines:
            return None

        # Parse header
        header = lines[0]

        # Match: type(scope)!: description
        pattern = r'^(\w+)(?:\(([^)]+)\))?(!)?: (.+)$'
        match = re.match(pattern, header)

        if not match:
            return None

        type_str, scope, breaking_marker, description = match.groups()

        # Parse type
        try:
            commit_type = CommitType(type_str)
        except ValueError:
            return None

        # Parse body and footers
        body_lines = []
        footers = {}
        issues = []
        breaking = breaking_marker == "!"

        in_body = True
        for i in range(1, len(lines)):
            line = lines[i].strip()

            if not line:
                in_body = False  # Empty line ends body
                continue

            # Check if line starts with "Closes" (issue reference)
            if line.startswith("Closes"):
                in_body = False
                # Extract issue number
                issue_match = re.search(r'#?(\d+)', line)
                if issue_match:
                    issues.append(issue_match.group(1))
            # Check for footer pattern
            elif ": " in line and not line.startswith(" ") and not in_body:
                key, value = line.split(": ", 1)

                if key == "BREAKING CHANGE":
                    breaking = True
                    footers[key] = value
                else:
                    footers[key] = value
            elif in_body:
                body_lines.append(line)

        body = "\n".join(body_lines) if body_lines else None

        return cls(
            type=commit_type,
            description=description,
            scope=scope,
            body=body,
            breaking=breaking,
            issues=issues,
            footers=footers
        )


class CommitStrategy:
    """
    Generate commit messages based on changes.
    """

    @staticmethod
    def from_task(
        task_description: str,
        files_changed: List[str],
        scope: Optional[str] = None
    ) -> ConventionalCommit:
        """
        Create commit message from task.

        Args:
            task_description: Task description
            files_changed: List of changed files
            scope: Optional scope

        Returns:
            ConventionalCommit
        """
        # Infer type from task description
        commit_type = CommitStrategy._infer_type(task_description, files_changed)

        # Clean description
        description = task_description.strip()
        if description.endswith("."):
            description = description[:-1]

        # Infer scope if not provided
        if not scope:
            scope = CommitStrategy._infer_scope(files_changed)

        # Generate body
        body_parts = [f"Changes in {len(files_changed)} file(s):"]
        for file in files_changed[:5]:  # List first 5 files
            body_parts.append(f"- {file}")
        if len(files_changed) > 5:
            body_parts.append(f"- ... and {len(files_changed) - 5} more")

        body = "\n".join(body_parts)

        return ConventionalCommit(
            type=commit_type,
            description=description,
            scope=scope,
            body=body
        )

    @staticmethod
    def from_fix(
        issue: str,
        description: str,
        files_changed: List[str],
        scope: Optional[str] = None
    ) -> ConventionalCommit:
        """
        Create commit message for fix.

        Args:
            issue: Issue number
            description: Fix description
            files_changed: List of changed files
            scope: Optional scope

        Returns:
            ConventionalCommit
        """
        if not scope:
            scope = CommitStrategy._infer_scope(files_changed)

        body_parts = [f"Fixed {len(files_changed)} file(s)"]

        return ConventionalCommit(
            type=CommitType.FIX,
            description=description,
            scope=scope,
            body="\n".join(body_parts),
            issues=[issue] if issue else []
        )

    @staticmethod
    def from_changes(
        files_changed: List[str],
        diffs: Optional[Dict[str, str]] = None
    ) -> ConventionalCommit:
        """
        Auto-generate commit message from file changes.

        Args:
            files_changed: List of changed files
            diffs: Optional file diffs

        Returns:
            ConventionalCommit
        """
        # Infer type from files
        commit_type = CommitStrategy._infer_type_from_files(files_changed)

        # Infer scope
        scope = CommitStrategy._infer_scope(files_changed)

        # Generate description
        description = CommitStrategy._generate_description(
            files_changed, diffs
        )

        # Generate body
        body_parts = []
        for file in files_changed[:10]:
            body_parts.append(f"- {file}")

        if len(files_changed) > 10:
            body_parts.append(f"- ... and {len(files_changed) - 10} more files")

        return ConventionalCommit(
            type=commit_type,
            description=description,
            scope=scope,
            body="\n".join(body_parts) if body_parts else None
        )

    @staticmethod
    def _infer_type(description: str, files: List[str]) -> CommitType:
        """Infer commit type from description and files"""
        desc_lower = description.lower()

        # Check description keywords
        if any(word in desc_lower for word in ["fix", "bug", "issue", "error"]):
            return CommitType.FIX
        elif any(word in desc_lower for word in ["add", "new", "implement", "feature"]):
            return CommitType.FEAT
        elif any(word in desc_lower for word in ["doc", "readme", "comment"]):
            return CommitType.DOCS
        elif any(word in desc_lower for word in ["test", "spec"]):
            return CommitType.TEST
        elif any(word in desc_lower for word in ["refactor", "restructure", "reorganize"]):
            return CommitType.REFACTOR
        elif any(word in desc_lower for word in ["perf", "optimize", "speed"]):
            return CommitType.PERF
        elif any(word in desc_lower for word in ["style", "format", "lint"]):
            return CommitType.STYLE

        # Check files
        return CommitStrategy._infer_type_from_files(files)

    @staticmethod
    def _infer_type_from_files(files: List[str]) -> CommitType:
        """Infer commit type from changed files"""
        # Count file types
        test_files = sum(1 for f in files if "test" in f.lower())
        doc_files = sum(1 for f in files if any(ext in f.lower() for ext in [".md", "readme", "doc"]))
        config_files = sum(1 for f in files if any(ext in f.lower() for ext in [".yml", ".yaml", ".json", ".toml", "dockerfile"]))

        # Infer based on majority
        if test_files > len(files) / 2:
            return CommitType.TEST
        elif doc_files > len(files) / 2:
            return CommitType.DOCS
        elif config_files > len(files) / 2:
            return CommitType.BUILD

        # Default to chore
        return CommitType.CHORE

    @staticmethod
    def _infer_scope(files: List[str]) -> Optional[str]:
        """Infer scope from file paths"""
        if not files:
            return None

        # Extract common directory
        paths = [f.split("/") for f in files]

        # Find common prefix
        if not paths:
            return None

        common = []
        for parts in zip(*paths):
            if len(set(parts)) == 1:
                common.append(parts[0])
            else:
                break

        if common and common[0] in ["src", "lib", "app"]:
            # Use second level if first is generic
            if len(common) > 1:
                return common[1]

        if common:
            return common[0]

        return None

    @staticmethod
    def _generate_description(
        files: List[str],
        diffs: Optional[Dict[str, str]] = None
    ) -> str:
        """Generate description from file changes"""
        if len(files) == 1:
            file = files[0]
            filename = file.split("/")[-1]
            return f"update {filename}"

        # Multiple files
        scope = CommitStrategy._infer_scope(files)

        if scope:
            return f"update {scope} module"
        else:
            return f"update {len(files)} files"

    @staticmethod
    def merge_commits(
        commits: List[ConventionalCommit],
        title: str
    ) -> ConventionalCommit:
        """
        Merge multiple commits into one.

        Args:
            commits: List of commits to merge
            title: Title for merged commit

        Returns:
            Merged ConventionalCommit
        """
        # Use most common type
        type_counts = {}
        for commit in commits:
            type_counts[commit.type] = type_counts.get(commit.type, 0) + 1

        merged_type = max(type_counts.items(), key=lambda x: x[1])[0]

        # Collect all scopes
        scopes = [c.scope for c in commits if c.scope]
        scope = scopes[0] if scopes else None

        # Merge bodies
        body_parts = []
        for i, commit in enumerate(commits, 1):
            body_parts.append(f"{i}. {commit.description}")
            if commit.body:
                body_parts.append(f"   {commit.body}")

        # Collect all issues
        all_issues = []
        for commit in commits:
            all_issues.extend(commit.issues)

        # Check if any breaking
        breaking = any(c.breaking for c in commits)

        return ConventionalCommit(
            type=merged_type,
            description=title,
            scope=scope,
            body="\n".join(body_parts),
            breaking=breaking,
            issues=list(set(all_issues))  # Deduplicate
        )


def validate_commit_message(message: str) -> bool:
    """
    Validate conventional commit message format.

    Args:
        message: Commit message to validate

    Returns:
        True if valid
    """
    commit = ConventionalCommit.parse(message)
    return commit is not None


def format_commit_for_squash(commits: List[str], title: str) -> str:
    """
    Format multiple commit messages for squashing.

    Args:
        commits: List of commit messages
        title: Title for squashed commit

    Returns:
        Formatted squashed commit message
    """
    body_parts = []

    for i, commit in enumerate(commits, 1):
        # Extract first line as description
        first_line = commit.split("\n")[0]
        body_parts.append(f"{i}. {first_line}")

    body = "\n".join(body_parts)

    return f"{title}\n\n{body}"
