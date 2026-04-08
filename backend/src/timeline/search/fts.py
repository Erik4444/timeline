"""SQLite FTS5 search."""
from __future__ import annotations

import re

from sqlalchemy import text
from sqlalchemy.orm import Session

from timeline.models.event import Event


def _sanitize_query(q: str) -> str:
    """Escape special FTS5 characters and handle empty query."""
    q = q.strip()
    if not q:
        return ""
    # Escape double-quotes by doubling them, wrap in quotes for phrase handling
    # Allow simple prefix search: words ending with * are kept
    # Strip characters that break FTS5
    safe = re.sub(r'[^\w\s\*\"\-]', ' ', q, flags=re.UNICODE)
    return safe.strip()


def fts_search(
    db: Session,
    query: str,
    from_date=None,
    to_date=None,
    sources: list[str] | None = None,
    limit: int = 50,
    offset: int = 0,
) -> list[tuple[Event, float]]:
    safe_q = _sanitize_query(query)
    if not safe_q:
        return []

    params: dict = {"query": safe_q, "limit": limit, "offset": offset}
    conditions = ["events_fts MATCH :query"]

    if from_date:
        conditions.append("e.occurred_at >= :from_date")
        params["from_date"] = from_date.isoformat()
    if to_date:
        conditions.append("e.occurred_at <= :to_date")
        params["to_date"] = to_date.isoformat()
    if sources:
        placeholders = ", ".join(f":src_{i}" for i in range(len(sources)))
        conditions.append(f"e.source IN ({placeholders})")
        for i, s in enumerate(sources):
            params[f"src_{i}"] = s

    where = " AND ".join(conditions)
    sql = text(f"""
        SELECT e.id, bm25(events_fts) AS rank
        FROM events e
        JOIN events_fts ON events_fts.id = e.id
        WHERE {where}
        ORDER BY rank
        LIMIT :limit OFFSET :offset
    """)

    rows = db.execute(sql, params).fetchall()
    if not rows:
        return []

    ids = [r[0] for r in rows]
    scores = {r[0]: float(r[1]) for r in rows}

    events = db.query(Event).filter(Event.id.in_(ids)).all()
    event_map = {e.id: e for e in events}

    return [(event_map[eid], scores[eid]) for eid in ids if eid in event_map]
