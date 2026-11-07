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


if __name__ == "__main__":
    unittest.main()
