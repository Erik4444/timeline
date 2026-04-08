import uuid

from sqlalchemy import ForeignKey, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from timeline.database import Base


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[str] = mapped_column(Text, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    source: Mapped[str] = mapped_column(Text, default="user")  # user | ai | parser

    event_tags: Mapped[list["EventTag"]] = relationship("EventTag", back_populates="tag", cascade="all, delete-orphan")


class EventTag(Base):
    __tablename__ = "event_tags"
    __table_args__ = (UniqueConstraint("event_id", "tag_id"),)

    event_id: Mapped[str] = mapped_column(Text, ForeignKey("events.id", ondelete="CASCADE"), primary_key=True)
    tag_id: Mapped[str] = mapped_column(Text, ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True)

    event: Mapped["Event"] = relationship("Event", back_populates="event_tags")
    tag: Mapped["Tag"] = relationship("Tag", back_populates="event_tags")
