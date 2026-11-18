"""Branded per-user installer and uninstaller for Enigma Hub."""
import argparse
import ctypes
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import winreg

from PyQt5.QtCore import Qt, QThread, QPropertyAnimation, QEasingCurve, pyqtSignal
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import QApplication, QCheckBox, QFileDialog, QFrame, QHBoxLayout, QLabel, QPushButton, QProgressBar, QStackedWidget, QVBoxLayout, QWidget

from enigma_hub import ROOT, STYLE, Cover, Hub, ui_icon, center_on_screen, dark_caption, create_shortcuts, configure_display

from hub_update import VERSION
from hub_safety import reject_reparse
from hub_experience import PREMIUM_STYLE
KEY = r"Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaHub"
EXE = "EnigmaHub.exe"
SETUP = "EnigmaHubSetup.exe"
MARKER = ".enigma-hub-install.json"


def existing_install():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, KEY) as key:
            return Path(winreg.QueryValueEx(key, "InstallLocation")[0])
    except OSError:
        return None


def validate_install_files(folder):
    reject_reparse(folder)
    names = (EXE, SETUP, MARKER, MARKER + ".new")
    for name in names:
        for suffix in ("", ".new", ".previous") if name.endswith(".exe") else ("",):
            reject_reparse(folder / (name + suffix))


def normalize_target(folder):
    target = Path(folder).expanduser().absolute()
    if target.name.lower() != "enigma hub":
        target = target / "Enigma Hub"
    validate_install_files(target)
    return target.resolve()


def shortcut_path():
    return Path(os.environ["APPDATA"]) / "Microsoft/Windows/Start Menu/Programs/Enigma Hub.lnk"


def register(folder):
    executable = str(folder / SETUP)
    with winreg.CreateKey(winreg.HKEY_CURRENT_USER, KEY) as key:
        fields = {
            "DisplayName": "Enigma Hub", "DisplayVersion": VERSION,
            "Publisher": "Enigma Studio", "InstallLocation": str(folder),
            "DisplayIcon": str(folder / EXE),
            "UninstallString": f'"{executable}" --uninstall --dir "{folder}"',
            "QuietUninstallString": f'"{executable}" --uninstall --quiet --dir "{folder}"',
        }
        for name, value in fields.items():
            winreg.SetValueEx(key, name, 0, winreg.REG_SZ, value)
        for name in ("NoModify", "NoRepair"):
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, 1)


def install(folder, desktop=False, progress=lambda value: None):
    if not getattr(sys, "frozen", False):
        raise RuntimeError("Build EnigmaHubSetup.exe before installing.")
    folder = normalize_target(folder)
    folder.mkdir(parents=True, exist_ok=True)
    if any(folder.iterdir()):
        try:
            previous = json.loads((folder / MARKER).read_text(encoding="utf-8"))
        except (OSError, ValueError):
            raise ValueError("This folder contains other files. Choose an empty folder.")
        if not isinstance(previous, dict) or previous.get("product") != "Enigma Hub":
            raise ValueError("Choose a folder belonging to Enigma Hub.")
        desktop = desktop or bool(previous.get("desktop"))
    payload = ROOT / "payload" / EXE
    manifest = json.loads((ROOT / "payload" / "release.json").read_text(encoding="utf-8"))
    if hashlib.sha256(payload.read_bytes()).hexdigest() != manifest["sha256"]:
        raise ValueError("The installer payload is damaged. Download the setup again.")
    progress(20)
    marker = {"product": "Enigma Hub", "version": VERSION, "files": [EXE, SETUP], "desktop": desktop}
    staged = {}
    backups = {}
    replaced = set()
    try:
        sources = {EXE: payload, SETUP: Path(sys.executable)}
        for index, (name, source) in enumerate(sources.items()):
            stage = folder / (name + ".new")
            shutil.copy2(source, stage)
            staged[name] = stage
            progress(35 + index * 20)
        for name, stage in staged.items():
            target = folder / name
            if target.exists():
                backup = folder / (name + ".previous")
                if backup.exists():
                    raise RuntimeError("Previous installation backup exists. Close Hub and try again.")
                target.replace(backup)
                backups[name] = backup
            stage.replace(target)
            replaced.add(name)
        progress(75)
        register(folder)
        create_shortcuts("Enigma Hub", folder / EXE)
        if desktop:
            start_link = shortcut_path()
            if start_link.is_file():
                shutil.copy2(start_link, Path(os.environ["USERPROFILE"]) / "Desktop/Enigma Hub.lnk")
        progress(90)
        marker_temp = folder / (MARKER + ".new")
        marker_temp.write_text(json.dumps(marker), encoding="utf-8")
        marker_temp.replace(folder / MARKER)
    except Exception:
        for name in staged:
            target = folder / name
            if name in backups:
                target.unlink(missing_ok=True)
                backups[name].replace(target)
            elif name in replaced and target.exists():
                target.unlink()
        raise
    finally:
        for stage in staged.values():
            stage.unlink(missing_ok=True)
        (folder / (MARKER + ".new")).unlink(missing_ok=True)
    for backup in backups.values():
        backup.unlink(missing_ok=True)
    progress(100)
    return folder


