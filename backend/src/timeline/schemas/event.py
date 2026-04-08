from datetime import datetime

from pydantic import BaseModel


class MediaOut(BaseModel):
    id: str
    file_path: str
    thumbnail_path: str | None
    mime_type: str | None
    width: int | None
    height: int | None

    model_config = {"from_attributes": True}


class TagOut(BaseModel):
    id: str
    name: str
    source: str

    model_config = {"from_attributes": True}


class ConnectionOut(BaseModel):
    id: str
    source_event_id: str
    target_event_id: str
    connection_type: str
    weight: float
    created_by: str

    model_config = {"from_attributes": True}


class EventOut(BaseModel):
    id: str
    source: str
    source_id: str | None
    event_type: str
    title: str | None
    body: str | None
    occurred_at: datetime
    occurred_at_precision: str
    location_lat: float | None
    location_lng: float | None
    location_name: str | None
    created_at: datetime
    media: list[MediaOut] = []
    tags: list[TagOut] = []

    model_config = {"from_attributes": True}

    @classmethod
    def from_orm_with_tags(cls, event):
        tags = [et.tag for et in event.event_tags]
        data = cls.model_validate(event)
        data.tags = [TagOut.model_validate(t) for t in tags]
        return data


class EventListOut(BaseModel):
    items: list[EventOut]
    total: int
    limit: int
    offset: int


class EventUpdate(BaseModel):
    title: str | None = None
    body: str | None = None
    tags: list[str] | None = None
