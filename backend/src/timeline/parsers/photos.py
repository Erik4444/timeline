"""
Local Photos Parser

Extracts EXIF metadata (date, GPS) from JPEG/HEIC/PNG images.
Falls back to file modification time if no EXIF date found.
"""
from __future__ import annotations

import json
import logging
import struct
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from timeline.parsers.base import BaseParser, ParsedEvent

logger = logging.getLogger(__name__)

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".heic", ".heif", ".png", ".tiff", ".tif", ".webp"}


def _exif_date_to_dt(exif_date_str: str) -> datetime | None:
    """Parse EXIF date string '2023:06:15 14:30:00' → datetime."""
    try:
        return datetime.strptime(exif_date_str, "%Y:%m:%d %H:%M:%S").replace(tzinfo=timezone.utc)
    except (ValueError, TypeError):
        return None


def _dms_to_decimal(dms, ref: str) -> float | None:
    """Convert EXIF GPS DMS tuple to decimal degrees."""
    try:
        d = float(dms[0])
        m = float(dms[1])
        s = float(dms[2])
        decimal = d + m / 60.0 + s / 3600.0
        if ref in ("S", "W"):
            decimal = -decimal
        return decimal
    except (TypeError, IndexError, ZeroDivisionError):
        return None


def _get_exif_data(path: Path) -> dict:
    """Extract EXIF data using piexif (JPEG only)."""
    if path.suffix.lower() not in {".jpg", ".jpeg"}:
        return {}
    try:
        import piexif
        exif = piexif.load(str(path))
        result = {}

        # Date
        zeroth = exif.get("0th", {})
        exif_ifd = exif.get("Exif", {})
        gps = exif.get("GPS", {})

        date_tag = exif_ifd.get(piexif.ExifIFD.DateTimeOriginal) or zeroth.get(piexif.ImageIFD.DateTime)
        if date_tag:
            dt = _exif_date_to_dt(date_tag.decode("ascii", errors="replace"))
            if dt:
                result["datetime"] = dt

        # GPS
        if gps:
            lat_dms = gps.get(piexif.GPSIFD.GPSLatitude)
            lat_ref = gps.get(piexif.GPSIFD.GPSLatitudeRef)
            lng_dms = gps.get(piexif.GPSIFD.GPSLongitude)
            lng_ref = gps.get(piexif.GPSIFD.GPSLongitudeRef)

            if lat_dms and lat_ref and lng_dms and lng_ref:
                # piexif returns tuples of (numerator, denominator)
                lat_dms_f = [n / d if d else 0 for n, d in lat_dms]
                lng_dms_f = [n / d if d else 0 for n, d in lng_dms]
                lat = _dms_to_decimal(lat_dms_f, lat_ref.decode("ascii", errors="replace"))
                lng = _dms_to_decimal(lng_dms_f, lng_ref.decode("ascii", errors="replace"))
                if lat is not None and lng is not None:
                    result["lat"] = lat
                    result["lng"] = lng

        # Camera model
        make = zeroth.get(piexif.ImageIFD.Make)
        model = zeroth.get(piexif.ImageIFD.Model)
        if make:
            result["make"] = make.decode("ascii", errors="replace").strip("\x00")
        if model:
            result["model"] = model.decode("ascii", errors="replace").strip("\x00")

        return result
    except Exception as e:
        logger.debug("EXIF extraction failed for %s: %s", path, e)
        return {}


class PhotosParser(BaseParser):
    SOURCE_NAME = "photos"
    DISPLAY_NAME = "Fotos & Bilder"
    SUPPORTED_EXTENSIONS = list(IMAGE_EXTENSIONS) + [".zip"]
    DESCRIPTION = "Lokale Fotos mit EXIF-Daten (Datum, GPS-Koordinaten). JPEG, HEIC, PNG, TIFF."

    def can_handle(self, path: Path) -> bool:
        if path.is_file():
            return path.suffix.lower() in IMAGE_EXTENSIONS
        if path.is_dir():
            return any(True for _ in self._find_images(path))
        return False

    def parse(self, path: Path) -> Iterator[ParsedEvent]:
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS:
            ev = self._parse_image(path)
            if ev:
                yield ev
        elif path.is_dir():
            for img_path in self._find_images(path):
                try:
                    ev = self._parse_image(img_path)
                    if ev:
                        yield ev
                except Exception as e:
                    logger.debug("Skipping %s: %s", img_path, e)

    def _find_images(self, directory: Path) -> Iterator[Path]:
        for ext in IMAGE_EXTENSIONS:
            yield from directory.rglob(f"*{ext}")
            yield from directory.rglob(f"*{ext.upper()}")

    def _parse_image(self, path: Path) -> ParsedEvent | None:
        exif = _get_exif_data(path)

        # Determine datetime
        dt = exif.get("datetime")
        if dt is None:
            mtime = path.stat().st_mtime
            dt = datetime.fromtimestamp(mtime, tz=timezone.utc)
            precision = "second"
        else:
            precision = "second"

        lat = exif.get("lat")
        lng = exif.get("lng")

        camera = exif.get("model") or exif.get("make")
        tags = ["foto"]
        if camera:
            tags.append(camera.lower()[:20])
        if lat and lng:
            tags.append("gps")

        stat = path.stat()
        title = path.name
        body_parts = []
        if camera:
            body_parts.append(f"Kamera: {camera}")
        if lat and lng:
            body_parts.append(f"GPS: {lat:.5f}, {lng:.5f}")

        return ParsedEvent(
            source="photos",
            source_id=f"{path.name}_{stat.st_size}_{dt.isoformat()}",
            event_type="photo",
            occurred_at=dt,
            occurred_at_precision=precision,
            title=title,
            body="\n".join(body_parts) or None,
            location_lat=lat,
            location_lng=lng,
            tags=tags,
            media_paths=[path],
            raw_data={
                "filename": path.name,
                "size": stat.st_size,
                "exif": {k: str(v) for k, v in exif.items() if k != "datetime"},
            },
        )
