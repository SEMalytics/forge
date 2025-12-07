"""
Project and task state management with SQLite + checkpoints
"""

import sqlite3
from datetime import datetime
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
from pathlib import Path
from forge.utils.logger import logger
from forge.utils.errors import StateError


@dataclass
class ProjectState:
    """Project state representation"""
    id: str
    name: str
    description: str
    stage: str  # 'planning', 'decomposition', 'generation', 'testing', 'review', 'deployment', 'complete'
    created_at: datetime
    updated_at: datetime
    metadata: Dict[str, Any]


@dataclass
class TaskState:
    """Task state representation"""
    id: str
    project_id: str
    title: str
    status: str  # 'pending', 'in_progress', 'complete', 'failed'
    priority: int
    dependencies: List[str]
    generated_files: Dict[str, str]
    test_results: Optional[Dict]
    commits: List[str]
    duration_seconds: float = 0.0
    error: Optional[str] = None


@dataclass
class Checkpoint:
    """Checkpoint for recovery"""
    id: int
    project_id: str
    stage: str
    timestamp: datetime
    state_snapshot: Dict[str, Any]
    description: str


class StateManager:
    """Manage project state with checkpoints and recovery"""

    def __init__(self, db_path: str = ".forge/state.db"):
        """
        Initialize state manager

        Args:
            db_path: Path to SQLite database
        """
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            self.conn = sqlite3.connect(db_path)
            self.conn.row_factory = sqlite3.Row
            self._setup_database()
        except Exception as e:
            raise StateError(f"Failed to initialize state database: {e}")

    def _setup_database(self):
        """Create tables for state management"""
        self.conn.executescript("""
            -- Projects table
            CREATE TABLE IF NOT EXISTS projects (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                stage TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT  -- JSON
            );

            -- Tasks table
            CREATE TABLE IF NOT EXISTS tasks (
                id TEXT PRIMARY KEY,
                project_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT NOT NULL,
                priority INTEGER,
                dependencies TEXT,  -- JSON array
                generated_files TEXT,  -- JSON object
                test_results TEXT,  -- JSON object
                commits TEXT,  -- JSON array
                duration_seconds REAL,
                error TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            -- Checkpoints table for recovery
            CREATE TABLE IF NOT EXISTS checkpoints (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                stage TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                state_snapshot TEXT NOT NULL,  -- JSON
                description TEXT,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            -- Test results table
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                task_id TEXT NOT NULL,
                test_type TEXT NOT NULL,  -- 'unit', 'integration', 'security', 'performance'
                passed INTEGER NOT NULL,
                failed INTEGER NOT NULL,
                coverage_percent REAL,
                duration_seconds REAL,
                details TEXT,  -- JSON
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (task_id) REFERENCES tasks(id)
            );

            -- Review results table
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                project_id TEXT NOT NULL,
                approved INTEGER NOT NULL,
                agent_approvals TEXT NOT NULL,  -- JSON object
                issues TEXT NOT NULL,  -- JSON array
                feedback TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (project_id) REFERENCES projects(id)
            );

            -- Indexes for performance
            CREATE INDEX IF NOT EXISTS idx_tasks_project
                ON tasks(project_id);
            CREATE INDEX IF NOT EXISTS idx_tasks_status
                ON tasks(status);
            CREATE INDEX IF NOT EXISTS idx_checkpoints_project
                ON checkpoints(project_id);
        """)
        self.conn.commit()

    def create_project(
        self,
        project_id: str,
        name: str,
        description: str,
        metadata: Optional[Dict] = None
    ) -> ProjectState:
        """
        Create new project

        Args:
            project_id: Unique project identifier
            name: Project name
            description: Project description
            metadata: Optional metadata

        Returns:
            Created project state
        """
        now = datetime.now()

        try:
            self.conn.execute("""
                INSERT INTO projects (id, name, description, stage, created_at, updated_at, metadata)
                VALUES (?, ?, ?, 'planning', ?, ?, ?)
            """, (
                project_id,
                name,
                description,
                now,
                now,
                json.dumps(metadata or {})
            ))
            self.conn.commit()

            logger.info(f"Created project: {project_id}")

            return ProjectState(
                id=project_id,
                name=name,
                description=description,
                stage='planning',
                created_at=now,
                updated_at=now,
                metadata=metadata or {}
            )
        except Exception as e:
            raise StateError(f"Failed to create project: {e}")

    def get_project(self, project_id: str) -> Optional[ProjectState]:
        """
        Get project by ID

        Args:
            project_id: Project identifier

        Returns:
            Project state or None if not found
        """
        cursor = self.conn.execute("""
            SELECT id, name, description, stage, created_at, updated_at, metadata
            FROM projects
            WHERE id = ?
        """, (project_id,))

        row = cursor.fetchone()
        if row:
            return ProjectState(
                id=row['id'],
                name=row['name'],
                description=row['description'],
                stage=row['stage'],
                created_at=datetime.fromisoformat(row['created_at']),
                updated_at=datetime.fromisoformat(row['updated_at']),
                metadata=json.loads(row['metadata'])
            )
        return None

    def update_project_stage(self, project_id: str, stage: str):
        """
        Update project stage

        Args:
            project_id: Project identifier
            stage: New stage
        """
        self.conn.execute("""
            UPDATE projects
            SET stage = ?, updated_at = ?
            WHERE id = ?
        """, (stage, datetime.now(), project_id))
        self.conn.commit()

        logger.info(f"Updated project {project_id} to stage: {stage}")

    def create_task(self, task: TaskState):
        """
        Create new task

        Args:
            task: Task state to create
        """
        try:
            self.conn.execute("""
                INSERT INTO tasks
                (id, project_id, title, status, priority, dependencies,
                 generated_files, test_results, commits, duration_seconds, error)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                task.id,
                task.project_id,
                task.title,
                task.status,
                task.priority,
                json.dumps(task.dependencies),
                json.dumps(task.generated_files),
                json.dumps(task.test_results) if task.test_results else None,
                json.dumps(task.commits),
                task.duration_seconds,
                task.error
            ))
            self.conn.commit()
        except Exception as e:
            raise StateError(f"Failed to create task: {e}")

    def update_task_status(
        self,
        task_id: str,
        status: str,
        generated_files: Optional[Dict] = None,
        duration: Optional[float] = None,
        error: Optional[str] = None
    ):
        """
        Update task status

        Args:
            task_id: Task identifier
            status: New status
            generated_files: Optional generated files
            duration: Optional duration in seconds
            error: Optional error message
        """
        updates = ["status = ?"]
        params = [status]

        if generated_files is not None:
            updates.append("generated_files = ?")
            params.append(json.dumps(generated_files))

        if duration is not None:
            updates.append("duration_seconds = ?")
            params.append(duration)

        if error is not None:
            updates.append("error = ?")
            params.append(error)

        params.append(task_id)

        self.conn.execute(f"""
            UPDATE tasks
            SET {', '.join(updates)}
            WHERE id = ?
        """, params)
        self.conn.commit()

    def get_project_tasks(self, project_id: str) -> List[TaskState]:
        """
        Get all tasks for a project

        Args:
            project_id: Project identifier

        Returns:
            List of task states
        """
        cursor = self.conn.execute("""
            SELECT id, project_id, title, status, priority, dependencies,
                   generated_files, test_results, commits, duration_seconds, error
            FROM tasks
            WHERE project_id = ?
            ORDER BY priority
        """, (project_id,))

        tasks = []
        for row in cursor.fetchall():
            tasks.append(TaskState(
                id=row['id'],
                project_id=row['project_id'],
                title=row['title'],
                status=row['status'],
                priority=row['priority'],
                dependencies=json.loads(row['dependencies']),
                generated_files=json.loads(row['generated_files']) if row['generated_files'] else {},
                test_results=json.loads(row['test_results']) if row['test_results'] else None,
                commits=json.loads(row['commits']),
                duration_seconds=row['duration_seconds'] or 0.0,
                error=row['error']
            ))

        return tasks

    def checkpoint(
        self,
        project_id: str,
        stage: str,
        state: Dict[str, Any],
        description: str
    ):
        """
        Create checkpoint for recovery

        Args:
            project_id: Project identifier
            stage: Current stage
            state: State snapshot
            description: Checkpoint description
        """
        self.conn.execute("""
            INSERT INTO checkpoints (project_id, stage, state_snapshot, description)
            VALUES (?, ?, ?, ?)
        """, (
            project_id,
            stage,
            json.dumps(state, default=str),
            description
        ))
        self.conn.commit()

        logger.info(f"Created checkpoint for {project_id}: {stage}")

    def get_latest_checkpoint(self, project_id: str) -> Optional[Checkpoint]:
        """
        Get latest checkpoint for recovery

        Args:
            project_id: Project identifier

        Returns:
            Latest checkpoint or None
        """
        cursor = self.conn.execute("""
            SELECT id, project_id, stage, timestamp, state_snapshot, description
            FROM checkpoints
            WHERE project_id = ?
            ORDER BY timestamp DESC
            LIMIT 1
        """, (project_id,))

        row = cursor.fetchone()
        if row:
            return Checkpoint(
                id=row['id'],
                project_id=row['project_id'],
                stage=row['stage'],
                timestamp=datetime.fromisoformat(row['timestamp']),
                state_snapshot=json.loads(row['state_snapshot']),
                description=row['description']
            )
        return None

    def save_test_results(
        self,
        task_id: str,
        test_type: str,
        passed: int,
        failed: int,
        coverage: Optional[float] = None,
        duration: Optional[float] = None,
        details: Optional[Dict] = None
    ):
        """
        Save test results

        Args:
            task_id: Task identifier
            test_type: Type of test (unit, integration, etc.)
            passed: Number of passed tests
            failed: Number of failed tests
            coverage: Optional coverage percentage
            duration: Optional duration in seconds
            details: Optional detailed results
        """
        self.conn.execute("""
            INSERT INTO test_results
            (task_id, test_type, passed, failed, coverage_percent,
             duration_seconds, details)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, (
            task_id,
            test_type,
            passed,
            failed,
            coverage,
            duration,
            json.dumps(details) if details else None
        ))
        self.conn.commit()

    def save_review_results(
        self,
        project_id: str,
        approved: bool,
        agent_approvals: Dict[str, bool],
        issues: List[Dict],
        feedback: str
    ):
        """
        Save review results

        Args:
            project_id: Project identifier
            approved: Whether review approved
            agent_approvals: Agent approval map
            issues: List of issues found
            feedback: Overall feedback
        """
        self.conn.execute("""
            INSERT INTO reviews
            (project_id, approved, agent_approvals, issues, feedback)
            VALUES (?, ?, ?, ?, ?)
        """, (
            project_id,
            int(approved),
            json.dumps(agent_approvals),
            json.dumps(issues),
            feedback
        ))
        self.conn.commit()

    def close(self):
        """Close database connection"""
        if self.conn:
            self.conn.close()

    def __enter__(self):
        """Context manager entry"""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()
