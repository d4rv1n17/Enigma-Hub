"""Build the app payload and the matching branded installer."""
import hashlib
import json
from pathlib import Path
import subprocess
import sys
from hub_update import VERSION

if sys.version_info < (3, 13):
    raise RuntimeError("Use supported Python 3.13 or newer to build a release.")

root = Path(__file__).resolve().parent
output = root / "Output"
payload = root / "build/payload"
payload.mkdir(parents=True, exist_ok=True)

def bundle(name, entry, destination, extra=()):
    subprocess.run([
        sys.executable, "-m", "PyInstaller", "--noconfirm", "--onefile", "--windowed",
        "--name", name, "--distpath", str(destination),
        "--icon", "assets/hub-icon.ico", "--add-data", "assets;assets",
        *extra, entry,
    ], cwd=root, check=True)

bundle("EnigmaHub", "enigma_hub.py", output)
exe = output / "EnigmaHub.exe"
import shutil
shutil.copy2(exe, payload / exe.name)
(payload / "release.json").write_text(json.dumps({
    "version": VERSION, "sha256": hashlib.sha256(exe.read_bytes()).hexdigest()
}), encoding="utf-8")
bundle("EnigmaHubSetup", "hub_setup.py", output, ("--add-data", str(payload) + ";payload"))
release_files = (output / "EnigmaHub.exe", output / "EnigmaHubSetup.exe")
checksums = [
    hashlib.sha256(file.read_bytes()).hexdigest() + "  " + file.name
    for file in release_files
]
(output / "SHA256SUMS.txt").write_text("\n".join(checksums) + "\n", encoding="ascii")
import importlib.metadata
report = {
    "version": VERSION,
    "python": sys.version,
    "packages": {name: importlib.metadata.version(name) for name in ("PyQt5", "PyQt5-Qt5", "PyQt5-sip", "PyInstaller")},
}
(output / "build-info.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
print("Ready:", output / "EnigmaHubSetup.exe")
