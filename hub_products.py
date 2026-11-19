"""Detect product versions independently of Hub's saved preferences."""
import ctypes
from functools import lru_cache
import os
from pathlib import Path
import re


def version_key(value):
    match = re.fullmatch(r"v?(\d+(?:\.\d+){1,3})(?:\+[-\w.]+)?", str(value).strip())
    if not match:
        return ()
    parts = tuple(map(int, match[1].split(".")))
    return parts + (0,) * (4 - len(parts))


def registered_version(product, folder):
    try:
        import winreg
        key = r"Software\Microsoft\Windows\CurrentVersion\Uninstall" + "\\" + ("EnigmaCube" if product["id"] == "cube" else "EnigmaDisk")
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, key) as handle:
            location = winreg.QueryValueEx(handle, "InstallLocation")[0]
            version = str(winreg.QueryValueEx(handle, "DisplayVersion")[0])
        normalize = lambda path: os.path.normcase(os.path.abspath(str(path).rstrip("\\/")))
        if normalize(location) == normalize(folder) and version_key(version):
            return version
    except (ImportError, OSError, TypeError, ValueError):
        pass
    return None


@lru_cache(maxsize=64)
def _exe_version(path, modified, size):
    if os.name != "nt":
        return None
    api = ctypes.WinDLL("version", use_last_error=True)
    api.GetFileVersionInfoSizeW.argtypes = [ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_uint32)]
    api.GetFileVersionInfoSizeW.restype = ctypes.c_uint32
    api.GetFileVersionInfoW.argtypes = [ctypes.c_wchar_p, ctypes.c_uint32, ctypes.c_uint32, ctypes.c_void_p]
    api.VerQueryValueW.argtypes = [ctypes.c_void_p, ctypes.c_wchar_p, ctypes.POINTER(ctypes.c_void_p), ctypes.POINTER(ctypes.c_uint)]
    ignored = ctypes.c_uint32()
    length = api.GetFileVersionInfoSizeW(path, ctypes.byref(ignored))
    if not length:
        return None
    buffer = ctypes.create_string_buffer(length)
    if not api.GetFileVersionInfoW(path, 0, length, buffer):
        return None
    pointer, count = ctypes.c_void_p(), ctypes.c_uint()
    if not api.VerQueryValueW(buffer, "\\", ctypes.byref(pointer), ctypes.byref(count)) or count.value < 52:
        return None
    fields = ctypes.cast(pointer, ctypes.POINTER(ctypes.c_uint32 * 13)).contents
    if fields[0] != 0xFEEF04BD:
        return None
    high, low = fields[2], fields[3]
    parts = (high >> 16, high & 65535, low >> 16, low & 65535)
    return ".".join(map(str, parts[:3] if parts[3] == 0 else parts)) if any(parts) else None


def executable_version(path):
    try:
        path = Path(path).resolve()
        stat = path.stat()
        return _exe_version(str(path), stat.st_mtime_ns, stat.st_size)
    except (OSError, ValueError):
        return None


def installed_version(product, folder):
    if not (Path(folder) / product["exe"]).is_file():
        return None
    # Cube's installer owns its registration; Disk may replace its own EXE.
    if product["id"] == "cube":
        return registered_version(product, folder) or executable_version(Path(folder) / product["exe"])
    return executable_version(Path(folder) / product["exe"]) or registered_version(product, folder)
