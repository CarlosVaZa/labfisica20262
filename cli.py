"""
Línea de Comandos (CLI) - Grupo 1 Lab Física
============================================
Medición de la velocidad del sonido mediante resonancia acústica y programación en Python.
Fórmulas:
    f1 = v / (4 * L)
    v = 4 * L * f1
"""

import sys
import os
import argparse
import numpy as np

from core.physics_engine import calculate_speed_of_sound, calculate_theoretical_frequency
from core.signal_processing import filter_ambient_noise, analyze_fft, detect_resonance_frequency
from core.audio_capture import record_microphone, load_audio_wav
from core.data_manager import ExperimentRegistry


def main():
    parser = argparse.ArgumentParser(description="Medición de la velocidad del sonido por resonancia acústica - Grupo 1")
    parser.add_argument("--length-cm", "-L", type=float, default=20.0, help="Longitud de la columna de aire en cm (ej. 20 cm)")
    parser.add_argument("--freq-hz", "-f", type=float, default=None, help="Frecuencia fundamental en Hz (opcional, si no se usa micrófono)")
    parser.add_argument("--record", "-r", action="store_true", help="Capturar audio del micrófono")
    parser.add_argument("--duration", "-d", type=float, default=2.0, help="Duración de captura en segundos (ej. 2.0)")
    parser.add_argument("--wav", "-w", type=str, default=None, help="Cargar archivo WAV")

    args = parser.parse_args()

    length_m = args.length_cm / 100.0

    print("=" * 65)
    print("  GRUPO 1 - LABORATORIO DE FÍSICA: VELOCIDAD DEL SONIDO")
    print("=" * 65)
    print(f"Longitud de columna de aire (L): {args.length_cm:.1f} cm ({length_m:.3f} m)")

    if args.freq_hz is not None:
        f1 = args.freq_hz
        print(f"Frecuencia ingresada: {f1:.1f} Hz")
    elif args.wav:
        print(f"Cargando archivo WAV: {args.wav}...")
        audio, sr = load_audio_wav(args.wav)
        filtered = filter_ambient_noise(audio, sr)
        freqs, mags = analyze_fft(filtered, sr)
        peak = detect_resonance_frequency(freqs, mags)
        f1 = peak["frequency_hz"]
        print(f"Frecuencia detectada por FFT: {f1:.1f} Hz")
    else:
        print(f"Capturando {args.duration:.1f} s de audio con micrófono (sople sobre el tubo)...")
        audio = record_microphone(args.duration, 44100)
        filtered = filter_ambient_noise(audio, 44100)
        freqs, mags = analyze_fft(filtered, 44100)
        peak = detect_resonance_frequency(freqs, mags)
        f1 = peak["frequency_hz"]
        print(f"Frecuencia de resonancia detectada por FFT: {f1:.1f} Hz")

    calc = calculate_speed_of_sound(length_m, f1, theoretical_speed=343.0)

    print("\n--- CÁLCULOS FÍSICOS SEGÚN EL DOCUMENTO ---")
    print(f"Fórmula: {calc['formula_text']}")
    print(f"Sustitución: {calc['sustitucion_text']}")
    print(f"Resultado: {calc['resultado_text']}")
    print(f"Valor teórico a 20 °C: {calc['v_theoretical']:.1f} m/s")
    print(f"Error porcentual: {calc['error_porcentual']:.2f} %")
    print(f"Precisión de la medición: {calc['precision']:.2f} %")
    print("=" * 65)


if __name__ == "__main__":
    main()
