"""Launch the real entry point, including the local activation channel."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


class StartupTests(unittest.TestCase):
    def test_reopening_activates_first_instance_without_exiting_it(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            environment = dict(os.environ, APPDATA=folder)
            command = [sys.executable, str(root / "enigma_hub.py")]
            log = Path(folder) / "process.log"
            with log.open("w") as output:
                first = subprocess.Popen(command, cwd=root, env=environment, stdout=output, stderr=output)
                try:
                    time.sleep(3)
                    self.assertIsNone(first.poll(), "Hub exited during startup")
                    second = subprocess.run(command, cwd=root, env=environment, stdout=output, stderr=output, timeout=10)
                    self.assertEqual(second.returncode, 0)
                    self.assertIsNone(first.poll(), "Opening Hub again terminated the original instance")
                finally:
                    if first.poll() is None:
                        first.terminate()
                    first.wait(timeout=10)
            self.assertNotIn("Traceback", log.read_text())
