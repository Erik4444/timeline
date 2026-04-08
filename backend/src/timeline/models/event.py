import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, LargeBinary, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from timeline.database import Base


def _new_id() -> str:
    return str(uuid.uuid4())


def _now() -> datetime:
    return datetime.now(timezone.utc)


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (UniqueConstraint("source", "source_id", name="uq_source_source_id"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=_new_id)
    source: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    source_id: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_type: Mapped[str] = mapped_column(Text, nullable=False, index=True)
    title: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    occurred_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False, index=True)
    occurred_at_precision: Mapped[str] = mapped_column(Text, default="second")
    location_lat: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_lng: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_name: Mapped[str | None] = mapped_column(Text, nullable=True)
    raw_data: Mapped[str | None] = mapped_column(Text, nullable=True)  # JSON
    embedding: Mapped[bytes | None] = mapped_column(LargeBinary, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_now, onupdate=_now)

    media: Mapped[list["Media"]] = relationship("Media", back_populates="event", cascade="all, delete-orphan")
    event_tags: Mapped[list["EventTag"]] = relationship("EventTag", back_populates="event", cascade="all, delete-orphan")
    outgoing_connections: Mapped[list["Connection"]] = relationship(
        "Connection", foreign_keys="Connection.source_event_id",
        back_populates="source_event", cascade="all, delete-orphan"
    )
    incoming_connections: Mapped[list["Connection"]] = relationship(
        "Connection", foreign_keys="Connection.target_event_id",
        back_populates="target_event", cascade="all, delete-orphan"
    )
