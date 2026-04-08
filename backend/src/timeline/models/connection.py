import uuid
from datetime import datetime, timezone

from sqlalchemy import DateTime, Float, ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from timeline.database import Base


class Connection(Base):
    __tablename__ = "connections"
    __table_args__ = (UniqueConstraint("source_event_id", "target_event_id", "connection_type"),)

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    source_event_id: Mapped[str] = mapped_column(Text, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    target_event_id: Mapped[str] = mapped_column(Text, ForeignKey("events.id", ondelete="CASCADE"), nullable=False, index=True)
    connection_type: Mapped[str] = mapped_column(Text, nullable=False)
    weight: Mapped[float] = mapped_column(Float, default=1.0)
    metadata_: Mapped[str | None] = mapped_column("metadata", Text, nullable=True)  # JSON
    created_by: Mapped[str] = mapped_column(Text, default="user")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=lambda: datetime.now(timezone.utc)
    )

    source_event: Mapped["Event"] = relationship("Event", foreign_keys=[source_event_id], back_populates="outgoing_connections")
    target_event: Mapped["Event"] = relationship("Event", foreign_keys=[target_event_id], back_populates="incoming_connections")
