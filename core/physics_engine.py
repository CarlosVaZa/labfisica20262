"""
Módulo de Física - Grupo 1 Laboratorio de Física
===============================================
Cálculo de la velocidad del sonido según el documento:
GRUPO 1- LAB FISICA-TARDE

Fórmulas del documento:
    f1 = v / (4 * L)
    v = 4 * L * f1

Ejemplo del documento:
    L = 20 cm = 0.20 m, f1 = 425 Hz
    v = 4 * (0.20) * (425) = 340 m/s
    Valor teórico a 20 °C = 343 m/s
"""

from typing import Dict, Any


def calculate_speed_of_sound(length_meters: float, frequency_hz: float, theoretical_speed: float = 343.0) -> Dict[str, Any]:
    """
    Calcula la velocidad del sonido a partir de la longitud de la columna de aire y la frecuencia fundamental,
    mostrando el paso a paso del cálculo según las fórmulas del documento:

        v = 4 * L * f1

    Parámetros:
        length_meters: Longitud del espacio que queda lleno de aire (L) en metros.
        frequency_hz: Frecuencia fundamental de resonancia (f1) en Hz.
        theoretical_speed: Valor teórico a 20 °C (343 m/s según el documento).

    Retorna:
        Diccionario con los resultados y las cadenas de texto del procedimiento paso a paso.
    """
    if length_meters <= 0:
        raise ValueError("La longitud de la columna de aire debe ser mayor a cero.")
    if frequency_hz <= 0:
        raise ValueError("La frecuencia fundamental debe ser mayor a cero.")

    # Fórmula: v = 4 * L * f1
    v_experimental = 4.0 * length_meters * frequency_hz

    # Comparación con el valor teórico (343 m/s)
    error_porcentual = abs(v_experimental - theoretical_speed) / theoretical_speed * 100.0
    precision = max(0.0, 100.0 - error_porcentual)

    # Texto descriptivo del cálculo paso a paso
    formula_text = "v = 4 · L · f1"
    sustitucion_text = f"v = 4 · ({length_meters:.3f} m) · ({frequency_hz:.1f} Hz)"
    resultado_text = f"v = {v_experimental:.2f} m/s"

    return {
        "length_meters": float(length_meters),
        "length_cm": float(length_meters * 100.0),
        "frequency_hz": float(frequency_hz),
        "v_experimental": float(v_experimental),
        "v_theoretical": float(theoretical_speed),
        "error_porcentual": float(error_porcentual),
        "precision": float(precision),
        "formula_text": formula_text,
        "sustitucion_text": sustitucion_text,
        "resultado_text": resultado_text,
    }


def calculate_theoretical_frequency(length_meters: float, sound_speed: float = 343.0) -> float:
    """
    Calcula la frecuencia teórica esperada para una longitud L dada:
        f1 = v / (4 * L)
    """
    if length_meters <= 0:
        return 0.0
    return sound_speed / (4.0 * length_meters)
