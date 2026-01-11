"""In-memory session store for chat context."""

import uuid
from dataclasses import dataclass, field
from typing import Optional

from parallel_u.schemas import BriefOutput


@dataclass
class Session:
    """Stores context for a user session."""

    session_id: str
    user_id: str
    topics: list[str]
    goal: str
    brief: BriefOutput
    browsing_results: list[dict]
    chat_history: list[dict] = field(default_factory=list)


class SessionStore:
    """In-memory store for user sessions (for MVP; use Redis/DB in production)."""

    def __init__(self):
        self._sessions: dict[str, Session] = {}

    def create(
        self,
        user_id: str,
        topics: list[str],
        goal: str,
        brief: BriefOutput,
        browsing_results: list[dict],
    ) -> str:
        """Create a new session and return its ID."""
        session_id = str(uuid.uuid4())
        self._sessions[session_id] = Session(
            session_id=session_id,
            user_id=user_id,
            topics=topics,
            goal=goal,
            brief=brief,
            browsing_results=browsing_results,
        )
        return session_id

    def get(self, session_id: str) -> Optional[Session]:
        """Get a session by ID."""
        return self._sessions.get(session_id)

    def add_chat_message(self, session_id: str, role: str, content: str) -> bool:
        """Add a message to the chat history."""
        session = self._sessions.get(session_id)
        if session:
            session.chat_history.append({"role": role, "content": content})
            return True
        return False

    def delete(self, session_id: str) -> bool:
        """Delete a session."""
        if session_id in self._sessions:
            del self._sessions[session_id]
            return True
        return False
