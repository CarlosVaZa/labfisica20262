"""
Pruebas Unitarias para el Registro de Mediciones
================================================
"""

import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.data_manager import ExperimentRegistry
from core.physics_engine import calculate_helmholtz_frequency
import csv


class TestDataManager(unittest.TestCase):

    def test_models_and_csv_dimensions(self):
        tube = self.registry.add_measurement(20, 425, diameter_cm=4)
        frequency = calculate_helmholtz_frequency(.028, .032, .0006, .0002)
        bottle = self.registry.add_measurement(model="bottle", frequency_hz=frequency,
            diameter_cm=2.8, neck_length_cm=3.2, body_volume_ml=600, water_volume_ml=200)
        self.assertAlmostEqual(tube["v_calculada"], 360.74)
        self.assertAlmostEqual(bottle["v_calculada"], 343)
        self.assertAlmostEqual(bottle["air_volume_ml"], 400)
        self.assertIsNone(bottle["length_cm"])
        self.assertEqual(self.registry.get_data_arrays()[0], [20])
        with tempfile.TemporaryDirectory() as directory:
            path = os.path.join(directory, "models.csv")
            self.registry.export_csv(path)
            with open(path, encoding="utf-8", newline="") as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]["model"], "tube")
            self.assertEqual(rows[1]["model"], "bottle")
            self.assertEqual(float(rows[1]["body_volume_ml"]), 600)
            self.assertEqual(float(rows[1]["water_volume_ml"]), 200)
            self.assertEqual(rows[1]["length_cm"], "")

    def test_invalid_measurement_not_stored(self):
        with self.assertRaises(ValueError):
            self.registry.add_measurement(model="bottle", frequency_hz=425, diameter_cm=2.8,
                neck_length_cm=3.2, body_volume_ml=600, water_volume_ml=600)
        self.assertEqual(self.registry.measurements, [])

    def setUp(self):
        self.registry = ExperimentRegistry()

    def test_add_and_calculate_speed(self):
        # Medición con L = 20 cm, f1 = 425 Hz
        entry = self.registry.add_measurement(length_cm=20.0, frequency_hz=425.0)

        self.assertEqual(len(self.registry.measurements), 1)
        self.assertEqual(entry["v_calculada"], 340.0)
        self.assertEqual(entry["v_teorica"], 343.0)
        self.assertAlmostEqual(entry["error_pct"], 0.87, places=2)

    def test_export_csv(self):
        self.registry.add_measurement(length_cm=20.0, frequency_hz=425.0)
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.registry.export_csv(tmp_path)
            self.assertTrue(os.path.exists(tmp_path))
            with open(tmp_path, "r", encoding="utf-8") as f:
                content = f.read()
            self.assertIn("340.0", content)
            self.assertIn("425.0", content)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()
