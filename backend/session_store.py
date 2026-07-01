"""In-memory store of per-session analytics contexts for uploaded datasets.

Each upload produces an isolated AnalyticsContext keyed by a session id, so one
user's uploaded data never overwrites the demo dataset or another upload. This
is intentionally process-local and capacity-bounded (LRU eviction); it is not a
durable store and resets on restart.
"""

from __future__ import annotations

import threading
import uuid
from collections import OrderedDict

from ai.context import AnalyticsContext
from ingest import IngestResult


class SessionStore:
    def __init__(self, max_sessions: int = 50) -> None:
        self._max = max_sessions
        self._lock = threading.Lock()
        self._sessions: "OrderedDict[str, AnalyticsContext]" = OrderedDict()

    def create(self, result: IngestResult) -> str:
        """Build a context from parsed data and store it under a new session id."""
        ctx = AnalyticsContext(items_df=result.items_df, lines_df=result.lines_df)
        # Compute eagerly so parse-time errors surface in the upload response.
        _ = ctx.matrix_df
        _ = ctx.associations_df

        session_id = f"upload-{uuid.uuid4().hex[:12]}"
        with self._lock:
            self._sessions[session_id] = ctx
            self._sessions.move_to_end(session_id)
            while len(self._sessions) > self._max:
                self._sessions.popitem(last=False)
        return session_id

    def get(self, session_id: str | None) -> AnalyticsContext | None:
        if not session_id:
            return None
        with self._lock:
            ctx = self._sessions.get(session_id)
            if ctx is not None:
                self._sessions.move_to_end(session_id)
            return ctx


session_store = SessionStore()
