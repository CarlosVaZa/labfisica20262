"""
Módulo de Gestión de Datos Experimentales
========================================
Permite almacenar, cargar, exportar e importar las series de mediciones
de laboratorio en formatos CSV y JSON, así como proveer datasets de prueba.
"""

from typing import List, Dict, Optional, Any
import os
import json
import csv
from datetime import datetime
import pandas as pd

from .physics_engine import sound_speed_from_point, theoretical_sound_speed


class ExperimentDataset:
    """
    Administra la colección de mediciones de un experimento acústico.
    """

    def __init__(self, experiment_name: str = "Medición Velocidad Sonido"):
        self.experiment_name = experiment_name
        self.temperature_c = 20.0
        self.tube_radius_m = 0.015  # 1.5 cm de radio (3 cm de diámetro típico)
        self.measurements: List[Dict[str, Any]] = []

    def clear(self) -> None:
        """Limpia todas las mediciones."""
        self.measurements.clear()

    def add_measurement(
        self,
        length_m: float,
        frequency_hz: float,
        notes: str = "",
        timestamp: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Agrega un nuevo punto de medición experimental.
        """
        if length_m <= 0 or frequency_hz <= 0:
            raise ValueError("Longitud y frecuencia deben ser números positivos.")

        v_point = sound_speed_from_point(
            length_m=length_m,
            freq_hz=frequency_hz,
            tube_radius_m=self.tube_radius_m
        )

        entry = {
            "id": len(self.measurements) + 1,
            "timestamp": timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "length_cm": round(length_m * 100.0, 2),
            "length_m": round(length_m, 4),
            "frequency_hz": round(frequency_hz, 2),
            "v_point_m_s": round(v_point, 2),
            "notes": notes
        }
        self.measurements.append(entry)
        return entry

    def remove_measurement(self, measurement_id: int) -> bool:
        """Elimina una medición por su identificador."""
        original_len = len(self.measurements)
        self.measurements = [m for m in self.measurements if m["id"] != measurement_id]
        # Re-enumerar IDs
        for idx, m in enumerate(self.measurements):
            m["id"] = idx + 1
        return len(self.measurements) < original_len

    def get_lengths_and_frequencies(self) -> tuple[List[float], List[float]]:
        """Retorna las listas de longitudes (m) y frecuencias (Hz)."""
        lengths = [m["length_m"] for m in self.measurements]
        frequencies = [m["frequency_hz"] for m in self.measurements]
        return lengths, frequencies

    def to_dataframe(self) -> pd.DataFrame:
        """Convierte los datos a un DataFrame de pandas."""
        if not self.measurements:
            return pd.DataFrame(columns=[
                "id", "timestamp", "length_cm", "length_m", "frequency_hz", "v_point_m_s", "notes"
            ])
        return pd.DataFrame(self.measurements)

    def export_csv(self, file_path: str) -> None:
        """Exporta las mediciones a un archivo CSV."""
        df = self.to_dataframe()
        df.to_csv(file_path, index=False, encoding="utf-8")

    def import_csv(self, file_path: str) -> None:
        """Importa mediciones desde un archivo CSV."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        df = pd.read_csv(file_path)
        self.clear()
        for _, row in df.iterrows():
            length_m = float(row.get("length_m", row.get("length_cm", 0.0) / 100.0))
            freq = float(row.get("frequency_hz", 0.0))
            notes = str(row.get("notes", ""))
            ts = str(row.get("timestamp", ""))
            if length_m > 0 and freq > 0:
                self.add_measurement(length_m, freq, notes=notes, timestamp=ts)

    def export_json(self, file_path: str) -> None:
        """Exporta el experimento completo con metadatos a formato JSON."""
        payload = {
            "experiment_name": self.experiment_name,
            "temperature_c": self.temperature_c,
            "tube_radius_m": self.tube_radius_m,
            "v_theoretical_m_s": theoretical_sound_speed(self.temperature_c),
            "export_timestamp": datetime.now().isoformat(),
            "measurements": self.measurements
        }
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=4, ensure_ascii=False)

    def import_json(self, file_path: str) -> None:
        """Importa el experimento desde un archivo JSON."""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")

        with open(file_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        self.experiment_name = data.get("experiment_name", self.experiment_name)
        self.temperature_c = float(data.get("temperature_c", self.temperature_c))
        self.tube_radius_m = float(data.get("tube_radius_m", self.tube_radius_m))
        self.clear()

        for m in data.get("measurements", []):
            length_m = float(m.get("length_m", 0.0))
            freq = float(m.get("frequency_hz", 0.0))
            notes = str(m.get("notes", ""))
            ts = str(m.get("timestamp", ""))
            if length_m > 0 and freq > 0:
                self.add_measurement(length_m, freq, notes=notes, timestamp=ts)

    def load_sample_dataset(self) -> None:
        """
        Carga un conjunto de datos realistas de laboratorio para demostraciones inmediatas.
        Basado en un tubo con agua variando de 10 cm a 45 cm a ~20 °C (v ≈ 343 m/s).
        """
        self.clear()
        self.temperature_c = 20.0
        self.tube_radius_m = 0.015  # r = 1.5 cm

        # Longitudes típicas en cm y sus frecuencias con ligera dispersión experimental realista
        samples = [
            (0.12, 690.5, "Columna pequeña (12 cm)"),
            (0.16, 523.2, "Nota C5 aprox (16 cm)"),
            (0.20, 422.8, "Ejemplo del documento guía (20 cm)"),
            (0.25, 340.1, "Columna intermedia (25 cm)"),
            (0.30, 284.6, "Columna media (30 cm)"),
            (0.35, 244.7, "Columna larga (35 cm)"),
            (0.40, 214.3, "Columna profunda (40 cm)"),
        ]

        for L, f, note in samples:
            self.add_measurement(L, f, notes=note)

