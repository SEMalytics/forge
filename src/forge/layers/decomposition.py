"""
Intelligent task decomposition using KnowledgeForge patterns

Combines Compound Engineering planning with KnowledgeForge pattern matching
to create optimized, pattern-backed task breakdowns.
"""

from typing import List, Dict, Optional, Any
from pathlib import Path

from forge.knowledgeforge.pattern_store import PatternStore
from forge.integrations.compound_engineering import (
    CompoundEngineeringClient,
    Task,
    CompoundEngineeringError
)
from forge.core.state_manager import StateManager
from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class DecompositionError(ForgeError):
    """Errors during task decomposition"""
    pass


class TaskDecomposer:
    """
    Intelligent task decomposition combining CE patterns with KF knowledge.

    Breaks down projects into optimal tasks and enriches them with
    relevant KnowledgeForge patterns for implementation guidance.
    """

    def __init__(
        self,
        pattern_store: Optional[PatternStore] = None,
        ce_client: Optional[CompoundEngineeringClient] = None,
        state_manager: Optional[StateManager] = None
    ):
        """
        Initialize task decomposer.

        Args:
            pattern_store: PatternStore instance (creates new if None)
            ce_client: CompoundEngineeringClient instance (creates new if None)
            state_manager: StateManager instance (creates new if None)
        """
        self.pattern_store = pattern_store or PatternStore()
        self.ce_client = ce_client or CompoundEngineeringClient()
        self.state_manager = state_manager or StateManager()

        logger.info("TaskDecomposer initialized")

    def decompose(
        self,
        project_description: str,
        tech_stack: Optional[List[str]] = None,
        project_id: Optional[str] = None
    ) -> List[Task]:
        """
        Break project into optimal tasks with KF pattern enrichment.

        Args:
            project_description: Description of the project to decompose
            tech_stack: Optional list of technologies being used
            project_id: Optional project ID to save decomposition to

        Returns:
            List of Task objects with KF patterns attached

        Raises:
            DecompositionError: If decomposition fails
        """
        try:
            logger.info(f"Decomposing project: {project_description[:100]}...")

            # Step 1: Get relevant KF patterns
            logger.debug("Searching for relevant KF patterns...")
            search_query = self._build_pattern_search_query(project_description, tech_stack)
            patterns = self.pattern_store.search(search_query, max_results=15, method='hybrid')

            logger.info(f"Found {len(patterns)} relevant KF patterns")

            # Step 2: Generate task breakdown using CE
            logger.debug("Generating task breakdown with CE...")
            tasks = self.ce_client.plan(project_description, tech_stack)

            logger.info(f"Generated {len(tasks)} tasks")

            # Step 3: Enrich tasks with KF patterns
            logger.debug("Enriching tasks with KF patterns...")
            for task in tasks:
                task.kf_patterns = self._find_relevant_patterns(task, patterns, tech_stack)

            # Step 4: Validate task structure
            logger.debug("Validating task dependencies...")
            if not self.ce_client.validate_task_dependencies(tasks):
                raise DecompositionError("Invalid task dependencies detected")

            # Step 5: Save to project if project_id provided
            if project_id:
                self._save_decomposition(project_id, tasks, patterns)

            logger.info(f"Successfully decomposed project into {len(tasks)} tasks")
            return tasks

        except CompoundEngineeringError as e:
            logger.error(f"CE planning failed: {e}")
            raise DecompositionError(f"Failed to generate task breakdown: {e}")
        except Exception as e:
            logger.error(f"Decomposition failed: {e}")
            raise DecompositionError(f"Failed to decompose project: {e}")

    def _build_pattern_search_query(
        self,
        description: str,
        tech_stack: Optional[List[str]] = None
    ) -> str:
        """
        Build optimized search query for KF patterns.

        Combines project description with tech stack to find most relevant patterns.
        """
        query_parts = [description]

        if tech_stack:
            query_parts.append(" ".join(tech_stack))

        # Add common architectural terms
        keywords = [
            "implementation", "architecture", "testing",
            "deployment", "best practices", "patterns"
        ]

        query = " ".join(query_parts)

        # Add relevant keywords if not already in description
        for keyword in keywords:
            if keyword not in query.lower():
                query += f" {keyword}"

        return query

    def _find_relevant_patterns(
        self,
        task: Task,
        patterns: List[Dict[str, Any]],
        tech_stack: Optional[List[str]] = None
    ) -> List[str]:
        """
        Find KF patterns relevant to a specific task.

        Uses multiple relevance signals:
        - Task title and description matching
        - Tech stack alignment
        - Task type (setup, implementation, testing, etc.)
        - Pattern score from initial search
        """
        relevant = []

        task_text = f"{task.title} {task.description}".lower()
        task_tags = set(task.tags)

        for pattern in patterns:
            relevance_score = 0

            # Check filename/title relevance
            filename = pattern.get('filename', '').lower()
            title = pattern.get('title', '').lower()

            # Direct keyword matches
            keywords = self._extract_task_keywords(task)
            for keyword in keywords:
                if keyword in filename or keyword in title:
                    relevance_score += 2

            # Tech stack alignment
            if tech_stack:
                content = pattern.get('content', '').lower()
                for tech in tech_stack:
                    if tech.lower() in content:
                        relevance_score += 1

            # Task type matching
            pattern_categories = self._categorize_pattern(pattern)
            if task_tags & pattern_categories:
                relevance_score += 3

            # Use pattern's search score
            if pattern.get('score', 0) > 0.7:
                relevance_score += 2

            # Add pattern if relevant
            if relevance_score >= 3:
                relevant.append(pattern['filename'])

        # Limit to top 3 most relevant patterns per task
        return relevant[:3]

    def _extract_task_keywords(self, task: Task) -> List[str]:
        """
        Extract key terms from task for pattern matching.
        """
        text = f"{task.title} {task.description}".lower()

        # Common keywords to look for
        technical_keywords = [
            "api", "database", "auth", "authentication", "test", "testing",
            "deploy", "deployment", "setup", "config", "configuration",
            "security", "validation", "error handling", "logging",
            "caching", "optimization", "performance", "scalability",
            "documentation", "monitoring", "ci/cd", "integration"
        ]

        found_keywords = []
        for keyword in technical_keywords:
            if keyword in text:
                found_keywords.append(keyword)

        # Also add task tags
        found_keywords.extend(task.tags)

        return list(set(found_keywords))

    def _categorize_pattern(self, pattern: Dict[str, Any]) -> set:
        """
        Categorize a KF pattern based on its content.

        Returns set of category tags like 'setup', 'testing', 'deployment', etc.
        """
        categories = set()

        filename = pattern.get('filename', '').lower()
        title = pattern.get('title', '').lower()
        content = pattern.get('content', '')[:500].lower()  # First 500 chars

        full_text = f"{filename} {title} {content}"

        # Category mappings
        category_keywords = {
            'setup': ['setup', 'initialization', 'bootstrap', 'scaffold'],
            'implementation': ['implement', 'build', 'create', 'develop', 'code'],
            'testing': ['test', 'qa', 'quality', 'validation', 'assert'],
            'deployment': ['deploy', 'production', 'release', 'ci/cd', 'pipeline'],
            'documentation': ['docs', 'documentation', 'readme', 'guide'],
            'architecture': ['architecture', 'design', 'structure', 'pattern'],
            'security': ['security', 'auth', 'authentication', 'authorization'],
            'performance': ['performance', 'optimization', 'caching', 'scaling'],
            'database': ['database', 'sql', 'migration', 'schema', 'data'],
            'api': ['api', 'rest', 'graphql', 'endpoint', 'route'],
            'frontend': ['frontend', 'ui', 'interface', 'component', 'view'],
            'backend': ['backend', 'server', 'service', 'business logic']
        }

        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in full_text:
                    categories.add(category)
                    break

        return categories

    def _save_decomposition(
        self,
        project_id: str,
        tasks: List[Task],
        patterns: List[Dict[str, Any]]
    ):
        """
        Save decomposition to project state.

        Args:
            project_id: Project ID to save to
            tasks: List of tasks to save
            patterns: List of patterns used
        """
        try:
            # Convert tasks to dict format
            tasks_data = [task.to_dict() for task in tasks]

            # Save as checkpoint
            self.state_manager.checkpoint(
                project_id=project_id,
                stage="decomposition",
                state={
                    "tasks": tasks_data,
                    "task_count": len(tasks),
                    "patterns_used": [p.get('filename') for p in patterns],
                    "pattern_count": len(patterns)
                },
                description=f"Task decomposition completed: {len(tasks)} tasks generated"
            )

            # Also create tasks in state manager
            for task in tasks:
                self.state_manager.create_task(
                    project_id=project_id,
                    task_id=task.id,
                    title=task.title,
                    description=task.description,
                    dependencies=task.dependencies,
                    metadata={
                        "kf_patterns": task.kf_patterns,
                        "complexity": task.estimated_complexity,
                        "acceptance_criteria": task.acceptance_criteria,
                        "tags": task.tags
                    }
                )

            logger.info(f"Saved decomposition for project {project_id}")

        except Exception as e:
            logger.error(f"Failed to save decomposition: {e}")
            # Don't fail the whole decomposition if save fails
            pass

    def get_task_summary(self, tasks: List[Task]) -> Dict[str, Any]:
        """
        Generate summary statistics for a task list.

        Args:
            tasks: List of tasks to summarize

        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total_tasks": len(tasks),
            "by_priority": {},
            "by_complexity": {},
            "by_tag": {},
            "total_patterns": 0,
            "avg_dependencies": 0,
            "max_dependency_depth": 0
        }

        # Count by priority
        for task in tasks:
            priority = f"priority_{task.priority}"
            summary["by_priority"][priority] = summary["by_priority"].get(priority, 0) + 1

            # Count by complexity
            complexity = task.estimated_complexity
            summary["by_complexity"][complexity] = summary["by_complexity"].get(complexity, 0) + 1

            # Count by tag
            for tag in task.tags:
                summary["by_tag"][tag] = summary["by_tag"].get(tag, 0) + 1

            # Count patterns
            summary["total_patterns"] += len(task.kf_patterns)

        # Calculate average dependencies
        if tasks:
            total_deps = sum(len(t.dependencies) for t in tasks)
            summary["avg_dependencies"] = total_deps / len(tasks)

        # Calculate max dependency depth
        summary["max_dependency_depth"] = self._calculate_max_depth(tasks)

        return summary

    def _calculate_max_depth(self, tasks: List[Task]) -> int:
        """
        Calculate maximum dependency depth (longest chain).
        """
        task_map = {t.id: t for t in tasks}
        memo = {}

        def depth(task_id: str) -> int:
            if task_id in memo:
                return memo[task_id]

            task = task_map.get(task_id)
            if not task or not task.dependencies:
                memo[task_id] = 0
                return 0

            max_dep_depth = max(depth(dep) for dep in task.dependencies)
            memo[task_id] = max_dep_depth + 1
            return max_dep_depth + 1

        if not tasks:
            return 0

        return max(depth(t.id) for t in tasks)

    def visualize_dependency_graph(self, tasks: List[Task]) -> str:
        """
        Generate simple text visualization of task dependencies.

        Args:
            tasks: List of tasks to visualize

        Returns:
            Text representation of dependency graph
        """
        lines = ["Task Dependency Graph", "=" * 50, ""]

        # Get tasks in execution order
        ordered_tasks = self.ce_client.get_task_execution_order(tasks)

        for task in ordered_tasks:
            indent = len(task.dependencies) * 2
            prefix = " " * indent + "└─ " if indent > 0 else ""

            lines.append(f"{prefix}{task.id}: {task.title}")

            if task.dependencies:
                dep_str = ", ".join(task.dependencies)
                lines.append(f"{' ' * (indent + 3)}[depends on: {dep_str}]")

            if task.kf_patterns:
                pattern_str = ", ".join(task.kf_patterns)
                lines.append(f"{' ' * (indent + 3)}[patterns: {pattern_str}]")

            lines.append("")

        return "\n".join(lines)

    def close(self):
        """Close state manager connection"""
        if self.state_manager:
            self.state_manager.close()
