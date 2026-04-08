"""
WhatsApp Chat Export Parser

Supports:
- WhatsApp .txt export format (both iOS and Android variants)
- WhatsApp JSON export (if available)

Each message becomes one event. Chat title is derived from filename.
"""
from __future__ import annotations

import json
import logging
import re
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

import chardet

from timeline.parsers.base import BaseParser, ParsedEvent

logger = logging.getLogger(__name__)

# iOS: [DD.MM.YY, HH:MM:SS] Author: Message
# Android: DD.MM.YY, HH:MM - Author: Message  (or with AM/PM)
_PATTERNS = [
    # iOS format: [01.01.24, 14:30:00] Name: text
    re.compile(
        r"^\[(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4}),\s*(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\]\s*(?P<author>[^:]+?):\s*(?P<msg>.+)$",
        re.IGNORECASE,
    ),
    # Android format: 01.01.24, 14:30 - Name: text
    re.compile(
        r"^(?P<date>\d{1,2}[./]\d{1,2}[./]\d{2,4}),\s*(?P<time>\d{1,2}:\d{2}(?::\d{2})?(?:\s*[AP]M)?)\s*-\s*(?P<author>[^:]+?):\s*(?P<msg>.+)$",
        re.IGNORECASE,
    ),
]

_DATE_FORMATS = [
    "%d.%m.%y", "%d.%m.%Y", "%m/%d/%y", "%m/%d/%Y",
    "%d/%m/%y", "%d/%m/%Y",
]
_TIME_FORMATS = ["%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p"]


def _parse_datetime(date_str: str, time_str: str) -> datetime | None:
    time_str = time_str.strip()
    for df in _DATE_FORMATS:
        for tf in _TIME_FORMATS:
            try:
                dt = datetime.strptime(f"{date_str} {time_str}", f"{df} {tf}")
                return dt.replace(tzinfo=timezone.utc)
            except ValueError:
                continue
    return None


def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    detected = chardet.detect(raw)
    enc = detected.get("encoding") or "utf-8"
    return raw.decode(enc, errors="replace")


class WhatsAppParser(BaseParser):
    SOURCE_NAME = "whatsapp"
    DISPLAY_NAME = "WhatsApp"
    SUPPORTED_EXTENSIONS = [".txt", ".zip"]
    DESCRIPTION = "WhatsApp Chatverlauf Export (.txt oder .zip mit _chat.txt)"

    def can_handle(self, path: Path) -> bool:
        if path.is_file():
            if path.suffix == ".txt":
                # Quick peek for WhatsApp date pattern
                try:
                    sample = path.read_bytes()[:2000].decode("utf-8", errors="replace")
                    return any(p.search(sample) for p in _PATTERNS)
                except Exception:
                    return False
            if path.suffix == ".zip":
                try:
                    with zipfile.ZipFile(path) as zf:
                        return any("_chat.txt" in n or n.endswith(".txt") for n in zf.namelist())
                except Exception:
                    return False
        if path.is_dir():
            return bool(list(path.glob("*.txt")) or list(path.glob("**/_chat.txt")))
        return False

    def parse(self, path: Path) -> Iterator[ParsedEvent]:
        txt_files: list[tuple[str, Path | None, str]] = []  # (chat_name, media_dir, text)

        if path.is_file() and path.suffix == ".zip":
            yield from self._parse_zip(path)
            return

        if path.is_file() and path.suffix == ".txt":
            txt_files.append((path.stem, None, _read_text(path)))

        elif path.is_dir():
            for txt_path in sorted(path.glob("**/*.txt")):
                txt_files.append((txt_path.stem, txt_path.parent, _read_text(txt_path)))

        for chat_name, _media_dir, text in txt_files:
            yield from self._parse_text(text, chat_name)

    def _parse_zip(self, zip_path: Path) -> Iterator[ParsedEvent]:
        import tempfile, os
        with tempfile.TemporaryDirectory() as tmpdir:
            with zipfile.ZipFile(zip_path) as zf:
                zf.extractall(tmpdir)
            tmp = Path(tmpdir)
            for txt_path in sorted(tmp.glob("**/*.txt")):
                text = _read_text(txt_path)
                yield from self._parse_text(text, txt_path.stem)

    def _parse_text(self, text: str, chat_name: str) -> Iterator[ParsedEvent]:
        lines = text.splitlines()
        current: dict | None = None

        for line in lines:
            matched = False
            for pattern in _PATTERNS:
                m = pattern.match(line)
                if m:
                    if current:
                        ev = self._make_event(current, chat_name)
                        if ev:
                            yield ev
                    dt = _parse_datetime(m.group("date"), m.group("time"))
                    if dt:
                        current = {
                            "dt": dt,
                            "author": m.group("author").strip(),
                            "msg": m.group("msg").strip(),
                        }
                    matched = True
                    break

            if not matched and current:
                # Continuation of previous message
                current["msg"] += "\n" + line

        if current:
            ev = self._make_event(current, chat_name)
            if ev:
                yield ev

    def _make_event(self, data: dict, chat_name: str) -> ParsedEvent | None:
        msg = data["msg"].strip()
        if not msg or msg in ("<Medien ausgeschlossen>", "<Media omitted>", "‎image omitted", "‎video omitted"):
            return None
        author = data["author"]
        title = f"{author} in {chat_name}"
        source_id = f"{chat_name}_{data['dt'].isoformat()}_{author}_{hash(msg) & 0xFFFFFFFF}"
        return ParsedEvent(
            source="whatsapp",
            source_id=source_id,
            event_type="message",
            occurred_at=data["dt"],
            title=title,
            body=msg,
            tags=["whatsapp", "chat", chat_name.lower()[:30]],
            raw_data={"author": author, "chat": chat_name, "message": msg},
        )
