"""Failure-path regressions from the complete Hub review."""
import hashlib
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from test_experience import APP
import enigma_hub as hub
import hub_games
import hub_setup
import hub_update


class AuditUiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.patches = [patch.object(hub, "APPDATA", self.root), patch.object(hub, "STATE_FILE", self.root / "settings.json"), patch.object(hub.Hub, "load_news"), patch.object(hub.Hub, "check_updates"), patch.object(hub.Hub, "check_hub_update")]
        for item in self.patches:
            item.start()
        self.window = hub.Hub()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        APP.processEvents()
        for item in reversed(self.patches):
            item.stop()
        self.temp.cleanup()

    def test_failed_settings_commit_keeps_previous_file_and_reports_error(self):
        self.window.save_state()
        previous = hub.STATE_FILE.read_bytes()
        self.window.state["motion"] = not self.window.state["motion"]
        with patch.object(Path, "replace", side_effect=PermissionError("profile is read-only")), patch.object(self.window, "notify") as notice:
            self.assertFalse(self.window.save_state())
            APP.processEvents()
            notice.assert_called_once()
        self.assertEqual(hub.STATE_FILE.read_bytes(), previous)
        self.assertFalse(hub.STATE_FILE.with_suffix(".tmp").exists())

    def test_settings_retry_clears_the_queued_warning(self):
        with patch.object(self.window, "notify") as notice:
            with patch.object(Path, "replace", side_effect=OSError("temporary failure")):
                self.assertFalse(self.window.save_state())
            self.assertTrue(self.window.save_state())
            APP.processEvents()
            notice.assert_not_called()
        self.assertIsNone(self.window.last_save_error)

    def test_windows_bom_settings_are_read(self):
        hub.STATE_FILE.write_text(json.dumps({"lang": "ru", "motion": False}), encoding="utf-8-sig")
        state = self.window.load_state()
        self.assertEqual(state["lang"], "ru")
        self.assertFalse(state["motion"])

    def test_offline_news_does_not_clear_available_releases(self):
        previous = list(self.window.news_items)
        self.window.finish_news_refresh({}, ["offline"])
        self.assertEqual(self.window.news_items, previous)
        self.assertEqual(self.window.news_status.text(), hub.NEWS_OFFLINE[hub.Hub.lang])

    def test_withdrawn_hub_update_removes_ready_button(self):
        self.window.hub_update_ready({"version": "99.0.0"}, "")
        self.assertTrue(hasattr(self.window, "hub_update_button"))
        self.window.hub_update_ready(None, "")
        self.assertIsNone(self.window.hub_release)
        self.assertFalse(hasattr(self.window, "hub_update_button"))

    def test_reopening_during_background_shutdown_cancels_pending_close(self):
        from PyQt5.QtTest import QTest
        worker = hub.NewsWorker()
        with patch.object(worker, "isRunning", return_value=True):
            self.window.workers.append(worker)
            self.window.close()
            self.assertTrue(self.window.closing)
            self.window.restore_window()
            QTest.qWait(180)
            self.assertFalse(self.window.closing)
            self.assertTrue(self.window.centralWidget().isEnabled())
            self.assertTrue(self.window.isVisible())
            self.window.workers.remove(worker)


