"""
Módulo de Física y Modelos Acústicos
===================================
Implementa los modelos teóricos de resonancia acústica para tubos semicerrados,
resonadores de Helmholtz, cálculo de velocidad del sonido teórica, corrección
de extremo y análisis de regresión lineal para datos experimentales.
"""

from typing import Tuple, List, Dict, Optional
import numpy as np


def theoretical_sound_speed(temp_celsius: float = 20.0) -> float:
    """
    Calcula la velocidad teórica del sonido en aire seco en función de la temperatura.

    Fórmula termodinámica:
        v = v_0 * sqrt(1 + T / 273.15)
        donde v_0 = 331.3 m/s a 0 °C (273.15 K).

    Parámetros:
        temp_celsius: Temperatura ambiente en grados Celsius (°C).

    Retorna:
        Velocidad del sonido teórica en m/s.
    """
    kelvin = temp_celsius + 273.15
    if kelvin <= 0:
        raise ValueError("La temperatura absoluta debe ser mayor a 0 K.")
    return 331.3 * np.sqrt(kelvin / 273.15)


def fundamental_frequency(
    length_m: float,
    sound_speed: float = 343.0,
    tube_radius_m: float = 0.0,
    harmonic_n: int = 1
) -> float:
    """
    Calcula la frecuencia de resonancia de un tubo semicerrado (abierto en un extremo,
    cerrado en el otro por el agua).

    Fórmula:
        f_n = (2n - 1) * v / (4 * L_eff)
        L_eff = L + 0.61 * r  (corrección de extremo de Levine & Schwinger)

    Parámetros:
        length_m: Longitud de la columna de aire en metros (L).
        sound_speed: Velocidad del sonido en m/s (por defecto 343 m/s a ~20°C).
        tube_radius_m: Radio interno del tubo en metros (opcional, para corrección de extremo).
        harmonic_n: Número de armónico (1 para fundamental, 2 para primer sobretono f3, etc.).

    Retorna:
        Frecuencia en Hz.
    """
    if length_m <= 0:
        raise ValueError("La longitud del tubo debe ser positiva.")
    if harmonic_n < 1:
        raise ValueError("El orden armónico debe ser mayor o igual a 1.")

    effective_length = length_m + 0.61 * tube_radius_m
    mode_number = 2 * harmonic_n - 1
    return (mode_number * sound_speed) / (4.0 * effective_length)


def sound_speed_from_point(
    length_m: float,
    freq_hz: float,
    tube_radius_m: float = 0.0,
    harmonic_n: int = 1
) -> float:
    """
    Calcula la velocidad del sonido a partir de una única medición puntual de longitud
    y frecuencia de resonancia.

    Fórmula:
        v = (4 * L_eff * f_n) / (2n - 1)
        L_eff = L + 0.61 * r

    Parámetros:
        length_m: Longitud de la columna de aire en metros.
        freq_hz: Frecuencia de resonancia detectada en Hz.
        tube_radius_m: Radio interno del tubo en metros.
        harmonic_n: Número del armónico (1 para fundamental).

    Retorna:
        Velocidad estimada en m/s.
    """
    if length_m <= 0 or freq_hz <= 0:
        raise ValueError("Longitud y frecuencia deben ser valores positivos.")
    effective_length = length_m + 0.61 * tube_radius_m
    mode_number = 2 * harmonic_n - 1
    return (4.0 * effective_length * freq_hz) / mode_number


def helmholtz_frequency(
    cavity_volume_m3: float,
    neck_radius_m: float,
    neck_length_m: float,
    sound_speed: float = 343.0
) -> float:
    """
    Calcula la frecuencia de resonancia de Helmholtz (adecuada para botellas
    con cuello estrecho y cuerpo ancho).

    Fórmula:
        f_H = (v / (2 * pi)) * sqrt( A / (V * L_eff) )
        donde A = pi * r^2, L_eff = L_cuello + 1.6 * r

    Parámetros:
        cavity_volume_m3: Volumen de aire en el cuerpo de la botella (m^3).
        neck_radius_m: Radio del cuello o abertura en metros.
        neck_length_m: Longitud del cuello en metros.
        sound_speed: Velocidad del sonido en m/s.

    Retorna:
        Frecuencia de Helmholtz en Hz.
    """
    if cavity_volume_m3 <= 0 or neck_radius_m <= 0 or neck_length_m < 0:
        raise ValueError("Los parámetros dimensionales deben ser estrictamente positivos.")

    area = np.pi * (neck_radius_m ** 2)
    effective_neck = neck_length_m + 1.6 * neck_radius_m
    return (sound_speed / (2.0 * np.pi)) * np.sqrt(area / (cavity_volume_m3 * effective_neck))


