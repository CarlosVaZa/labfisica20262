"""Comprobaciones de integración de la cuarta pestaña con el registro existente."""

import unittest
from unittest.mock import patch

from gui.app import AcousticLabApp


class TestStatisticsTab(unittest.TestCase):
    def setUp(self):
        self.app = AcousticLabApp()
        self.app.withdraw()

    def tearDown(self):
        self.app.destroy()

    def test_registration_deletion_and_clear_refresh_analysis(self):
        app = self.app
        self.assertEqual(len(app.notebook.tabs()), 5)
        self.assertEqual(app.notebook.tab(4, "text"), "Resultados estadísticos globales")
        app.notebook.select(4)
        self.assertEqual(app.notebook.select(), str(app.statistics_tab.results_tab))
        self.assertTrue(str(app.statistics_tab.results_text).startswith(str(app.statistics_tab.results_tab) + "."))
        self.assertFalse(str(app.statistics_tab.results_text).startswith(str(app.statistics_tab) + "."))
        self.assertEqual(app.statistics_tab.message.cget("text"),
                         "No hay mediciones de tubo uniforme registradas")
        # Changing a preview does not add a point to the analysis.
        app.current_freq_hz = 425.123456789
        app.var_length_cm.set("20")
        self.assertEqual(app.statistics_tab.analysis["rows"], [])
        for length, frequency in ((20, 425.123456789), (30, 283.7654321), (40, 213.13579)):
            app.var_length_cm.set(str(length))
            app.current_freq_hz = frequency
            app._register_measurement()
        fit = app.statistics_tab.analysis["fit"]
        self.assertEqual(fit["n"], 3)
        self.assertIsNotNone(fit["speed_ci95"])
        self.assertEqual(len(app.statistics_tab.table.get_children()), 3)
        original_reference = fit["reference"]
        app.var_temperature_celsius.set("30")
        self.assertEqual(app.statistics_tab.analysis["fit"]["reference"], original_reference)
        self.assertEqual(app.registry.measurements[0]["temperature_celsius"], 20)
        app._delete_selected()
        self.assertEqual(app.statistics_tab.analysis["fit"]["n"], 2)
        self.assertIsNone(app.statistics_tab.analysis["fit"]["speed_ci95"])
        with patch("gui.app.messagebox.askyesno", return_value=True):
            app._clear_table()
        self.assertIsNone(app.statistics_tab.analysis["fit"])
        self.assertEqual(len(app.statistics_tab.table.get_children()), 0)
        self.assertEqual(len(app.statistics_tab.axis.lines), 0)

    def test_bottle_is_registered_but_excluded_from_statistics(self):
        app = self.app
        app.var_model.set("bottle")
        for variable, value in ((app.var_neck_diameter_cm, "2.8"),
                                (app.var_neck_length_cm, "3.2"),
                                (app.var_body_volume_ml, "600"),
                                (app.var_water_volume_ml, "200")):
            variable.set(value)
        app.current_freq_hz = 300
        app._register_measurement()
        self.assertEqual(len(app.registry.measurements), 1)
        self.assertEqual(app.registry.measurements[0]["model"], "bottle")
        self.assertEqual(len(app.tree.get_children()), 1)
        self.assertEqual(app.statistics_tab.analysis["rows"], [])
        self.assertEqual(app.statistics_tab.message.cget("text"),
                         "No hay mediciones de tubo uniforme registradas")

    def test_switching_model_registration_and_deletion(self):
        app = self.app
        app.current_freq_hz = 425.123456
        app._register_measurement()
        app.var_model.set("bottle")
        for variable, value in ((app.var_neck_diameter_cm, "2.8"),
                                (app.var_neck_length_cm, "3.2"), (app.var_body_volume_ml, "600")):
            variable.set(value)
        app.statistics_tab.var_model.set("bottle")
        self.assertEqual(app.statistics_tab.analysis["rows"], [])
        for water, frequency in ((0, 225.123456), (100, 250.234567), (200, 275.345678)):
            app.var_water_volume_ml.set(str(water))
            app.current_freq_hz = frequency
            app._register_measurement()
        fit = app.statistics_tab.analysis["fit"]
        self.assertEqual(fit["n"], 3)
        self.assertIsNotNone(fit["speed_ci95"])
        self.assertEqual(len(app.statistics_tab.table["columns"]), 6)
        self.assertIn("2πm", app.statistics_tab.results_text.cget("text"))
        self.assertIn("Botella", app.statistics_tab.results_model.cget("text"))
        self.assertIn("fH", app.statistics_tab.fit_text.cget("text"))
        self.assertEqual([r["id"] for r in app.statistics_tab.analysis["rows"]], [2, 3, 4])
        app.statistics_tab.canvas.draw()  # Includes the Helmholtz MathText axis label.
        app.statistics_tab.var_model.set("tube")
        self.assertIn("Tubo uniforme", app.statistics_tab.results_model.cget("text"))
        self.assertEqual(len(app.statistics_tab.table["columns"]), 4)
        self.assertEqual(len(app.statistics_tab.analysis["rows"]), 1)
        self.assertIsNone(app.statistics_tab.analysis["fit"])
        app.statistics_tab.var_model.set("bottle")
        self.assertEqual(app.statistics_tab.analysis["fit"], fit)
        app._delete_selected()
        self.assertEqual(app.statistics_tab.analysis["fit"]["n"], 2)
        self.assertIsNone(app.statistics_tab.analysis["fit"]["speed_ci95"])
        with patch("gui.app.messagebox.askyesno", return_value=True):
            app._clear_table()
        self.assertEqual(app.statistics_tab.analysis["rows"], [])
        self.assertEqual(app.statistics_tab.message.cget("text"),
                         "No hay mediciones de botella registradas")


if __name__ == "__main__":
    unittest.main()
