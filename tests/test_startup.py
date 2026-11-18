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
            script = """import enigma_hub as h
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
original = h.Hub.__init__
def initialize(self):
    original(self)
    QTimer.singleShot(7000, QApplication.instance().quit)
h.Hub.__init__ = initialize
h.Hub.load_news = lambda self: None
h.Hub.check_updates = lambda self, silent=False: None
h.Hub.check_hub_update = lambda self: None
raise SystemExit(h.main())
"""
            command = [sys.executable, "-c", script]
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
                    try:
                        first.wait(timeout=12)
                    except subprocess.TimeoutExpired:
                        if sys.platform == "win32":
                            subprocess.run(["taskkill", "/PID", str(first.pid), "/T", "/F"], capture_output=True)
                        else:
                            first.kill()
                        first.wait(timeout=5)
            self.assertNotIn("Traceback", log.read_text())
