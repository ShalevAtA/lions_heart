# lions_heart

A small python Windows tool.
originally built for the great noga L. 

Two processes appear in Task Manager:
| Process name                     | Role                       |
|----------------------------------|----------------------------|
| `Windows session manager daemon` | Supervisor (watchdog)      |
| `lions_heart`                    | The popup        |

A popup asks for a password (picked at random from a small set). Getting it right buys you a delay before the next one. Typing the **stop password** shuts the whole thing down permanently.

> ⚠️ Windows only. Uses `ctypes` + Win32 APIs (`user32`, `kernel32`) and copies of `pythonw.exe`.

---

## Features

- **Random password gate** — one of `config.PASSWORDS` is chosen every time the pop-up is created.
- **Watchdog** — if the pop-up is killed, it is restarted after `RESTART_GRACE_SECONDS` (5 s).
- **Process renaming** — the interpreter is copied into `%LOCALAPPDATA%\MicrosoftEdgeCache` under names like `lions_heart.exe` and `Windows session manager daemon.exe`, so Task Manager's *Name* column shows those names instead of `pythonw.exe`.
- **Detached processes** — spawned with `DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP`, so the two aren't grouped and killing one doesn't take down the other.
- **Task Manager tripwire** — opening `taskmgr.exe` pops up a warning window.
- **Ghost typing** — ~50 % of printable keystrokes in the popup are silently swallowed.
- **Startup persistence** — writes `run_tool.bat` into the user's Startup folder on first run.
- **logging** to `%LOCALAPPDATA%\lions_heart.log`.

---

## Files

lions_heart.py entry point + process-mode dispatch
config.py tunable constants (passwords, delays, names, flags)
log.py timestamped best-effort logging
launcher.py copies/renames pythonw.exe and spawns detached children
popup.py the Tk password window
watchdog.py the supervising loop (waits for pop-up verdicts)
intruder.py Task Manager tripwire + its pop-up


---

## Requirements

- Windows
- Python 3.9+ (uses `from __future__ import annotations`)
- Tkinter (bundled with the standard python.org installer)

No third-party packages.

---

## Running

python lions_heart.py # console + log lines
pythonw lions_heart.py # silent


On first launch the script rexecutes itself from `%LOCALAPPDATA%\MicrosoftEdgeCache\Windows session manager daemon.exe` and exits. The renamed process is the real supervisor.

---

## Stopping

Type the value of `config.STOP_PASSWORD` into the pop-up and submit. The watchdog sees the `stop` verdict and exits the whole program. There is no other clean shutdown the pop-up's **X** button is deliberately disabled.

---

## Configuration (`config.py`)

| Constant | Meaning |
|---|---|
| `PASSWORDS` | Pool the unlock password is drawn from (`password`, `password1`–`4`). |
| `STOP_PASSWORD` | Typing this permanently terminates the program. |
| `DELAY_MIN_SECONDS` / `DELAY_MAX_SECONDS` | Delay after a correct password. Defaults are **60 / 180 seconds** (the module docstring's "1–3 h" note is stale). Override with `LIONS_HEART_MIN_DELAY` / `LIONS_HEART_MAX_DELAY` (env vars, in **seconds**). |
| `RESTART_GRACE_SECONDS` | Delay before restarting a popup that died without a verdict. |
| `ACCEPT_ANY_FROM_SET` | If `True`, any password from `PASSWORDS` unlocks. |
| `CACHE_DIR_NAME` | Folder under `%LOCALAPPDATA%` holding the renamed `pythonw.exe` copies. |
| `LOG_FILE` | `%LOCALAPPDATA%\lions_heart.log`. |
| `GHOST_TYPING_ENABLED` | Toggle the keyswallowing behaviour. |
| `GHOST_TYPE_SKIP_CHANCE` | Fraction of printable keys dropped (0.0 - 1.0). |
| `INTRUDER_MESSAGE` / cooldown / poll | Text and timing for the Task Manager tripwire. |

---

## How the pieces fit together
lions_heart.py
│ first launch
├─ ensure_startup_bat() → %APPDATA%...\Startup\run_tool.bat
├─ launcher(WATCHDOG_PROCESS_NAME) → ...\MicrosoftEdgeCache\Windows session manager daemon.exe
└─ spawn(exe, [SCRIPT]) ← this is now the watchdog process
│
└─ watchdog_main()
├─ thread: watch_task_manager() (intruder pop-ups)
└─ loop: run_popup_once()
├─ launcher(POPUP_PROCESS_NAME)
├─ spawn(popup exe, --popup --result <tmpfile>)
└─ read verdict: ok / stop / killed


**IPC** between the popup and the watchdog is a temporary **result file**, not a pipe so a killed popup can never raise `BrokenPipeError` in the watchdog.

**Verdicts:**

- `ok` → next popup after a random `DELAY_MIN_SECONDS … DELAY_MAX_SECONDS`.
- `stop` → watchdog logs the shutdown and exits.
- `killed` (or pop-up exited without writing) → restart after `RESTART_GRACE_SECONDS`.

---

## Caveats

- The **startup `.bat`** hard-codes `C:\Scripts\lions_heart.py`. Move the script there, or edit `ensure_startup_bat()` in `lions_heart.py`, or the startup entry won't work after a reboot.
- The renamed `pythonw.exe` copies live outside their install directory, so `launcher.python_env()` fixes `PATH` / `PYTHONHOME` so the copied interpreter can still find `python3XX.dll`, `python3.dll`, and the standard library.
- The "1–3 h" note in `config.py`'s docstring is out of date; the shipped defaults are **1–3 minutes**.
