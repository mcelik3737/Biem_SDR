"""User-bound Windows DPAPI envelope, not a process or administrator security boundary."""

import ctypes
import os
from pathlib import Path

MAGIC = b"BIEM-RADIA-DPAPI-1\0"


class Blob(ctypes.Structure):
    _fields_ = [("size", ctypes.c_ulong), ("data", ctypes.POINTER(ctypes.c_ubyte))]


def transform(data: bytes, *, decrypt: bool = False) -> bytes:
    if os.name != "nt":
        raise OSError("Kayıt koruması Windows DPAPI gerektirir.")
    buffer = (ctypes.c_ubyte * len(data)).from_buffer_copy(data)
    source = Blob(len(data), buffer)
    result = Blob()
    crypt = ctypes.WinDLL("crypt32", use_last_error=True)
    kernel = ctypes.WinDLL("kernel32", use_last_error=True)
    kernel.LocalFree.argtypes = [ctypes.c_void_p]
    kernel.LocalFree.restype = ctypes.c_void_p
    function = crypt.CryptUnprotectData if decrypt else crypt.CryptProtectData
    function.argtypes = [
        ctypes.POINTER(Blob),
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_void_p,
        ctypes.c_ulong,
        ctypes.POINTER(Blob),
    ]
    function.restype = ctypes.c_int
    if not function(ctypes.byref(source), None, None, None, None, 1, ctypes.byref(result)):
        raise ctypes.WinError(ctypes.get_last_error())
    try:
        return ctypes.string_at(result.data, result.size)
    finally:
        kernel.LocalFree(result.data)


def read_audio(path: Path) -> bytes:
    data = path.read_bytes()
    return transform(data[len(MAGIC) :], decrypt=True) if data.startswith(MAGIC) else data


def seal(path: Path) -> Path:
    """Verify decryptability before removing plaintext. A failed write preserves its source."""
    if path.suffix == ".radia":
        return path
    destination = path.with_name(path.name + ".radia")
    data = path.read_bytes()
    if destination.exists():
        if read_audio(destination) != data:
            raise OSError(f"Koruma hedefi zaten var ve farklı: {destination}")
    else:
        encrypted = MAGIC + transform(data)
        temporary = destination.with_name(destination.name + ".part")
        with temporary.open("xb") as stream:
            stream.write(encrypted)
            stream.flush()
            os.fsync(stream.fileno())
        if read_audio(temporary) != data:
            raise OSError("Şifreli kayıt doğrulanamadı; asıl dosya korundu.")
        temporary.replace(destination)
    # The caller updates database references before deleting the source.
    return destination
