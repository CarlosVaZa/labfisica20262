"""
Módulo de Procesamiento Digital de Señales (DSP)
===============================================
Implementa algoritmos de filtrado, ventanado, Transformada Rápida de Fourier (FFT),
detección de picos espectrales con interpolación parabólica y cálculo de SNR.
"""

from typing import Tuple, List, Dict, Optional
import numpy as np
from scipy import signal


def remove_dc_offset(audio_data: np.ndarray) -> np.ndarray:
    """
    Elimina la componente de corriente directa (DC offset / valor medio) de la señal.
    """
    if audio_data.size == 0:
        return audio_data
    return audio_data - np.mean(audio_data)


def apply_bandpass_filter(
    audio_data: np.ndarray,
    sample_rate: int,
    low_cutoff: float = 80.0,
    high_cutoff: float = 3000.0,
    order: int = 4
) -> np.ndarray:
    """
    Aplica un filtro Butterworth pasa-banda para eliminar zumbidos de baja frecuencia
    (mains 50/60 Hz, turbulencias de aire al soplar) y ruido de muy alta frecuencia.

    Parámetros:
        audio_data: Arreglo 1D con las muestras de audio.
        sample_rate: Frecuencia de muestreo en Hz (ej. 44100).
        low_cutoff: Frecuencia de corte inferior en Hz.
        high_cutoff: Frecuencia de corte superior en Hz.
        order: Orden del filtro Butterworth.

    Retorna:
        Señal filtrada.
    """
    if len(audio_data) == 0:
        return audio_data

    nyquist = 0.5 * sample_rate
    low = max(10.0, low_cutoff) / nyquist
    high = min(nyquist - 10.0, high_cutoff) / nyquist

    if low >= high or low <= 0 or high >= 1:
        # Fallback seguro si los cortes son incompatibles
        return audio_data

    b, a = signal.butter(order, [low, high], btype='bandpass')
    filtered = signal.filtfilt(b, a, audio_data)
    return filtered


