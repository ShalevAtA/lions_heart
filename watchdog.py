"""
# Watchdog process ("Windows session manager daemon")

The supervising loop.

`run_popup_once()` spawns one pop-up, waits for it, and returns its verdict:

- `ok`     — correct password entered.
- `stop`   — `config.STOP_PASSWORD` entered; the loop ends.
- `killed` — the pop-up died without reporting (e.g. from Task Manager).

IPC uses a temporary file, not a pipe, so a killed pop-up can never raise
`BrokenPipeError` here.  On `ok` the next pop-up is scheduled a random
`DELAY_MIN_SECONDS .. DELAY_MAX_SECONDS` later; on `killed` it is restarted
after `RESTART_GRACE_SECONDS`.
"""

from __future__ import annotations

import os
import random
import tempfile
import time

from config import (
    DELAY_MAX_SECONDS,
    DELAY_MIN_SECONDS,
    LOG_FILE,
    POPUP_PROCESS_NAME,
    RESTART_GRACE_SECONDS,
)
from launcher import launcher, spawn
from log import log


def run_popup_once(script: str) -> str:
    fd, result_path = tempfile.mkstemp(prefix="lh_", suffix=".txt")
    os.close(fd)

    popup_exe = launcher(POPUP_PROCESS_NAME)
    proc = spawn(popup_exe, [script, "--popup", "--result", result_path])
    proc.wait()  # returns as soon as the child exits, however it exits

    result = "killed"
    try:
        with open(result_path, encoding="utf-8") as fh:
            data = fh.read().strip()
        if data in ("ok", "stop"):
            result = data
    except Exception:
        pass
    finally:
        try:
            os.unlink(result_path)
        except OSError:
            pass

    return result


def watchdog_main(script: str) -> None:
    log(f"Watchdog started (PID {os.getpid()}). Log: {LOG_FILE}")
    while True:
        verdict = run_popup_once(script)

        if verdict == "stop":
            log("Stop password accepted — shutting the whole program down.")
            break

        if verdict == "ok":
            delay = random.randint(DELAY_MIN_SECONDS, DELAY_MAX_SECONDS)
            log(f"Password accepted. Next pop-up in {delay} s "
                f"({delay / 3600:.2f} h).")
            time.sleep(delay)
        else:
            log(f"Pop-up exited without a verdict (killed?). "
                f"Restarting in {RESTART_GRACE_SECONDS} s.")
            time.sleep(RESTART_GRACE_SECONDS)

    log("Watchdog exiting. Bye.")
