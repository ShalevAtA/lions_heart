"""
# Task Manager tripwire

When a visible `Taskmgr.exe` window appears, spawn a small topmost pop-up:

    "What are you doing ?"

Fires on the *rising edge* only (closed -> open) and at most once per
`INTRUDER_COOLDOWN_SECONDS`, so mashing Ctrl+Shift+Esc doesn't spawn an army
of windows. The alert is purely cosmetic — Task Manager keeps working and the
window closes normally. This is a joke, not a lockout.
"""

from __future__ import annotations

import ctypes
import os
import threading
import time
from ctypes import wintypes

from config import (
    INTRUDER_COOLDOWN_SECONDS,
    INTRUDER_MESSAGE,
    INTRUDER_POLL_SECONDS,
    INTRUDER_TARGET_IMAGE,
    POPUP_PROCESS_NAME,
)
from launcher import launcher, spawn
from log import log

user32 = ctypes.WinDLL("user32", use_last_error=True)
kernel32 = ctypes.WinDLL("kernel32", use_last_error=True)

PROCESS_QUERY_LIMITED_INFORMATION = 0x1000
WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

user32.EnumWindows.argtypes = [WNDENUMPROC, wintypes.LPARAM]
user32.IsWindowVisible.argtypes = [wintypes.HWND]
user32.GetWindowThreadProcessId.argtypes = [
    wintypes.HWND, ctypes.POINTER(wintypes.DWORD)
]
user32.GetClassNameW.argtypes = [wintypes.HWND, wintypes.LPWSTR, ctypes.c_int]
kernel32.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
kernel32.OpenProcess.restype = wintypes.HANDLE
kernel32.QueryFullProcessImageNameW.argtypes = [
    wintypes.HANDLE, wintypes.DWORD, wintypes.LPWSTR,
    ctypes.POINTER(wintypes.DWORD),
]
kernel32.CloseHandle.argtypes = [wintypes.HANDLE]


def _image_name(pid: int) -> str:
    h = kernel32.OpenProcess(PROCESS_QUERY_LIMITED_INFORMATION, False, pid)
    if not h:
        return ""
    try:
        buf = ctypes.create_unicode_buffer(1024)
        size = wintypes.DWORD(len(buf))
        if kernel32.QueryFullProcessImageNameW(h, 0, buf, ctypes.byref(size)):
            return os.path.basename(buf.value).lower()
        return ""
    finally:
        kernel32.CloseHandle(h)


def _class_name(hwnd) -> str:
    buf = ctypes.create_unicode_buffer(256)
    user32.GetClassNameW(hwnd, buf, 256)
    return buf.value


def task_manager_visible() -> bool:
    """True if any visible top-level window belongs to Task Manager."""
    found = [False]

    @WNDENUMPROC
    def cb(hwnd, _lparam):
        if not user32.IsWindowVisible(hwnd):
            return True
        # Fast path: window class is stable and localized-independent.
        if _class_name(hwnd).lower() == "taskmanagerwindow":
            found[0] = True
            return False
        # Fallback: ask the owning process (works if the class ever changes).
        pid = wintypes.DWORD()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
        if pid.value and _image_name(pid.value) == INTRUDER_TARGET_IMAGE:
            found[0] = True
            return False
        return True

    user32.EnumWindows(cb, 0)
    return found[0]


def intruder_main() -> None:
    """The 'what are you doing ?' window. Runs as its own process."""
    import tkinter as tk

    root = tk.Tk()
    root.title("...")
    root.attributes("-topmost", True)
    root.resizable(False, False)

    w, h = 360, 150
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 2}")

    tk.Label(root, text=INTRUDER_MESSAGE,
             font=("Segoe UI", 15, "bold")).pack(pady=(26, 6))
    tk.Label(root, text="(clue: task Manager wont help you delete me.)",
             fg="#666", font=("Segoe UI", 9)).pack()
    tk.Button(root, text="Nothing, sorry", width=16,
              font=("Segoe UI", 10), command=root.destroy).pack(pady=14)

    root.lift()
    root.focus_force()
    root.mainloop()


def watch_task_manager(script: str, stop: threading.Event) -> None:
    """Background thread. Polls cheaply; spawns the alert on rising edge."""
    armed = True
    last_fire = 0.0

    while not stop.is_set():
        visible = task_manager_visible()
        now = time.monotonic()

        if visible and armed and (now - last_fire) >= INTRUDER_COOLDOWN_SECONDS:
            spawn(launcher(POPUP_PROCESS_NAME), [script, "--intruder"])
            last_fire = now
            armed = False
            log("Task Manager opened — sending the 'what are you doing ?' pop-up.")
        elif not visible:
            armed = True   # re-arm once it closes

        stop.wait(INTRUDER_POLL_SECONDS)