def uninstall(folder, progress=lambda value: None):
    folder = Path(folder).absolute()
    validate_install_files(folder)
    folder = folder.resolve()
    marker = json.loads((folder / MARKER).read_text(encoding="utf-8"))
    if not isinstance(marker, dict) or marker.get("product") != "Enigma Hub" or folder.name.lower() != "enigma hub":
        raise ValueError("This folder is not an Enigma Hub installation.")
    # Only the two known installed executables are removed. User folders remain intact.
    for index, name in enumerate((EXE, SETUP)):
        (folder / name).unlink(missing_ok=True)
        progress(35 + index * 25)
    (folder / MARKER).unlink()
    registered = existing_install()
    if registered and registered.resolve() == folder:
        winreg.DeleteKey(winreg.HKEY_CURRENT_USER, KEY)
        shortcut_path().unlink(missing_ok=True)
        if marker.get("desktop"):
            (Path(os.environ["USERPROFILE"]) / "Desktop/Enigma Hub.lnk").unlink(missing_ok=True)
    if not any(folder.iterdir()):
        folder.rmdir()
    progress(100)


class Operation(QThread):
    progress = pyqtSignal(int)
    completed = pyqtSignal(str, str)

    def __init__(self, folder, removing, desktop):
        super().__init__()
        self.folder, self.removing, self.desktop = folder, removing, desktop

    def run(self):
        try:
            if self.removing:
                uninstall(self.folder, self.progress.emit)
            else:
                self.folder = install(self.folder, self.desktop, self.progress.emit)
            self.completed.emit(str(self.folder), "")
        except Exception as error:
            self.completed.emit("", str(error))


SETUP_STYLE = """
QWidget#setupRoot { background: #141414; }
QFrame#setupBrand { background: #1C1C1C; border-right: 1px solid #37342B; }
QLabel#setupTitle { color: #F7F7F7; font-size: 29px; font-weight: 700; }
QLabel#setupStep { color: #B8B8B8; font-size: 12px; }
QLabel#setupStage { color: #F4CC0C; font-size: 12px; font-weight: 700; }
QLabel#setupFolder { color: #DCDCDC; font-size: 12px; }
QFrame#setupCard { background: #202020; border: 1px solid #3B3B3B; border-radius: 12px; }
QCheckBox { color: #DDDDDD; spacing: 10px; padding: 5px 0; font-size: 12px; }
QCheckBox::indicator { width: 16px; height: 16px; background: #292929; border: 1px solid #626262; border-radius: 4px; }
QCheckBox::indicator:checked { background: #F4CC0C; border: 1px solid #F4CC0C; image: url(assets/setup-check.svg); }
QCheckBox::indicator:hover { border-color: #F4CC0C; }
QProgressBar { min-height: 7px; max-height: 7px; background: #353535; }
QLabel#setupError { color: #F4CC0C; background: #302A1B; border: 1px solid #6A5625; border-radius: 8px; padding: 10px; }
"""


