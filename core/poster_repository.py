from __future__ import annotations

import datetime as dt
from typing import Optional, Dict, Any, List

from core.database import get_connection

class PosterRepository:
    """
    Simple CRUD + retry logic on top of SQLite.
    Stores which poster type we WANTED and which we actually USED.
    """

    def save_result(
        self,
        tmdb_id: int,
        media_type: str,
        wanted_type: str,
        actual_type: str,
        poster_url: str,
    ) -> None:
        """
        Upsert the record for a given TMDB id.
        """
        sql = """
        INSERT INTO poster_cache (tmdb_id, media_type, wanted_type, actual_type, poster_url, last_checked)
        VALUES (?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(tmdb_id) DO UPDATE SET
            media_type = excluded.media_type,
            wanted_type = excluded.wanted_type,
            actual_type = excluded.actual_type,
            poster_url = excluded.poster_url,
            last_checked = CURRENT_TIMESTAMP
        """
        with get_connection() as conn:
            conn.execute(sql, (tmdb_id, media_type, wanted_type, actual_type, poster_url))

    def get(self, tmdb_id: int) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM poster_cache WHERE tmdb_id = ?"
        with get_connection() as conn:
            row = conn.execute(sql, (tmdb_id,)).fetchone()
            return dict(row) if row else None

    def mark_checked_now(self, tmdb_id: int) -> None:
        sql = "UPDATE poster_cache SET last_checked = CURRENT_TIMESTAMP WHERE tmdb_id = ?"
        with get_connection() as conn:
            conn.execute(sql, (tmdb_id,))

    def needs_retry(self, tmdb_id: int, retry_after_days: int, wanted_type: str = "textless") -> bool:
        """
        Return True if:
          - the record exists,
          - actual_type != wanted_type,
          - last_checked is older than retry_after_days
        """
        row = self.get(tmdb_id)
        if not row:
            return False
        if row["actual_type"] == wanted_type:
            return False

        last = row["last_checked"]
        # last comes as string "YYYY-MM-DD HH:MM:SS" from sqlite unless parsed — handle both
        if isinstance(last, str):
            last_dt = dt.datetime.fromisoformat(last)
        else:
            last_dt = last  # already a datetime
        return (dt.datetime.now() - last_dt) >= dt.timedelta(days=retry_after_days)

    def due_retries(self, retry_after_days: int, wanted_type: str = "textless", limit: int = 100) -> List[Dict[str, Any]]:
        """
        Return a list of items that should be retried.
        """
        sql = """
        SELECT * FROM poster_cache
        WHERE actual_type <> ?
          AND datetime(last_checked) <= datetime('now', ?)
        ORDER BY last_checked ASC
        LIMIT ?
        """
        # e.g. '-7 days'
        delta = f"-{retry_after_days} days"
        with get_connection() as conn:
            rows = conn.execute(sql, (wanted_type, delta, limit)).fetchall()
            return [dict(r) for r in rows]
