"""Local persistence for roadmaps and their progress.

Progress used to live only in the Streamlit session, so a refresh wiped it.
SQLite keeps plans and checkboxes across sessions and restarts.
"""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from typing import Any, Dict, Iterator, List, Optional, Tuple

from config import AppConfig
from models import LearningRoadmap

SCHEMA = """
CREATE TABLE IF NOT EXISTS roadmaps (
    id          TEXT PRIMARY KEY,
    title       TEXT NOT NULL,
    goal        TEXT NOT NULL,
    day_count   INTEGER NOT NULL,
    payload     TEXT NOT NULL,
    completion  TEXT NOT NULL DEFAULT '{}',
    created_at  TEXT,
    updated_at  TEXT NOT NULL
);
"""


def _db_path():
    return AppConfig.get_data_dir() / "app.db"


@contextmanager
def _connect() -> Iterator[sqlite3.Connection]:
    connection = sqlite3.connect(_db_path(), timeout=10)
    connection.row_factory = sqlite3.Row
    try:
        connection.execute("PRAGMA journal_mode=WAL")
        connection.executescript(SCHEMA)
        yield connection
        connection.commit()
    finally:
        connection.close()


def _now() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _to_int_keys(raw: Dict[str, Any]) -> Dict[int, bool]:
    result: Dict[int, bool] = {}
    for key, value in (raw or {}).items():
        try:
            result[int(key)] = bool(value)
        except (TypeError, ValueError):
            continue
    return result


def save_roadmap(roadmap: LearningRoadmap, completion: Optional[Dict[int, bool]] = None) -> str:
    """Insert or update a plan. Returns its id."""
    payload = roadmap.model_dump_json()
    completion_json = json.dumps({str(k): bool(v) for k, v in (completion or {}).items()})
    with _connect() as connection:
        connection.execute(
            """
            INSERT INTO roadmaps (id, title, goal, day_count, payload, completion, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                title=excluded.title,
                goal=excluded.goal,
                day_count=excluded.day_count,
                payload=excluded.payload,
                completion=excluded.completion,
                updated_at=excluded.updated_at
            """,
            (
                roadmap.id,
                roadmap.title,
                roadmap.goal,
                len(roadmap.days),
                payload,
                completion_json,
                roadmap.created_at or _now(),
                _now(),
            ),
        )
    return roadmap.id


def save_completion(roadmap_id: str, completion: Dict[int, bool]) -> None:
    if not roadmap_id:
        return
    with _connect() as connection:
        connection.execute(
            "UPDATE roadmaps SET completion = ?, updated_at = ? WHERE id = ?",
            (json.dumps({str(k): bool(v) for k, v in completion.items()}), _now(), roadmap_id),
        )


def get_roadmap(roadmap_id: str) -> Optional[Tuple[LearningRoadmap, Dict[int, bool]]]:
    if not roadmap_id:
        return None
    with _connect() as connection:
        row = connection.execute("SELECT * FROM roadmaps WHERE id = ?", (roadmap_id,)).fetchone()
    if row is None:
        return None
    try:
        roadmap = LearningRoadmap.model_validate_json(row["payload"])
    except Exception:
        return None
    return roadmap, _to_int_keys(json.loads(row["completion"] or "{}"))


def list_roadmaps() -> List[Dict[str, Any]]:
    """Lightweight rows for the library view."""
    with _connect() as connection:
        rows = connection.execute(
            "SELECT id, title, goal, day_count, completion, created_at, updated_at "
            "FROM roadmaps ORDER BY updated_at DESC"
        ).fetchall()
    summaries: List[Dict[str, Any]] = []
    for row in rows:
        completion = _to_int_keys(json.loads(row["completion"] or "{}"))
        done = sum(1 for value in completion.values() if value)
        summaries.append(
            {
                "id": row["id"],
                "title": row["title"],
                "goal": row["goal"],
                "day_count": row["day_count"],
                "completed": min(done, row["day_count"]),
                "created_at": row["created_at"],
                "updated_at": row["updated_at"],
            }
        )
    return summaries


def delete_roadmap(roadmap_id: str) -> None:
    if not roadmap_id:
        return
    with _connect() as connection:
        connection.execute("DELETE FROM roadmaps WHERE id = ?", (roadmap_id,))


def count_roadmaps() -> int:
    with _connect() as connection:
        row = connection.execute("SELECT COUNT(*) AS total FROM roadmaps").fetchone()
    return int(row["total"]) if row else 0