class Setup(QWidget):
    def __init__(self, folder, removing=False):
        super().__init__()
        Hub.lang = "en"
        self.folder = folder
        self.removing = removing
        self.done = False
        self.busy = False
        self.setObjectName("setupRoot")
        self.setWindowTitle("Enigma Hub — Setup")
        self.setWindowIcon(QIcon(str(ROOT / "assets/hub-icon.ico")))
        self.setMinimumSize(800, 570)
        self.resize(850, 590)
        check_path = (ROOT / "assets/setup-check.svg").as_posix()
        self.setStyleSheet(STYLE + PREMIUM_STYLE + SETUP_STYLE.replace("assets/setup-check.svg", check_path))
        shell = QHBoxLayout(self)
        shell.setContentsMargins(0, 0, 0, 0)
        shell.setSpacing(0)

        brand = QFrame(objectName="setupBrand")
        brand.setFixedWidth(260)
        left = QVBoxLayout(brand)
        left.setContentsMargins(23, 26, 23, 24)
        left.setSpacing(18)
        left.addWidget(Hub.asset_image("hub-fold-koulen.png", 204), 0, Qt.AlignLeft)
        left.addStretch()
        left.addWidget(Cover("hub-universe.svg", 180))
        slogan = Hub.copy_label("One hub.\nMore to discover.", "setupTitle")
        left.addWidget(slogan)
        left.addWidget(Hub.copy_label("Your studio apps and games,\ntogether in one place.", "body"))
        left.addStretch()
        left.addWidget(Hub.copy_label("ENIGMA STUDIO   /   " + VERSION, "muted"))
        shell.addWidget(brand)

        right = QVBoxLayout()
        right.setContentsMargins(27, 26, 27, 22)
        right.setSpacing(15)
        steps = QHBoxLayout()
        self.step_labels = []
        for index, text in enumerate(("Preferences", "Installing", "Ready")):
            label = Hub.copy_label(text, "setupStage" if index == 0 else "setupStep")
            self.step_labels.append(label)
            steps.addWidget(label)
            if index < 2:
                steps.addWidget(QLabel("›", objectName="muted"))
        right.addLayout(steps)
        self.heading = Hub.copy_label("Remove Enigma Hub?" if removing else "Make room for Enigma.", "setupTitle")
        right.addWidget(self.heading)
        self.description = Hub.copy_label(
            "Your studio apps, games and personal preferences will stay on this computer." if removing
            else "Choose where Hub lives. Everything else is ready.",
            "body")
        right.addWidget(self.description)

        self.pages = QStackedWidget()
        self.options = QWidget()
        choices = QVBoxLayout(self.options)
        choices.setContentsMargins(0, 3, 0, 0)
        choices.setSpacing(13)
        folder_card = QFrame(objectName="setupCard")
        folder_box = QVBoxLayout(folder_card)
        folder_box.setContentsMargins(15, 14, 15, 14)
        folder_header = QHBoxLayout()
        folder_header.addWidget(Hub.icon_label("folder", "#F4CC0C", 19))
        folder_header.addWidget(Hub.copy_label("INSTALL LOCATION", "eyebrow"), 1)
        folder_box.addLayout(folder_header)
        self.path = Hub.copy_label("", "setupFolder")
        Hub.set_path_text(self.path, str(folder))
        self.path.setTextInteractionFlags(Qt.TextSelectableByMouse)
        folder_box.addWidget(self.path)
        choose = QPushButton("Change folder", objectName="secondary")
        choose.setIcon(ui_icon("folder"))
        choose.setVisible(not removing)
        choose.clicked.connect(self.choose)
        folder_box.addWidget(choose, 0, Qt.AlignLeft)
        choices.addWidget(folder_card)
        self.desktop = QCheckBox("Add a desktop shortcut")
        self.desktop.setVisible(not removing)
        choices.addWidget(self.desktop)
        self.launch = QCheckBox("Open Enigma Hub when finished")
        self.launch.setChecked(True)
        self.launch.setVisible(not removing)
        choices.addWidget(self.launch)
        trust = QHBoxLayout()
        trust.addWidget(Hub.icon_label("shield", "#BDBDBD", 18))
        trust.addWidget(Hub.copy_label("Just for your Windows account.\nNo administrator permissions needed.", "muted"), 1)
        choices.addLayout(trust)
        choices.addStretch()
        self.pages.addWidget(self.options)

        work = QWidget()
        work_box = QVBoxLayout(work)
        work_box.setContentsMargins(0, 10, 0, 10)
        work_box.setSpacing(20)
        self.operation_rows = []
        for text in ("Verify package", "Copy application", "Add shortcuts"):
            row = QHBoxLayout()
            icon = Hub.icon_label("check", "#F4CC0C", 18)
            label = Hub.copy_label(text, "body")
            self.operation_rows.append((icon, label))
            row.addWidget(icon)
            row.addWidget(label, 1)
            work_box.addLayout(row)
        self.progress = QProgressBar()
        self.progress.setTextVisible(False)
        self.progress.setRange(0, 100)
        work_box.addWidget(self.progress)
        self.percent = Hub.copy_label("0%", "eyebrow")
        work_box.addWidget(self.percent)
        work_box.addStretch()
        self.pages.addWidget(work)

        finished = QWidget()
        complete_box = QVBoxLayout(finished)
        complete_box.setContentsMargins(0, 10, 0, 10)
        complete_box.setSpacing(15)
        complete_box.addWidget(Hub.icon_label("check", "#F4CC0C", 48), 0, Qt.AlignLeft)
        self.complete_path = Hub.copy_label("", "body")
        complete_box.addWidget(self.complete_path)
        complete_box.addStretch()
        self.pages.addWidget(finished)
        right.addWidget(self.pages, 1)

        self.status = Hub.copy_label("", "setupError")
        self.status.hide()
        right.addWidget(self.status)
        actions = QHBoxLayout()
        self.cancel = QPushButton("Cancel", objectName="secondary")
        self.cancel.clicked.connect(self.close)
        actions.addWidget(self.cancel)
        actions.addStretch()
        self.primary = QPushButton(objectName="primary")
        self.update_action()
        self.primary.clicked.connect(self.start)
        actions.addWidget(self.primary)
        right.addLayout(actions)
        shell.addLayout(right, 1)
        self.progress_motion = QPropertyAnimation(self.progress, b"value", self)
        self.progress_motion.setDuration(220)
        self.progress_motion.setEasingCurve(QEasingCurve.OutCubic)

    def update_action(self):
        self.primary.setText("Uninstall" if self.removing else ("Update Hub" if (self.folder / MARKER).is_file() else "Install Hub"))
        self.primary.setIcon(ui_icon("download", "#141414"))

    def choose(self):
        picker = QFileDialog(self, "Choose installation folder", str(self.folder))
        picker.setOption(QFileDialog.DontUseNativeDialog)
        picker.setFileMode(QFileDialog.Directory)
        picker.setOption(QFileDialog.ShowDirsOnly)
        dark_caption(picker)
        try:
            if picker.exec_() == QFileDialog.Accepted and picker.selectedFiles():
                self.folder = normalize_target(picker.selectedFiles()[0])
                Hub.set_path_text(self.path, str(self.folder))
                self.update_action()
        except (OSError, ValueError) as error:
            self.status.setText(str(error))
            self.status.show()
        finally:
            picker.deleteLater()

    def set_stage(self, stage):
        for index, label in enumerate(self.step_labels):
            label.setObjectName("setupStage" if index == stage else "setupStep")
            label.style().unpolish(label)
            label.style().polish(label)

    def advance(self, value):
        self.progress_motion.stop()
        self.progress_motion.setStartValue(self.progress.value())
        self.progress_motion.setEndValue(value)
        self.progress_motion.start()
        self.percent.setText(f"{value}%")
        for index, (icon, label) in enumerate(self.operation_rows):
            active = value >= (0, 30, 65)[index]
            icon.setVisible(active)
            label.setEnabled(active)

    def start(self):
        if self.busy:
            return
        if self.done:
            if not self.removing and self.launch.isChecked():
                try:
                    subprocess.Popen([str(self.folder / EXE)], cwd=str(self.folder))
                except OSError as error:
                    self.status.setText(str(error))
                    self.status.show()
                    return
            self.close()
            return
        self.busy = True
        self.status.hide()
        self.primary.setEnabled(False)
        self.cancel.setEnabled(False)
        self.heading.setText("Removing Enigma Hub…" if self.removing else "Building your workspace.")
        self.description.setText("This only takes a moment. Keep this window open.")
        self.step_labels[1].setText("Removing" if self.removing else "Installing")
        if self.removing:
            for (_, label), text in zip(self.operation_rows, ("Remove application", "Remove shortcuts", "Keep personal data")):
                label.setText(text)
        self.set_stage(1)
        self.pages.setCurrentIndex(1)
        self.advance(0)
        self.worker = Operation(self.folder, self.removing, self.desktop.isChecked())
        self.worker.progress.connect(self.advance)
        self.worker.completed.connect(self.complete)
        self.worker.start()

    def complete(self, folder, error):
        self.worker.wait()
        self.busy = False
        self.progress_motion.stop()
        self.cancel.setEnabled(True)
        self.primary.setEnabled(True)
        if error:
            self.pages.setCurrentIndex(0)
            self.set_stage(0)
            self.heading.setText("Let’s try that again.")
            self.description.setText("Installation could not finish. Review the message below.")
            self.status.setText(error)
            self.status.show()
            self.primary.setText("Retry")
            return
        self.folder = Path(folder)
        self.done = True
        self.heading.setText("Enigma Hub removed." if self.removing else "Your next discovery awaits.")
        self.description.setText("Your personal data is still here." if self.removing else "All set. Your Enigma workspace is ready.")
        self.complete_path.setText("Hub has been removed from this computer." if self.removing else str(self.folder))
        self.pages.setCurrentIndex(2)
        self.set_stage(2)
        self.primary.setText("Done" if self.removing else ("Open Hub" if self.launch.isChecked() else "Finish"))
        self.primary.setIcon(ui_icon("check", "#141414"))
        self.cancel.hide()

    def closeEvent(self, event):
        if self.busy:
            event.ignore()
        else:
            event.accept()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--uninstall", action="store_true")
    parser.add_argument("--dir")
    parser.add_argument("--quiet", action="store_true")
    parser.add_argument("--detached", action="store_true")
    parser.add_argument("--wait-pid", type=int)
    parser.add_argument("--launch", action="store_true")
    args = parser.parse_args()
    if args.wait_pid:
        kernel = ctypes.windll.kernel32
        kernel.OpenProcess.restype = ctypes.c_void_p
        handle = kernel.OpenProcess(0x00100000, False, args.wait_pid)
        if handle:
            try:
                if kernel.WaitForSingleObject(ctypes.c_void_p(handle), 180000) != 0:
                    return 1
            finally:
                kernel.CloseHandle(ctypes.c_void_p(handle))
    folder = Path(args.dir) if args.dir else (existing_install() or Path(os.environ["LOCALAPPDATA"]) / "Programs/Enigma Hub")
    if args.uninstall and getattr(sys, "frozen", False) and not args.detached:
        helper = Path(tempfile.mkdtemp(prefix="EnigmaHub-remove-")) / SETUP
        shutil.copy2(sys.executable, helper)
        command = [str(helper), "--uninstall", "--detached", "--dir", str(folder)]
        if args.quiet:
            command.append("--quiet")
        subprocess.Popen(command)
        return 0
    if args.quiet:
        try:
            installed = None
            if args.uninstall:
                uninstall(folder)
            else:
                installed = install(folder)
            if args.launch and installed:
                subprocess.Popen([str(installed / EXE)], cwd=str(installed))
            return 0
        except Exception as error:
            if args.launch and (normalize_target(folder) / EXE).is_file():
                subprocess.Popen([str(normalize_target(folder) / EXE)], cwd=str(normalize_target(folder)))
            log = Path(os.environ.get("APPDATA", tempfile.gettempdir())) / "EnigmaHub"
            log.mkdir(parents=True, exist_ok=True)
            (log / "update-error.log").write_text(str(error), encoding="utf-8")
            return 1
    configure_display()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setFont(QFont("Segoe UI", 10))
    window = Setup(folder, args.uninstall)
    dark_caption(window)
    center_on_screen(window, app.primaryScreen())
    window.show()
    return app.exec_()


if __name__ == "__main__":
    sys.exit(main())
