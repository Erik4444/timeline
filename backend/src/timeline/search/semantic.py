"""Semantic search via embeddings."""
from __future__ import annotations

import logging

import numpy as np
from sqlalchemy.orm import Session

from timeline.ai.embeddings import decode_embedding, cosine_similarity_batch, embed_text
from timeline.models.event import Event

logger = logging.getLogger(__name__)


async def semantic_search(
    db: Session,
    query: str,
    limit: int = 20,
    threshold: float = 0.6,
) -> list[tuple[Event, float]]:
    query_bytes = await embed_text(query)
    if query_bytes is None:
        return []

    query_vec = decode_embedding(query_bytes)

    # Load all events with embeddings
    rows = db.query(Event.id, Event.embedding).filter(Event.embedding.isnot(None)).all()
    if not rows:
        return []

    ids = [r[0] for r in rows]
    matrix = np.stack([decode_embedding(r[1]) for r in rows])

    scores = cosine_similarity_batch(query_vec, matrix)

    # Filter by threshold and sort
    above = [(ids[i], float(scores[i])) for i in range(len(ids)) if scores[i] >= threshold]
    above.sort(key=lambda x: x[1], reverse=True)
    top = above[:limit]

    if not top:
        return []

    top_ids = [t[0] for t in top]
    score_map = {t[0]: t[1] for t in top}

    events = db.query(Event).filter(Event.id.in_(top_ids)).all()
    event_map = {e.id: e for e in events}

    return [(event_map[eid], score_map[eid]) for eid in top_ids if eid in event_map]