class AuditInstallerTests(unittest.TestCase):
    def payload(self, root):
        payload = root / "payload"
        payload.mkdir()
        app = payload / hub_setup.EXE
        app.write_bytes(b"application")
        (payload / "release.json").write_text(json.dumps({"sha256": hashlib.sha256(app.read_bytes()).hexdigest()}))
        setup = root / "setup.exe"
        setup.write_bytes(b"installer")
        return app, setup

    def test_copy_failure_cleans_every_staged_installer_file(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            app, setup = self.payload(root)
            original = hub_setup.shutil.copy2
            def fail_copy(source, target):
                if Path(source) == setup:
                    Path(target).write_bytes(b"incomplete")
                    raise OSError("disk full")
                return original(source, target)
            with patch.object(hub_setup, "ROOT", root), patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(setup)), patch.object(hub_setup.shutil, "copy2", side_effect=fail_copy), patch.object(hub_setup, "register") as register:
                with self.assertRaises(OSError):
                    hub_setup.install(root / "target")
                register.assert_not_called()
            self.assertEqual(list((root / "target/Enigma Hub").iterdir()), [])

    def test_late_install_failure_rolls_back_files_marker_and_registration(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            app, setup = self.payload(root)
            undo = Mock()
            with patch.object(hub_setup, "ROOT", root), patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(setup)), patch.object(hub_setup, "register", side_effect=[None, undo]), patch.object(hub_setup, "create_shortcuts", side_effect=[None, OSError("shortcut failed")]):
                target = hub_setup.install(root / "target")
                before = {p.name: p.read_bytes() for p in target.iterdir()}
                app.write_bytes(b"new application")
                setup.write_bytes(b"new installer")
                (root / "payload/release.json").write_text(json.dumps({"sha256": hashlib.sha256(app.read_bytes()).hexdigest()}))
                with self.assertRaises(OSError):
                    hub_setup.install(target)
                self.assertEqual({p.name: p.read_bytes() for p in target.iterdir()}, before)
                undo.assert_called_once()

    def test_partial_registration_failure_restores_previous_values(self):
        previous = {"DisplayVersion": ("1.0.0", 1)}
        with patch.object(hub_setup, "registration_snapshot", return_value=previous), patch.object(hub_setup, "write_registration", side_effect=OSError("registry write failed")), patch.object(hub_setup, "restore_registration") as restore:
            with self.assertRaises(OSError):
                hub_setup.register(Path("Enigma Hub"))
            restore.assert_called_once_with(previous)

    def test_hub_download_rejects_unsafe_version_before_writing(self):
        with tempfile.TemporaryDirectory() as folder:
            release = {"version": "../elsewhere", "size": 1, "sha256": "a" * 64, "url": "https://github.com/d4rv1n17/Enigma-Hub/releases/download/v1.0.0/EnigmaHubSetup.exe"}
            with patch.object(hub_update, "urlopen") as request:
                with self.assertRaises(ValueError):
                    hub_update.download_installer(release, folder)
                request.assert_not_called()
            self.assertEqual(list(Path(folder).iterdir()), [])

    def test_hub_download_rejects_linked_cache_folder(self):
        release = {"version": "9.0.0", "size": 1, "sha256": "a" * 64, "url": "https://github.com/d4rv1n17/Enigma-Hub/releases/download/v9.0.0/EnigmaHubSetup.exe"}
        with patch.object(hub_update, "reject_reparse", side_effect=ValueError("junction")), patch.object(hub_update, "urlopen") as request:
            with self.assertRaises(ValueError):
                hub_update.download_installer(release, "cache")
            request.assert_not_called()

    def test_removal_cleanup_never_targets_the_installed_setup(self):
        with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", r"D:\Programs\Enigma Hub\EnigmaHubSetup.exe"), patch.object(hub_setup.subprocess, "Popen") as launch:
            self.assertFalse(hub_setup.cleanup_removal_helper())
            launch.assert_not_called()

    def test_removal_cleanup_is_limited_to_the_owned_temporary_copy(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            helper = root / "EnigmaHub-remove-test" / hub_setup.SETUP
            helper.parent.mkdir()
            helper.write_bytes(b"test")
            with patch.object(sys, "frozen", True, create=True), patch.object(sys, "executable", str(helper)), patch.object(hub_setup.tempfile, "gettempdir", return_value=str(root)), patch.object(hub_setup.subprocess, "Popen") as launch:
                self.assertTrue(hub_setup.cleanup_removal_helper())
                command = launch.call_args[0][0]
                self.assertIn(str(helper.resolve()), command[-1])
                self.assertNotIn("-Recurse", command[-1])
                self.assertIn("Hidden", command)

    def test_quiet_install_preserves_original_error_if_recovery_path_is_invalid(self):
        with tempfile.TemporaryDirectory() as folder, patch.object(sys, "frozen", False, create=True), patch.object(sys, "argv", ["setup", "--quiet", "--launch", "--dir", "invalid"]), patch.dict(hub_setup.os.environ, {"APPDATA": folder}), patch.object(hub_setup, "install", side_effect=RuntimeError("original install failure")), patch.object(hub_setup, "normalize_target", side_effect=ValueError("bad recovery path")):
            self.assertEqual(hub_setup.main(), 1)
            self.assertEqual((Path(folder) / "EnigmaHub/update-error.log").read_text(), "original install failure")

    def test_network_failure_does_not_replace_existing_product(self):
        product = hub.PRODUCTS[1]
        payload = b"partial download"
        release = {"tag_name": "v2.0.0", "assets": [{"name": product["asset"], "digest": "sha256:" + "a" * 64, "size": 1000, "browser_download_url": "https://github.com/" + product["repo"] + "/releases/download/v2.0.0/" + product["asset"]}]}
        stream = Mock()
        stream.__enter__ = Mock(return_value=stream)
        stream.__exit__ = Mock(return_value=False)
        stream.read.side_effect = [payload, OSError("connection reset")]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            target = root / "app"
            target.mkdir()
            executable = target / product["exe"]
            executable.write_bytes(b"previous working app")
            results = []
            worker = hub.ProductWorker(product, "install", target)
            worker.done.connect(lambda *args: results.append(args))
            with patch.object(hub, "APPDATA", root), patch.object(hub, "urlopen", side_effect=[io.BytesIO(json.dumps(release).encode()), stream]):
                worker.run()
            self.assertIn("connection reset", results[0][2])
            self.assertEqual(executable.read_bytes(), b"previous working app")
            self.assertEqual(list((root / "downloads").glob("*.part")), [])

    def test_failed_product_copy_cleans_partial_executable(self):
        product = hub.PRODUCTS[1]
        payload = b"verified payload"
        release = {"tag_name": "v2.0.0", "assets": [{"name": product["asset"], "digest": "sha256:" + hashlib.sha256(payload).hexdigest(), "size": len(payload), "browser_download_url": "https://github.com/" + product["repo"] + "/releases/download/v2.0.0/" + product["asset"]}]}
        with tempfile.TemporaryDirectory() as folder:
            root, results = Path(folder), []
            def fail_copy(source, destination):
                Path(destination).write_bytes(b"incomplete")
                raise OSError("copy failed")
            worker = hub.ProductWorker(product, "install", root / "app")
            worker.done.connect(lambda *args: results.append(args))
            with patch.object(hub, "APPDATA", root), patch.object(hub, "urlopen", side_effect=[io.BytesIO(json.dumps(release).encode()), io.BytesIO(payload)]), patch.object(hub.shutil, "copy2", side_effect=fail_copy):
                worker.run()
            self.assertIn("copy failed", results[0][2])
            self.assertEqual(list((root / "app").iterdir()), [])


class AuditGameTests(unittest.TestCase):
    def test_nondefault_steam_library_requires_completed_install(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            client, library = root / "client", root / "library"
            (client / "steamapps").mkdir(parents=True)
            (library / "steamapps/common/Test Game").mkdir(parents=True)
            (client / "steamapps/libraryfolders.vdf").write_text('"path" "' + library.as_posix() + '"')
            manifest = library / "steamapps/appmanifest_12345.acf"
            with patch.object(hub_games, "steam_client_path", return_value=client):
                manifest.write_text('"appid" "12345" "installdir" "Test Game" "StateFlags" "1026"')
                self.assertIsNone(hub_games.find_installed_game({"steam_app_id": "12345"}))
                manifest.write_text('"appid" "12345" "installdir" "Test Game" "StateFlags" "4"')
                self.assertEqual(hub_games.find_installed_game({"steam_app_id": "12345"}), manifest)

    def test_corrupt_game_settings_do_not_launch_non_executable_files(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "not-a-game.acf"
            path.write_text("test")
            self.assertIsNone(hub_games.find_installed_game({"exe": str(path)}))
        self.assertFalse(hub_games.valid_web_url("file:///C:/Windows"))
        self.assertTrue(hub_games.valid_web_url("https://store.steampowered.com/app/12345"))
