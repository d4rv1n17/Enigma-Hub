"""Security regressions in update validation and installer target handling."""
import io
import json
import hashlib
from pathlib import Path
import tempfile
import sys
import unittest
from unittest.mock import patch

import hub_update
import hub_setup


class UpdateSecurityTests(unittest.TestCase):
    def test_rejects_invalid_download_and_removes_partial(self):
        payload = b"payload"
        release = {"version": "9.0.0", "url": "https://github.com/d4rv1n17/Enigma-Hub/releases/download/v9.0.0/EnigmaHubSetup.exe", "size": len(payload), "sha256": "0" * 64}
        with tempfile.TemporaryDirectory() as temp:
            with patch.object(hub_update, "urlopen", return_value=io.BytesIO(payload)):
                with self.assertRaises(ValueError):
                    hub_update.download_installer(release, temp)
            self.assertEqual(list(Path(temp).rglob("*.exe")), [])
            self.assertEqual(list(Path(temp).rglob("*.part")), [])

    def test_rejects_wrong_release_host(self):
        release = {"tag_name": "v99.0.0", "assets": [{"name": hub_update.ASSET_NAME, "digest": "sha256:" + "a" * 64, "size": 12, "browser_download_url": "https://attacker.example/installer.exe"}]}
        with patch.object(hub_update, "urlopen", return_value=io.BytesIO(json.dumps(release).encode())):
            with self.assertRaises(ValueError):
                hub_update.latest_installer()

    def test_rejects_prerelease_version_string(self):
        with self.assertRaises(ValueError):
            hub_update.version_tuple("v1.0.3-beta")

    def test_rejects_installer_reparse_attribute(self):
        attributes = type("Stat", (), {"st_mode": 0o100644, "st_file_attributes": 0x400})()
        with patch.object(Path, "lstat", return_value=attributes):
            with self.assertRaises(ValueError):
                hub_setup.reject_reparse(Path("Enigma Hub") / "EnigmaHub.exe")

    def test_target_appends_product_folder(self):
        with tempfile.TemporaryDirectory() as temp:
            self.assertEqual(hub_setup.normalize_target(temp), Path(temp).resolve() / "Enigma Hub")

    def test_install_update_remove_preserves_user_files(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            payload = root / "payload"
            payload.mkdir()
            app = payload / hub_setup.EXE
            app.write_bytes(b"first verified application")
            setup = root / "setup.exe"
            setup.write_bytes(b"setup")
            def manifest():
                (payload / "release.json").write_text(json.dumps({"sha256": hashlib.sha256(app.read_bytes()).hexdigest()}))
            manifest()
            with patch.object(hub_setup, "ROOT", root), patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(setup)), patch.object(hub_setup, "register"), patch.object(hub_setup, "create_shortcuts"), patch.object(hub_setup, "existing_install", return_value=None):
                target = hub_setup.install(root / "install")
                personal = target / "personal.txt"
                personal.write_text("keep me")
                app.write_bytes(b"updated verified application")
                manifest()
                hub_setup.install(target)
                self.assertEqual((target / hub_setup.EXE).read_bytes(), app.read_bytes())
                hub_setup.uninstall(target)
                self.assertEqual(personal.read_text(), "keep me")
                self.assertFalse((target / hub_setup.EXE).exists())


if __name__ == "__main__":
    unittest.main()
