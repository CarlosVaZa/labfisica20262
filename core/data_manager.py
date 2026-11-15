"""
Módulo de Registro y Almacenamiento de Mediciones
================================================
Grupo 1 - Lab Física (Tarde)
Permite almacenar y comparar las diferentes mediciones del experimento (Sección 7 y 8).
"""

from typing import List, Dict, Any, Tuple
import csv
import pandas as pd
from .physics_engine import calculate_speed_of_sound, calculate_helmholtz_speed, calculate_reference_speed


class ExperimentRegistry:
    """
    Gestiona el registro de mediciones del laboratorio.
    Inicia vacío para recibir los datos reales del usuario.
    """

    def __init__(self):
        self.measurements: List[Dict[str, Any]] = []

    def clear(self) -> None:
        """Limpia todas las mediciones."""
        self.measurements.clear()

    def add_measurement(self, length_cm=None, frequency_hz=None, notes: str = "", *,
                        model="tube", diameter_cm=None, neck_length_cm=None,
                        body_volume_ml=None, water_volume_ml=None, temperature_celsius=None) -> Dict[str, Any]:
        """
        Calcula y registra el modelo elegido. Entradas en cm, mL y Hz;
        conversiones al SI antes de llamar al motor físico.
        """
        reference = 343.0 if temperature_celsius is None else calculate_reference_speed(temperature_celsius)
        if model == "tube":
            length_m = float(length_cm) / 100.0
            calc = calculate_speed_of_sound(length_m, frequency_hz, theoretical_speed=reference, diameter_meters=(
                None if diameter_cm is None else float(diameter_cm) / 100))
        elif model == "bottle":
            length_m = None
            calc = calculate_helmholtz_speed(float(diameter_cm) / 100, float(neck_length_cm) / 100,
                                            float(body_volume_ml) * 1e-6,
                                            float(water_volume_ml) * 1e-6, frequency_hz, theoretical_speed=reference)
        else:
            raise ValueError("Modelo desconocido: utilice tube o bottle.")

        entry = {
            "id": len(self.measurements) + 1,
            "model": model,
            "temperature_celsius": None if temperature_celsius is None else float(temperature_celsius),
            "length_cm": None if length_m is None else float(length_cm),
            "length_m": length_m,
            "diameter_cm": diameter_cm,
            "radius_m": calc["radius_meters"],
            "effective_length_m": calc["effective_length_meters"],
            "neck_length_cm": neck_length_cm if model == "bottle" else None,
            "body_volume_ml": body_volume_ml if model == "bottle" else None,
            "water_volume_ml": water_volume_ml if model == "bottle" else None,
            "air_volume_ml": calc.get("air_volume_m3", 0) * 1e6 if model == "bottle" else None,
            "area_m2": calc.get("area_m2"),
            "theoretical_frequency_hz": calc["theoretical_frequency_hz"],
            "frequency_hz": round(frequency_hz, 2),
            # Preserve the existing display/CSV field and retain the original
            # experimental frequency for statistical calculations without rounding.
            "frequency_hz_full_precision": float(frequency_hz),
            "formula": calc["formula_text"],
            "v_calculada": round(calc["v_experimental"], 2),
            "v_teorica": round(calc["v_theoretical"], 2),
            "error_pct": round(calc["error_porcentual"], 2),
            "precision_pct": round(calc["precision"], 2),
            "notes": notes
        }
        self.measurements.append(entry)
        return entry

    def remove_measurement(self, index: int) -> bool:
        """Elimina una medición por índice (0-indexed)."""
        if 0 <= index < len(self.measurements):
            self.measurements.pop(index)
            # Reenumerar
            for i, m in enumerate(self.measurements):
                m["id"] = i + 1
            return True
        return False

    def get_data_arrays(self) -> Tuple[List[float], List[float], List[float]]:
        """Retorna listas de (longitudes_cm, frecuencias_hz, velocidades_calculadas)."""
        tubes = [m for m in self.measurements if m["model"] == "tube"]
        lengths = [m["length_cm"] for m in tubes]
        freqs = [m["frequency_hz"] for m in tubes]
        speeds = [m["v_calculada"] for m in tubes]
        return lengths, freqs, speeds

    def export_csv(self, file_path: str) -> None:
        """Exporta la tabla de resultados a formato CSV."""
        df = pd.DataFrame(self.measurements)
        df.to_csv(file_path, index=False, encoding="utf-8")
