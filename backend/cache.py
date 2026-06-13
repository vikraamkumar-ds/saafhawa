"""Tiny SQLite key/value cache with TTL. Local, free, no server."""
import json
import sqlite3
import time
from typing import Optional, Any
from config import CACHE_DB

_conn = sqlite3.connect(CACHE_DB, check_same_thread=False)
_conn.execute(
    "CREATE TABLE IF NOT EXISTS cache (k TEXT PRIMARY KEY, v TEXT, exp REAL)"
)
_conn.commit()


def get(key: str) -> Optional[Any]:
    row = _conn.execute("SELECT v, exp FROM cache WHERE k = ?", (key,)).fetchone()
    if not row:
        return None
    value, exp = row
    if exp < time.time():
        _conn.execute("DELETE FROM cache WHERE k = ?", (key,))
        _conn.commit()
        return None
    return json.loads(value)


def set(key: str, value: Any, ttl: int) -> None:
    _conn.execute(
        "INSERT OR REPLACE INTO cache (k, v, exp) VALUES (?, ?, ?)",
        (key, json.dumps(value), time.time() + ttl),
    )
    _conn.commit()


def get_last_good(key: str) -> Optional[Any]:
    """Return the last value ever stored under `<key>:last`, ignoring TTL.
    Used for the graceful offline fallback so guidance always loads."""
    row = _conn.execute("SELECT v FROM cache WHERE k = ?", (f"{key}:last",)).fetchone()
    return json.loads(row[0]) if row else None


def set_last_good(key: str, value: Any) -> None:
    _conn.execute(
        "INSERT OR REPLACE INTO cache (k, v, exp) VALUES (?, ?, ?)",
        (f"{key}:last", json.dumps(value), 10**12),  # effectively never expires
    )
    _conn.commit()
