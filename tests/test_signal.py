"""
Pruebas Unitarias para Procesamiento de Señales
===============================================
Verifica el filtrado de ruido, la FFT y la detección del pico de frecuencia.
"""

import unittest
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.signal_processing import filter_ambient_noise, analyze_fft, detect_resonance_frequency


class TestSignalProcessing(unittest.TestCase):

    def test_fft_and_peak_detection(self):
        # Crear señal pura a 425 Hz (el ejemplo del documento)
        fs = 44100
        duration = 1.0
        t = np.linspace(0, duration, int(fs * duration), endpoint=False)
        target_f = 425.0
        signal = 0.8 * np.sin(2.0 * np.pi * target_f * t)

        filtered = filter_ambient_noise(signal, sample_rate=fs)
        freqs, mags = analyze_fft(filtered, sample_rate=fs)
        peak = detect_resonance_frequency(freqs, mags, min_freq=120.0, max_freq=1800.0)

        self.assertAlmostEqual(peak["frequency_hz"], target_f, delta=1.5)
        self.assertGreater(peak["amplitude"], 0.3)

    def test_filter_and_search_band_discrimination(self):
        """Prueba solicitada: con filtro 40 Hz y banda 50-2500 elige ~100 Hz;
        con corte 500 Hz y banda 500-2500 elige ~1200 Hz."""
        fs = 44100
        duration = 2.0
        n_samples = int(fs * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        np.random.seed(42)
        noise = np.random.normal(0, 0.01, n_samples)
        # 1200 Hz con amplitud 0.05 + 100 Hz con amplitud 1.0 + ruido
        signal = 1.0 * np.sin(2.0 * np.pi * 100.0 * t) + 0.05 * np.sin(2.0 * np.pi * 1200.0 * t) + noise

        # Caso 1: filtro 40 Hz y banda 50-2500 Hz -> debe elegir ~100 Hz
        filtered_1 = filter_ambient_noise(signal, sample_rate=fs, low_cutoff=40.0, high_cutoff=2500.0)
        freqs_1, mags_1 = analyze_fft(filtered_1, sample_rate=fs)
        peak_1 = detect_resonance_frequency(freqs_1, mags_1, min_freq=50.0, max_freq=2500.0,
                                            smoothing_hz=0.0, sample_rate=fs, n_samples=n_samples)
        self.assertAlmostEqual(peak_1["frequency_hz"], 100.0, delta=2.0)

        # Caso 2: corte 500 Hz y banda 500-2500 Hz -> debe elegir ~1200 Hz
        filtered_2 = filter_ambient_noise(signal, sample_rate=fs, low_cutoff=500.0, high_cutoff=2500.0)
        freqs_2, mags_2 = analyze_fft(filtered_2, sample_rate=fs)
        peak_2 = detect_resonance_frequency(freqs_2, mags_2, min_freq=500.0, max_freq=2500.0,
                                            smoothing_hz=0.0, sample_rate=fs, n_samples=n_samples)
        self.assertAlmostEqual(peak_2["frequency_hz"], 1200.0, delta=2.0)

    def test_audio_samples_default_results(self):
        """Verifica que con los valores por defecto los audios de data/audio_samples
        detecten las frecuencias esperadas coincidentes con sus nombres."""
        from core.audio_capture import load_audio_wav
        samples_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "audio_samples"))
        expected_peaks = {
            "tubo_12cm_663Hz.wav": 663.0,
            "tubo_16cm_506Hz.wav": 506.0,
            "tubo_20cm_409Hz.wav": 410.0,
            "tubo_25cm_330Hz.wav": 330.0,
            "tubo_30cm_277Hz.wav": 277.0,
            "tubo_35cm_238Hz.wav": 238.0,
            "tubo_40cm_209Hz.wav": 209.0,
        }
        for filename, expected_f in expected_peaks.items():
            path = os.path.join(samples_dir, filename)
            if not os.path.exists(path):
                continue
            audio, sr = load_audio_wav(path)
            filtered = filter_ambient_noise(audio, sample_rate=sr, low_cutoff=40.0, high_cutoff=2500.0)
            freqs, mags = analyze_fft(filtered, sample_rate=sr)
            peak = detect_resonance_frequency(freqs, mags, min_freq=50.0, max_freq=2500.0,
                                              smoothing_hz=0.0, sample_rate=sr, n_samples=len(audio))
            self.assertAlmostEqual(peak["frequency_hz"], expected_f, delta=1.5)

    def test_filter_high_cutoff_attenuation(self):
        """Prueba que el corte superior (high_cutoff) atenúe frecuencias por encima de él."""
        fs = 44100
        duration = 1.0
        n_samples = int(fs * duration)
        t = np.linspace(0, duration, n_samples, endpoint=False)
        # 300 Hz (amplitud 0.2) + 2000 Hz (amplitud 1.0)
        signal = 0.2 * np.sin(2.0 * np.pi * 300.0 * t) + 1.0 * np.sin(2.0 * np.pi * 2000.0 * t)

        # Con high_cutoff=2500 Hz, 2000 Hz domina
        filt_wide = filter_ambient_noise(signal, sample_rate=fs, low_cutoff=40.0, high_cutoff=2500.0)
        freqs_w, mags_w = analyze_fft(filt_wide, sample_rate=fs)
        peak_w = detect_resonance_frequency(freqs_w, mags_w, min_freq=50.0, max_freq=2500.0,
                                            sample_rate=fs, n_samples=n_samples)
        self.assertAlmostEqual(peak_w["frequency_hz"], 2000.0, delta=2.0)

        # Con high_cutoff=1000 Hz, 2000 Hz queda filtrado y debe dominar 300 Hz
        filt_low = filter_ambient_noise(signal, sample_rate=fs, low_cutoff=40.0, high_cutoff=1000.0)
        freqs_l, mags_l = analyze_fft(filt_low, sample_rate=fs)
        peak_l = detect_resonance_frequency(freqs_l, mags_l, min_freq=50.0, max_freq=2500.0,
                                            sample_rate=fs, n_samples=n_samples)
        self.assertAlmostEqual(peak_l["frequency_hz"], 300.0, delta=2.0)


if __name__ == "__main__":
    unittest.main()
