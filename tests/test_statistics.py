"""Validación numérica y de integridad del análisis conjunto de tubos."""

import copy
import unittest

import numpy as np
from scipy.stats import linregress, t

from core.data_manager import ExperimentRegistry
from core.statistical_analysis import analyze_tube_measurements, analyze_bottle_measurements


class TestTubeStatistics(unittest.TestCase):
    def records(self, lengths=(10, 15, 20, 30, 40), noise=(1, -2, 3, -1, 2)):
        registry = ExperimentRegistry()
        for length, error in zip(lengths, noise):
            effective = length / 100 + .61 * .01
            registry.add_measurement(length, 85 / effective + 7 + error,
                                     diameter_cm=2, temperature_celsius=20)
        return registry.measurements

    def test_fit_matches_scipy_and_confidence_interval(self):
        records = self.records()
        snapshot = copy.deepcopy(records)
        result = analyze_tube_measurements(records)
        fit = result["fit"]
        x = [1 / r["effective_length_m"] for r in records]
        y = [r["frequency_hz_full_precision"] for r in records]
        expected = linregress(x, y)
        self.assertAlmostEqual(fit["slope"], expected.slope)
        self.assertAlmostEqual(fit["intercept"], expected.intercept)
        self.assertAlmostEqual(fit["r_squared"], expected.rvalue ** 2)
        self.assertAlmostEqual(fit["slope_stderr"], expected.stderr)
        margin = 4 * t.ppf(.975, 3) * expected.stderr
        self.assertAlmostEqual(fit["speed_ci95"][0], 4 * expected.slope - margin)
        self.assertAlmostEqual(fit["speed_ci95"][1], 4 * expected.slope + margin)
        self.assertEqual(records, snapshot)
        self.assertEqual(fit["n"], 5)

    def test_filtering_empty_and_invalid(self):
        self.assertEqual(analyze_tube_measurements([])["message"],
                         "No hay mediciones de tubo uniforme registradas")
        records = self.records()
        bottle = dict(records[0], model="bottle", frequency_hz_full_precision=99999)
        invalid = [dict(records[0], effective_length_m=v) for v in (0, -1, None, "bad", float("nan"), float("inf"))]
        invalid += [dict(records[0], frequency_hz_full_precision=0), dict(records[0], length_m=-1)]
        result = analyze_tube_measurements(records + [bottle] + invalid)
        self.assertEqual(result["fit"]["n"], 5)
        self.assertEqual(result["excluded"], 8)
        self.assertEqual(analyze_tube_measurements([bottle])["rows"], [])

    def test_insufficient_same_lengths_and_constant_frequency(self):
        records = self.records()
        self.assertIsNone(analyze_tube_measurements(records[:1])["fit"])
        two = analyze_tube_measurements(records[:2])["fit"]
        self.assertIsNotNone(two)
        self.assertIsNone(two["speed_ci95"])
        self.assertIsNone(analyze_tube_measurements([records[0]] * 3)["fit"])
        for row in records:
            row["frequency_hz_full_precision"] = 400
        fit = analyze_tube_measurements(records)["fit"]
        self.assertIsNone(fit["r_squared"])
        self.assertEqual(fit["slope"], 0)
        self.assertEqual(fit["speed_ci95"], (0, 0))

    def test_exact_fit_and_nonpositive_slope(self):
        rows = [dict(id=i, model="tube", length_m=1/x, effective_length_m=1/x,
                     frequency_hz=80*x+10, frequency_hz_full_precision=80*x+10,
                     temperature_celsius=20) for i, x in enumerate((1, 2, 3), 1)]
        fit = analyze_tube_measurements(rows)["fit"]
        self.assertEqual(fit["speed"], 320)
        self.assertEqual(fit["speed_ci95"], (320, 320))
        self.assertEqual(fit["r_squared"], 1)
        for row in rows:
            row["frequency_hz_full_precision"] = 1000 - row["frequency_hz_full_precision"]
        result = analyze_tube_measurements(rows)
        self.assertLess(result["fit"]["speed"], 0)
        self.assertTrue(any("físicamente" in w for w in result["warnings"]))

    def test_original_temperatures_and_legacy_precision(self):
        records = self.records()
        for row, temperature in zip(records, (20, 21, 22, 24, 25)):
            row["temperature_celsius"] = temperature
            row["v_teorica"] = 999  # Temperature function is the authoritative reference.
            row["theoretical_frequency_hz"] = 99999  # Never used in OLS.
        result = analyze_tube_measurements(records)
        fit = result["fit"]
        reference = np.mean([331.3 + .606 * temp for temp in (20, 21, 22, 24, 25)])
        self.assertAlmostEqual(fit["reference"], reference)
        self.assertAlmostEqual(fit["mean_temperature"], 22.4)
        self.assertAlmostEqual(fit["difference"], fit["speed"] - reference)
        self.assertTrue(any("temperatura varía" in w for w in result["warnings"]))
        self.assertNotEqual(records[0]["frequency_hz"], records[0]["frequency_hz_full_precision"])
        records[0].pop("frequency_hz_full_precision")
        records[0]["temperature_celsius"] = None
        records[0]["v_teorica"] = 343
        result = analyze_tube_measurements(records)
        self.assertIsNone(result["fit"]["mean_temperature"])
        self.assertIsNotNone(result["fit"]["reference"])
        records[0]["v_teorica"] = float("nan")
        self.assertIsNone(analyze_tube_measurements(records)["fit"]["reference"])


