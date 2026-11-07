"""
Pruebas Unitarias para el Módulo de Física
==========================================
Verifica los cálculos del documento GRUPO 1- LAB FISICA-TARDE
"""

import unittest
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.physics_engine import calculate_speed_of_sound, calculate_theoretical_frequency


class TestPhysicsEngine(unittest.TestCase):

    def test_example_document_exact(self):
        """
        Verifica el ejemplo del documento:
        L = 20 cm = 0.20 m, f1 = 425 Hz -> v = 4 * (0.20) * (425) = 340 m/s
        """
        result = calculate_speed_of_sound(length_meters=0.20, frequency_hz=425.0, theoretical_speed=343.0)

        self.assertAlmostEqual(result["v_experimental"], 340.0, places=2)
        self.assertAlmostEqual(result["v_theoretical"], 343.0, places=2)

        # Error porcentual: |340 - 343| / 343 * 100% = 0.8746%
        expected_error = (3.0 / 343.0) * 100.0
        self.assertAlmostEqual(result["error_porcentual"], expected_error, places=2)

        # Texto de la fórmula y sustitución
        self.assertEqual(result["formula_text"], "v = 4 · L · f1")
        self.assertIn("v = 4 · (0.200 m) · (425.0 Hz)", result["sustitucion_text"])
        self.assertEqual(result["resultado_text"], "v = 340.00 m/s")

    def test_theoretical_frequency(self):
        """
        f1 = v / (4 * L) -> para v = 343 m/s y L = 0.20 m:
        f1 = 343 / (4 * 0.20) = 428.75 Hz
        """
        f_theo = calculate_theoretical_frequency(length_meters=0.20, sound_speed=343.0)
        self.assertAlmostEqual(f_theo, 428.75, places=2)


if __name__ == "__main__":
    unittest.main()
