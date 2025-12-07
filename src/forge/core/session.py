"""
Session management for Forge
"""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime
import json
from pathlib import Path
from forge.utils.logger import logger


@dataclass
class Message:
    """Conversation message"""
    role: str  # 'user', 'assistant', 'system'
    content: str
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Session:
    """User session"""
    id: str
    project_id: Optional[str]
    created_at: datetime
    updated_at: datetime
    messages: List[Message] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class SessionManager:
    """Manage user sessions"""

    def __init__(self, session_dir: str = ".forge/sessions"):
        """
        Initialize session manager

        Args:
            session_dir: Directory to store session files
        """
        self.session_dir = Path(session_dir)
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.current_session: Optional[Session] = None

    def create_session(
        self,
        session_id: Optional[str] = None,
        project_id: Optional[str] = None
    ) -> Session:
        """
        Create new session

        Args:
            session_id: Optional session ID (generated if not provided)
            project_id: Optional project ID

        Returns:
            Created session
        """
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())

        now = datetime.now()
        session = Session(
            id=session_id,
            project_id=project_id,
            created_at=now,
            updated_at=now
        )

        self.current_session = session
        self._save_session(session)

        logger.info(f"Created session: {session_id}")
        return session

    def load_session(self, session_id: str) -> Optional[Session]:
        """
        Load existing session

        Args:
            session_id: Session identifier

        Returns:
            Loaded session or None
        """
        session_file = self.session_dir / f"{session_id}.json"

        if not session_file.exists():
            return None

        try:
            with open(session_file) as f:
                data = json.load(f)

            session = Session(
                id=data['id'],
                project_id=data.get('project_id'),
                created_at=datetime.fromisoformat(data['created_at']),
                updated_at=datetime.fromisoformat(data['updated_at']),
                messages=[
                    Message(
                        role=msg['role'],
                        content=msg['content'],
                        timestamp=datetime.fromisoformat(msg['timestamp']),
                        metadata=msg.get('metadata', {})
                    )
                    for msg in data.get('messages', [])
                ],
                metadata=data.get('metadata', {})
            )

            self.current_session = session
            logger.info(f"Loaded session: {session_id}")
            return session

        except Exception as e:
            logger.error(f"Failed to load session {session_id}: {e}")
            return None

    def add_message(
        self,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
        session: Optional[Session] = None
    ) -> Message:
        """
        Add message to session

        Args:
            role: Message role (user, assistant, system)
            content: Message content
            metadata: Optional metadata
            session: Optional session (uses current if not provided)

        Returns:
            Created message
        """
        if session is None:
            session = self.current_session

        if session is None:
            raise ValueError("No active session")

        message = Message(
            role=role,
            content=content,
            metadata=metadata or {}
        )

        session.messages.append(message)
        session.updated_at = datetime.now()

        self._save_session(session)

        return message

    def get_conversation_history(
        self,
        session: Optional[Session] = None,
        limit: Optional[int] = None
    ) -> List[Message]:
        """
        Get conversation history

        Args:
            session: Optional session (uses current if not provided)
            limit: Optional limit on number of messages

        Returns:
            List of messages
        """
        if session is None:
            session = self.current_session

        if session is None:
            return []

        messages = session.messages
        if limit:
            messages = messages[-limit:]

        return messages

    def clear_session(self, session: Optional[Session] = None):
        """
        Clear session messages

        Args:
            session: Optional session (uses current if not provided)
        """
        if session is None:
            session = self.current_session

        if session is None:
            return

        session.messages.clear()
        session.updated_at = datetime.now()

        self._save_session(session)
        logger.info(f"Cleared session: {session.id}")

    def list_sessions(self) -> List[str]:
        """
        List all session IDs

        Returns:
            List of session IDs
        """
        return [
            f.stem for f in self.session_dir.glob("*.json")
        ]

    def _save_session(self, session: Session):
        """Save session to file"""
        session_file = self.session_dir / f"{session.id}.json"

        data = {
            'id': session.id,
            'project_id': session.project_id,
            'created_at': session.created_at.isoformat(),
            'updated_at': session.updated_at.isoformat(),
            'messages': [
                {
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.timestamp.isoformat(),
                    'metadata': msg.metadata
                }
                for msg in session.messages
            ],
            'metadata': session.metadata
        }

        with open(session_file, 'w') as f:
            json.dump(data, f, indent=2)
