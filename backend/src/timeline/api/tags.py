from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from timeline.database import get_db
from timeline.models.tag import EventTag, Tag

router = APIRouter()


@router.get("")
def list_tags(db: Session = Depends(get_db)):
    rows = (
        db.query(Tag, func.count(EventTag.event_id).label("count"))
        .outerjoin(EventTag, Tag.id == EventTag.tag_id)
        .group_by(Tag.id)
        .order_by(func.count(EventTag.event_id).desc())
        .all()
    )
    return [
        {"id": tag.id, "name": tag.name, "source": tag.source, "count": count}
        for tag, count in rows
    ]
