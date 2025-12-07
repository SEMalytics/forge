"""
Fix generation with pattern-based code repair

Generates targeted fixes that:
- Create fix prompts with context
- Apply relevant KF patterns
- Minimize code changes
- Preserve working functionality
- Generate descriptive commit messages
"""

import os
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from pathlib import Path

from forge.layers.failure_analyzer import FixSuggestion, Priority
from forge.knowledgeforge.pattern_store import PatternStore
from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class FixGenerationError(ForgeError):
    """Errors during fix generation"""
    pass


@dataclass
class GeneratedFix:
    """Generated fix with code changes"""
    suggestion: FixSuggestion
    file_changes: Dict[str, str]  # file_path -> new_content
    commit_message: str
    applied: bool = False
    success: bool = False


class FixGenerator:
    """
    Generate targeted code fixes.

    Features:
    - Context-aware fix generation
    - Pattern-based code repair
    - Minimal code changes
    - Preserve working code
    - Generate descriptive commits
    """

    def __init__(
        self,
        pattern_store: Optional[PatternStore] = None,
        use_ai: bool = True,
        api_key: Optional[str] = None
    ):
        """
        Initialize fix generator.

        Args:
            pattern_store: KnowledgeForge pattern store
            use_ai: Whether to use AI for fix generation
            api_key: API key for AI service (Anthropic)
        """
        self.pattern_store = pattern_store or PatternStore()
        self.use_ai = use_ai
        self.api_key = api_key or os.getenv('ANTHROPIC_API_KEY')

        logger.info(f"Initialized FixGenerator (AI={use_ai})")

    async def generate_fixes(
        self,
        suggestions: List[FixSuggestion],
        code_files: Dict[str, str],
        project_context: str = ""
    ) -> List[GeneratedFix]:
        """
        Generate fixes for suggestions.

        Args:
            suggestions: List of fix suggestions
            code_files: Current code files
            project_context: Project description

        Returns:
            List of generated fixes
        """
        logger.info(f"Generating fixes for {len(suggestions)} suggestions")

        fixes = []

        for suggestion in suggestions:
            try:
                fix = await self._generate_single_fix(
                    suggestion, code_files, project_context
                )
                fixes.append(fix)

            except Exception as e:
                logger.error(f"Failed to generate fix for {suggestion.root_cause}: {e}")

        logger.info(f"Generated {len(fixes)} fixes")
        return fixes

    async def _generate_single_fix(
        self,
        suggestion: FixSuggestion,
        code_files: Dict[str, str],
        project_context: str
    ) -> GeneratedFix:
        """Generate a single fix"""
        if self.use_ai and self.api_key:
            # Use AI to generate fix
            return await self._generate_ai_fix(
                suggestion, code_files, project_context
            )
        else:
            # Use pattern-based fix
            return self._generate_pattern_fix(
                suggestion, code_files
            )

    async def _generate_ai_fix(
        self,
        suggestion: FixSuggestion,
        code_files: Dict[str, str],
        project_context: str
    ) -> GeneratedFix:
        """Generate fix using AI"""
        from anthropic import AsyncAnthropic

        client = AsyncAnthropic(api_key=self.api_key)

        # Build fix prompt
        prompt = self._build_fix_prompt(
            suggestion, code_files, project_context
        )

        # Call Claude API
        try:
            response = await client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Parse response
            fix_content = response.content[0].text

            # Extract file changes
            file_changes = self._parse_ai_response(fix_content, code_files)

            # Generate commit message
            commit_message = self._extract_commit_message(fix_content, suggestion)

            return GeneratedFix(
                suggestion=suggestion,
                file_changes=file_changes,
                commit_message=commit_message
            )

        except Exception as e:
            logger.error(f"AI fix generation failed: {e}")
            # Fallback to pattern-based fix
            return self._generate_pattern_fix(suggestion, code_files)

    def _build_fix_prompt(
        self,
        suggestion: FixSuggestion,
        code_files: Dict[str, str],
        project_context: str
    ) -> str:
        """Build AI prompt for fix generation"""
        # Load relevant patterns
        patterns_text = ""
        if suggestion.relevant_patterns:
            patterns = []
            for pattern_name in suggestion.relevant_patterns:
                pattern = self.pattern_store.get_pattern_by_filename(pattern_name)
                if pattern:
                    patterns.append(pattern['content'][:500])  # Truncate

            if patterns:
                patterns_text = "\n\n".join(patterns)

        # Get affected files
        affected_files = {}
        for change in suggestion.code_changes:
            file_path = change.get('file', '')
            if file_path in code_files:
                affected_files[file_path] = code_files[file_path]

        # Build prompt
        prompt = f"""You are a code repair assistant. Your task is to fix the following issue:

**Project Context**: {project_context}

**Issue Type**: {suggestion.failure_type.value}
**Root Cause**: {suggestion.root_cause}
**Suggested Fix**: {suggestion.suggested_fix}
**Priority**: {suggestion.priority.value}

**Explanation**: {suggestion.explanation}

**Affected Files**:
```
{self._format_files(affected_files)}
```

**Relevant Patterns**:
```
{patterns_text}
```

Please provide:
1. Fixed code for each affected file
2. A descriptive commit message
3. Brief explanation of the changes

Format your response as:

## File: <path>
```<language>
<fixed code>
```

## Commit Message
<message>

## Explanation
<explanation>

IMPORTANT:
- Make minimal changes to fix the issue
- Preserve all working code
- Follow existing code style
- Add comments if needed
- Ensure changes are safe and tested
"""

        return prompt

    def _format_files(self, files: Dict[str, str]) -> str:
        """Format files for prompt"""
        result = []
        for path, content in files.items():
            result.append(f"=== {path} ===")
            result.append(content[:1000])  # Truncate for context
            result.append("")

        return "\n".join(result)

    def _parse_ai_response(
        self,
        response: str,
        original_files: Dict[str, str]
    ) -> Dict[str, str]:
        """Parse AI response to extract file changes"""
        import re

        file_changes = {}

        # Extract file sections
        file_pattern = r'## File: (.+?)\n```(?:\w+)?\n(.*?)\n```'
        matches = re.findall(file_pattern, response, re.DOTALL)

        for file_path, new_content in matches:
            file_path = file_path.strip()
            file_changes[file_path] = new_content.strip()

        return file_changes

    def _extract_commit_message(
        self, response: str, suggestion: FixSuggestion
    ) -> str:
        """Extract commit message from AI response"""
        import re

        # Try to extract commit message section
        match = re.search(r'## Commit Message\n(.+?)(?:\n##|$)', response, re.DOTALL)
        if match:
            return match.group(1).strip()

        # Fallback: generate from suggestion
        return self._generate_commit_message(suggestion)

    def _generate_pattern_fix(
        self,
        suggestion: FixSuggestion,
        code_files: Dict[str, str]
    ) -> GeneratedFix:
        """Generate fix using patterns (no AI)"""
        file_changes = {}

        # Apply suggested code changes
        for change in suggestion.code_changes:
            file_path = change.get('file', '')
            if file_path not in code_files:
                continue

            old_content = code_files[file_path]

            # Apply change
            if 'old' in change and 'new' in change:
                new_content = old_content.replace(
                    change['old'], change['new'], 1
                )
                file_changes[file_path] = new_content

        # Generate commit message
        commit_message = self._generate_commit_message(suggestion)

        return GeneratedFix(
            suggestion=suggestion,
            file_changes=file_changes,
            commit_message=commit_message
        )

    def _generate_commit_message(self, suggestion: FixSuggestion) -> str:
        """Generate commit message from suggestion"""
        # Format: <type>: <subject>
        #
        # <body>
        #
        # Fixes: <issue>

        type_map = {
            Priority.CRITICAL: 'fix(critical)',
            Priority.HIGH: 'fix',
            Priority.MEDIUM: 'fix',
            Priority.LOW: 'chore'
        }

        commit_type = type_map.get(suggestion.priority, 'fix')

        # Subject line (max 50 chars)
        subject = f"{commit_type}: {suggestion.suggested_fix[:40]}"

        # Body
        body = f"""{suggestion.root_cause}

{suggestion.explanation[:200]}

Type: {suggestion.failure_type.value}
Priority: {suggestion.priority.value}
Confidence: {suggestion.confidence:.0%}
"""

        # Add patterns reference
        if suggestion.relevant_patterns:
            body += f"\nPatterns: {', '.join(suggestion.relevant_patterns[:3])}"

        # Full message
        commit_message = f"{subject}\n\n{body}"

        return commit_message

    async def apply_fix(
        self,
        fix: GeneratedFix,
        output_dir: Path
    ) -> bool:
        """
        Apply fix to files.

        Args:
            fix: Fix to apply
            output_dir: Directory containing files

        Returns:
            True if successful
        """
        try:
            first_line = fix.commit_message.split('\n')[0]
            logger.info(f"Applying fix: {first_line}")

            # Write file changes
            for file_path, new_content in fix.file_changes.items():
                full_path = output_dir / file_path

                # Create directories if needed
                full_path.parent.mkdir(parents=True, exist_ok=True)

                # Write file
                full_path.write_text(new_content)

                logger.debug(f"Updated {file_path}")

            fix.applied = True
            fix.success = True

            logger.info("Fix applied successfully")
            return True

        except Exception as e:
            logger.error(f"Failed to apply fix: {e}")
            fix.applied = True
            fix.success = False
            return False

    def rollback_fix(
        self,
        fix: GeneratedFix,
        original_files: Dict[str, str],
        output_dir: Path
    ) -> bool:
        """
        Rollback a fix.

        Args:
            fix: Fix to rollback
            original_files: Original file contents
            output_dir: Directory containing files

        Returns:
            True if successful
        """
        try:
            logger.info("Rolling back fix")

            for file_path in fix.file_changes.keys():
                if file_path in original_files:
                    full_path = output_dir / file_path
                    full_path.write_text(original_files[file_path])

            fix.applied = False
            logger.info("Fix rolled back")
            return True

        except Exception as e:
            logger.error(f"Failed to rollback fix: {e}")
            return False

    def prioritize_fixes(
        self, fixes: List[GeneratedFix]
    ) -> List[GeneratedFix]:
        """
        Prioritize fixes by impact and confidence.

        Args:
            fixes: List of fixes

        Returns:
            Prioritized list
        """
        # Sort by priority (critical first) and confidence (high first)
        return sorted(
            fixes,
            key=lambda f: (
                ['critical', 'high', 'medium', 'low'].index(f.suggestion.priority.value),
                -f.suggestion.confidence
            )
        )

    def estimate_impact(self, fix: GeneratedFix) -> str:
        """
        Estimate impact of fix.

        Args:
            fix: Fix to evaluate

        Returns:
            Impact description
        """
        file_count = len(fix.file_changes)
        lines_changed = sum(
            len(content.split('\n'))
            for content in fix.file_changes.values()
        )

        if file_count == 0:
            return "No changes"
        elif file_count == 1 and lines_changed < 10:
            return "Minimal impact (1 file, <10 lines)"
        elif file_count <= 3 and lines_changed < 50:
            return f"Low impact ({file_count} files, {lines_changed} lines)"
        elif file_count <= 5 and lines_changed < 100:
            return f"Medium impact ({file_count} files, {lines_changed} lines)"
        else:
            return f"High impact ({file_count} files, {lines_changed} lines)"

    def close(self):
        """Close pattern store"""
        if self.pattern_store:
            self.pattern_store.close()
