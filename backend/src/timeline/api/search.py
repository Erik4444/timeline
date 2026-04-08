from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session, selectinload

from timeline.database import get_db
from timeline.models.tag import EventTag
from timeline.schemas.event import EventOut
from timeline.search.fts import fts_search

router = APIRouter()


@router.get("")
async def search(
    q: str = Query(..., min_length=1),
    mode: str = Query(default="hybrid"),  # fts | semantic | hybrid
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    sources: list[str] = Query(default=[]),
    limit: int = Query(default=50, le=200),
    offset: int = 0,
    db: Session = Depends(get_db),
):
    results: list[tuple] = []
    actual_mode = "fts"

    if mode in ("semantic", "hybrid"):
        from timeline.ai.client import get_backend
        from timeline.search.semantic import semantic_search
        backend = await get_backend()
        if await backend.is_available():
            sem_results = await semantic_search(db, q, limit=limit)
            if mode == "semantic":
                results = sem_results
                actual_mode = "semantic"
            else:
                # Hybrid: RRF fusion
                fts_results = fts_search(db, q, from_date, to_date, sources or None, limit, offset)
                results = _rrf_fusion(fts_results, sem_results, limit)
                actual_mode = "hybrid"
        else:
            results = fts_search(db, q, from_date, to_date, sources or None, limit, offset)
    else:
        results = fts_search(db, q, from_date, to_date, sources or None, limit, offset)

    # Reload with relationships
    from timeline.models.event import Event
    ids = [e.id for e, _ in results]
    if ids:
        events = (
            db.query(Event)
            .options(
                selectinload(Event.media),
                selectinload(Event.event_tags).selectinload(EventTag.tag),
            )
            .filter(Event.id.in_(ids))
            .all()
        )
        event_map = {e.id: e for e in events}
        ordered = [event_map[eid] for eid, _ in [(e.id, s) for e, s in results] if eid in event_map]
    else:
        ordered = []

    from timeline.schemas.event import EventOut
    return {
        "items": [EventOut.from_orm_with_tags(e) for e in ordered],
        "total": len(ordered),
        "mode": actual_mode,
        "query": q,
    }


def _rrf_fusion(
    fts: list[tuple], semantic: list[tuple], limit: int, k: int = 60
) -> list[tuple]:
    """Reciprocal Rank Fusion."""
    scores: dict[str, float] = {}
    fts_map = {}
    for rank, (event, score) in enumerate(fts):
        scores[event.id] = scores.get(event.id, 0) + 1 / (k + rank + 1)
        fts_map[event.id] = event
    sem_map = {}
    for rank, (event, score) in enumerate(semantic):
        scores[event.id] = scores.get(event.id, 0) + 1 / (k + rank + 1)
        sem_map[event.id] = event

    all_events = {**fts_map, **sem_map}
    sorted_ids = sorted(scores.keys(), key=lambda eid: scores[eid], reverse=True)[:limit]
    return [(all_events[eid], scores[eid]) for eid in sorted_ids if eid in all_events]
