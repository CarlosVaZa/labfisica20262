"""
Módulo Generador de Sonidos y Simulación Acústica
================================================
Permite generar tonos puros, barridos de frecuencia (sine sweep) y ruido acústico
para excitar la resonancia del tubo mediante parlantes, así como sintetizar
la respuesta resonante de una columna de aire para pruebas y simulaciones.
"""

from typing import Optional, Tuple
import numpy as np
import sounddevice as sd


def generate_pure_tone(
    freq_hz: float,
    duration_sec: float = 2.0,
    sample_rate: int = 44100,
    amplitude: float = 0.5
) -> np.ndarray:
    """
    Genera un tono sinusoidal puro con envolvente suave (fade-in / fade-out) para evitar clics.
    """
    total_samples = int(duration_sec * sample_rate)
    t = np.linspace(0.0, duration_sec, total_samples, endpoint=False)
    tone = amplitude * np.sin(2.0 * np.pi * freq_hz * t)

    # Envolvente anti-clic de 20 ms
    fade_len = min(int(0.02 * sample_rate), total_samples // 4)
    if fade_len > 0:
        fade_in = np.linspace(0.0, 1.0, fade_len)
        fade_out = np.linspace(1.0, 0.0, fade_len)
        tone[:fade_len] *= fade_in
        tone[-fade_len:] *= fade_out

    return tone.astype(np.float32)


def generate_frequency_sweep(
    start_freq: float = 200.0,
    end_freq: float = 1200.0,
    duration_sec: float = 4.0,
    sample_rate: int = 44100,
    amplitude: float = 0.5
) -> np.ndarray:
    """
    Genera un barrido senoidal continuo (Chirp lineal) entre dos frecuencias.
    Permite excitar todas las frecuencias naturales del tubo mediante un altavoz.
    """
    total_samples = int(duration_sec * sample_rate)
    t = np.linspace(0.0, duration_sec, total_samples, endpoint=False)

    # Fase instantánea para modulación lineal de frecuencia
    k = (end_freq - start_freq) / duration_sec
    phase = 2.0 * np.pi * (start_freq * t + 0.5 * k * (t ** 2))
    sweep = amplitude * np.sin(phase)

    # Suavizado de bordes
    fade_len = int(0.03 * sample_rate)
    if fade_len > 0 and 2 * fade_len < total_samples:
        sweep[:fade_len] *= np.linspace(0.0, 1.0, fade_len)
        sweep[-fade_len:] *= np.linspace(1.0, 0.0, fade_len)

    return sweep.astype(np.float32)


def generate_white_noise(
    duration_sec: float = 2.0,
    sample_rate: int = 44100,
    amplitude: float = 0.2
) -> np.ndarray:
    """
    Genera ruido blanco gaussiano para excitación acústica de banda ancha.
    """
    total_samples = int(duration_sec * sample_rate)
    noise = np.random.normal(0.0, 1.0, total_samples)
    max_val = np.max(np.abs(noise))
    if max_val > 0:
        noise = (noise / max_val) * amplitude
    return noise.astype(np.float32)


def simulate_pipe_resonance(
    length_m: float,
    sound_speed: float = 343.0,
    tube_radius_m: float = 0.015,
    duration_sec: float = 2.0,
    sample_rate: int = 44100,
    noise_level: float = 0.05
) -> Tuple[np.ndarray, float]:
    """
    Sintetiza la respuesta sonora acústica de un tubo semicerrado al soplar sobre su abertura.

    Modela la resonancia acústica del modo fundamental (f1) y armónicos impares (3f1, 5f1)
    con atenuación natural y ruido turbulento de aire.

    Parámetros:
        length_m: Longitud de la columna de aire en metros.
        sound_speed: Velocidad del sonido en m/s.
        tube_radius_m: Radio interno del tubo.
        duration_sec: Duración de la señal en segundos.
        sample_rate: Frecuencia de muestreo.
        noise_level: Amplitud relativa de ruido blanco turbulento.

    Retorna:
        (audio_array, f1_fundamental_hz)
    """
    effective_length = length_m + 0.61 * tube_radius_m
    f1 = sound_speed / (4.0 * effective_length)
    f3 = 3.0 * f1
    f5 = 5.0 * f1

    total_samples = int(duration_sec * sample_rate)
    t = np.linspace(0.0, duration_sec, total_samples, endpoint=False)

    # Modulación suave de soplido (envolvente asimétrica)
    envelope = np.sin(np.pi * (t / duration_sec)) ** 0.8

    # Componente fundamental predominante (80%) + armónicos impares amortiguados
    signal_wave = (
        0.75 * np.sin(2.0 * np.pi * f1 * t) +
        0.18 * np.sin(2.0 * np.pi * f3 * t) +
        0.05 * np.sin(2.0 * np.pi * f5 * t)
    )

    # Turbulencia de aire (ruido aleatorio coloreado)
    air_turbulence = np.random.normal(0.0, noise_level, total_samples)

    final_audio = (signal_wave + air_turbulence) * envelope
    max_amp = np.max(np.abs(final_audio))
    if max_amp > 0:
        final_audio = (final_audio / max_amp) * 0.7

    return final_audio.astype(np.float32), float(f1)


def play_audio(audio_data: np.ndarray, sample_rate: int = 44100) -> None:
    """
    Reproduce un arreglo de audio a través de los parlantes de forma asíncrona.
    """
    sd.stop()
    sd.play(audio_data, samplerate=sample_rate)


def stop_audio() -> None:
    """
    Detiene cualquier reproducción de audio en curso.
    """
    sd.stop()

