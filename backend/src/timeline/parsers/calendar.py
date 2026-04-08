"""
Calendar Parser (.ics)

Supports:
- Google Calendar export (.ics from Google Takeout)
- Apple Calendar / iCloud export (.ics)
- Any standard iCalendar file

Each VEVENT becomes one timeline event.
"""
from __future__ import annotations

import logging
import zipfile
from datetime import datetime, date, timezone, timedelta
from pathlib import Path
from typing import Iterator

from icalendar import Calendar, Event as ICalEvent
from icalendar.prop import vDatetime, vDate, vDDDLists

from timeline.parsers.base import BaseParser, ParsedEvent

logger = logging.getLogger(__name__)


def _to_datetime(val) -> datetime | None:
    if val is None:
        return None
    if isinstance(val, datetime):
        if val.tzinfo is None:
            return val.replace(tzinfo=timezone.utc)
        return val.astimezone(timezone.utc)
    if isinstance(val, date):
        return datetime(val.year, val.month, val.day, tzinfo=timezone.utc)
    return None


class CalendarParser(BaseParser):
    SOURCE_NAME = "calendar"
    DISPLAY_NAME = "Kalender (.ics)"
    SUPPORTED_EXTENSIONS = [".ics", ".zip"]
    DESCRIPTION = "iCalendar-Dateien: Google Calendar, Apple Kalender, Outlook (.ics)"

    def can_handle(self, path: Path) -> bool:
        if path.is_file():
            if path.suffix.lower() == ".ics":
                return True
            if path.suffix.lower() == ".zip":
                try:
                    with zipfile.ZipFile(path) as zf:
                        return any(n.lower().endswith(".ics") for n in zf.namelist())
                except Exception:
                    return False
        if path.is_dir():
            return bool(list(path.glob("**/*.ics")) or list(path.glob("**/*.ICS")))
        return False

    def parse(self, path: Path) -> Iterator[ParsedEvent]:
        if path.is_file() and path.suffix.lower() == ".ics":
            yield from self._parse_ics_file(path)
        elif path.is_file() and path.suffix.lower() == ".zip":
            yield from self._parse_zip(path)
        elif path.is_dir():
            for ics_path in sorted(path.glob("**/*.ics")):
                yield from self._parse_ics_file(ics_path)

    def _parse_zip(self, zip_path: Path) -> Iterator[ParsedEvent]:
        import tempfile
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmpdir)
            for ics_path in sorted(Path(tmpdir).glob("**/*.ics")):
                yield from self._parse_ics_file(ics_path)

    def _parse_ics_file(self, path: Path) -> Iterator[ParsedEvent]:
        try:
            data = path.read_bytes()
            cal = Calendar.from_ical(data)
        except Exception as e:
            logger.warning("Failed to parse %s: %s", path, e)
            return

        cal_name = str(cal.get("X-WR-CALNAME", path.stem))

        for component in cal.walk():
            if component.name != "VEVENT":
                continue
            try:
                ev = self._parse_vevent(component, cal_name)
                if ev:
                    yield ev
            except Exception as e:
                logger.debug("Skipping VEVENT: %s", e)

    def _parse_vevent(self, component, cal_name: str) -> ParsedEvent | None:
        uid = str(component.get("UID", ""))
        summary = str(component.get("SUMMARY", "")).strip() or "(kein Titel)"
        description = str(component.get("DESCRIPTION", "")).strip() or None
        location = str(component.get("LOCATION", "")).strip() or None

        dtstart = _to_datetime(component.get("DTSTART").dt if component.get("DTSTART") else None)
        if dtstart is None:
            return None

        # Determine precision: all-day events have date precision
        raw_start = component.get("DTSTART")
        precision = "day" if isinstance(raw_start.dt if raw_start else None, date) and not isinstance(raw_start.dt if raw_start else None, datetime) else "second"

        # Duration / end
        dtend_raw = component.get("DTEND")
        dtend = _to_datetime(dtend_raw.dt if dtend_raw else None)

        duration_text = ""
        if dtend and dtend > dtstart:
            delta = dtend - dtstart
            hours, remainder = divmod(int(delta.total_seconds()), 3600)
            minutes = remainder // 60
            if hours > 0:
                duration_text = f" ({hours}h {minutes:02d}min)"
            elif minutes > 0:
                duration_text = f" ({minutes}min)"

        body_parts = []
        if description:
            body_parts.append(description)
        if duration_text:
            body_parts.append(f"Dauer:{duration_text}")
        if cal_name:
            body_parts.append(f"Kalender: {cal_name}")

        tags = ["kalender", cal_name.lower()[:30]]
        if location:
            tags.append("ort")

        return ParsedEvent(
            source="calendar",
            source_id=uid or f"cal_{dtstart.isoformat()}_{hash(summary) & 0xFFFFFFFF}",
            event_type="calendar_event",
            occurred_at=dtstart,
            occurred_at_precision=precision,
            title=summary,
            body="\n".join(body_parts) if body_parts else None,
            location_name=location,
            tags=tags,
            raw_data={
                "uid": uid,
                "summary": summary,
                "description": description,
                "location": location,
                "calendar": cal_name,
            },
        )
