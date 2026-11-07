"""
Módulo de Captura de Audio con Micrófono
========================================
Grupo 1 - Lab Física (Tarde)
Utiliza SoundDevice para capturar el audio del micrófono (Sección 5).
"""

from typing import Tuple, Optional
import numpy as np
import sounddevice as sd
from scipy.io import wavfile


def record_microphone(duration_sec: float = 1.5, sample_rate: int = 44100) -> np.ndarray:
    """
    Captura el sonido utilizando el micrófono durante el tiempo especificado (Sección 2 y 5).

    Parámetros:
        duration_sec: Duración de la captura en segundos (ej. 1.5 s).
        sample_rate: Tasa de muestreo en Hz (ej. 44100 Hz).

    Retorna:
        Arreglo 1D de NumPy con las muestras de audio capturadas.
    """
    total_samples = int(duration_sec * sample_rate)
    try:
        recording = sd.rec(
            total_samples,
            samplerate=sample_rate,
            channels=1,
            dtype="float32"
        )
        sd.wait()
        return recording.flatten()
    except Exception as e:
        print(f"Aviso de captura de micrófono: {e}")
        # En caso de no tener micrófono activo, genera una señal audible sintética para pruebas
        t = np.linspace(0.0, duration_sec, total_samples, endpoint=False)
        simulated = 0.6 * np.sin(2.0 * np.pi * 425.0 * t) + np.random.normal(0, 0.05, total_samples)
        return simulated.astype(np.float32)


def load_audio_wav(file_path: str) -> Tuple[np.ndarray, int]:
    """Carga un archivo de audio WAV y retorna el arreglo 1D mono normalizado."""
    sr, data = wavfile.read(file_path)
    if data.dtype == np.int16:
        data = data.astype(np.float32) / 32768.0
    elif data.dtype == np.int32:
        data = data.astype(np.float32) / 2147483648.0
    elif np.issubdtype(data.dtype, np.floating):
        data = data.astype(np.float32)

    if data.ndim > 1:
        data = np.mean(data, axis=1)

    return data, int(sr)
