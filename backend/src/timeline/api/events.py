from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session, selectinload

from timeline.database import get_db
from timeline.models.event import Event
from timeline.models.tag import Tag, EventTag
from timeline.schemas.event import EventListOut, EventOut, EventUpdate, TagOut

router = APIRouter()


def _load_event(event_id: str, db: Session) -> Event:
    event = (
        db.query(Event)
        .options(
            selectinload(Event.media),
            selectinload(Event.event_tags).selectinload(EventTag.tag),
        )
        .filter(Event.id == event_id)
        .first()
    )
    if not event:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    return event


def _serialize(event: Event) -> EventOut:
    return EventOut.from_orm_with_tags(event)


@router.get("", response_model=EventListOut)
def list_events(
    sources: list[str] = Query(default=[]),
    event_types: list[str] = Query(default=[]),
    tags: list[str] = Query(default=[]),
    from_date: Optional[datetime] = None,
    to_date: Optional[datetime] = None,
    q: Optional[str] = None,
    limit: int = Query(default=200, le=1000),
    offset: int = 0,
    sort: str = "occurred_at_asc",
    db: Session = Depends(get_db),
):
    query = db.query(Event).options(
        selectinload(Event.media),
        selectinload(Event.event_tags).selectinload(EventTag.tag),
    )

    if sources:
        query = query.filter(Event.source.in_(sources))
    if event_types:
        query = query.filter(Event.event_type.in_(event_types))
    if from_date:
        query = query.filter(Event.occurred_at >= from_date)
    if to_date:
        query = query.filter(Event.occurred_at <= to_date)
    if tags:
        for tag_name in tags:
            query = query.filter(
                Event.event_tags.any(
                    EventTag.tag.has(Tag.name == tag_name.lower())
                )
            )

    total = query.count()

    if sort == "occurred_at_desc":
        query = query.order_by(Event.occurred_at.desc())
    else:
        query = query.order_by(Event.occurred_at.asc())

    events = query.offset(offset).limit(limit).all()

    return EventListOut(
        items=[_serialize(e) for e in events],
        total=total,
        limit=limit,
        offset=offset,
    )


@router.get("/sources")
def get_sources(db: Session = Depends(get_db)):
    from sqlalchemy import func, distinct
    rows = db.query(Event.source, func.count(Event.id)).group_by(Event.source).all()
    return [{"source": r[0], "count": r[1]} for r in rows]


@router.get("/date-range")
def get_date_range(db: Session = Depends(get_db)):
    from sqlalchemy import func
    row = db.query(func.min(Event.occurred_at), func.max(Event.occurred_at)).first()
    if not row or not row[0]:
        return {"min": None, "max": None}
    return {"min": row[0].isoformat(), "max": row[1].isoformat()}


@router.get("/{event_id}", response_model=EventOut)
def get_event(event_id: str, db: Session = Depends(get_db)):
    return _serialize(_load_event(event_id, db))


@router.patch("/{event_id}", response_model=EventOut)
def update_event(event_id: str, update: EventUpdate, db: Session = Depends(get_db)):
    event = _load_event(event_id, db)
    if update.title is not None:
        event.title = update.title
    if update.body is not None:
        event.body = update.body
    if update.tags is not None:
        # Remove existing user tags, add new ones
        user_event_tags = [et for et in event.event_tags if et.tag.source == "user"]
        for et in user_event_tags:
            db.delete(et)
        db.flush()
        for tag_name in set(update.tags):
            tag_name = tag_name.strip().lower()[:50]
            if not tag_name:
                continue
            tag = db.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name, source="user")
                db.add(tag)
                db.flush()
            if not db.query(EventTag).filter_by(event_id=event.id, tag_id=tag.id).first():
                db.add(EventTag(event_id=event.id, tag_id=tag.id))
    db.commit()
    db.refresh(event)
    return _serialize(_load_event(event_id, db))


@router.delete("/{event_id}")
def delete_event(event_id: str, db: Session = Depends(get_db)):
    event = db.query(Event).filter(Event.id == event_id).first()
    if not event:
        raise HTTPException(status_code=404, detail="Event nicht gefunden")
    db.delete(event)
    db.commit()
    return {"ok": True}
