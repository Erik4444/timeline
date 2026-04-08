"""
Import Pipeline Coordinator

Orchestrates: detect_parser → parse → dedup → media → store → AI queue
"""
from __future__ import annotations

import asyncio
import json
import logging
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable

from sqlalchemy.orm import Session

from timeline.config import settings
from timeline.models.event import Event
from timeline.models.import_job import ImportJob
from timeline.models.media import Media
from timeline.models.tag import EventTag, Tag
from timeline.parsers import detect_parser, get_parser
from timeline.parsers.base import ParsedEvent
from timeline.pipeline.media_processor import process_media_file

logger = logging.getLogger(__name__)

# Global progress queues keyed by job_id
_progress_queues: dict[str, asyncio.Queue] = {}


def get_progress_queue(job_id: str) -> asyncio.Queue:
    if job_id not in _progress_queues:
        _progress_queues[job_id] = asyncio.Queue(maxsize=1000)
    return _progress_queues[job_id]


def remove_progress_queue(job_id: str):
    _progress_queues.pop(job_id, None)


async def run_import(
    job_id: str,
    file_path: Path,
    source_name: str,
    db_factory: Callable[[], Session],
):
    """Main import coroutine — runs in background."""
    queue = get_progress_queue(job_id)

    with db_factory() as db:
        job = db.get(ImportJob, job_id)
        if not job:
            return
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        db.commit()

    try:
        parser = get_parser(source_name)
        if parser is None:
            parser = detect_parser(file_path)
        if parser is None:
            raise ValueError(f"Kein Parser für Quelle '{source_name}' gefunden")

        imported = 0
        batch: list[ParsedEvent] = []

        for parsed_event in parser.parse(file_path):
            batch.append(parsed_event)
            if len(batch) >= settings.import_batch_size:
                count = await _flush_batch(batch, db_factory)
                imported += count
                batch.clear()
                await _emit(queue, {"type": "progress", "imported": imported})

        if batch:
            count = await _flush_batch(batch, db_factory)
            imported += count

        with db_factory() as db:
            job = db.get(ImportJob, job_id)
            if job:
                job.status = "done"
                job.imported_events = imported
                job.total_events = imported
                job.finished_at = datetime.now(timezone.utc)
                db.commit()

        await _emit(queue, {"type": "done", "imported": imported})
        logger.info("Import %s done: %d events from %s", job_id, imported, source_name)

    except Exception as e:
        logger.exception("Import %s failed", job_id)
        with db_factory() as db:
            job = db.get(ImportJob, job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.finished_at = datetime.now(timezone.utc)
                db.commit()
        await _emit(queue, {"type": "error", "message": str(e)})


async def _flush_batch(
    batch: list[ParsedEvent],
    db_factory: Callable[[], Session],
) -> int:
    """Persist a batch of ParsedEvents, skip duplicates. Returns count inserted."""
    inserted = 0
    with db_factory() as db:
        for pe in batch:
            try:
                # Dedup check
                existing = (
                    db.query(Event)
                    .filter(Event.source == pe.source, Event.source_id == pe.source_id)
                    .first()
                )
                if existing:
                    continue

                event = Event(
                    id=str(uuid.uuid4()),
                    source=pe.source,
                    source_id=pe.source_id,
                    event_type=pe.event_type,
                    title=pe.title,
                    body=pe.body,
                    occurred_at=pe.occurred_at,
                    occurred_at_precision=pe.occurred_at_precision,
                    location_lat=pe.location_lat,
                    location_lng=pe.location_lng,
                    location_name=pe.location_name,
                    raw_data=json.dumps(pe.raw_data, ensure_ascii=False, default=str) if pe.raw_data else None,
                )
                db.add(event)
                db.flush()  # Get ID without committing

                # Tags
                for tag_name in set(pe.tags):
                    tag_name = tag_name.strip().lower()[:50]
                    if not tag_name:
                        continue
                    tag = db.query(Tag).filter(Tag.name == tag_name).first()
                    if not tag:
                        tag = Tag(name=tag_name, source="parser")
                        db.add(tag)
                        db.flush()
                    db.add(EventTag(event_id=event.id, tag_id=tag.id))

                # Media
                for media_path in pe.media_paths:
                    try:
                        media_info = process_media_file(media_path)
                        if media_info:
                            db.add(Media(
                                event_id=event.id,
                                **media_info,
                            ))
                    except Exception as e:
                        logger.debug("Media processing failed: %s", e)

                inserted += 1

            except Exception as e:
                logger.debug("Skipping event %s/%s: %s", pe.source, pe.source_id, e)
                db.rollback()
                continue

        db.commit()
    return inserted


async def _emit(queue: asyncio.Queue, msg: dict):
    try:
        await asyncio.wait_for(queue.put(msg), timeout=1.0)
    except (asyncio.TimeoutError, asyncio.QueueFull):
        pass
