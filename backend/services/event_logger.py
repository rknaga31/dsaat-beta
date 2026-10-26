"""
Event Logger Service.
Maintains an in-memory chronological buffer and persistent disk audit trail
for system alerts, risk changes, and hardware events.
"""

import json
import logging
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Dict, Any, Optional

logger = logging.getLogger("event_logger")


class EventLogger:
    """Stores and retrieves historical events for frontend dashboards and safety auditing."""

    def __init__(self, max_buffer_size: int = 200, log_dir: Optional[str] = "logs"):
        self.buffer: deque = deque(maxlen=max_buffer_size)
        self.log_dir = Path(log_dir) if log_dir else None
        if self.log_dir:
            self.log_dir.mkdir(parents=True, exist_ok=True)
            self.file_path = self.log_dir / "system_events.jsonl"
        else:
            self.file_path = None

    def log_event(self, event_type: str, payload: Dict[str, Any]) -> Dict[str, Any]:
        """Records an event packet into memory and optionally writes to JSONL on disk."""
        event_record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event_type": event_type,
            "data": payload,
        }
        self.buffer.append(event_record)

        if self.file_path:
            try:
                with open(self.file_path, "a", encoding="utf-8") as f:
                    f.write(json.dumps(event_record) + "\n")
            except IOError as err:
                logger.error(f"Failed to append to disk log: {err}")

        return event_record

    def get_recent_events(
        self, limit: int = 50, event_type: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Retrieves recent events in reverse chronological order."""
        events = list(self.buffer)
        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]
        events.reverse()
        return events[:limit]

    def clear(self):
        """Clears in-memory buffer (primarily for unit tests)."""
        self.buffer.clear()


# Global singleton instance
event_logger = EventLogger()
