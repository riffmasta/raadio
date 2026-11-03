"""Kontrollib protsessi ja salvesti viimast edukat tsüklit (ka R2 režiimis)."""

import os
import time
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


def heartbeat_is_fresh():
    heartbeat = Path(os.environ.get("RAADIO_STATE_DIR", "/state")) / "heartbeat"
    try:
        return 0 <= time.time() - heartbeat.stat().st_mtime < 180
    except OSError:
        return False


if __name__ == "__main__":
    raise SystemExit(0 if recorder_is_running() and heartbeat_is_fresh() else 1)
