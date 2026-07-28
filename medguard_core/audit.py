from __future__ import annotations

import json
import time
from collections import deque
from pathlib import Path
from typing import Any

from .config import MedGuardConfig


class AuditLogger:
    """Stores recent dashboard events and optionally appends JSONL audit logs."""

    def __init__(self, config: MedGuardConfig):
        self.config = config
        self._events: deque[dict[str, Any]] = deque(maxlen=100)
        self._next_id = 1
        self._file = None
        if config.audit_enabled:
            path = Path(config.audit_log_path)
            path.parent.mkdir(parents=True, exist_ok=True)
            self._file = path.open("a", encoding="utf-8")

    def log(self, event: str, data: dict[str, Any]) -> None:
        entry = {
            "id": self._next_id,
            "timestamp": time.time(),
            "event": event,
            **data,
        }
        self._next_id += 1
        self._events.append(entry)
        if self._file:
            self._file.write(json.dumps(entry, ensure_ascii=False) + "\n")
            self._file.flush()

    def recent(self) -> list[dict[str, Any]]:
        return list(reversed(self._events))

    def close(self) -> None:
        if self._file:
            self._file.close()
