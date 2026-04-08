from __future__ import annotations

import abc
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Iterator

logger = logging.getLogger(__name__)


@dataclass
class ParsedEvent:
    source: str
    source_id: str
    event_type: str
    occurred_at: datetime
    title: str | None = None
    body: str | None = None
    location_lat: float | None = None
    location_lng: float | None = None
    location_name: str | None = None
    raw_data: dict = field(default_factory=dict)
    media_paths: list[Path] = field(default_factory=list)
    tags: list[str] = field(default_factory=list)
    occurred_at_precision: str = "second"


class BaseParser(abc.ABC):
    SOURCE_NAME: str
    DISPLAY_NAME: str
    SUPPORTED_EXTENSIONS: list[str]
    DESCRIPTION: str

    @abc.abstractmethod
    def can_handle(self, path: Path) -> bool:
        """Quick check — no heavy parsing. Used for auto-detection."""
        ...

    @abc.abstractmethod
    def parse(self, path: Path) -> Iterator[ParsedEvent]:
        """Yield ParsedEvents lazily. Never raise on individual bad records."""
        ...

    def estimate_count(self, path: Path) -> int | None:
        return None
