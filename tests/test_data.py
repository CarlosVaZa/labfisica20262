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


class TestDataManager(unittest.TestCase):

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
