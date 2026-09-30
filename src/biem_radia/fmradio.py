import queue
import threading

import numpy as np
import sounddevice as sd
from scipy import signal

from .models import SAMPLE_RATE
from .sources import USBSource


class WFM:
    def __init__(self):
        self.rf = np.asarray(signal.butter(8, 90000, fs=SAMPLE_RATE, output="sos"))
        self.rf_state = np.zeros((len(self.rf), 2), dtype=np.complex128)
        self.audio = np.asarray(signal.butter(6, 15000, fs=240000, output="sos"))
        self.audio_state = np.zeros((len(self.audio), 2))
        self.position = 0
        self.if_position = 0
        self.previous = 0j
        self.alpha = float(np.exp(-1 / (48000 * 50e-6)))
        self.de_state = np.zeros(1)

    def process(self, iq):
        filtered, self.rf_state = signal.sosfilt(self.rf, iq, zi=self.rf_state)
        narrow = filtered[(-self.position) % 4 :: 4]
        self.position += len(iq)
        if not len(narrow):
            return np.zeros(0, dtype=np.float32)
        fm = (
            np.angle(narrow * np.conj(np.concatenate(([self.previous], narrow[:-1]))))
            * 240000
            / (2 * np.pi * 75000)
        )
        self.previous = narrow[-1]
        audio, self.audio_state = signal.sosfilt(self.audio, fm, zi=self.audio_state)
        down = audio[(-self.if_position) % 5 :: 5]
        self.if_position += len(narrow)
        out, self.de_state = signal.lfilter(
            [1 - self.alpha], [1, -self.alpha], down, zi=self.de_state
        )
        return np.clip(out, -1, 1).astype(np.float32)


class FMRadio:
    def __init__(self):
        self.thread = None
        self.stop_event = threading.Event()
        self.messages = queue.Queue()
        self.volume = 0.7

    @property
    def running(self):
        return self.thread is not None and self.thread.is_alive()

    def start(self, dll, frequency, ppm, gain, index=0):
        if self.running:
            raise ValueError("FM RADIO zaten açık.")
        if not 88500000 <= frequency <= 108000000:
            raise ValueError("FM RADIO: 88,5–108 MHz.")
        self.stop_event.clear()
        self.thread = threading.Thread(
            target=self._run, args=(dll, frequency, ppm, gain, index), daemon=True
        )
        self.thread.start()

    def stop(self):
        self.stop_event.set()

    def _run(self, dll, frequency, ppm, gain, index):
        source = None
        try:
            source = USBSource(dll, frequency, index=index, ppm=ppm, gain_db=gain)
            demod = WFM()
            with sd.OutputStream(
                samplerate=48000, channels=1, dtype="float32", latency="high"
            ) as output:
                self.messages.put(f"FM RADIO • {frequency / 1e6:.1f} MHz • WFM mono")
                while not self.stop_event.is_set():
                    audio = demod.process(source.read()) * self.volume
                    if len(audio):
                        output.write(audio)
        except Exception as exc:
            self.messages.put(f"FM RADIO hatası: {exc}")
        finally:
            if source is not None:
                try:
                    source.close()
                except Exception as exc:
                    self.messages.put(str(exc))
            self.messages.put("FM RADIO kapalı")
