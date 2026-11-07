"""
Pruebas Unitarias para el Módulo de Procesamiento de Señales
"""

import unittest
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.signal_processing import (
    remove_dc_offset,
    apply_bandpass_filter,
    compute_fft,
    find_spectral_peaks,
    refine_peak_parabolic
)
from core.audio_generator import generate_pure_tone, simulate_pipe_resonance


class TestSignalProcessing(unittest.TestCase):

    def test_dc_removal(self):
        signal_with_dc = np.ones(1000) * 2.5 + np.sin(np.linspace(0, 10, 1000))
        cleaned = remove_dc_offset(signal_with_dc)
        self.assertAlmostEqual(np.mean(cleaned), 0.0, places=5)

    def test_fft_peak_detection(self):
        target_f = 425.0
        sample_rate = 44100
        duration = 1.0
        tone = generate_pure_tone(target_f, duration_sec=duration, sample_rate=sample_rate)

        freqs, mag, mag_db = compute_fft(tone, sample_rate=sample_rate, window_type="hann")
        peaks = find_spectral_peaks(freqs, mag, min_freq=200.0, max_freq=800.0)

        self.assertTrue(len(peaks) > 0)
        detected_freq = peaks[0]["frequency"]
        self.assertAlmostEqual(detected_freq, target_f, delta=1.0)

    def test_simulated_resonance_peak(self):
        # Para tubo de 20 cm sin corrección: f1 = 343 / (4 * 0.20) = 428.75 Hz
        length = 0.20
        audio, f1_true = simulate_pipe_resonance(length_m=length, sound_speed=343.0, tube_radius_m=0.0)
        freqs, mag, _ = compute_fft(audio, sample_rate=44100, window_type="hann")
        peaks = find_spectral_peaks(freqs, mag, min_freq=150.0, max_freq=1000.0)

        self.assertTrue(len(peaks) > 0)
        self.assertAlmostEqual(peaks[0]["frequency"], f1_true, delta=5.0)


if __name__ == "__main__":
    unittest.main()
