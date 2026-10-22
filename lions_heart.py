#!/usr/bin/env python3
"""
# lions_heart

A Windows password gate with a watchdog, for a consented machine.

Two separate processes are visible in Task Manager:

- **Windows session manager daemon** — the supervisor (watchdog).
- **lions_heart** — the pop-up that asks for the password.

## Module map

- `config`   — tunable constants (passwords, delays, names).
- `log`      — best-effort timestamped logging.
- `launcher` — copies/renames the interpreter and spawns detached children.
- `popup`    — the Tk password window.
- `watchdog` — the supervising loop.
- `lions_heart` (this file) — the entry point and process-mode dispatch.

## Running

```
python  lions_heart.py     # console + log lines
pythonw lions_heart.py     # silent
```

Entering `config.STOP_PASSWORD` in the pop-up shuts the whole program down.
"""

from __future__ import annotations

import os
import sys

from config import WATCHDOG_PROCESS_NAME
from launcher import launcher, spawn
from log import log
from popup import popup_main
from watchdog import watchdog_main

# Absolute path to this entry script — needed when re-spawning ourselves.
try:
    SCRIPT: str = os.path.abspath(__file__)
except NameError:
    SCRIPT = os.path.abspath(sys.argv[0])


def already_renamed_as(target: str) -> bool:
    name = os.path.splitext(os.path.basename(sys.executable))[0]
    return name == target


def main() -> None:
    # ---- pop-up mode ------------------------------------------------------
    if "--intruder" in sys.argv:
        try:
            from intruder import intruder_main
            intruder_main()
        except Exception as exc:
            log(f"Intruder popup crashed: {exc!r}")
        return
    if "--popup" in sys.argv:
        result_path = None
        if "--result" in sys.argv:
            i = sys.argv.index("--result")
            if i + 1 < len(sys.argv):
                result_path = sys.argv[i + 1]
        try:
            popup_main(result_path)
        except Exception as exc:
            log(f"Popup crashed: {exc!r}")
            # Write "ok" so the watchdog does not restart us in a tight loop.
            if result_path:
                try:
                    with open(result_path, "w", encoding="utf-8") as fh:
                        fh.write("ok")
                except Exception:
                    pass
        return

    # ---- watchdog mode ---------------------------------------------------
    if not already_renamed_as(WATCHDOG_PROCESS_NAME):
        # First launch — relaunch ourselves from the renamed exe and exit.
        exe = launcher(WATCHDOG_PROCESS_NAME)
        spawn(exe, [SCRIPT])
        return

    watchdog_main(SCRIPT)


if __name__ == "__main__":
    main()
