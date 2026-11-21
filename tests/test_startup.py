"""Launch the real entry point, including the local activation channel."""
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest


class StartupTests(unittest.TestCase):
    def test_product_request_is_forwarded_to_existing_hub(self):
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as folder:
            environment = dict(os.environ, APPDATA=folder)
            script = """import os, json
from pathlib import Path
import enigma_hub as h
from PyQt5.QtCore import QTimer
from PyQt5.QtWidgets import QApplication
original = h.Hub.__init__
def initialize(self):
    original(self)
    QTimer.singleShot(7000, QApplication.instance().quit)
h.Hub.__init__ = initialize
h.Hub.load_news = lambda self: None
h.Hub.check_updates = lambda *args, **kwargs: None
h.Hub.check_hub_update = lambda *args, **kwargs: None
h.Hub.ecosystem_request = lambda self, request: Path(os.environ['APPDATA'], 'request.json').write_text(json.dumps(request))
raise SystemExit(h.main())
"""
            command = [sys.executable, '-c', script]
            with (Path(folder) / 'process.log').open('w') as log:
                first = subprocess.Popen(command, cwd=root, env=environment, stdout=log, stderr=log)
                try:
                    time.sleep(3)
                    second = subprocess.run(command + ['--product', 'disk', '--action', 'launch', '--product-exe', 'C:/Apps/Enigma Disk/EnigmaDisk.exe'],
                                            cwd=root, env=environment, stdout=log, stderr=log, timeout=10)
                    self.assertEqual(second.returncode, 0)
                    received = Path(folder) / 'request.json'
                    deadline = time.monotonic() + 2
                    while not received.exists() and time.monotonic() < deadline:
                        time.sleep(.05)
                    import json
                    request = json.loads(received.read_text())
                    self.assertEqual(request['product'], 'disk')
                    self.assertEqual(request['action'], 'launch')
                    self.assertEqual(request['exe'], 'C:/Apps/Enigma Disk/EnigmaDisk.exe')
                    self.assertIsNone(first.poll())
                finally:
                    first.wait(timeout=12)
            self.assertNotIn('Traceback', (Path(folder) / 'process.log').read_text())

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
