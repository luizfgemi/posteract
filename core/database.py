import os
import sqlite3
from pathlib import Path
from typing import Optional, Tuple

_DB_PATH = Path("data/posteract.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS poster_cache (
    tmdb_id        INTEGER      PRIMARY KEY,
    media_type     TEXT         NOT NULL,         -- 'movie' or 'tv'
    wanted_type    TEXT         NOT NULL,         -- e.g. 'textless'
    actual_type    TEXT         NOT NULL,         -- e.g. 'textless', 'en', 'pt', 'fallback'
    poster_url     TEXT         NOT NULL,
    last_checked   TIMESTAMP    DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_poster_cache_last_checked
  ON poster_cache(last_checked);
"""

def get_connection() -> sqlite3.Connection:
    os.makedirs(_DB_PATH.parent, exist_ok=True)
    conn = sqlite3.connect(_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    conn.row_factory = sqlite3.Row
    _ensure_schema(conn)
    return conn

def _ensure_schema(conn: sqlite3.Connection) -> None:
    with conn:
        conn.executescript(_SCHEMA)
