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
from core.physics_engine import calculate_helmholtz_speed, calculate_helmholtz_frequency
import math


class TestPhysicsEngine(unittest.TestCase):

    def test_tube_diameter_and_inverse(self):
        # D = 4 cm: r = 0.02 m, L efectiva = 0.2122 m.
        result = calculate_speed_of_sound(.2, 425, diameter_meters=.04)
        self.assertAlmostEqual(result["v_experimental"], 360.74)
        self.assertAlmostEqual(result["effective_length_meters"], .2122)
        frequency = calculate_theoretical_frequency(.2, diameter_meters=.04)
        self.assertAlmostEqual(calculate_speed_of_sound(.2, frequency, diameter_meters=.04)["v_experimental"], 343)

    def test_bottle_geometry_and_inverse(self):
        # Imagen: D=2.8 cm, cuello=3.2 cm, cuerpo=600 mL, agua=200 mL.
        area = math.pi * .014 ** 2
        effective = .032 + 1.46 * .014
        frequency = 343 / (2 * math.pi) * math.sqrt(area / (.0004 * effective))
        result = calculate_helmholtz_speed(.028, .032, .0006, .0002, frequency)
        self.assertAlmostEqual(result["air_volume_m3"], .0004)
        self.assertAlmostEqual(result["effective_length_meters"], .05244)
        self.assertAlmostEqual(result["area_m2"], area)
        self.assertAlmostEqual(result["v_experimental"], 343)
        self.assertAlmostEqual(result["error_porcentual"], 0)
        self.assertAlmostEqual(calculate_helmholtz_frequency(.028, .032, .0006, .0002), frequency)
        self.assertGreater(calculate_helmholtz_frequency(.028, .032, .0006, .0003), frequency)

    def test_invalid_inputs(self):
        for value in (0, -1, float("nan"), float("inf")):
            with self.subTest(value=value):
                with self.assertRaises(ValueError):
                    calculate_speed_of_sound(value, 425)
                with self.assertRaises(ValueError):
                    calculate_speed_of_sound(.2, value)
                with self.assertRaises(ValueError):
                    calculate_speed_of_sound(.2, 425, diameter_meters=value)
                with self.assertRaises(ValueError):
                    calculate_helmholtz_speed(value, .032, .0006, .0002, 425)
        for water in (-.0001, .0006, .0007, float("nan"), float("inf")):
            with self.assertRaises(ValueError):
                calculate_helmholtz_speed(.028, .032, .0006, water, 425)
        self.assertGreater(calculate_helmholtz_speed(.028, .032, .0006, 0, 425)["v_experimental"], 0)

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
