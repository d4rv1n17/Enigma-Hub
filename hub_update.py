"""Verified background delivery of Enigma Hub installers."""
import hashlib
import json
import os
from pathlib import Path
import re
from urllib.error import HTTPError
from urllib.request import Request, urlopen

from PyQt5.QtCore import QThread, pyqtSignal
from hub_safety import reject_reparse

VERSION = "1.3.1"
REPOSITORY = "d4rv1n17/Enigma-Hub"
ASSET_NAME = "EnigmaHubSetup.exe"


def version_tuple(value):
    match = re.fullmatch(r"v?(\d+)\.(\d+)\.(\d+)", value)
    if not match:
        raise ValueError("Invalid Hub release version")
    return tuple(map(int, match.groups()))


def digest_file(path):
    digest = hashlib.sha256()
    with Path(path).open("rb") as stream:
        for block in iter(lambda: stream.read(131072), b""):
            digest.update(block)
    return digest.hexdigest()


def latest_installer():
    request = Request(
        f"https://api.github.com/repos/{REPOSITORY}/releases/latest",
        headers={"User-Agent": "EnigmaHub/" + VERSION, "Accept": "application/vnd.github+json"},
    )
    try:
        with urlopen(request, timeout=15) as response:
            release = json.loads(response.read(2 * 1024 * 1024))
    except HTTPError as error:
        if error.code == 404:
            return None
        raise
    if release.get("draft") or release.get("prerelease"):
        return None
    version = release["tag_name"]
    if version_tuple(version) <= version_tuple(VERSION):
        return None
    asset = next((a for a in release.get("assets", []) if a.get("name") == ASSET_NAME), None)
    if not asset:
        raise ValueError("Hub release has no installer")
    digest = str(asset.get("digest", ""))
    if not re.fullmatch(r"sha256:[a-fA-F0-9]{64}", digest):
        raise ValueError("Hub release has no SHA-256 digest")
    size = asset.get("size")
    if not isinstance(size, int) or not 0 < size < 512 * 1024 * 1024:
        raise ValueError("Invalid Hub installer size")
    url = str(asset.get("browser_download_url", ""))
    if not url.startswith(f"https://github.com/{REPOSITORY}/releases/download/{version}/"):
        raise ValueError("Unexpected Hub installer address")
    return {"version": version.lstrip("v"), "url": url, "size": size, "sha256": digest[7:].lower()}


def download_installer(release, folder):
    version_tuple(release["version"])
    if not re.fullmatch(r"[a-fA-F0-9]{64}", str(release.get("sha256", ""))):
        raise ValueError("Invalid Hub installer digest")
    if not isinstance(release.get("size"), int) or not 0 < release["size"] < 512 * 1024 * 1024:
        raise ValueError("Invalid Hub installer size")
    if not str(release.get("url", "")).startswith(f"https://github.com/{REPOSITORY}/releases/download/"):
        raise ValueError("Unexpected Hub installer address")
    folder = Path(folder) / release["version"]
    reject_reparse(folder)
    folder.mkdir(parents=True, exist_ok=True)
    target = folder / ASSET_NAME
    temporary = target.with_suffix(".part")
    reject_reparse(target)
    reject_reparse(temporary)
    if target.is_file() and digest_file(target) == release["sha256"]:
        return target
    try:
        total = 0
        request = Request(release["url"], headers={"User-Agent": "EnigmaHub/" + VERSION})
        with urlopen(request, timeout=30) as source, temporary.open("wb") as output:
            while True:
                block = source.read(131072)
                if not block:
                    break
                total += len(block)
                if total > release["size"]:
                    raise ValueError("Hub installer exceeds expected size")
                output.write(block)
        if total != release["size"] or digest_file(temporary) != release["sha256"]:
            raise ValueError("Hub installer failed SHA-256 verification")
        os.replace(temporary, target)
        return target
    finally:
        temporary.unlink(missing_ok=True)


class HubUpdateWorker(QThread):
    completed = pyqtSignal(object, str)

    def __init__(self, folder):
        super().__init__()
        self.folder = folder

    def run(self):
        try:
            release = latest_installer()
            if release:
                release["path"] = str(download_installer(release, self.folder))
            self.completed.emit(release, "")
        except Exception as error:
            self.completed.emit(None, str(error))
