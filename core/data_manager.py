"""
Módulo de Registro y Almacenamiento de Mediciones
================================================
Grupo 1 - Lab Física (Tarde)
Permite almacenar y comparar las diferentes mediciones del experimento (Sección 7 y 8).
"""

from typing import List, Dict, Any, Tuple
import csv
import pandas as pd
from .physics_engine import calculate_speed_of_sound


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

    def add_measurement(self, length_cm: float, frequency_hz: float, notes: str = "") -> Dict[str, Any]:
        """
        Calcula la velocidad del sonido según la fórmula v = 4 * L * f1
        y registra el resultado en la tabla.
        """
        length_m = length_cm / 100.0
        calc = calculate_speed_of_sound(length_m, frequency_hz, theoretical_speed=343.0)

        entry = {
            "id": len(self.measurements) + 1,
            "length_cm": round(length_cm, 2),
            "length_m": round(length_m, 4),
            "frequency_hz": round(frequency_hz, 2),
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
        lengths = [m["length_cm"] for m in self.measurements]
        freqs = [m["frequency_hz"] for m in self.measurements]
        speeds = [m["v_calculada"] for m in self.measurements]
        return lengths, freqs, speeds

    def export_csv(self, file_path: str) -> None:
        """Exporta la tabla de resultados a formato CSV."""
        df = pd.DataFrame(self.measurements)
        df.to_csv(file_path, index=False, encoding="utf-8")
