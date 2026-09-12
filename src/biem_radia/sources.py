from __future__ import annotations

import ctypes as ct
import os
import queue
import socket
import struct
import threading
from pathlib import Path

import numpy as np

from .models import SAMPLE_RATE


def decode_iq(raw: bytes) -> np.ndarray:
    if len(raw) % 2:
        raise ValueError("Eksik I/Q örneği.")
    values = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 127.5) / 128.0
    return values[::2] + 1j * values[1::2]


class RtlLibrary:
    def __init__(self, path: Path):
        self.directory = os.add_dll_directory(str(path.parent.resolve()))
        self.lib = ct.CDLL(str(path.resolve()))
        self.lib.rtlsdr_get_device_count.restype = ct.c_uint32
        self.lib.rtlsdr_get_device_name.argtypes = [ct.c_uint32]
        self.lib.rtlsdr_get_device_name.restype = ct.c_char_p
        self.lib.rtlsdr_open.argtypes = [ct.POINTER(ct.c_void_p), ct.c_uint32]
        for name in ("rtlsdr_close", "rtlsdr_reset_buffer", "rtlsdr_cancel_async"):
            getattr(self.lib, name).argtypes = [ct.c_void_p]
        for name in ("rtlsdr_set_sample_rate", "rtlsdr_set_center_freq"):
            getattr(self.lib, name).argtypes = [ct.c_void_p, ct.c_uint32]
        for name in (
            "rtlsdr_set_tuner_gain_mode",
            "rtlsdr_set_tuner_gain",
            "rtlsdr_set_freq_correction",
        ):
            getattr(self.lib, name).argtypes = [ct.c_void_p, ct.c_int]
        self.lib.rtlsdr_get_tuner_gains.argtypes = [ct.c_void_p, ct.POINTER(ct.c_int)]
        self.callback_type = ct.CFUNCTYPE(None, ct.POINTER(ct.c_ubyte), ct.c_uint32, ct.c_void_p)
        self.lib.rtlsdr_read_async.argtypes = [
            ct.c_void_p,
            self.callback_type,
            ct.c_void_p,
            ct.c_uint32,
            ct.c_uint32,
        ]

    def devices(self) -> list[str]:
        return [
            self.lib.rtlsdr_get_device_name(i).decode(errors="replace")
            for i in range(self.lib.rtlsdr_get_device_count())
        ]


class USBSource:
    def __init__(self, dll: Path, center: int, index: int = 0, ppm: int = 0, gain_db: float = 19):
        self.library = RtlLibrary(dll)
        self.handle = ct.c_void_p()
        self.queue: queue.Queue[bytes] = queue.Queue(maxsize=32)
        self.error: str | None = None
        self.thread: threading.Thread | None = None
        self.closed = False
        self.callback = self.library.callback_type(self._callback)
        if index >= len(self.library.devices()):
            raise RuntimeError("RTL-SDR bulunamadı. USB bağlantısını kontrol edin.")
        self._check(
            self.library.lib.rtlsdr_open(ct.byref(self.handle), index),
            "USB açma; SDR# cihazı kullanıyor olabilir",
        )
        try:
            for operation, value in (
                ("rtlsdr_set_sample_rate", SAMPLE_RATE),
                ("rtlsdr_set_center_freq", center),
                ("rtlsdr_set_tuner_gain_mode", 1),
            ):
                self._check(getattr(self.library.lib, operation)(self.handle, value), operation)
            count = self.library.lib.rtlsdr_get_tuner_gains(self.handle, None)
            if count <= 0 or count > 256:
                raise RuntimeError("Tuner kazanç listesi alınamadı.")
            gains = (ct.c_int * count)()
            self._check(
                self.library.lib.rtlsdr_get_tuner_gains(self.handle, gains), "Kazanç listesi"
            )
            gain = min(gains, key=lambda value: abs(value - gain_db * 10))
            self._check(self.library.lib.rtlsdr_set_tuner_gain(self.handle, gain), "Tuner kazancı")
            self.gain_db = gain / 10
            if ppm:
                self._check(self.library.lib.rtlsdr_set_freq_correction(self.handle, ppm), "PPM")
            self._check(self.library.lib.rtlsdr_reset_buffer(self.handle), "USB tampon sıfırlama")
            self.thread = threading.Thread(target=self._run, daemon=True)
            self.thread.start()
        except Exception:
            self.close()
            raise

    @staticmethod
    def _check(code: int, operation: str):
        if code < 0:
            raise RuntimeError(f"{operation}: hata {code}")

    def _callback(self, buffer, length, context):
        try:
            self.queue.put_nowait(ct.string_at(buffer, length))
        except queue.Full:
            self.error = "USB işleme kuyruğu doldu; kayıt kaybını önlemek için alım durduruldu."

    def _run(self):
        result = self.library.lib.rtlsdr_read_async(self.handle, self.callback, None, 12, 32768)
        if not self.closed:
            self.error = f"USB akışı sonlandı ({result})."

    def read(self) -> np.ndarray:
        if self.error:
            raise RuntimeError(self.error)
        try:
            return decode_iq(self.queue.get(timeout=3))
        except queue.Empty as exc:
            raise RuntimeError("USB cihazından 3 saniyedir veri alınamıyor.") from exc

    def close(self):
        self.closed = True
        if self.handle:
            if self.thread is not None:
                self.library.lib.rtlsdr_cancel_async(self.handle)
                self.thread.join(timeout=3)
                if self.thread.is_alive():
                    raise RuntimeError("USB iş parçacığı kapanmadı; uygulamayı yeniden başlatın.")
            self.library.lib.rtlsdr_close(self.handle)
            self.handle = ct.c_void_p()


class TCPSource:
    """rtl_tcp unsigned 8-bit I/Q protocol; this is not a repeater voice protocol."""

    def __init__(self, host: str, port: int, center: int, ppm: int = 0):
        self.socket = socket.create_connection((host, port), timeout=3)
        try:
            header = self._exact(12)
            if header[:4] != b"RTL0":
                raise RuntimeError("Sunucu rtl_tcp protokolü kullanmıyor.")
            for command, value in ((2, SAMPLE_RATE), (1, center), (3, 0), (5, ppm & 0xFFFFFFFF)):
                self.socket.sendall(struct.pack(">BI", command, value))
        except Exception:
            self.socket.close()
            raise

    def _exact(self, size: int) -> bytes:
        data = bytearray()
        while len(data) < size:
            part = self.socket.recv(size - len(data))
            if not part:
                raise RuntimeError("Ethernet SDR bağlantısı kesildi.")
            data.extend(part)
        return bytes(data)

    def read(self) -> np.ndarray:
        return decode_iq(self._exact(32768))

    def close(self):
        self.socket.close()
