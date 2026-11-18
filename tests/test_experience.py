"""Workspace regressions with isolated settings and no live installs or requests."""
import copy
import io
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from PyQt5.QtWidgets import QApplication, QDialog, QScrollArea
from PyQt5.QtCore import QTimer
import enigma_hub as hub

if QApplication.instance() is None:
    hub.configure_display()
APP = QApplication.instance() or QApplication([])
APP.setQuitOnLastWindowClosed(False)
APP.setStyle("Fusion")


class WorkspaceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.directory = Path(self.temp.name)
        self.patches = [patch.object(hub, "APPDATA", self.directory), patch.object(hub, "STATE_FILE", self.directory / "settings.json"), patch.object(hub.Hub, "load_news"), patch.object(hub.Hub, "check_updates"), patch.object(hub.Hub, "check_hub_update")]
        for p in self.patches:
            p.start()
        self.window = hub.Hub()
        self.window.show()
        APP.processEvents()

    def tearDown(self):
        self.window.close()
        self.window.deleteLater()
        APP.processEvents()
        for p in reversed(self.patches):
            p.stop()
        self.temp.cleanup()

    def test_catalog_search_and_filter(self):
        self.window.navigate(1, False)
        self.window.catalog_search.setText("disk")
        APP.processEvents()
        visible = [key for key, (tile, _) in self.window.catalog_tiles.items() if not tile.isHidden()]
        self.assertEqual(visible, ["disk"])
        self.window.filter_catalog(2)
        self.assertTrue(self.window.catalog_empty.isVisible())

    def test_dialog_has_no_dead_context_help_button(self):
        from PyQt5.QtCore import Qt
        dialog, content = self.window.dialog_panel("Activity")
        self.assertFalse(dialog.windowFlags() & Qt.WindowContextHelpButtonHint)
        dialog.deleteLater()

    def test_vector_assets_and_icons_render_at_large_resolution(self):
        image = self.window.asset_image("hub-fold-koulen.png", 162)
        self.assertTrue(image.renderer.isValid())
        icon = hub.ui_icon("library").pixmap(256, 256)
        self.assertEqual(icon.width() / icon.devicePixelRatio(), 256)
        self.assertEqual(icon.height() / icon.devicePixelRatio(), 256)
        image.deleteLater()

    def test_library_choice_menu_changes_filter_and_selection(self):
        selector = self.window.library_filter_menu
        selector.options[1].trigger()
        self.assertEqual(self.window.library_filter, "favorites")
        self.assertTrue(selector.options[1].isChecked())
        self.assertFalse(selector.options[0].isChecked())

    def test_language_changes_in_place_across_all_pages(self):
        for code in ("ru", "ro", "de", "es", "fr", "en"):
            self.window.change_language(code)
            for index in range(5):
                self.window.navigate(index, False)
                for width in (820, 1040, 1440):
                    self.window.resize(width, 680)
                    APP.processEvents()
                    page = self.window.stack.currentWidget()
                    self.assertIsInstance(page, QScrollArea)
                    self.assertLessEqual(page.horizontalScrollBar().maximum(), 1, (code, index, width))
            self.assertFalse(self.window.closing)
            self.assertEqual(hub.Hub.lang, code)

    def test_library_favorites_and_last_launch(self):
        product = hub.PRODUCTS[0]
        folder = self.directory / "cube"
        folder.mkdir()
        (folder / product["exe"]).write_bytes(b"fixture only")
        self.window.state["paths"]["cube"] = str(folder)
        self.window.state["favorites"] = ["cube"]
        self.window.record_activity(product, "launch")
        self.window.set_library_option("filter", "favorites")
        self.window.navigate(2, False)
        APP.processEvents()
        self.assertIn("cube", self.window.state["recent"])
        self.assertEqual(self.window.state["history"][-1]["action"], "launch")
        self.window.set_library_option("query", "does not exist")
        self.window.set_library_option("query", "")
        self.window.resize(900, 640)
        APP.processEvents()

    def test_malformed_preferences_are_normalized(self):
        hub.STATE_FILE.write_text(json.dumps({"installed": {"disk": []}, "recent": [], "hashes": False, "motion": "false", "favorites": {}, "history": [None]}))
        state = self.window.load_state()
        self.assertEqual(state["installed"], {})
        self.assertEqual(state["history"], [])
        self.assertIs(state["motion"], True)

    def test_update_check_continues_after_first_product_failure(self):
        worker = hub.UpdateCheckWorker()
        results = []
        worker.checked.connect(lambda versions, error: results.append((versions, error)))
        with patch.object(hub, "urlopen", side_effect=[OSError("offline"), io.BytesIO(b'{"tag_name":"v9.0.0"}')]):
            worker.run()
        self.assertEqual(results[0][0], {"disk": "9.0.0"})
        self.assertIn("offline", results[0][1])

    def test_news_reader_renders_markdown_in_dialog(self):
        def inspect():
            dialog = APP.activeModalWidget()
            self.assertIsInstance(dialog, QDialog)
            dialog.accept()
        QTimer.singleShot(30, inspect)
        self.window.read_article({"title": "Release", "name": "Enigma Hub", "date": "2026-11-18", "body": "## New\n\n**Clear** release notes", "url": "https://github.com/d4rv1n17/Enigma-Hub/releases"})

    def test_product_install_verify_and_remove_preserve_other_files(self):
        payload = b"verified application fixture"
        product = hub.PRODUCTS[1]
        target = self.directory / "Enigma Disk"
        release = {"tag_name": "v2.0.0", "assets": [{"name": product["asset"], "digest": "sha256:" + hashlib.sha256(payload).hexdigest(), "size": len(payload), "browser_download_url": "https://github.com/" + product["repo"] + "/releases/download/v2.0.0/" + product["asset"]}]}
        with patch.object(hub, "urlopen", side_effect=[io.BytesIO(json.dumps(release).encode()), io.BytesIO(payload)]), patch.object(hub, "create_shortcuts"), patch.object(hub, "remove_shortcuts"):
            results = []
            worker = hub.ProductWorker(product, "install", target)
            worker.done.connect(lambda *args: results.append(args))
            worker.run()
            self.assertEqual(results[0][2], "")
            self.assertEqual((target / product["exe"]).read_bytes(), payload)
            verify = hub.ProductWorker(product, "verify", target, hashlib.sha256(payload).hexdigest())
            verify.done.connect(lambda *args: results.append(args))
            verify.run()
            self.assertEqual(results[-1][0:3], ("verify", "", ""))
            personal = target / "user-settings.json"
            personal.write_text("keep")
            remove = hub.ProductWorker(product, "remove", target)
            remove.run()
            self.assertEqual(personal.read_text(), "keep")
            self.assertFalse((target / product["exe"]).exists())

    def test_bad_product_download_does_not_install_or_leave_partial(self):
        product = hub.PRODUCTS[1]
        release = {"tag_name": "v2.0.0", "assets": [{"name": product["asset"], "digest": "sha256:" + "0" * 64, "size": 3, "browser_download_url": "https://github.com/" + product["repo"] + "/releases/download/v2.0.0/" + product["asset"]}]}
        target = self.directory / "bad"
        results = []
        with patch.object(hub, "urlopen", side_effect=[io.BytesIO(json.dumps(release).encode()), io.BytesIO(b"bad")]):
            worker = hub.ProductWorker(product, "install", target)
            worker.done.connect(lambda *args: results.append(args))
            worker.run()
        self.assertTrue(results[0][2])
        self.assertFalse(target.exists())
        self.assertEqual(list((self.directory / "downloads").iterdir()), [])

    def test_all_product_and_game_details_fit_small_window(self):
        self.window.state["motion"] = False
        for item in hub.PRODUCTS + hub.GAMES:
            if item in hub.PRODUCTS:
                self.window.show_product_detail(item)
            else:
                self.window.show_game_detail(item)
            self.window.resize(820, 600)
            APP.processEvents()
            self.assertLessEqual(self.window.stack.currentWidget().horizontalScrollBar().maximum(), 1, item["id"])

    def test_cancelled_download_never_installs_and_removes_partial(self):
        payload = b"cancel before committing"
        product = hub.PRODUCTS[1]
        release = {"tag_name": "v2.0.0", "assets": [{"name": product["asset"], "digest": "sha256:" + hashlib.sha256(payload).hexdigest(), "size": len(payload), "browser_download_url": "https://github.com/" + product["repo"] + "/releases/download/v2.0.0/" + product["asset"]}]}
        target = self.directory / "cancelled"
        worker = hub.ProductWorker(product, "install", target)
        results, transfers = [], []
        worker.done.connect(lambda *args: results.append(args))
        worker.transfer.connect(lambda *args: transfers.append(args))
        with patch.object(hub, "urlopen", side_effect=[io.BytesIO(json.dumps(release).encode()), io.BytesIO(payload)]), patch.object(worker, "isInterruptionRequested", side_effect=[False, False, False, True]):
            worker.run()
        self.assertEqual(results[0][0:3], ("cancelled", "", ""))
        self.assertFalse(target.exists())
        self.assertEqual(list((self.directory / "downloads").iterdir()), [])
        self.assertEqual(transfers[0][0:2], (len(payload), len(payload)))

    def test_insufficient_space_does_not_download_installer(self):
        product = hub.PRODUCTS[1]
        release = {"tag_name": "v2.0.0", "assets": [{"name": product["asset"], "digest": "sha256:" + "a" * 64, "size": 100, "browser_download_url": "https://github.com/" + product["repo"] + "/releases/download/v2.0.0/" + product["asset"]}]}
        worker = hub.ProductWorker(product, "install", self.directory / "no-space")
        results = []
        worker.done.connect(lambda *args: results.append(args))
        with patch.object(hub, "urlopen", return_value=io.BytesIO(json.dumps(release).encode())) as request, patch.object(hub, "available_space", return_value=0):
            worker.run()
        self.assertEqual(request.call_count, 1)
        self.assertTrue(results[0][2])
        self.assertFalse((self.directory / "no-space").exists())

    def test_home_recent_only_offers_existing_apps(self):
        product = hub.PRODUCTS[1]
        folder = self.directory / "recent-app"
        folder.mkdir()
        executable = folder / product["exe"]
        executable.write_bytes(b"fixture")
        self.window.state["paths"][product["id"]] = str(folder)
        self.window.record_activity(product, "launch")
        self.assertEqual(self.window.home_recent.count(), 1)
        executable.unlink()
        self.window.refresh_home_recent()
        self.assertTrue(self.window.home_recent_panel.isHidden())

    def test_transfer_panel_reports_progress_and_safely_finishes_cancel(self):
        with patch.object(hub.ProductWorker, "start"), patch.object(self.window, "notify") as notify:
            self.window.start_task(hub.PRODUCTS[1], "install")
            self.window.transfer_progress(1000000, 4000000, 500000.0, 6)
            self.assertIn("1.0 MB / 4.0 MB", self.window.transfer_details.text())
            self.assertIn("00:06", self.window.transfer_details.text())
            self.window.resize(820, 600)
            APP.processEvents()
            self.assertTrue(self.window.task_strip.isVisible())
            self.window.task_progress(85, "Installing")
            self.assertFalse(self.window.cancel_download.isEnabled())
            self.window.task_done(hub.PRODUCTS[1], "cancelled", "", "", str(self.directory))
            notify.assert_not_called()
            self.assertEqual(self.window.state["history"][-1]["status"], "cancelled")

    def test_settings_tabs_and_switches_save_preferences(self):
        self.window.navigate(4, False)
        self.window.select_settings_section(2)
        APP.processEvents()
        self.assertTrue(self.window.settings_sections[2].isVisible())
        self.assertTrue(self.window.settings_tabs[2].isChecked())
        self.assertTrue(self.window.settings_sections[0].isHidden())
        previous = self.window.state["auto_check"]
        self.window.auto_check_button.click()
        self.assertEqual(self.window.state["auto_check"], not previous)
        saved = json.loads(hub.STATE_FILE.read_text())
        self.assertEqual(saved["auto_check"], not previous)

    def test_sidebar_controls_share_geometry_and_icon_size(self):
        controls = self.window.nav_buttons + [self.window.nav_activity, self.window.nav_settings]
        APP.processEvents()
        self.assertEqual({button.height() for button in controls}, {46})
        self.assertEqual(len({button.width() for button in controls}), 1)
        self.assertEqual({button.iconSize().width() for button in controls}, {20})

    def test_banner_vector_keeps_source_aspect_ratio(self):
        cover = hub.Cover("hub-universe.svg", 180)
        for width in (280, 600):
            cover.resize(width, 180)
            rectangles = []
            render = cover.vector.render
            def record(painter, target):
                rectangles.append(hub.QRectF(target))
                render(painter, target)
            with patch.object(cover.vector, "render", new=record):
                cover.grab()
            target = rectangles[-1]
            self.assertAlmostEqual(target.width() / target.height(), 2.0)
        cover.deleteLater()

    def test_language_choice_keeps_selection_if_operation_blocks_change(self):
        self.window.change_language("en")
        chooser = next(button for button in self.window.findChildren(hub.ChoiceButton) if button.accessibleName() == hub.tr("language"))
        with patch.object(self.window, "product_busy", return_value=True):
            chooser.options[1].trigger()
        self.assertEqual(hub.Hub.lang, "en")
        self.assertEqual(chooser.text(), "English")
        self.assertTrue(chooser.options[0].isChecked())
        self.assertFalse(chooser.options[1].isChecked())

    def test_settings_sections_fit_in_all_languages(self):
        self.window.resize(820, 600)
        for language in ("en", "ru", "ro", "de", "es", "fr"):
            self.window.change_language(language)
            self.window.navigate(4, False)
            for index in range(4):
                self.window.select_settings_section(index)
                APP.processEvents()
                self.assertLessEqual(self.window.stack.currentWidget().horizontalScrollBar().maximum(), 1, (language, index))


if __name__ == "__main__":
    unittest.main()
