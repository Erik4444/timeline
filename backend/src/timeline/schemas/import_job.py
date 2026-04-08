from datetime import datetime

from pydantic import BaseModel


class ImportJobOut(BaseModel):
    id: str
    source: str
    status: str
    original_filename: str | None
    total_events: int
    imported_events: int
    error_message: str | None
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ParserInfo(BaseModel):
    source_name: str
    display_name: str
    description: str
    supported_extensions: list[str]
