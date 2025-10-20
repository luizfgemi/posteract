"""Utility module providing SQLite-backed persistence for poster workflow."""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Any, Dict, Optional
from datetime import datetime, timedelta

from utils.logger import get_logger

logger = get_logger(__name__)

_DEFAULT_DB_PATH = Path("data/posteract.sqlite")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS poster_jobs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    media_id TEXT NOT NULL,
    tmdb_id INTEGER,
    source_used TEXT,
    poster_type TEXT,
    status TEXT NOT NULL,
    retry_count INTEGER NOT NULL DEFAULT 0,
    last_error TEXT,
    last_attempt_at TEXT,
    next_retry_at TEXT,
    created_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    updated_at TEXT NOT NULL DEFAULT (DATETIME('now')),
    UNIQUE(media_id)
);
"""

class PosterJobStore:
    """Simple SQLite persistence layer for poster workflow state."""

    def __init__(self, db_path: Path | str = _DEFAULT_DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._ensure_schema()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _ensure_schema(self) -> None:
        with self._get_conn() as conn:
            conn.executescript(_SCHEMA)

    def upsert(
        self,
        media_id: str,
        tmdb_id: Optional[int],
        source_used: Optional[str],
        poster_type: Optional[str],
        status: str,
    ) -> None:
        sql = """
        INSERT INTO poster_jobs (media_id, tmdb_id, source_used, poster_type, status)
        VALUES (?, ?, ?, ?, ?)
        ON CONFLICT(media_id) DO UPDATE SET
            tmdb_id = excluded.tmdb_id,
            source_used = excluded.source_used,
            poster_type = excluded.poster_type,
            status = excluded.status,
            updated_at = DATETIME('now')
        """
        with self._get_conn() as conn:
            conn.execute(sql, (media_id, tmdb_id, source_used, poster_type, status))

    def update_status(
        self,
        media_id: str,
        status: str,
        error: Optional[str] = None,
        retry_in: Optional[timedelta] = None,
    ) -> None:
        retry_delta = retry_in or timedelta(hours=6)
        should_retry = status in {"failed", "not_found"}
        next_retry: Optional[str] = (
            (datetime.utcnow() + retry_delta).isoformat() if should_retry else None
        )

        sql = """
        UPDATE poster_jobs
        SET status = ?,
            last_error = ?,
            last_attempt_at = DATETIME('now'),
            next_retry_at = ?,
            retry_count = CASE WHEN ? THEN retry_count + 1 ELSE retry_count END,
            updated_at = DATETIME('now')
        WHERE media_id = ?
        """

        with self._get_conn() as conn:
            conn.execute(sql, (status, error, next_retry, 1 if should_retry else 0, media_id))

    def mark_uploaded(self, media_id: str) -> None:
        sql = """
        UPDATE poster_jobs
        SET status = 'uploaded',
            last_error = NULL,
            next_retry_at = NULL,
            retry_count = 0,
            last_attempt_at = DATETIME('now'),
            updated_at = DATETIME('now')
        WHERE media_id = ?
        """
        with self._get_conn() as conn:
            conn.execute(sql, (media_id,))

    def get(self, media_id: str) -> Optional[Dict[str, Any]]:
        sql = "SELECT * FROM poster_jobs WHERE media_id = ?"
        with self._get_conn() as conn:
            row = conn.execute(sql, (media_id,)).fetchone()
            return dict(row) if row else None

    def clear(self) -> None:
        with self._get_conn() as conn:
            conn.execute("DELETE FROM poster_jobs")
        with self._get_conn() as conn:
            conn.execute("VACUUM")
        logger.info("Poster job store cleared")
