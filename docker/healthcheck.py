"""Kontrollib, et salvesti põhiprotsess töötab ka R2 režiimis, kus veebiserverit pole."""

from pathlib import Path


def recorder_is_running():
    for cmdline in Path("/proc").glob("[0-9]*/cmdline"):
        try:
            command = cmdline.read_bytes().replace(b"\0", b" ")
        except (FileNotFoundError, PermissionError, ProcessLookupError):
            continue
        if b"recorder/kuku_recorder.py" in command and b"healthcheck.py" not in command:
            return True
    return False


raise SystemExit(0 if recorder_is_running() else 1)
