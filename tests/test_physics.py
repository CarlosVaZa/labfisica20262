"""
Pruebas Unitarias para el Módulo de Física
"""

import unittest
import os
import sys
import numpy as np

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.physics_engine import (
    theoretical_sound_speed,
    fundamental_frequency,
    sound_speed_from_point,
    helmholtz_frequency,
    analyze_resonance_series,
    estimate_water_level,
    frequency_to_musical_note
)


class TestPhysicsEngine(unittest.TestCase):

    def test_theoretical_speed_at_20c(self):
        v = theoretical_sound_speed(20.0)
        self.assertAlmostEqual(v, 343.2, delta=0.5)

    def test_fundamental_frequency_example_doc(self):
        # Del documento: L = 20 cm = 0.20 m, f1 = 425 Hz -> v = 340 m/s (sin corrección de radio)
        v = sound_speed_from_point(0.20, 425.0, tube_radius_m=0.0)
        self.assertAlmostEqual(v, 340.0, places=2)

    def test_resonance_series_regression(self):
        # Tubo con v conocida de 343 m/s y radio 0.015 m
        v_true = 343.0
        r_tube = 0.015
        delta_l_true = 0.61 * r_tube

        lengths = [0.15, 0.20, 0.25, 0.30, 0.35, 0.40]
        frequencies = [fundamental_frequency(L, sound_speed=v_true, tube_radius_m=r_tube) for L in lengths]

        result = analyze_resonance_series(lengths, frequencies, temp_celsius=19.7, tube_radius_m=r_tube)

        self.assertAlmostEqual(result["v_experimental"], v_true, delta=0.5)
        self.assertGreater(result["r_squared"], 0.999)
        self.assertAlmostEqual(result["experimental_end_correction_m"], delta_l_true, delta=0.005)

    def test_water_level_estimation(self):
        total_tube = 0.50  # 50 cm
        # Si la columna de aire es 20 cm, el agua debe estar a 30 cm
        f_20cm = 343.0 / (4.0 * 0.20)
        est = estimate_water_level(f_20cm, total_tube_length_m=total_tube, sound_speed=343.0)
        self.assertAlmostEqual(est["air_column_m"], 0.20, places=2)
        self.assertAlmostEqual(est["water_height_m"], 0.30, places=2)
        self.assertAlmostEqual(est["fill_percentage"], 60.0, places=1)

    def test_musical_note_tuner(self):
        a4 = frequency_to_musical_note(440.0)
        self.assertEqual(a4["note"], "A4")
        self.assertAlmostEqual(a4["cents_deviation"], 0.0, delta=0.5)
        self.assertTrue(a4["is_in_tune"])


if __name__ == "__main__":
    unittest.main()
