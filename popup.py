"""
# Pop-up process ("lions_heart")

Shows the password window and writes the verdict to the result file.

One password is chosen at random from `config.PASSWORDS` each time.  Typing
`config.STOP_PASSWORD` instead writes a `stop` verdict and ends the program.
Closing the window via the **X** is refused; only the Unlock button (or
Return) submits.
"""

from __future__ import annotations

import random

from config import ACCEPT_ANY_FROM_SET, PASSWORDS, POPUP_PROCESS_NAME, STOP_PASSWORD
from log import log


def popup_main(result_path: str | None) -> None:
    import tkinter as tk

    required = random.choice(PASSWORDS)
    outcome = ["ok"]  # mutable container so the nested closure can set it

    root = tk.Tk()
    root.title(POPUP_PROCESS_NAME)
    root.attributes("-topmost", True)
    root.resizable(False, False)

    w, h = 400, 210
    sw, sh = root.winfo_screenwidth(), root.winfo_screenheight()
    root.geometry(f"{w}x{h}+{(sw - w) // 2}+{(sh - h) // 3}")

    tk.Label(root, text="Enter password",
             font=("Segoe UI", 13, "bold")).pack(pady=(22, 8))

    entry = tk.Entry(root, show="•", width=26,
                     font=("Segoe UI", 12), justify="center")
    entry.pack(pady=4)

    msg = tk.Label(root, text="", fg="#b00020", font=("Segoe UI", 9))
    msg.pack(pady=(4, 2))

    def submit(_event=None) -> None:
        value = entry.get()
        if value == STOP_PASSWORD:
            outcome[0] = "stop"
            root.destroy()
            return
        unlocked = value == required or (ACCEPT_ANY_FROM_SET and value in PASSWORDS)
        if unlocked:
            outcome[0] = "ok"
            root.destroy()
            return
        msg.config(text="Incorrect password.")
        entry.delete(0, tk.END)

    tk.Button(root, text="Unlock", width=14, command=submit,
              font=("Segoe UI", 10)).pack(pady=10)
    root.bind("<Return>", submit)
    root.protocol("WM_DELETE_WINDOW",
                  lambda: msg.config(text="You must enter the password."))

    entry.focus_force()
    root.after(50, lambda: root.focus_force())
    root.lift()
    root.mainloop()

    if result_path:
        try:
            with open(result_path, "w", encoding="utf-8") as fh:
                fh.write(outcome[0])
        except Exception as exc:
            log(f"Popup could not write result: {exc!r}")
