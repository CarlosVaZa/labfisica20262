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

    def export_html_report(self, file_path: str) -> None:
        """
        Genera un informe completo de laboratorio en formato HTML con diseño limpio y listo para imprimir.
        """
        from .physics_engine import analyze_resonance_series

        lengths, freqs = self.get_lengths_and_frequencies()
        has_regression = len(lengths) >= 2
        res = None
        if has_regression:
            try:
                res = analyze_resonance_series(lengths, freqs, temp_celsius=self.temperature_c, tube_radius_m=self.tube_radius_m)
            except Exception:
                pass

        v_theo = theoretical_sound_speed(self.temperature_c)

        rows_html = ""
        for m in self.measurements:
            f = m["frequency_hz"]
            inv_f = (1.0 / f * 1000.0) if f > 0 else 0.0
            rows_html += f"""
            <tr>
                <td>{m['id']}</td>
                <td>{m['length_cm']:.2f}</td>
                <td>{m['frequency_hz']:.2f}</td>
                <td>{inv_f:.3f}</td>
                <td>{m['v_point_m_s']:.2f}</td>
                <td>{m.get('notes', '')}</td>
            </tr>
            """

        stats_html = ""
        if res:
            stats_html = f"""
            <div class="card">
                <h3>Resultados de la Regresión Lineal (L vs 1/f)</h3>
                <div class="grid-2">
                    <div>
                        <p><strong>Velocidad Experimental (v<sub>exp</sub>):</strong> <span class="highlight">{res['v_experimental']:.2f} ± {res['v_uncertainty']:.2f} m/s</span></p>
                        <p><strong>Velocidad Teórica ({self.temperature_c:.1f} °C):</strong> {v_theo:.2f} m/s</p>
                        <p><strong>Error Porcentual:</strong> <span class="badge {'badge-green' if res['percentage_error'] < 3 else 'badge-yellow'}">{res['percentage_error']:.2f} %</span></p>
                    </div>
                    <div>
                        <p><strong>Coeficiente R<sup>2</sup>:</strong> {res['r_squared']:.5f}</p>
                        <p><strong>Pendiente (m = v/4):</strong> {res['slope']:.4f} ± {res['slope_uncertainty']:.4f} m·s</p>
                        <p><strong>Corrección de Extremo Exp. (ΔL):</strong> {res['experimental_end_correction_m']*1000:.2f} mm</p>
                    </div>
                </div>
            </div>
            """

        html_content = f"""<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <title>Informe de Laboratorio - {self.experiment_name}</title>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Arial, sans-serif; margin: 40px; color: #1e293b; background: #ffffff; line-height: 1.5; }}
        h1 {{ color: #1d4ed8; font-size: 24px; margin-bottom: 4px; }}
        h2 {{ color: #334155; font-size: 16px; font-weight: normal; margin-top: 0; }}
        h3 {{ color: #0f172a; margin-top: 20px; }}
        .header {{ border-bottom: 2px solid #e2e8f0; padding-bottom: 15px; margin-bottom: 25px; }}
        .card {{ background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; padding: 18px; margin-bottom: 20px; }}
        .grid-2 {{ display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }}
        table {{ width: 100%; border-collapse: collapse; margin-top: 15px; margin-bottom: 25px; }}
        th, td {{ border: 1px solid #cbd5e1; padding: 10px; text-align: center; }}
        th {{ background: #f1f5f9; font-weight: 600; color: #334155; }}
        tr:nth-child(even) {{ background: #f8fafc; }}
        .highlight {{ color: #1d4ed8; font-weight: bold; font-size: 1.1em; }}
        .badge {{ padding: 3px 8px; border-radius: 4px; font-weight: bold; font-size: 0.9em; }}
        .badge-green {{ background: #dcfce7; color: #15803d; }}
        .badge-yellow {{ background: #fef9c3; color: #a16207; }}
        .footer {{ font-size: 12px; color: #64748b; margin-top: 40px; border-top: 1px solid #e2e8f0; padding-top: 10px; }}
        @media print {{ body {{ margin: 20px; }} .card {{ page-break-inside: avoid; }} }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Informe de Laboratorio: Medición de la Velocidad del Sonido</h1>
        <h2>Grupo 1 • Laboratorio de Física (Tarde) • Resonancia Acústica y Programación en Python</h2>
        <p><small>Fecha de generación: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</small></p>
    </div>

    <div class="card">
        <h3>Parámetros Experimentales del Laboratorio</h3>
        <p><strong>Temperatura Ambiente (T):</strong> {self.temperature_c:.1f} °C &nbsp;|&nbsp; <strong>Radio Interno del Tubo (r):</strong> {self.tube_radius_m*100:.2f} cm &nbsp;|&nbsp; <strong>Velocidad Teórica v(T):</strong> {v_theo:.2f} m/s</p>
    </div>

    {stats_html}

    <h3>Tabla de Mediciones Registradas</h3>
    <table>
        <thead>
            <tr>
                <th>#ID</th>
                <th>Longitud L (cm)</th>
                <th>Frecuencia f<sub>1</sub> (Hz)</th>
                <th>Periodo 1/f (ms)</th>
                <th>Velocidad Puntual (m/s)</th>
                <th>Observaciones</th>
            </tr>
        </thead>
        <tbody>
            {rows_html if rows_html else '<tr><td colspan="6">No hay mediciones registradas.</td></tr>'}
        </tbody>
    </table>

    <div class="footer">
        <p>Laboratorio de Física - Ondas y Fluidos • Sistema Automatizado de Captura y FFT en Python • Grupo 1</p>
    </div>
</body>
</html>
"""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(html_content)

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

