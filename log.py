"""
# Logging

Append a timestamped line to `config.LOG_FILE` (best effort; never raises).
"""

from __future__ import annotations

from datetime import datetime

from config import LOG_FILE


def log(message: str) -> None:
    try:
        line = f"[{datetime.now().isoformat(timespec='seconds')}] {message}"
        with open(LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
        print(line, flush=True)
    except Exception:
        pass
