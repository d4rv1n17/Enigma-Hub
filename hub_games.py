"""Locate ready Steam installs, including non-default client/library folders."""
import os
from pathlib import Path
import re
from urllib.parse import urlsplit


def valid_web_url(value):
    try:
        address = urlsplit(value)
        return address.scheme in ("http", "https") and bool(address.hostname)
    except (ValueError, TypeError):
        return False


def steam_client_path():
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as key:
            return Path(winreg.QueryValueEx(key, "SteamPath")[0])
    except (ImportError, OSError, TypeError, ValueError):
        return None


def steam_roots():
    roots = [Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam", Path(os.environ.get("ProgramFiles", r"C:\Program Files")) / "Steam"]
    registered = steam_client_path()
    if registered:
        roots.insert(0, registered)
    for root in list(roots):
        try:
            data = (root / "steamapps/libraryfolders.vdf").read_text(encoding="utf-8-sig", errors="replace")
            roots.extend(Path(path.replace("\\\\", "\\")) for path in re.findall(r'"path"\s+"([^"]+)"', data))
        except OSError:
            pass
    return list(dict.fromkeys(roots))


def find_installed_game(config):
    custom = config.get("exe", "")
    if custom:
        try:
            path = Path(custom)
            if path.suffix.lower() == ".exe" and path.is_file():
                return path
        except (OSError, ValueError):
            pass
    appid = str(config.get("steam_app_id", ""))
    if not re.fullmatch(r"[0-9]+", appid):
        return None
    for root in steam_roots():
        manifest = root / "steamapps" / f"appmanifest_{appid}.acf"
        try:
            data = manifest.read_text(encoding="utf-8-sig", errors="replace")
            fields = dict(re.findall(r'"(appid|installdir|StateFlags)"\s+"([^"]*)"', data))
            name = fields.get("installdir", "")
            if fields.get("appid") != appid or not int(fields.get("StateFlags", "0")) & 4:
                continue
            if not name or name in (".", "..") or any(character in name for character in "\\/:"):
                continue
            if (root / "steamapps/common" / name).is_dir():
                return manifest
        except (OSError, ValueError):
            pass
    return None
