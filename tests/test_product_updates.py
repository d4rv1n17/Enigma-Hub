import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import enigma_hub as hub
import hub_products as versions


class ProductUpdateTests(unittest.TestCase):
    def test_equivalent_release_versions_ignore_padding_and_build_metadata(self):
        self.assertEqual(versions.version_key("2.0"), versions.version_key("v2.0.0+1234567"))
        self.assertEqual(versions.version_key("2.0.0.0"), versions.version_key("2.0.0"))
        self.assertEqual(versions.version_key("unknown"), ())
        self.assertEqual(versions.version_key("2.0-beta"), ())

    def test_update_worker_skips_equal_and_newer_installed_versions(self):
        for current in ("2.0", "2.0.0", "2.0.0.0", "2.1.0"):
            with self.subTest(current=current), tempfile.TemporaryDirectory() as folder:
                product = hub.PRODUCTS[1]
                executable = Path(folder) / product["exe"]
                executable.write_bytes(b"already installed")
                worker = hub.ProductWorker(product, "update", folder, current_version="1.0")
                result = []
                worker.done.connect(lambda *args: result.append(args))
                with patch.object(hub, "installed_version", return_value=current), patch.object(hub, "urlopen", return_value=io.BytesIO(b'{"tag_name":"v2.0.0","assets":[]}')) as request, patch.object(hub.subprocess, "run") as installer:
                    worker.run()
                self.assertEqual(result[0][0], "current")
                self.assertEqual(result[0][1], current)
                self.assertEqual(request.call_count, 1)
                installer.assert_not_called()
                self.assertEqual(executable.read_bytes(), b"already installed")

    def test_disk_prefers_executable_version_after_external_update(self):
        with tempfile.TemporaryDirectory() as folder:
            product = hub.PRODUCTS[1]
            (Path(folder) / product["exe"]).write_bytes(b"fixture")
            with patch.object(versions, "executable_version", return_value="2.1.0"), patch.object(versions, "registered_version", return_value="2.0.0"):
                self.assertEqual(versions.installed_version(product, folder), "2.1.0")

    def test_portable_disk_with_matching_release_digest_is_not_downloaded_again(self):
        import hashlib
        payload = b"same portable application"
        product = hub.PRODUCTS[1]
        release = {"tag_name": "v2.0.0", "assets": [{"name": product["asset"], "digest": "sha256:" + hashlib.sha256(payload).hexdigest(), "size": len(payload), "browser_download_url": "https://github.com/" + product["repo"] + "/releases/download/v2.0.0/" + product["asset"]}]}
        with tempfile.TemporaryDirectory() as folder:
            (Path(folder) / product["exe"]).write_bytes(payload)
            worker = hub.ProductWorker(product, "update", folder)
            result = []
            worker.done.connect(lambda *args: result.append(args))
            with patch.object(hub, "installed_version", return_value=None), patch.object(hub, "urlopen", return_value=io.BytesIO(json.dumps(release).encode())) as request:
                worker.run()
            self.assertEqual(result[0][0:3], ("current", "2.0.0", ""))
            self.assertEqual(request.call_count, 1)

    def test_registry_version_is_not_used_for_a_different_installation(self):
        import winreg
        with patch.object(winreg, "OpenKey"), patch.object(winreg, "QueryValueEx", side_effect=[(r"C:\Other\Enigma Cube", 1), ("99.0.0", 1)]):
            self.assertIsNone(versions.registered_version(hub.PRODUCTS[0], Path(r"C:\Portable\Enigma Cube")))