def compute_fft(
    audio_data: np.ndarray,
    sample_rate: int,
    window_type: str = "hann",
    zero_padding_factor: int = 2
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Calcula la Transformada Rápida de Fourier (FFT) unilateral de la señal de audio.

    Aplica ventanado para minimizar fuga espectral (spectral leakage) y zero-padding
    opcional para aumentar la densidad de muestreo frecuencial.

    Parámetros:
        audio_data: Muestras de audio 1D normalizadas [-1, 1].
        sample_rate: Tasa de muestreo en Hz.
        window_type: Tipo de ventana ('hann', 'hamming', 'blackman', 'rectangular').
        zero_padding_factor: Factor multiplicador para longitud N (1 = sin relleno, 2, 4).

    Retorna:
        freqs: Arreglo de frecuencias en Hz (eje X).
        magnitude: Magnitud lineal normalizada del espectro (eje Y).
        magnitude_db: Magnitud en decibelios (dB, normalizada al máximo = 0 dB).
    """
    n_samples = len(audio_data)
    if n_samples == 0:
        return np.array([]), np.array([]), np.array([])

    clean_data = remove_dc_offset(audio_data)

    # Ventana temporal
    if window_type == "hann":
        window = np.hanning(n_samples)
    elif window_type == "hamming":
        window = np.hamming(n_samples)
    elif window_type == "blackman":
        window = np.blackman(n_samples)
    else:
        window = np.ones(n_samples)

    windowed_data = clean_data * window
    window_correction = np.sum(window) if np.sum(window) > 0 else n_samples

    # Zero-padding para mayor resolución visual e interpolación
    n_fft = int(n_samples * max(1, zero_padding_factor))
    fft_complex = np.fft.rfft(windowed_data, n=n_fft)
    freqs = np.fft.rfftfreq(n_fft, d=1.0 / sample_rate)

    # Magnitud normalizada (conservación de amplitud sinusoidal)
    magnitude = 2.0 * np.abs(fft_complex) / window_correction
    if len(magnitude) > 0:
        magnitude[0] /= 2.0  # Componente DC

    # Cálculo en dB con piso acústico en -100 dB
    peak_val = np.max(magnitude) if len(magnitude) > 0 else 1.0
    safe_peak = max(peak_val, 1e-9)
    magnitude_db = 20.0 * np.log10(np.clip(magnitude / safe_peak, 1e-5, 1.0))

    return freqs, magnitude, magnitude_db


def refine_peak_parabolic(
    freqs: np.ndarray,
    magnitude: np.ndarray,
    peak_idx: int
) -> Tuple[float, float]:
    """
    Aplica interpolación parabólica cuadrática de 3 puntos (Quinn / Smith)
    alrededor del bin de pico para obtener la frecuencia y amplitud continuas reales
    con precisión sub-bin (< 0.1 Hz).

    Parámetros:
        freqs: Arreglo de frecuencias discretas.
        magnitude: Magnitud del espectro.
        peak_idx: Índice del bin máximo detectado.

    Retorna:
        (refined_frequency_hz, refined_amplitude)
    """
    if peak_idx <= 0 or peak_idx >= len(magnitude) - 1:
        return freqs[peak_idx], magnitude[peak_idx]

    alpha = magnitude[peak_idx - 1]
    beta = magnitude[peak_idx]
    gamma = magnitude[peak_idx + 1]

    denom = alpha - 2.0 * beta + gamma
    if abs(denom) < 1e-12:
        return freqs[peak_idx], beta

    delta = 0.5 * (alpha - gamma) / denom
    delta = np.clip(delta, -1.0, 1.0)

    # Espaciado entre bins
    df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    refined_freq = freqs[peak_idx] + delta * df
    refined_mag = beta - 0.25 * (alpha - gamma) * delta

    return float(refined_freq), float(refined_mag)


def find_spectral_peaks(
    freqs: np.ndarray,
    magnitude: np.ndarray,
    min_freq: float = 100.0,
    max_freq: float = 2500.0,
    prominence_ratio: float = 0.25,
    min_distance_hz: float = 30.0,
    max_peaks: int = 5
) -> List[Dict[str, float]]:
    """
    Detecta los picos de resonancia más prominentes dentro de un rango frecuencial de interés.

    Parámetros:
        freqs: Arreglo de frecuencias en Hz.
        magnitude: Magnitud lineal del espectro.
        min_freq: Frecuencia mínima de búsqueda en Hz.
        max_freq: Frecuencia máxima de búsqueda en Hz.
        prominence_ratio: Fracción de la amplitud máxima necesaria para considerar un pico relevante.
        min_distance_hz: Separación mínima entre picos detectados en Hz.
        max_peaks: Número máximo de picos a retornar.

    Retorna:
        Lista de diccionarios ordenados por prominencia descendente con información de cada pico:
        [{'frequency': float, 'amplitude': float, 'snr_db': float, 'bin_index': int}, ...]
    """
    if len(freqs) < 3 or len(magnitude) < 3:
        return []

    # Filtrar solo el rango de frecuencias de interés
    mask = (freqs >= min_freq) & (freqs <= max_freq)
    if not np.any(mask):
        return []

    sub_freqs = freqs[mask]
    sub_mag = magnitude[mask]
    indices_in_original = np.where(mask)[0]

    if len(sub_mag) < 3:
        return []

    max_mag_in_range = np.max(sub_mag)
    if max_mag_in_range <= 1e-9:
        return []

    df = freqs[1] - freqs[0] if len(freqs) > 1 else 1.0
    distance_bins = max(1, int(np.round(min_distance_hz / df)))
    prominence_val = prominence_ratio * max_mag_in_range

    peak_indices_sub, properties = signal.find_peaks(
        sub_mag,
        distance=distance_bins,
        prominence=prominence_val
    )

    if len(peak_indices_sub) == 0:
        # Si no supera el umbral estricto, tomar el valor máximo como candidato
        best_sub_idx = int(np.argmax(sub_mag))
        peak_indices_sub = np.array([best_sub_idx])

    # Estimar piso de ruido (mediana del espectro en el rango)
    noise_floor = np.median(sub_mag)
    safe_noise = max(noise_floor, 1e-9)

    detected_peaks = []
    for sub_idx in peak_indices_sub:
        orig_idx = int(indices_in_original[sub_idx])
        refined_f, refined_a = refine_peak_parabolic(freqs, magnitude, orig_idx)
        snr_db = 20.0 * np.log10(max(refined_a, 1e-9) / safe_noise)

        detected_peaks.append({
            "frequency": float(refined_f),
            "amplitude": float(refined_a),
            "snr_db": float(snr_db),
            "bin_index": orig_idx
        })

    # Ordenar de mayor a menor amplitud
    detected_peaks.sort(key=lambda p: p["amplitude"], reverse=True)
    return detected_peaks[:max_peaks]


def calculate_signal_rms(audio_data: np.ndarray) -> float:
    """
    Calcula el valor cuadrático medio (RMS) de la señal como indicador de nivel de entrada.
    """
    if len(audio_data) == 0:
        return 0.0
    return float(np.sqrt(np.mean(audio_data ** 2)))

