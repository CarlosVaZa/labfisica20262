"""Análisis OLS independiente de mediciones registradas de tubo y botella, sin modificar los registros."""

import math

import numpy as np
from scipy.stats import t

from .physics_engine import calculate_reference_speed


TEMPERATURE_WARNING_RANGE_C = 2.0


def analyze_tube_measurements(measurements):
    """Ajusta f = m / Lef + b en SI, usando solo frecuencias experimentales.

    Para registros anteriores al soporte de precisión completa se utiliza la
    frecuencia disponible. Las referencias antiguas sin temperatura se conservan,
    pero la temperatura media no se inventa.
    """
    return _analyze_measurements(measurements, "tube")


def analyze_bottle_measurements(measurements):
    """Ajusta fH = m sqrt(A / (Vaire Lef)) + b; v global = 2πm."""
    return _analyze_measurements(measurements, "bottle")


def _analyze_measurements(measurements, model):
    bottle = model == "bottle"
    factor = 2.0 * math.pi if bottle else 4.0
    name = "botella" if bottle else "tubo uniforme"
    records = [record for record in measurements if record.get("model") == model]
    result = dict(rows=[], excluded=0, warnings=[], fit=None, message="")
    if not records:
        result["message"] = f"No hay mediciones de {name} registradas"
        return result

    for record in records:
        try:
            effective = float(record["effective_length_m"])
            frequency = float(record.get("frequency_hz_full_precision", record["frequency_hz"]))
            if bottle:
                # Geometry is already stored by the physics engine; only mL -> m³
                # remains necessary. Do not recreate Helmholtz corrections here.
                area = float(record["area_m2"])
                volume = float(record["air_volume_ml"]) * 1e-6
                values = (area, volume, effective, frequency)
            else:
                length = float(record["length_m"])
                values = (length, effective, frequency)
            if not all(math.isfinite(v) and v > 0 for v in values):
                raise ValueError("Medición inválida")
            inverse = math.sqrt(area / volume / effective) if bottle else 1.0 / effective
            if not math.isfinite(inverse) or inverse <= 0:
                raise ValueError("Variable independiente inválida")
        except (KeyError, TypeError, ValueError, OverflowError):
            result["excluded"] += 1
            continue
        temperature = reference = None
        try:
            if record.get("temperature_celsius") is not None:
                temperature = float(record["temperature_celsius"])
                if bottle:
                    calculate_reference_speed(temperature)  # Validate historical temperature.
                    reference = float(record["v_teorica"])
                    if not math.isfinite(reference) or reference <= 0:
                        reference = None
                else:
                    reference = calculate_reference_speed(temperature)
            else:
                reference = float(record["v_teorica"])
                if not math.isfinite(reference) or reference <= 0:
                    reference = None
        except (KeyError, TypeError, ValueError, OverflowError):
            temperature = reference = None
        row = dict(id=record.get("id", "-"), effective_length_m=effective,
                   x=inverse, frequency_hz=frequency, temperature=temperature, reference=reference)
        if bottle:
            row.update(area_m2=area, air_volume_m3=volume)
        else:
            row.update(length_m=length, inverse_length=inverse)
        result["rows"].append(row)


    rows = result["rows"]
    n = len(rows)
    if result["excluded"]:
        result["warnings"].append(f"Se excluyeron {result['excluded']} registros de {name} con datos inválidos.")
    if any("frequency_hz_full_precision" not in r for r in records):
        result["warnings"].append("Los registros anteriores usan la precisión de frecuencia con la que fueron guardados.")
    temperatures = [r["temperature"] for r in rows if r["temperature"] is not None]
    if temperatures and max(temperatures) - min(temperatures) >= TEMPERATURE_WARNING_RANGE_C:
        result["warnings"].append(
            f"La temperatura varía {max(temperatures) - min(temperatures):.2f} °C "
            "(umbral de aviso: 2 °C). La pendiente global supone una velocidad común; "
            "considere analizar mediciones a temperatura estable.")
    if n < 2:
        result["message"] = ("Se requieren al menos 2 mediciones válidas con valores X distintos para calcular la regresión." if bottle else
                             "Se requieren al menos 2 mediciones válidas con longitudes efectivas distintas para calcular la regresión.")
        return result

    x = np.array([r["x"] for r in rows])
    y = np.array([r["frequency_hz"] for r in rows])
    if np.unique(x).size < 2:
        result["message"] = ("No se puede calcular la regresión: todos los valores X son iguales." if bottle else
                             "No se puede calcular la regresión: todas las longitudes efectivas son iguales.")
        return result
    # Centering avoids unnecessary loss of precision when estimating the intercept.
    with np.errstate(over="ignore", invalid="ignore", divide="ignore", under="ignore"):
        dx, dy = x - np.mean(x), y - np.mean(y)
        sxx = float(np.dot(dx, dx))
        syy = float(np.dot(dy, dy))
        slope = float(np.dot(dx, dy) / sxx)
        intercept = float(np.mean(y) - slope * np.mean(x))
        residuals = dy - slope * dx
        sse = float(np.dot(residuals, residuals))
        speed = factor * slope
    if sxx <= 0 or not all(math.isfinite(v) for v in (sxx, syy, slope, intercept, sse, speed)):
        result["message"] = "No se puede calcular un ajuste finito con estas magnitudes. Revise las mediciones."
        return result
    r_squared = None if syy == 0 else 1.0 - sse / syy
    ci = stderr = None
    if n >= 3 and (not bottle or np.unique(x).size >= 3):
        stderr = math.sqrt(sse / (n - 2) / sxx)
        margin = factor * float(t.ppf(.975, n - 2)) * stderr
        ci = (speed - margin, speed + margin)
        if not all(math.isfinite(v) for v in ci):
            ci = None
            result["warnings"].append("El intervalo de confianza no es finito para estas magnitudes.")
    else:
        result["warnings"].append("Se requieren al menos 3 mediciones con valores X distintos para calcular el intervalo de confianza del 95 %." if bottle else
                                  "Se requieren al menos 3 mediciones para calcular el intervalo de confianza del 95 %.")
    reference = None
    if all(r["reference"] is not None for r in rows):
        reference = math.fsum(r["reference"] / n for r in rows)
    else:
        result["warnings"].append("No se dispone de una referencia válida para todas las mediciones; comparación global no disponible.")
    mean_temperature = math.fsum(temperatures) / n if len(temperatures) == n else None
    if mean_temperature is None:
        result["warnings"].append("Temperatura promedio no disponible: faltan temperaturas históricas válidas.")
    if slope <= 0:
        result["warnings"].append("La pendiente no es positiva: la velocidad ajustada no es físicamente válida para este modelo.")
    if syy == 0:
        result["warnings"].append("R² no definido: todas las frecuencias experimentales son iguales.")
    if sse == 0 and ci is not None:
        result["warnings"].append("Residuos nulos: el intervalo estadístico tiene ancho cero; no incluye incertidumbres instrumentales.")
    if not bottle and np.unique(x).size < 5:
        result["warnings"].append("Para el procedimiento experimental se recomiendan al menos 5 longitudes efectivas distintas.")
    result["fit"] = dict(n=n, slope=slope, intercept=intercept, r_squared=r_squared,
                         sse=sse, slope_stderr=stderr, speed=speed, speed_ci95=ci,
                         reference=reference, mean_temperature=mean_temperature,
                         difference=None if reference is None else speed - reference,
                         error_pct=None if reference is None else abs(speed - reference) / reference * 100)
    return result