class TestBottleStatistics(unittest.TestCase):
    def records(self):
        registry = ExperimentRegistry()
        for water, frequency, temperature in ((0, 225.1234567, 20), (100, 250.2345678, 21),
                                               (200, 275.3456789, 24), (300, 320.4567891, 25)):
            registry.add_measurement(model="bottle", frequency_hz=frequency, diameter_cm=2.8,
                                     neck_length_cm=3.2, body_volume_ml=600,
                                     water_volume_ml=water, temperature_celsius=temperature)
        return registry.measurements

    def test_helmholtz_fit_and_speed_interval(self):
        records = self.records()
        original = copy.deepcopy(records)
        result = analyze_bottle_measurements(records)
        fit = result["fit"]
        x = np.array([np.sqrt(r["area_m2"] / (r["air_volume_ml"] * 1e-6 * r["effective_length_m"])) for r in records])
        y = [r["frequency_hz_full_precision"] for r in records]
        expected = linregress(x, y)
        self.assertAlmostEqual(fit["slope"], expected.slope)
        self.assertAlmostEqual(fit["intercept"], expected.intercept)
        self.assertAlmostEqual(fit["r_squared"], expected.rvalue ** 2)
        self.assertAlmostEqual(fit["speed"], 2 * np.pi * expected.slope)
        margin = 2 * np.pi * t.ppf(.975, 2) * expected.stderr
        self.assertAlmostEqual(fit["speed_ci95"][0], fit["speed"] - margin)
        self.assertAlmostEqual(fit["speed_ci95"][1], fit["speed"] + margin)
        self.assertEqual(records, original)
        self.assertAlmostEqual(result["rows"][0]["air_volume_m3"], .0006)
        self.assertTrue(any("temperatura varía" in w for w in result["warnings"]))

    def test_separate_models_and_saved_reference(self):
        records = self.records()
        for row in records:
            row["v_teorica"] = 345.6789
            row["theoretical_frequency_hz"] = 99999
        tube = ExperimentRegistry().add_measurement(20, 425, temperature_celsius=20)
        result = analyze_bottle_measurements(records + [tube])
        self.assertEqual(result["fit"]["n"], 4)
        self.assertAlmostEqual(result["fit"]["reference"], 345.6789)
        self.assertAlmostEqual(result["fit"]["mean_temperature"], 22.5)
        self.assertAlmostEqual(result["fit"]["error_pct"],
                               abs(result["fit"]["speed"] - 345.6789) / 345.6789 * 100)
        self.assertEqual(analyze_bottle_measurements([tube])["message"],
                         "No hay mediciones de botella registradas")

    def test_invalid_geometry_frequency_and_duplicate_x(self):
        records = self.records()
        invalid = [dict(records[0], **{key: value})
                   for key in ("area_m2", "air_volume_ml", "effective_length_m", "frequency_hz_full_precision")
                   for value in (0, -1, None, "bad", float("nan"), float("inf"))]
        result = analyze_bottle_measurements(records + invalid)
        self.assertEqual(result["fit"]["n"], 4)
        self.assertEqual(result["excluded"], 24)
        self.assertIsNone(analyze_bottle_measurements(records[:1])["fit"])
        self.assertIsNone(analyze_bottle_measurements([records[0]] * 3)["fit"])
        self.assertIsNone(analyze_bottle_measurements(records[:2])["fit"]["speed_ci95"])
        self.assertIsNone(analyze_bottle_measurements([records[0], records[0], records[1]])["fit"]["speed_ci95"])
        self.assertIsNotNone(analyze_bottle_measurements(records[:3])["fit"]["speed_ci95"])

    def test_constant_frequency_is_degenerate(self):
        records = self.records()
        for row in records:
            row["frequency_hz_full_precision"] = 300
        fit = analyze_bottle_measurements(records)["fit"]
        self.assertIsNone(fit["r_squared"])
        self.assertEqual(fit["speed_ci95"], (0, 0))


if __name__ == "__main__":
    unittest.main()
