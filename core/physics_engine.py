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
import math


def _positive(value: float, name: str) -> float:
    value = float(value)
    if not math.isfinite(value) or value <= 0:
        raise ValueError(f"{name} debe ser un número finito mayor a cero.")
    return value


def calculate_reference_speed(temperature_celsius: float) -> float:
    """Velocidad de referencia del aire en m/s: 331.3 + 0.606 T (°C)."""
    temperature = float(temperature_celsius)
    if not math.isfinite(temperature) or temperature <= -273.15:
        raise ValueError("Ingrese una temperatura finita mayor que -273.15 °C.")
    return _positive(331.3 + 0.606 * temperature, "La velocidad de referencia")


def calculate_speed_of_sound(length_meters: float, frequency_hz: float, theoretical_speed: float = 343.0, diameter_meters=None) -> Dict[str, Any]:
    """
    Calcula la velocidad del sonido a partir de la longitud de la columna de aire y la frecuencia fundamental,
    mostrando el paso a paso del cálculo según las fórmulas del documento:

        v = 4 * L * f1

    Parámetros:
        length_meters: Longitud del espacio que queda lleno de aire (L) en metros.
        frequency_hz: Frecuencia fundamental de resonancia (f1) en Hz.
        theoretical_speed: Valor teórico a 20 °C (343 m/s según el documento).
        diameter_meters: Diámetro interior opcional. Si se proporciona, utiliza
            L efectiva = L + 0.61 × (diámetro / 2), en metros.

    Retorna:
        Diccionario con los resultados y las cadenas de texto del procedimiento paso a paso.
    """
    length_meters = _positive(length_meters, "La longitud de aire")
    frequency_hz = _positive(frequency_hz, "La frecuencia")
    theoretical_speed = _positive(theoretical_speed, "La velocidad de referencia")
    radius = 0.0 if diameter_meters is None else _positive(diameter_meters, "El diámetro") / 2
    effective_length = length_meters + 0.61 * radius

    # Sin diámetro, la longitud efectiva coincide con L.
    v_experimental = 4.0 * effective_length * frequency_hz

    # Comparación con el valor teórico (343 m/s)
    error_porcentual = abs(v_experimental - theoretical_speed) / theoretical_speed * 100.0
    precision = max(0.0, 100.0 - error_porcentual)

    # Texto descriptivo del cálculo paso a paso
    formula_text = "v = 4 · L · f1"
    sustitucion_text = f"v = 4 · ({length_meters:.3f} m) · ({frequency_hz:.1f} Hz)"
    resultado_text = f"v = {v_experimental:.2f} m/s"
    if diameter_meters is not None:
        formula_text = "v ≈ 4 × f1 × (L + 0.61r)"
        sustitucion_text = (f"r = {radius:.6g} m; L efectiva = {effective_length:.6g} m\n"
                            f"v ≈ 4 × {frequency_hz:.6g} Hz × ({length_meters:.6g} + 0.61 × {radius:.6g}) m")

    return {
        "model": "tube",
        "diameter_meters": diameter_meters,
        "radius_meters": radius,
        "effective_length_meters": effective_length,
        "theoretical_frequency_hz": theoretical_speed / (4 * effective_length),
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


def calculate_theoretical_frequency(length_meters: float, sound_speed: float = 343.0, diameter_meters=None) -> float:
    """
    Calcula f1 = v / (4 * L efectiva), con la misma corrección opcional
    del cálculo de velocidad. Todas las longitudes se expresan en metros.
    """
    length_meters = _positive(length_meters, "La longitud de aire")
    sound_speed = _positive(sound_speed, "La velocidad de referencia")
    radius = 0 if diameter_meters is None else _positive(diameter_meters, "El diámetro") / 2
    return sound_speed / (4.0 * (length_meters + 0.61 * radius))


def bottle_geometry(diameter_meters, neck_length_meters, body_volume_m3, water_volume_m3):
    """Volumen de cavidad excluyendo el cuello; corrección aproximada 1.46r."""
    diameter = _positive(diameter_meters, "El diámetro del cuello")
    neck = _positive(neck_length_meters, "La longitud del cuello")
    body = _positive(body_volume_m3, "La capacidad del cuerpo")
    water = float(water_volume_m3)
    if not math.isfinite(water) or not 0 <= water < body:
        raise ValueError("El volumen de agua debe ser finito, no negativo y menor que la capacidad del cuerpo.")
    radius = diameter / 2
    return {
        "diameter_meters": diameter, "radius_meters": radius,
        "neck_length_meters": neck, "body_volume_m3": body,
        "water_volume_m3": water, "air_volume_m3": body - water,
        "area_m2": math.pi * radius ** 2,
        "effective_length_meters": neck + 1.46 * radius,
    }


def calculate_helmholtz_frequency(diameter_meters, neck_length_meters, body_volume_m3,
                                 water_volume_m3, sound_speed=343.0):
    geometry = bottle_geometry(diameter_meters, neck_length_meters, body_volume_m3, water_volume_m3)
    return _positive(sound_speed, "La velocidad de referencia") / (2 * math.pi) * math.sqrt(
        geometry["area_m2"] / (geometry["air_volume_m3"] * geometry["effective_length_meters"]))


def calculate_helmholtz_speed(diameter_meters, neck_length_meters, body_volume_m3,
                              water_volume_m3, frequency_hz, theoretical_speed=343.0):
    geometry = bottle_geometry(diameter_meters, neck_length_meters, body_volume_m3, water_volume_m3)
    frequency = _positive(frequency_hz, "La frecuencia")
    reference = _positive(theoretical_speed, "La velocidad de referencia")
    v = 2 * math.pi * frequency * math.sqrt(
        geometry["air_volume_m3"] * geometry["effective_length_meters"] / geometry["area_m2"])
    error = abs(v - reference) / reference * 100
    return {
        **geometry, "model": "bottle", "frequency_hz": frequency,
        "v_experimental": v, "v_theoretical": reference,
        "error_porcentual": error, "precision": max(0.0, 100 - error),
        "theoretical_frequency_hz": frequency * reference / v,
        "formula_text": "v = 2π × fH × √(V × Lef / A)",
        "sustitucion_text": (
            f"r = {geometry['radius_meters']:.6g} m; A = {geometry['area_m2']:.6g} m²\n"
            f"V = {geometry['air_volume_m3']:.6g} m³; Lef = {geometry['effective_length_meters']:.6g} m\n"
            f"v = 2π × {frequency:.6g} × √({geometry['air_volume_m3']:.6g} × "
            f"{geometry['effective_length_meters']:.6g} / {geometry['area_m2']:.6g})"),
        "resultado_text": f"v = {v:.2f} m/s",
    }
