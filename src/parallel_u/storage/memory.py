from datetime import datetime
from threading import Lock
from typing import Dict, Optional

from parallel_u.models.schemas import PreferencesOut, Depth


class MemoryStore:
    def __init__(self) -> None:
        self._prefs: Dict[str, PreferencesOut] = {}
        self._lock = Lock()

    def upsert_preferences(
        self,
        user_id: str,
        topics: str,
        depth: Depth,
        time_budget_min: int,
    ) -> PreferencesOut:
        rec = PreferencesOut(
            user_id=user_id,
            topics=topics,
            depth=depth,
            time_budget_min=time_budget_min,
            updated_at=datetime.utcnow(),
        )
        with self._lock:
            self._prefs[user_id] = rec
        return rec

    def get_preferences(self, user_id: str) -> Optional[PreferencesOut]:
        with self._lock:
            return self._prefs.get(user_id)
