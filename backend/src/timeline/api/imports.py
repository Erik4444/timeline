import asyncio
import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from timeline.config import settings
from timeline.database import get_db
from timeline.models.import_job import ImportJob
from timeline.parsers import detect_parser, list_parser_info
from timeline.pipeline.coordinator import get_progress_queue, remove_progress_queue, run_import
from timeline.schemas.import_job import ImportJobOut, ParserInfo

router = APIRouter()


@router.get("/parsers", response_model=list[ParserInfo])
def get_parsers():
    return list_parser_info()


@router.get("", response_model=list[ImportJobOut])
def list_imports(db: Session = Depends(get_db)):
    return db.query(ImportJob).order_by(ImportJob.created_at.desc()).all()


@router.get("/{job_id}", response_model=ImportJobOut)
def get_import(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ImportJob, job_id)
    if not job:
        raise HTTPException(404, "Job nicht gefunden")
    return job


@router.post("", response_model=ImportJobOut)
async def start_import(
    file: UploadFile = File(...),
    source: str = Form(...),
    db: Session = Depends(get_db),
):
    job_id = str(uuid.uuid4())
    import_dir = settings.data_dir / "imports" / job_id
    import_dir.mkdir(parents=True, exist_ok=True)

    original_filename = file.filename or "upload"
    dest = import_dir / original_filename
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    job = ImportJob(
        id=job_id,
        source=source,
        status="pending",
        file_path=str(dest),
        original_filename=original_filename,
    )
    db.add(job)
    db.commit()
    db.refresh(job)

    # Launch background task
    from timeline.database import SessionLocal
    asyncio.create_task(
        run_import(job_id, dest, source, lambda: SessionLocal())
    )

    return job


@router.get("/{job_id}/stream")
async def stream_progress(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ImportJob, job_id)
    if not job:
        raise HTTPException(404, "Job nicht gefunden")

    async def event_generator():
        import json
        queue = get_progress_queue(job_id)
        try:
            while True:
                try:
                    msg = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(msg)}\n\n"
                    if msg.get("type") in ("done", "error"):
                        break
                except asyncio.TimeoutError:
                    yield "data: {\"type\":\"ping\"}\n\n"
        finally:
            remove_progress_queue(job_id)

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
        },
    )


@router.post("/{job_id}/detect-parser")
async def detect_parser_for_file(job_id: str, db: Session = Depends(get_db)):
    job = db.get(ImportJob, job_id)
    if not job or not job.file_path:
        raise HTTPException(404, "Job nicht gefunden")
    path = Path(job.file_path)
    parser = detect_parser(path)
    if parser:
        return {"source_name": parser.SOURCE_NAME, "display_name": parser.DISPLAY_NAME}
    return {"source_name": None, "display_name": None}
