"""Spotify Streaming History Parser"""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator

from timeline.parsers.base import BaseParser, ParsedEvent

logger = logging.getLogger(__name__)


class SpotifyParser(BaseParser):
    SOURCE_NAME = "spotify"
    DISPLAY_NAME = "Spotify"
    SUPPORTED_EXTENSIONS = [".json", ".zip"]
    DESCRIPTION = "Spotify Streaming-Verlauf (Einstellungen > Datenschutz > Daten herunterladen)"

    def can_handle(self, path: Path) -> bool:
        if path.is_file() and path.suffix == ".json":
            return "StreamingHistory" in path.name or "Streaming_History" in path.name
        if path.is_dir():
            return bool(list(path.glob("StreamingHistory*.json")) or list(path.glob("Streaming_History*.json")))
        return False

    def parse(self, path: Path) -> Iterator[ParsedEvent]:
        files = [path] if path.is_file() else (
            sorted(path.glob("StreamingHistory*.json")) +
            sorted(path.glob("Streaming_History*.json"))
        )
        for json_file in files:
            try:
                records = json.loads(json_file.read_text(encoding="utf-8"))
            except Exception as e:
                logger.warning("Failed to read %s: %s", json_file, e)
                continue
            for record in records:
                try:
                    ev = self._parse_record(record)
                    if ev:
                        yield ev
                except Exception as e:
                    logger.debug("Skipping record: %s", e)

    def _parse_record(self, r: dict) -> ParsedEvent | None:
        # New format uses 'master_metadata_track_name', old uses 'trackName'
        artist = r.get("master_metadata_album_artist_name") or r.get("artistName", "")
        track = r.get("master_metadata_track_name") or r.get("trackName", "")
        if not artist and not track:
            return None

        end_time = r.get("ts") or r.get("endTime", "")
        if not end_time:
            return None

        try:
            end_time = end_time.replace(" ", "T")
            if not end_time.endswith("Z") and "+" not in end_time[10:]:
                end_time += "Z"
            played_at = datetime.fromisoformat(end_time.replace("Z", "+00:00"))
        except ValueError:
            return None

        ms_played = r.get("ms_played") or r.get("msPlayed", 0)
        duration_s = ms_played // 1000

        title = f"{artist} – {track}" if artist and track else (artist or track)
        body = f"Gehört für {duration_s}s" if duration_s else None

        return ParsedEvent(
            source="spotify",
            source_id=f"{end_time}_{artist}_{track}",
            event_type="music_play",
            occurred_at=played_at,
            title=title,
            body=body,
            tags=["musik", "spotify"] + ([artist.lower()[:30]] if artist else []),
            raw_data=r,
        )
