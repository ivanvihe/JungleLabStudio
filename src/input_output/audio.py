import numpy as np
import sounddevice as sd
from collections import deque
from typing import Optional, Tuple


class AudioInput:
    def __init__(self, device: Optional[str] = None, samplerate: int = 48000, blocksize: int = 1024):
        self.device = device
        self.samplerate = samplerate
        self.blocksize = blocksize
        self.stream: Optional[sd.InputStream] = None
        self.buffer = deque(maxlen=8)
        self.level = 0.0
        self.bands = (0.0, 0.0, 0.0)

    def start(self) -> None:
        self.stream = sd.InputStream(
            device=self.device,
            channels=2,
            samplerate=self.samplerate,
            blocksize=self.blocksize,
            callback=self._callback,
        )
        self.stream.start()

    def _callback(self, indata, frames, time_info, status) -> None:
        if status:
            return
        mono = np.mean(indata, axis=1)
        window = np.hanning(len(mono))
        fft = np.abs(np.fft.rfft(mono * window))
        self.level = float(np.clip(np.mean(fft) / 1000.0, 0.0, 10.0))
        self.bands = self._band_power(fft)
        self.buffer.append(fft)

    def fft_texture_data(self, bins: int = 512) -> np.ndarray:
        if not self.buffer:
            return np.zeros(bins, dtype=np.float32)
        latest = self.buffer[-1]
        sampled = np.interp(np.linspace(0, len(latest) - 1, bins), np.arange(len(latest)), latest)
        norm = sampled / (np.max(sampled) + 1e-6)
        return norm.astype(np.float32)

    def band_levels(self) -> tuple[float, float, float]:
        return self.bands

    def _band_power(self, fft: np.ndarray) -> tuple[float, float, float]:
        freqs = np.fft.rfftfreq(len(fft) * 2 - 2, 1 / self.samplerate)
        def band(lo, hi):
            mask = (freqs >= lo) & (freqs <= hi)
            if not np.any(mask):
                return 0.0
            return float(np.mean(fft[mask]) / (np.max(fft[mask]) + 1e-6))
        return (band(20, 140), band(140, 1200), band(1200, 6000))

    def stop(self) -> None:
        if self.stream:
            self.stream.stop()
            self.stream.close()
            self.stream = None

    @staticmethod
    def list_devices() -> Tuple[str, ...]:
        return tuple(d["name"] for d in sd.query_devices())
