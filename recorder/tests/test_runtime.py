"""Container lifecycle checks without network access or live radio streams."""
import importlib.util
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location("healthcheck", ROOT / "docker/healthcheck.py")
healthcheck = importlib.util.module_from_spec(spec)
spec.loader.exec_module(healthcheck)


class RuntimeTests(unittest.TestCase):
    def test_missing_and_stale_heartbeat_are_unhealthy(self):
        with tempfile.TemporaryDirectory() as folder, patch.dict(os.environ, {"RAADIO_STATE_DIR": folder}):
            self.assertFalse(healthcheck.heartbeat_is_fresh())
            heartbeat = Path(folder) / "heartbeat"
            heartbeat.touch()
            self.assertTrue(healthcheck.heartbeat_is_fresh())
            old = time.time() - 181
            os.utime(heartbeat, (old, old))
            self.assertFalse(healthcheck.heartbeat_is_fresh())

    @unittest.skipIf(sys.platform == "win32", "Docker uses Linux file locks")
    def test_single_instance_and_sigterm_waits_for_recording_to_save(self):
        # Exercise the real run loop and signals in separate processes. The worker
        # stands in for record(), including its final save before removing active.
        source = '''
import threading, time
from pathlib import Path
import kuku_recorder as k
r = k.Recorder()
r.start_web = lambda: None
def finish():
    while "job" not in r.cancel:
        time.sleep(.02)
    time.sleep(.1)
    (k.STATE_DIR / "saved").write_text("recording finalized")
    with r.lock:
        r.active.pop("job")
def tick():
    if not r.active:
        r.active["job"] = {}
        threading.Thread(target=finish, daemon=True).start()
r.tick = tick
r.run()
'''
        with tempfile.TemporaryDirectory() as folder:
            env = dict(os.environ, PYTHONPATH=str(ROOT / "recorder"),
                       RAADIO_ENV_CONFIG="1", RAADIO_DOCKER="1",
                       RAADIO_CONF=folder + "/missing.env", RAADIO_STATE_DIR=folder,
                       STORAGE="local", LOCAL_DIR=folder + "/recordings")
            first = subprocess.Popen([sys.executable, "-c", source], env=env,
                                     stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
            try:
                deadline = time.monotonic() + 10
                while not (Path(folder) / "heartbeat").exists():
                    if first.poll() is not None or time.monotonic() > deadline:
                        self.fail("Recorder did not start")
                    time.sleep(.02)
                second = subprocess.run([sys.executable, "-c", source], env=env,
                                        capture_output=True, text=True, timeout=5)
                self.assertNotEqual(second.returncode, 0)
                self.assertIn("Salvesti juba töötab", second.stderr)
                first.terminate()
                output, _ = first.communicate(timeout=5)
                self.assertEqual(first.returncode, 0, output)
                self.assertEqual((Path(folder) / "saved").read_text(), "recording finalized")
            finally:
                if first.poll() is None:
                    first.kill()
                    first.communicate()


if __name__ == "__main__":
    unittest.main()
