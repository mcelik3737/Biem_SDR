import io
import wave

import numpy as np
import sounddevice as sd


def stop():
    sd.stop()


def play(data: bytes, boost: bool = False):
    """Decode only in memory; never create a plaintext listening copy."""
    with wave.open(io.BytesIO(data), "rb") as wav:
        if wav.getsampwidth() != 2:
            raise ValueError("Dinleme için 16 bit PCM WAV gerekli.")
        samples = np.frombuffer(wav.readframes(wav.getnframes()), dtype="<i2")
        audio = samples.astype(np.float32).reshape(-1, wav.getnchannels()) / 32768
        rate = wav.getframerate()
    if boost:
        audio *= 2
        magnitude = abs(audio)
        audio = np.sign(audio) * np.where(
            magnitude <= 0.9,
            magnitude,
            0.9 + 0.1 * (1 - np.exp(-np.maximum(magnitude - 0.9, 0) / 0.1)),
        )
    sd.play(audio, rate, blocking=False)
