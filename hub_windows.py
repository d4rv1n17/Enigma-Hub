"""Windows shell identity shared by the process and its installed shortcut."""
import ctypes
from pathlib import Path
import uuid

APP_ID = 'EnigmaStudio.EnigmaHub'


class GUID(ctypes.Structure):
    _fields_ = [('data', ctypes.c_ubyte * 16)]

    @classmethod
    def parse(cls, value):
        return cls.from_buffer_copy(uuid.UUID(value).bytes_le)


class PROPERTYKEY(ctypes.Structure):
    _fields_ = [('fmtid', GUID), ('pid', ctypes.c_uint32)]


class PROPVARIANT(ctypes.Structure):
    _fields_ = [('vt', ctypes.c_ushort), ('reserved', ctypes.c_ushort * 3),
                ('data', ctypes.c_uint64 * 2)]


def check_hresult(result):
    if result < 0:
        raise OSError('Windows shell property error 0x%08X' % (result & 0xffffffff))


def set_shortcut_identity(shortcut):
    """Persist the same AppID as the process, so pinning finds the real .lnk.

    Use the Shell property store, not undocumented Taskband registry edits.
    """
    shortcut = Path(shortcut).resolve(strict=True)
    ole = ctypes.WinDLL('ole32')
    shell = ctypes.WinDLL('shell32')
    ole.CoInitializeEx.argtypes = (ctypes.c_void_p, ctypes.c_uint32)
    ole.CoInitializeEx.restype = ctypes.c_long
    initialized = ole.CoInitializeEx(None, 2)
    if initialized not in (0, 1, -2147417850):  # RPC_E_CHANGED_MODE: use current apartment.
        check_hresult(initialized)
    store = ctypes.c_void_p()
    variant = PROPVARIANT()
    try:
        iid = GUID.parse('886d8eeb-8cf2-4446-8d02-cdba1dbdcf99')
        shell.SHGetPropertyStoreFromParsingName.argtypes = (ctypes.c_wchar_p, ctypes.c_void_p,
            ctypes.c_uint32, ctypes.POINTER(GUID), ctypes.POINTER(ctypes.c_void_p))
        shell.SHGetPropertyStoreFromParsingName.restype = ctypes.c_long
        check_hresult(shell.SHGetPropertyStoreFromParsingName(str(shortcut), None, 2, ctypes.byref(iid), ctypes.byref(store)))
        table = ctypes.cast(store, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
        # InitPropVariantFromString is an SDK inline, not a propsys export.
        # SetValue copies this borrowed LPWSTR; keep its Python buffer alive.
        value = ctypes.create_unicode_buffer(APP_ID)
        variant.vt = 31  # VT_LPWSTR
        variant.data[0] = ctypes.addressof(value)
        key = PROPERTYKEY(GUID.parse('9f4c2855-9f79-4b39-a8d0-e1d42de1d5f3'), 5)
        set_value = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p, ctypes.POINTER(PROPERTYKEY), ctypes.POINTER(PROPVARIANT))(table[6])
        commit = ctypes.WINFUNCTYPE(ctypes.c_long, ctypes.c_void_p)(table[7])
        check_hresult(set_value(store, ctypes.byref(key), ctypes.byref(variant)))
        check_hresult(commit(store))
    finally:
        if store:
            table = ctypes.cast(store, ctypes.POINTER(ctypes.POINTER(ctypes.c_void_p))).contents
            ctypes.WINFUNCTYPE(ctypes.c_ulong, ctypes.c_void_p)(table[2])(store)
        if initialized in (0, 1):
            ole.CoUninitialize()
    shell.SHChangeNotify.argtypes = (ctypes.c_long, ctypes.c_uint32, ctypes.c_void_p, ctypes.c_void_p)
    shell.SHChangeNotify(0x2000, 5, ctypes.cast(ctypes.c_wchar_p(str(shortcut)), ctypes.c_void_p), None)


def set_process_identity():
    shell = ctypes.WinDLL('shell32')
    shell.SetCurrentProcessExplicitAppUserModelID.argtypes = (ctypes.c_wchar_p,)
    shell.SetCurrentProcessExplicitAppUserModelID.restype = ctypes.c_long
    check_hresult(shell.SetCurrentProcessExplicitAppUserModelID(APP_ID))
