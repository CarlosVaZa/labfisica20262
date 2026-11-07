"""
Pruebas Unitarias para el Módulo de Datos
"""

import unittest
import os
import sys
import tempfile

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.data_manager import ExperimentDataset


class TestDataManager(unittest.TestCase):

    def setUp(self):
        self.dataset = ExperimentDataset("Test Lab")

    def test_add_and_remove_measurements(self):
        self.dataset.add_measurement(0.20, 425.0, "Punto 1")
        self.dataset.add_measurement(0.30, 285.0, "Punto 2")
        self.assertEqual(len(self.dataset.measurements), 2)

        removed = self.dataset.remove_measurement(1)
        self.assertTrue(removed)
        self.assertEqual(len(self.dataset.measurements), 1)
        self.assertEqual(self.dataset.measurements[0]["id"], 1)

    def test_export_import_csv(self):
        self.dataset.load_sample_dataset()
        initial_len = len(self.dataset.measurements)

        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.dataset.export_csv(tmp_path)
            new_dataset = ExperimentDataset("Imported")
            new_dataset.import_csv(tmp_path)
            self.assertEqual(len(new_dataset.measurements), initial_len)
            self.assertAlmostEqual(new_dataset.measurements[0]["frequency_hz"], self.dataset.measurements[0]["frequency_hz"])
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)

    def test_export_import_json(self):
        self.dataset.load_sample_dataset()
        initial_len = len(self.dataset.measurements)

        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            self.dataset.export_json(tmp_path)
            new_dataset = ExperimentDataset("Imported JSON")
            new_dataset.import_json(tmp_path)
            self.assertEqual(len(new_dataset.measurements), initial_len)
            self.assertEqual(new_dataset.experiment_name, self.dataset.experiment_name)
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)


if __name__ == "__main__":
    unittest.main()

