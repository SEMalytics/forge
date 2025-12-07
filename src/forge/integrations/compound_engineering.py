"""
Compound Engineering integration for task planning

Provides intelligent task decomposition using CE patterns or fallback to basic planning.
"""

import subprocess
import json
import re
from typing import List, Dict, Optional, Any
from dataclasses import dataclass, field
from pathlib import Path

from forge.utils.logger import logger
from forge.utils.errors import ForgeError


class CompoundEngineeringError(ForgeError):
    """Errors during Compound Engineering integration"""
    pass


@dataclass
class Task:
    """
    Represents a decomposed task with dependencies and metadata.

    Attributes:
        id: Unique task identifier (e.g., "task-001")
        title: Brief task title
        description: Detailed task description
        dependencies: List of task IDs this task depends on
        priority: Task priority (1=highest)
        kf_patterns: KnowledgeForge patterns relevant to this task
        estimated_complexity: Complexity estimate (low, medium, high)
        acceptance_criteria: List of criteria for task completion
        tags: List of tags for categorization
    """
    id: str
    title: str
    description: str
    dependencies: List[str] = field(default_factory=list)
    priority: int = 1
    kf_patterns: List[str] = field(default_factory=list)
    estimated_complexity: str = "medium"
    acceptance_criteria: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert task to dictionary format"""
        return {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "dependencies": self.dependencies,
            "priority": self.priority,
            "kf_patterns": self.kf_patterns,
            "estimated_complexity": self.estimated_complexity,
            "acceptance_criteria": self.acceptance_criteria,
            "tags": self.tags
        }


class CompoundEngineeringClient:
    """
    Client for Compound Engineering plugin integration.

    Attempts to use Claude Code CE plugin for planning, falls back
    to basic planning if CE is unavailable.
    """

    def __init__(self, ce_plugin_path: Optional[Path] = None):
        """
        Initialize CE client.

        Args:
            ce_plugin_path: Path to CE plugin directory (defaults to ../compound-engineering)
        """
        if ce_plugin_path is None:
            # Default to sibling directory
            ce_plugin_path = Path(__file__).parent.parent.parent.parent.parent / "compound-engineering"

        self.ce_plugin_path = Path(ce_plugin_path)
        self.ce_available = self._check_ce_availability()

        if self.ce_available:
            logger.info(f"Compound Engineering plugin found at {self.ce_plugin_path}")
        else:
            logger.warning("CE plugin not available, using fallback planning")

    def _check_ce_availability(self) -> bool:
        """Check if CE plugin is available"""
        try:
            # Check if CE plugin directory exists
            if not self.ce_plugin_path.exists():
                return False

            # Check for key CE files
            plan_file = self.ce_plugin_path / "plugins" / "compound-engineering" / "commands" / "workflows" / "plan.md"
            return plan_file.exists()
        except Exception as e:
            logger.debug(f"CE availability check failed: {e}")
            return False

    def plan(self, project_description: str, tech_stack: Optional[List[str]] = None) -> List[Task]:
        """
        Generate project plan using CE plugin or fallback.

        Args:
            project_description: Description of the project to plan
            tech_stack: Optional list of technologies being used

        Returns:
            List of Task objects representing the project plan

        Raises:
            CompoundEngineeringError: If planning fails
        """
        try:
            # Try CE-style planning first
            if self.ce_available:
                logger.info("Attempting CE-style planning...")
                tasks = self._ce_style_plan(project_description, tech_stack)
                if tasks:
                    return tasks

            # Fallback to basic planning
            logger.info("Using basic planning fallback")
            return self._basic_plan(project_description, tech_stack)

        except Exception as e:
            logger.error(f"Planning failed: {e}")
            raise CompoundEngineeringError(f"Failed to generate plan: {e}")

    def _ce_style_plan(self, description: str, tech_stack: Optional[List[str]] = None) -> List[Task]:
        """
        Generate plan following CE patterns.

        CE planning follows a structured approach:
        1. Repository research and context gathering
        2. Issue planning and structure
        3. Technical analysis
        4. Task decomposition

        This method emulates CE patterns without requiring Claude Code.
        """
        tasks = []

        # Phase 1: Setup and Infrastructure
        tasks.append(Task(
            id="task-001",
            title="Project Setup and Infrastructure",
            description=f"Initialize project structure for: {description}",
            dependencies=[],
            priority=1,
            estimated_complexity="low",
            acceptance_criteria=[
                "Project directory structure created",
                "Dependencies configured",
                "Development environment set up",
                "Version control initialized"
            ],
            tags=["setup", "infrastructure"]
        ))

        # Phase 2: Core Implementation
        # Analyze description to identify core features
        core_features = self._extract_core_features(description)

        for idx, feature in enumerate(core_features, start=2):
            tasks.append(Task(
                id=f"task-{idx:03d}",
                title=f"Implement {feature}",
                description=f"Build core functionality for {feature}",
                dependencies=["task-001"],  # Depends on setup
                priority=2,
                estimated_complexity="medium",
                acceptance_criteria=[
                    f"{feature} implemented",
                    "Unit tests added",
                    "Integration tests passing",
                    "Documentation updated"
                ],
                tags=["feature", "core"]
            ))

        # Phase 3: Testing and Quality
        next_id = len(tasks) + 1
        tasks.append(Task(
            id=f"task-{next_id:03d}",
            title="Testing and Quality Assurance",
            description="Comprehensive testing and quality checks",
            dependencies=[t.id for t in tasks if "feature" in t.tags],  # Depends on all features
            priority=3,
            estimated_complexity="medium",
            acceptance_criteria=[
                "All tests passing",
                "Code coverage >80%",
                "Linting checks pass",
                "Security scan clean"
            ],
            tags=["testing", "qa"]
        ))

        # Phase 4: Documentation and Deployment
        next_id += 1
        tasks.append(Task(
            id=f"task-{next_id:03d}",
            title="Documentation and Deployment",
            description="Finalize documentation and prepare for deployment",
            dependencies=[f"task-{next_id-1:03d}"],  # Depends on testing
            priority=4,
            estimated_complexity="low",
            acceptance_criteria=[
                "README complete",
                "API documentation generated",
                "Deployment guide written",
                "CI/CD pipeline configured"
            ],
            tags=["documentation", "deployment"]
        ))

        logger.info(f"Generated {len(tasks)} tasks using CE-style planning")
        return tasks

    def _extract_core_features(self, description: str) -> List[str]:
        """
        Extract core features from project description.

        Uses simple heuristics to identify features:
        - Look for keywords like "with", "and", "including"
        - Extract noun phrases
        - Identify action verbs
        """
        features = []

        # Common feature keywords
        feature_keywords = [
            "authentication", "auth", "login", "user management",
            "api", "rest api", "graphql", "database", "storage",
            "search", "filtering", "sorting", "pagination",
            "notifications", "email", "messaging", "chat",
            "payment", "billing", "subscription", "checkout",
            "analytics", "reporting", "dashboard", "metrics",
            "upload", "download", "export", "import",
            "admin", "moderation", "review", "approval"
        ]

        description_lower = description.lower()

        # Extract features mentioned in description
        for keyword in feature_keywords:
            if keyword in description_lower:
                # Capitalize properly
                feature_name = keyword.title().replace("Api", "API")
                features.append(feature_name)

        # If no features found, create generic core feature
        if not features:
            features = ["Core Functionality", "Data Layer", "Business Logic"]

        # Limit to reasonable number of core features
        return features[:5]

    def _basic_plan(self, description: str, tech_stack: Optional[List[str]] = None) -> List[Task]:
        """
        Basic fallback planning without CE.

        Creates a simple 5-phase plan:
        1. Project setup
        2. Core implementation
        3. Testing
        4. Documentation
        5. Deployment
        """
        tech_str = f" using {', '.join(tech_stack)}" if tech_stack else ""

        tasks = [
            Task(
                id="task-001",
                title="Project Setup",
                description=f"Initialize project structure for: {description}{tech_str}",
                dependencies=[],
                priority=1,
                estimated_complexity="low",
                acceptance_criteria=[
                    "Project initialized",
                    "Dependencies installed",
                    "Development environment configured"
                ],
                tags=["setup"]
            ),
            Task(
                id="task-002",
                title="Core Implementation",
                description=f"Implement core functionality: {description}",
                dependencies=["task-001"],
                priority=2,
                estimated_complexity="high",
                acceptance_criteria=[
                    "Core features implemented",
                    "Basic tests added",
                    "Code follows conventions"
                ],
                tags=["implementation", "core"]
            ),
            Task(
                id="task-003",
                title="Testing and Validation",
                description="Add comprehensive tests and validation",
                dependencies=["task-002"],
                priority=3,
                estimated_complexity="medium",
                acceptance_criteria=[
                    "Unit tests complete",
                    "Integration tests added",
                    "Test coverage >70%"
                ],
                tags=["testing"]
            ),
            Task(
                id="task-004",
                title="Documentation",
                description="Write project documentation",
                dependencies=["task-002"],
                priority=4,
                estimated_complexity="low",
                acceptance_criteria=[
                    "README written",
                    "API docs generated",
                    "Usage examples added"
                ],
                tags=["documentation"]
            ),
            Task(
                id="task-005",
                title="Deployment Preparation",
                description="Prepare for production deployment",
                dependencies=["task-003", "task-004"],
                priority=5,
                estimated_complexity="medium",
                acceptance_criteria=[
                    "CI/CD configured",
                    "Deployment guide written",
                    "Monitoring set up"
                ],
                tags=["deployment"]
            )
        ]

        logger.info(f"Generated {len(tasks)} tasks using basic planning")
        return tasks

    def _parse_plan_output(self, output: str) -> List[Task]:
        """
        Parse CE plan output into Task objects.

        CE plans are typically in markdown format with sections for:
        - Tasks/Issues
        - Acceptance Criteria
        - Technical Approach
        - Dependencies
        """
        tasks = []

        # Try to extract tasks from markdown structure
        # This is a simplified parser for demonstration
        task_pattern = r'##\s+Task\s+(\d+):\s+(.+?)(?=##|$)'
        matches = re.finditer(task_pattern, output, re.DOTALL)

        for match in matches:
            task_num = match.group(1)
            task_content = match.group(2)

            # Extract title (first line)
            lines = task_content.strip().split('\n')
            title = lines[0].strip() if lines else f"Task {task_num}"

            # Extract description
            description = '\n'.join(lines[1:]).strip() if len(lines) > 1 else ""

            tasks.append(Task(
                id=f"task-{int(task_num):03d}",
                title=title,
                description=description,
                dependencies=[],
                priority=int(task_num)
            ))

        return tasks if tasks else self._basic_plan("Project from CE output")

    def validate_task_dependencies(self, tasks: List[Task]) -> bool:
        """
        Validate that task dependencies form a valid DAG (no cycles).

        Args:
            tasks: List of tasks to validate

        Returns:
            True if dependencies are valid, False if circular dependencies detected
        """
        task_ids = {task.id for task in tasks}

        # Check all dependencies exist
        for task in tasks:
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    logger.warning(f"Task {task.id} has invalid dependency: {dep_id}")
                    return False

        # Check for cycles using DFS
        visited = set()
        rec_stack = set()

        def has_cycle(task_id: str) -> bool:
            visited.add(task_id)
            rec_stack.add(task_id)

            # Get task
            task = next((t for t in tasks if t.id == task_id), None)
            if not task:
                return False

            # Check all dependencies
            for dep_id in task.dependencies:
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    logger.error(f"Circular dependency detected: {task_id} -> {dep_id}")
                    return True

            rec_stack.remove(task_id)
            return False

        # Check each task
        for task in tasks:
            if task.id not in visited:
                if has_cycle(task.id):
                    return False

        return True

    def get_task_execution_order(self, tasks: List[Task]) -> List[Task]:
        """
        Get tasks in execution order (topological sort).

        Args:
            tasks: List of tasks to sort

        Returns:
            Tasks sorted in valid execution order
        """
        if not self.validate_task_dependencies(tasks):
            raise CompoundEngineeringError("Invalid task dependencies - circular dependency detected")

        # Topological sort using Kahn's algorithm
        in_degree = {task.id: 0 for task in tasks}
        task_map = {task.id: task for task in tasks}

        # Calculate in-degrees
        for task in tasks:
            for dep in task.dependencies:
                in_degree[task.id] += 1

        # Queue of tasks with no dependencies
        queue = [task for task in tasks if in_degree[task.id] == 0]
        result = []

        while queue:
            # Sort by priority within same level
            queue.sort(key=lambda t: t.priority)
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree for dependent tasks
            for task in tasks:
                if current.id in task.dependencies:
                    in_degree[task.id] -= 1
                    if in_degree[task.id] == 0:
                        queue.append(task)

        if len(result) != len(tasks):
            raise CompoundEngineeringError("Failed to sort tasks - possible circular dependency")

        return result
