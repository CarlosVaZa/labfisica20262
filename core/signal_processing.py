"""
Módulo de Procesamiento de Audio y Frecuencias (FFT)
===================================================
Grupo 1 - Lab Física (Tarde)

Herramientas:
- SciPy: Analizar frecuencias y detectar picos.
- NumPy: Cálculos matemáticos y FFT.
"""

from typing import Tuple, List, Dict, Optional
import numpy as np
from scipy import signal


def filter_ambient_noise(
    audio_data: np.ndarray,
    sample_rate: int = 44100,
    low_cutoff: float = 80.0,
    high_cutoff: float = 2500.0
) -> np.ndarray:
    """
    Filtro pasa-banda digital para reducir el ruido ambiental (Sección 8 del documento).
    Elimina ruidos de baja frecuencia y ruido de alta frecuencia innecesario.
    """
    if len(audio_data) == 0:
        return audio_data

    # Quitar valor medio (DC)
    clean_audio = audio_data - np.mean(audio_data)

    nyquist = 0.5 * sample_rate
    low = max(10.0, low_cutoff) / nyquist
    high = min(nyquist - 10.0, high_cutoff) / nyquist

    if low >= high:
        return clean_audio

    try:
        b, a = signal.butter(4, [low, high], btype="bandpass")
        filtered = signal.filtfilt(b, a, clean_audio)
        return filtered.astype(np.float32)
    except Exception:
        return clean_audio


def analyze_fft(
    audio_data: np.ndarray,
    sample_rate: int = 44100
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Analiza la señal de audio mediante la Transformada Rápida de Fourier (FFT)
    como se especifica en la Sección 1, 3 y 5 del documento.

    Retorna:
        frecuencias: Arreglo de frecuencias en Hz.
        magnitudes: Amplitud / magnitud de cada componente frecuencial.
    """
    n_samples = len(audio_data)
    if n_samples == 0:
        return np.array([]), np.array([])

    # Ventana de Hann para reducir dispersión espectral
    window = np.hanning(n_samples)
    windowed_signal = audio_data * window

    # FFT unilateral
    fft_vals = np.fft.rfft(windowed_signal)
    freqs = np.fft.rfftfreq(n_samples, d=1.0 / sample_rate)

    # Magnitud normalizada
    magnitude = np.abs(fft_vals) / (n_samples / 2.0)

    return freqs, magnitude


def detect_resonance_frequency(
    freqs: np.ndarray,
    magnitudes: np.ndarray,
    min_freq: float = 120.0,
    max_freq: float = 1800.0,
    smoothing_hz: float = 0.0,
    sample_rate: int = 0,
    n_samples: int = 0,
) -> Dict[str, float]:
    """
    Detecta automáticamente el pico de resonancia de mayor amplitud dentro del rango útil
    utilizando SciPy (Sección 5 y 8 del documento).

    Parámetros:
        freqs: Arreglo de frecuencias en Hz.
        magnitudes: Magnitudes del espectro (sin suavizar).
        min_freq: Frecuencia mínima de búsqueda (Hz).
        max_freq: Frecuencia máxima de búsqueda (Hz).
        smoothing_hz: Ancho de la media móvil en Hz para la detección de picos.
            0 = sin suavizado (comportamiento original).
        sample_rate: Frecuencia de muestreo (necesaria si smoothing_hz > 0).
        n_samples: Número de muestras de la señal (necesaria si smoothing_hz > 0).

    Retorna:
        Diccionario con la frecuencia de resonancia (f1) en Hz, su amplitud,
        los picos prominentes encontrados y si se usó el fallback.
    """
    empty = {"frequency_hz": 0.0, "amplitude": 0.0, "prominent_peaks": [], "fallback": False}
    if len(freqs) == 0 or len(magnitudes) == 0:
        return empty

    # Limitar al rango acústico típico del tubo con agua (120 Hz a 1800 Hz)
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    if not np.any(mask):
        return empty

    sub_freqs = freqs[mask]
    sub_mags = magnitudes[mask]

    # Suavizado opcional por media móvil para la detección de picos
    if smoothing_hz > 0 and sample_rate > 0 and n_samples > 0:
        freq_resolution = sample_rate / n_samples
        window_bins = max(1, int(round(smoothing_hz / freq_resolution)))
        if window_bins > 1 and window_bins <= len(sub_mags):
            kernel = np.ones(window_bins) / window_bins
            smoothed = np.convolve(sub_mags, kernel, mode="same")
        else:
            smoothed = sub_mags
    else:
        smoothed = sub_mags

    # Encontrar picos con SciPy (sobre el espectro posiblemente suavizado)
    prominence = 0.2 * np.max(smoothed) if np.max(smoothed) > 0 else 0.01
    peaks, properties = signal.find_peaks(smoothed, prominence=prominence)

    fallback = False
    if len(peaks) > 0:
        # Pico más alto
        best_peak_idx = peaks[np.argmax(smoothed[peaks])]
        # Reportar amplitud del espectro original (no suavizado)
        peak_freq = sub_freqs[best_peak_idx]
        peak_amp = float(sub_mags[best_peak_idx])

        # Los 3 picos más prominentes (por amplitud del suavizado, reportando amplitud original)
        sorted_peaks = sorted(peaks, key=lambda i: smoothed[i], reverse=True)
        prominent_peaks = [
            {"frequency_hz": float(sub_freqs[i]), "amplitude": float(sub_mags[i])}
            for i in sorted_peaks[:3]
        ]
    else:
        # Si no supera la prominencia, tomar el valor máximo en el rango
        fallback = True
        best_idx = np.argmax(smoothed)
        peak_freq = sub_freqs[best_idx]
        peak_amp = float(sub_mags[best_idx])
        prominent_peaks = [{"frequency_hz": float(peak_freq), "amplitude": peak_amp}]

    return {
        "frequency_hz": float(peak_freq),
        "amplitude": peak_amp,
        "prominent_peaks": prominent_peaks,
        "fallback": fallback,
    }