def analyze_resonance_series(
    lengths_m: List[float],
    frequencies_hz: List[float],
    temp_celsius: float = 20.0,
    tube_radius_m: float = 0.0
) -> Dict[str, object]:
    """
    Realiza un análisis riguroso de regresión lineal sobre un conjunto de mediciones (L vs f)
    obtenidas al variar la cantidad de agua en el tubo.

    Modelo físico:
        L_i = (v / 4) * (1 / f_i) - Delta_L
        donde:
            x_i = 1 / f_i  (periodo espacial / inverso de frecuencia)
            y_i = L_i      (longitud de columna de aire)
            Pendiente m = v / 4  ==>  v_exp = 4 * m
            Intercepto c = -Delta_L  ==>  corrección de extremo experimental

    Parámetros:
        lengths_m: Lista de longitudes de columna de aire en metros.
        frequencies_hz: Lista de frecuencias fundamentales medidas en Hz.
        temp_celsius: Temperatura ambiente para cálculo del valor teórico.
        tube_radius_m: Radio interno del tubo (para comparación teórica de corrección).

    Retorna:
        Diccionario con estadísticas completas del ajuste, velocidad experimental,
        velocidad teórica, error porcentual, coeficiente R^2 e incertidumbres.
    """
    if len(lengths_m) != len(frequencies_hz):
        raise ValueError("Las listas de longitudes y frecuencias deben tener el mismo tamaño.")
    if len(lengths_m) < 2:
        raise ValueError("Se requieren al menos 2 mediciones para realizar regresión lineal.")

    x = 1.0 / np.array(frequencies_hz, dtype=np.float64)
    y = np.array(lengths_m, dtype=np.float64)
    n = len(x)

    # Regresión por mínimos cuadrados ordinarios (OLS)
    mean_x = np.mean(x)
    mean_y = np.mean(y)

    ss_xx = np.sum((x - mean_x) ** 2)
    ss_xy = np.sum((x - mean_x) * (y - mean_y))
    ss_yy = np.sum((y - mean_y) ** 2)

    if ss_xx == 0:
        raise ValueError("Las frecuencias no presentan suficiente variación.")

    slope = ss_xy / ss_xx
    intercept = mean_y - slope * mean_x

    # Predicción y residuos
    y_pred = slope * x + intercept
    residuals = y - y_pred
    ss_res = np.sum(residuals ** 2)

    # Coeficiente de determinación R^2
    r_squared = 1.0 - (ss_res / ss_yy) if ss_yy > 0 else 1.0

    # Desviación estándar del error y del slope
    dof = max(1, n - 2)
    s_err = np.sqrt(ss_res / dof) if dof > 0 else 0.0
    se_slope = s_err / np.sqrt(ss_xx) if ss_xx > 0 else 0.0
    se_intercept = s_err * np.sqrt(1.0 / n + (mean_x ** 2) / ss_xx) if ss_xx > 0 else 0.0

    # Velocidad experimental del sonido: v = 4 * slope
    v_exp = 4.0 * slope
    se_v_exp = 4.0 * se_slope

    # Valor teórico
    v_theo = theoretical_sound_speed(temp_celsius)
    pct_error = abs(v_exp - v_theo) / v_theo * 100.0

    # Corrección de extremo experimental (Delta L = -intercept)
    experimental_delta_l = -intercept
    theoretical_delta_l = 0.61 * tube_radius_m if tube_radius_m > 0 else None

    # Velocidades individuales puntuales (para análisis de dispersión)
    individual_velocities = [
        sound_speed_from_point(L, f, tube_radius_m=tube_radius_m)
        for L, f in zip(lengths_m, frequencies_hz)
    ]

    return {
        "n_samples": n,
        "v_experimental": float(v_exp),
        "v_uncertainty": float(se_v_exp),
        "v_theoretical": float(v_theo),
        "percentage_error": float(pct_error),
        "slope": float(slope),
        "slope_uncertainty": float(se_slope),
        "intercept": float(intercept),
        "intercept_uncertainty": float(se_intercept),
        "r_squared": float(r_squared),
        "experimental_end_correction_m": float(experimental_delta_l),
        "theoretical_end_correction_m": theoretical_delta_l,
        "x_inv_freq": x.tolist(),
        "y_lengths": y.tolist(),
        "y_pred": y_pred.tolist(),
        "residuals": residuals.tolist(),
        "individual_velocities": individual_velocities,
        "mean_individual_v": float(np.mean(individual_velocities)),
        "std_individual_v": float(np.std(individual_velocities, ddof=1)) if n > 1 else 0.0
    }


