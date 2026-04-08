"""
Media processor: copies files to data/media/, generates thumbnails.
"""
from __future__ import annotations

import hashlib
import logging
import mimetypes
import shutil
import uuid
from pathlib import Path

from timeline.config import settings

logger = logging.getLogger(__name__)


def process_media_file(source_path: Path) -> dict | None:
    """
    Copy a media file into data/media/ and generate a thumbnail.
    Returns dict with file_path, thumbnail_path, mime_type, width, height, file_size.
    """
    if not source_path.exists():
        return None

    media_dir = settings.data_dir / "media"
    thumb_dir = settings.data_dir / "media" / "thumbnails"
    media_dir.mkdir(parents=True, exist_ok=True)
    thumb_dir.mkdir(parents=True, exist_ok=True)

    # Use content hash for deduplication
    file_hash = _file_hash(source_path)
    dest_name = f"{file_hash}{source_path.suffix.lower()}"
    dest_path = media_dir / dest_name

    if not dest_path.exists():
        shutil.copy2(source_path, dest_path)

    mime_type = mimetypes.guess_type(str(dest_path))[0]
    file_size = dest_path.stat().st_size

    width = height = None
    thumbnail_path = None

    if mime_type and mime_type.startswith("image/"):
        width, height, thumbnail_path = _make_thumbnail(dest_path, thumb_dir, file_hash)

    return {
        "file_path": str(dest_path.relative_to(settings.data_dir)),
        "thumbnail_path": str(thumbnail_path.relative_to(settings.data_dir)) if thumbnail_path else None,
        "mime_type": mime_type,
        "width": width,
        "height": height,
        "file_size": file_size,
    }


def _file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:32]


def _make_thumbnail(
    image_path: Path, thumb_dir: Path, file_hash: str
) -> tuple[int | None, int | None, Path | None]:
    try:
        from PIL import Image, UnidentifiedImageError
        thumb_path = thumb_dir / f"{file_hash}_thumb.jpg"
        if not thumb_path.exists():
            with Image.open(image_path) as img:
                img.thumbnail((settings.thumbnail_max_size, settings.thumbnail_max_size))
                rgb = img.convert("RGB")
                rgb.save(thumb_path, "JPEG", quality=85, optimize=True)
        # Get dimensions from original
        with Image.open(image_path) as img:
            w, h = img.size
        return w, h, thumb_path
    except Exception as e:
        logger.debug("Thumbnail generation failed for %s: %s", image_path, e)
        return None, None, None
