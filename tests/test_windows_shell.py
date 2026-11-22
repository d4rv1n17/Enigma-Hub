import ctypes
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from hub_windows import APP_ID, PROPVARIANT, set_shortcut_identity


@unittest.skipUnless(sys.platform == 'win32', 'Windows Shell COM integration')
class ShellIdentityTests(unittest.TestCase):
    def test_real_shortcut_identity_survives_save_without_changing_launch_target(self):
        with tempfile.TemporaryDirectory() as directory:
            shortcut = Path(directory) / 'Enigma Hub.lnk'
            env = dict(os.environ, ENIGMA_TEST_SHORTCUT=str(shortcut), ENIGMA_TEST_EXE=sys.executable)
            subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:ENIGMA_TEST_SHORTCUT); $s.TargetPath=$env:ENIGMA_TEST_EXE; $s.Arguments='--version'; $s.Save()"],
                env=env, capture_output=True, check=True)
            set_shortcut_identity(shortcut)
            set_shortcut_identity(shortcut)  # Reinstall/repair is idempotent.
            result = subprocess.run(['powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
                "$s=(New-Object -ComObject WScript.Shell).CreateShortcut($env:ENIGMA_TEST_SHORTCUT); $shell=New-Object -ComObject Shell.Application; $item=$shell.Namespace((Split-Path $env:ENIGMA_TEST_SHORTCUT)).ParseName('Enigma Hub.lnk'); @{id=$item.ExtendedProperty('System.AppUserModel.ID'); target=$s.TargetPath; arguments=$s.Arguments} | ConvertTo-Json -Compress"],
                env=env, capture_output=True, text=True, check=True)
            properties = json.loads(result.stdout)
            self.assertEqual(properties['id'], APP_ID)
            self.assertEqual(os.path.normcase(properties['target']), os.path.normcase(sys.executable))
            self.assertEqual(properties['arguments'], '--version')

    def test_missing_shortcut_is_not_created_or_registered(self):
        with tempfile.TemporaryDirectory() as directory:
            missing = Path(directory) / 'missing.lnk'
            with self.assertRaises(FileNotFoundError):
                set_shortcut_identity(missing)
            self.assertFalse(missing.exists())

    def test_variant_layout_for_windows_x64(self):
        if ctypes.sizeof(ctypes.c_void_p) == 8:
            self.assertEqual(ctypes.sizeof(PROPVARIANT), 24)
