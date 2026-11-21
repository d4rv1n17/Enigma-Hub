"""Offline, one-use launch tickets. This is integration, not DRM.

Only the owning Hub process holds tickets; neither arguments nor persistent
settings grant a product permission to start. The HTTP listener is loopback
only and has no launch, download, shell, or filesystem commands.
"""
import json
import secrets
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer


def installed_hub_ready():
    """Products must be able to find a supported installed Hub after setup exits."""
    from pathlib import Path
    from hub_products import executable_version, version_key
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER,
                            r'Software\Microsoft\Windows\CurrentVersion\Uninstall\EnigmaHub') as key:
            folder = Path(winreg.QueryValueEx(key, 'InstallLocation')[0])
        marker = json.loads((folder / '.enigma-hub-install.json').read_text(encoding='utf-8'))
        exe = folder / 'EnigmaHub.exe'
        return (marker.get('product') == 'Enigma Hub' and
                version_key(marker.get('version')) >= (1, 3, 0, 0) and exe.is_file() and
                version_key(executable_version(exe)) >= (1, 3, 0, 0))
    except (ImportError, OSError, ValueError, TypeError, AttributeError):
        return False


def running_product(executable):
    """Exact-path process check, including products started before this Hub."""
    import ctypes
    from ctypes import wintypes
    import os
    import sys
    if sys.platform != 'win32':
        return False
    target = os.path.normcase(os.path.abspath(executable))
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    kernel.OpenProcess.restype = wintypes.HANDLE
    kernel.OpenProcess.argtypes = (wintypes.DWORD, wintypes.BOOL, wintypes.DWORD)
    kernel.CloseHandle.argtypes = (wintypes.HANDLE,)
    kernel.QueryFullProcessImageNameW.argtypes = (wintypes.HANDLE, wintypes.DWORD,
                                                wintypes.LPWSTR, ctypes.POINTER(wintypes.DWORD))
    ids = (wintypes.DWORD * 65536)()
    count = wintypes.DWORD()
    if not psapi.EnumProcesses(ids, ctypes.sizeof(ids), ctypes.byref(count)):
        raise OSError('Could not check running applications. Try again.')
    for pid in ids[:count.value // ctypes.sizeof(wintypes.DWORD)]:
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            continue
        try:
            size = wintypes.DWORD(32768)
            path = ctypes.create_unicode_buffer(size.value)
            if kernel.QueryFullProcessImageNameW(handle, 0, path, ctypes.byref(size)):
                if os.path.normcase(os.path.abspath(path.value)) == target:
                    return True
        finally:
            kernel.CloseHandle(handle)
    return False


class LaunchBroker:
    def __init__(self):
        self._tickets = {}
        self._lock = threading.Lock()
        broker = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def do_POST(self):
                self.connection.settimeout(2)
                try:
                    size = int(self.headers.get('Content-Length', '0'))
                    if self.path != '/claim' or not 0 < size <= 1024:
                        raise ValueError('Invalid request')
                    body = json.loads(self.rfile.read(size))
                    allowed = broker.claim(body.get('ticket'), body.get('product'))
                    self.send_response(200 if allowed else 403)
                    self.send_header('Content-Length', '0')
                    self.end_headers()
                except (ValueError, TypeError, AttributeError, OSError):
                    self.send_error(400)

        self.server = ThreadingHTTPServer(('127.0.0.1', 0), Handler)
        self.server.daemon_threads = True
        self.endpoint = 'http://127.0.0.1:' + str(self.server.server_port) + '/claim'
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)
        self.thread.start()

    def issue(self, product):
        if product not in ('cube', 'disk'):
            raise ValueError('Unknown product')
        token = secrets.token_urlsafe(32)
        with self._lock:
            now = time.monotonic()
            self._tickets = {k: v for k, v in self._tickets.items() if v[1] > now}
            self._tickets[token] = (product, now + 90)
        return token

    def claim(self, token, product):
        if not isinstance(token, str) or not isinstance(product, str):
            return False
        with self._lock:
            item = self._tickets.get(token)
            if not item or item[0] != product or item[1] <= time.monotonic():
                return False
            del self._tickets[token]
            return True

    def environment(self, product):
        import os
        env = os.environ.copy()
        env['ENIGMA_HUB_ENDPOINT'] = self.endpoint
        env['ENIGMA_HUB_TICKET'] = self.issue(product)
        return env

    def close(self):
        self.server.shutdown()
        self.server.server_close()