def estimate_water_level(
    detected_freq_hz: float,
    total_tube_length_m: float,
    sound_speed: float = 343.0,
    tube_radius_m: float = 0.0
) -> Dict[str, float]:
    """
    Estima el nivel de agua en un recipiente o tubo a partir de la frecuencia de resonancia.
    (Aplicación: Sensor acústico de nivel sin contacto).

    Fórmula:
        L_aire = v / (4 * f) - 0.61 * r
        H_agua = H_total - L_aire

    Parámetros:
        detected_freq_hz: Frecuencia detectada en Hz.
        total_tube_length_m: Altura total del tubo o recipiente en metros.
        sound_speed: Velocidad del sonido en m/s.
        tube_radius_m: Radio interno del tubo.

    Retorna:
        Diccionario con altura de agua (m), columna de aire (m), porcentaje de llenado (%).
    """
    if detected_freq_hz <= 0:
        return {"air_column_m": total_tube_length_m, "water_height_m": 0.0, "fill_percentage": 0.0}

    air_column = (sound_speed / (4.0 * detected_freq_hz)) - 0.61 * tube_radius_m
    # Limitar físicamente a límites del tubo
    air_column_clamped = max(0.01, min(air_column, total_tube_length_m))
    water_height = max(0.0, total_tube_length_m - air_column_clamped)
    pct = (water_height / total_tube_length_m) * 100.0 if total_tube_length_m > 0 else 0.0

    return {
        "air_column_m": float(air_column_clamped),
        "water_height_m": float(water_height),
        "fill_percentage": float(min(100.0, max(0.0, pct)))
    }


NOTE_NAMES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def frequency_to_musical_note(freq_hz: float) -> Dict[str, object]:
    """
    Convierte una frecuencia acústica a la nota musical más cercana en afinación temperada (A4 = 440 Hz),
    calculando la desviación en cents (centésimas de semitono).
    (Aplicación: Afinador acústico digital).

    Parámetros:
        freq_hz: Frecuencia en Hz.

    Retorna:
        Diccionario con nombre de nota, octava, frecuencia teórica y desviación en cents.
    """
    if freq_hz <= 10.0:
        return {"note": "-", "octave": 0, "target_freq": 0.0, "cents_deviation": 0.0}

    midi_number = 12.0 * np.log2(freq_hz / 440.0) + 69.0
    nearest_midi = int(np.round(midi_number))
    note_name = NOTE_NAMES[nearest_midi % 12]
    octave = (nearest_midi // 12) - 1
    target_freq = 440.0 * (2.0 ** ((nearest_midi - 69.0) / 12.0))
    cents = 1200.0 * np.log2(freq_hz / target_freq)

    return {
        "note": f"{note_name}{octave}",
        "octave": octave,
        "target_freq": float(target_freq),
        "cents_deviation": float(cents),
        "is_in_tune": bool(abs(cents) < 5.0)
    }

