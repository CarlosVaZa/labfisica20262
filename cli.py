"""
Interfaz de Línea de Comandos (CLI)
==================================
Permite ejecutar mediciones rápidas, análisis de series de resonancia,
generación acústica y demostraciones completas directamente desde la terminal.
"""

import argparse
import sys
import os
import time
import numpy as np
import matplotlib.pyplot as plt

from core.physics_engine import (
    theoretical_sound_speed,
    sound_speed_from_point,
    analyze_resonance_series,
    estimate_water_level,
    frequency_to_musical_note,
)
from core.signal_processing import (
    apply_bandpass_filter,
    compute_fft,
    find_spectral_peaks,
    calculate_signal_rms,
)
from core.audio_capture import record_burst, list_audio_devices
from core.audio_generator import (
    generate_pure_tone,
    generate_frequency_sweep,
    generate_white_noise,
    play_audio,
    simulate_pipe_resonance,
)
from core.data_manager import ExperimentDataset


def print_banner():
    banner = r"""
========================================================================
   GRUPO 1 - LABORATORIO DE FISICA: MEDICION DE LA VELOCIDAD DEL SONIDO
   MEDIANTE RESONANCIA ACUSTICA Y PROGRAMACION EN PYTHON
========================================================================
    """
    print(banner)


def cmd_devices(args):
    devs = list_audio_devices()
    print("\n--- Dispositivos de Entrada (Microfonos) ---")
    for d in devs["inputs"]:
        def_mark = " [* PREDETERMINADO]" if d["is_default"] else ""
        print(f"[{d['id']}] {d['name']} ({d['channels']} canales, {d['default_samplerate']} Hz){def_mark}")

    print("\n--- Dispositivos de Salida (Altavoces) ---")
    for d in devs["outputs"]:
        def_mark = " [* PREDETERMINADO]" if d["is_default"] else ""
        print(f"[{d['id']}] {d['name']} ({d['channels']} canales, {d['default_samplerate']} Hz){def_mark}")


def cmd_record(args):
    print(f"\n[+] Iniciando captura acustica...")
    print(f"    Longitud de columna de aire (L): {args.length_cm:.1f} cm ({args.length_cm / 100.0:.3f} m)")
    print(f"    Temperatura ambiente: {args.temp:.1f} °C")
    print(f"    Duracion: {args.duration:.1f} s")

    L_m = args.length_cm / 100.0
    r_m = args.radius_cm / 100.0

    if args.simulate:
        print("    [MODO SIMULACION ACTIVO: Sintetizando resonancia acustica]")
        audio = record_burst(duration_sec=args.duration, sample_rate=args.samplerate, simulated_length_m=L_m)
    else:
        print("    [GRABANDO MICROFONO... Sople suavemente sobre la boca del tubo o acerque el altavoz]")
        audio = record_burst(duration_sec=args.duration, sample_rate=args.samplerate, device_id=args.device)

    # Procesamiento DSP
    filtered_audio = apply_bandpass_filter(audio, sample_rate=args.samplerate, low_cutoff=80.0, high_cutoff=3000.0)
    freqs, mag, mag_db = compute_fft(filtered_audio, sample_rate=args.samplerate, window_type="hann")
    peaks = find_spectral_peaks(freqs, mag, min_freq=args.min_freq, max_freq=args.max_freq)

    if not peaks:
        print("[-] No se detectaron picos claros de frecuencia en el rango especificado.")
        return

    f_res = peaks[0]["frequency"]
    amp = peaks[0]["amplitude"]
    snr = peaks[0]["snr_db"]
    v_exp = sound_speed_from_point(L_m, f_res, tube_radius_m=r_m)
    v_theo = theoretical_sound_speed(args.temp)
    err = abs(v_exp - v_theo) / v_theo * 100.0
    note_info = frequency_to_musical_note(f_res)

    print("\n" + "=" * 50)
    print("           RESULTADOS DE LA MEDICION")
    print("=" * 50)
    print(f"  * Frecuencia fundamental (f1) : {f_res:.2f} Hz")
    print(f"  * Amplitud relativa           : {amp:.4f}")
    print(f"  * Relacion Senal/Ruido (SNR)  : {snr:.1f} dB")
    print(f"  * Nota musical aproximada     : {note_info['note']} ({note_info['cents_deviation']:+.1f} cents)")
    print(f"  * Velocidad del sonido exper. : {v_exp:.2f} m/s")
    print(f"  * Velocidad teorica a {args.temp:.1f} °C : {v_theo:.2f} m/s")
    print(f"  * Error porcentual            : {err:.2f} %")
    print("=" * 50)

    if args.plot:
        plt.figure(figsize=(10, 5))
        plt.subplot(1, 2, 1)
        t = np.linspace(0, len(audio) / args.samplerate, len(audio))
        plt.plot(t[:2000], audio[:2000], color="#2b5c8f")
        plt.title("Senal Temporal (Oscilograma)")
        plt.xlabel("Tiempo (s)")
        plt.ylabel("Amplitud")
        plt.grid(True, alpha=0.3)

        plt.subplot(1, 2, 2)
        mask = (freqs >= 50) & (freqs <= 2000)
        plt.plot(freqs[mask], mag[mask], color="#e74c3c", label="Espectro FFT")
        plt.plot(f_res, amp, "ro", markersize=8, label=f"Pico f1 = {f_res:.1f} Hz")
        plt.title("Espectro de Frecuencia")
        plt.xlabel("Frecuencia (Hz)")
        plt.ylabel("Magnitud")
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()

        out_img = "grafica_captura.png"
        plt.savefig(out_img, dpi=150)
        print(f"[+] Grafica guardada exitosamente en: {os.path.abspath(out_img)}")
        try:
            plt.show()
        except Exception:
            pass


def cmd_analyze(args):
    dataset = ExperimentDataset()
    if args.file and os.path.exists(args.file):
        print(f"[+] Cargando mediciones reales desde: {args.file}")
        if args.file.endswith(".json"):
            dataset.import_json(args.file)
        else:
            dataset.import_csv(args.file)
    else:
        print("\n[-] No se especifico un archivo de mediciones con --file.")
        print("[*] Inicie la interfaz visual con:  python main.py")
        print("[*] O ejecute el asistente interactivo con:  python cli.py interactive\n")
        return

    dataset.temperature_c = args.temp
    dataset.tube_radius_m = args.radius_cm / 100.0

    lengths, freqs = dataset.get_lengths_and_frequencies()
    if len(lengths) < 2:
        print("[-] Se requieren al menos 2 mediciones para realizar la regresion.")
        return

    res = analyze_resonance_series(lengths, freqs, temp_celsius=dataset.temperature_c, tube_radius_m=dataset.tube_radius_m)

    print("\n" + "=" * 65)
    print("      REPORTE DE REGRESION LINEAL Y VELOCIDAD DEL SONIDO")
    print("=" * 65)
    print(f" Numero de mediciones analizadas : {res['n_samples']}")
    print(f" Temperatura ambiente            : {dataset.temperature_c:.1f} °C")
    print(f" Pendiente m = v/4               : {res['slope']:.4f} +- {res['slope_uncertainty']:.4f} m*s")
    print(f" Intercepto c = -Delta_L         : {res['intercept']:.4f} +- {res['intercept_uncertainty']:.4f} m")
    print(f" Coeficiente R^2 (Ajuste)        : {res['r_squared']:.5f}")
    print("-" * 65)
    print(f" > VELOCIDAD EXPERIMENTAL (v)   : {res['v_experimental']:.2f} +- {res['v_uncertainty']:.2f} m/s")
    print(f" > VELOCIDAD TEORICA             : {res['v_theoretical']:.2f} m/s")
    print(f" > ERROR PORCENTUAL              : {res['percentage_error']:.2f} %")
    print(f" > Correccion de extremo exp.    : {res['experimental_end_correction_m'] * 1000.0:.2f} mm")
    if res['theoretical_end_correction_m'] is not None:
        print(f" > Correccion teorica (0.61*r)   : {res['theoretical_end_correction_m'] * 1000.0:.2f} mm")
    print("=" * 65)

    # Generar grafica de ajuste
    plt.figure(figsize=(9, 5.5))
    x_inv = np.array(res["x_inv_freq"])
    y_len = np.array(res["y_lengths"])
    y_pred = np.array(res["y_pred"])

    plt.scatter(x_inv * 1000.0, y_len * 100.0, color="#1f77b4", s=60, zorder=5, label="Datos Experimentales (L vs 1/f)")
    x_line = np.linspace(min(x_inv) * 0.9, max(x_inv) * 1.1, 100)
    y_line = (res["slope"] * x_line + res["intercept"]) * 100.0
    plt.plot(x_line * 1000.0, y_line, color="#d62728", lw=2, label=f"Ajuste: L = {res['slope']:.3f}(1/f) {res['intercept']:+.3f}\n(v = {res['v_experimental']:.1f} m/s, R²={res['r_squared']:.4f})")

    plt.title("Medición de la Velocidad del Sonido por Resonancia Acústica", fontsize=12, fontweight="bold")
    plt.xlabel("Inverso de Frecuencia (1/f) [ms]", fontsize=10)
    plt.ylabel("Longitud de Columna de Aire L [cm]", fontsize=10)
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.legend(fontsize=9)
    plt.tight_layout()

    out_file = args.out or "grafica_regresion.png"
    plt.savefig(out_file, dpi=150)
    print(f"[+] Grafica guardada exitosamente en: {os.path.abspath(out_file)}")


def cmd_interactive(args):
    """Asistente interactivo por consola para recibir datos reales del usuario sin datos quemados."""
    print_banner()
    print("--- ASISTENTE INTERACTIVO DE MEDICION (DATOS REALES DEL USUARIO) ---\n")

    try:
        t_input = input("1. Ingrese la temperatura ambiente del laboratorio en °C [Enter para 20.0 °C]: ").strip()
        temp_c = float(t_input) if t_input else 20.0

        r_input = input("2. Ingrese el radio interno del tubo en cm [Enter para 1.5 cm]: ").strip()
        radius_cm = float(r_input) if r_input else 1.5
    except ValueError:
        print("[-] Valor invalido. Usando valores predeterminados (20 °C, 1.5 cm).")
        temp_c = 20.0
        radius_cm = 1.5

    dataset = ExperimentDataset("Experimento Laboratorio Real")
    dataset.temperature_c = temp_c
    dataset.tube_radius_m = radius_cm / 100.0

    print("\n--- INGRESO DE PUNTOS EXPERIMENTALES ---")
    print("Puede ingresar cada longitud L medida con regla y capturar el sonido con microfono")
    print("o digitar directamente la frecuencia que midio.\n")

    point_idx = 1
    while True:
        print(f"\n>> Medicion #{point_idx}:")
        l_str = input(f"   Longitud L de la columna de aire en cm (o 'fin' para terminar): ").strip()
        if l_str.lower() in ("fin", "exit", "q", "terminar", ""):
            if len(dataset.measurements) < 2:
                print("[-] Ingrese al menos 2 mediciones para poder calcular la velocidad por regresion.")
                continue
            break

        try:
            length_cm = float(l_str)
            if length_cm <= 0:
                print("[-] La longitud debe ser positiva.")
                continue
        except ValueError:
            print("[-] Ingrese un numero valido.")
            continue

        modo = input("   ¿Desea (1) Capturar con microfono o (2) Ingresar frecuencia manual? [1/2]: ").strip()
        if modo == "2":
            f_str = input("   Ingrese la frecuencia fundamental f1 en Hz: ").strip()
            try:
                freq_hz = float(f_str)
            except ValueError:
                print("[-] Frecuencia invalida.")
                continue
        else:
            input("   Acerque el microfono al tubo y presione ENTER para grabar 1.5 s (sople suavemente)...")
            audio = record_burst(duration_sec=1.5, sample_rate=44100)
            filtered = apply_bandpass_filter(audio, sample_rate=44100, low_cutoff=80.0, high_cutoff=2500.0)
            freqs, mag, _ = compute_fft(filtered, sample_rate=44100)
            peaks = find_spectral_peaks(freqs, mag, min_freq=100.0, max_freq=1800.0)
            if not peaks:
                print("[-] No se detecto un pico claro. Digite la frecuencia manualmente:")
                f_str = input("   Frecuencia f1 (Hz): ").strip()
                try:
                    freq_hz = float(f_str)
                except ValueError:
                    continue
            else:
                freq_hz = peaks[0]["frequency"]
                print(f"   [+] Frecuencia detectada por FFT: {freq_hz:.2f} Hz (Amplitud: {peaks[0]['amplitude']:.3f})")

        entry = dataset.add_measurement(length_m=length_cm / 100.0, frequency_hz=freq_hz, notes=f"L={length_cm}cm")
        print(f"   [OK] Guardado: L = {length_cm:.1f} cm | f = {freq_hz:.1f} Hz | v puntual = {entry['v_point_m_s']:.1f} m/s")
        point_idx += 1

    # Analizar los datos reales ingresados
    lengths, freqs = dataset.get_lengths_and_frequencies()
    res = analyze_resonance_series(lengths, freqs, temp_celsius=temp_c, tube_radius_m=radius_cm / 100.0)

    print("\n" + "=" * 65)
    print("      REPORTE DE REGRESION LINEAL CON SUS DATOS REALES")
    print("=" * 65)
    print(f" Mediciones registradas         : {res['n_samples']}")
    print(f" Temperatura ambiente            : {temp_c:.1f} °C")
    print(f" Pendiente m = v/4               : {res['slope']:.4f} +- {res['slope_uncertainty']:.4f} m*s")
    print(f" Intercepto c = -Delta_L         : {res['intercept']:.4f} +- {res['intercept_uncertainty']:.4f} m")
    print(f" Coeficiente R^2 (Ajuste)        : {res['r_squared']:.5f}")
    print("-" * 65)
    print(f" > VELOCIDAD EXPERIMENTAL (v)   : {res['v_experimental']:.2f} +- {res['v_uncertainty']:.2f} m/s")
    print(f" > VELOCIDAD TEORICA             : {res['v_theoretical']:.2f} m/s")
    print(f" > ERROR PORCENTUAL              : {res['percentage_error']:.2f} %")
    print(f" > Correccion de extremo exp.    : {res['experimental_end_correction_m'] * 1000.0:.2f} mm")
    print("=" * 65)

    # Exportar resultados
    csv_file = "mediciones_laboratorio_reales.csv"
    dataset.export_csv(csv_file)
    print(f"[+] Mediciones guardadas en CSV: {os.path.abspath(csv_file)}")

    html_file = "informe_laboratorio.html"
    dataset.export_html_report(html_file)
    print(f"[+] Informe HTML generado en: {os.path.abspath(html_file)}")


def cmd_tone(args):
    print(f"[+] Generando tono sinusoidal de {args.freq:.1f} Hz durante {args.duration:.1f} s...")
    tone = generate_pure_tone(args.freq, duration_sec=args.duration)
    play_audio(tone)
    time.sleep(args.duration)
    print("[+] Reproduccion finalizada.")


def cmd_sweep(args):
    print(f"[+] Generando barrido de frecuencias ({args.start_freq:.0f} Hz -> {args.end_freq:.0f} Hz) en {args.duration:.1f} s...")
    sweep = generate_frequency_sweep(args.start_freq, args.end_freq, duration_sec=args.duration)
    play_audio(sweep)
    time.sleep(args.duration)
    print("[+] Barrido finalizado.")


def cmd_demo(args):
    print_banner()
    print("[*] Iniciando demostracion de prueba para validar algoritmos...")
    time.sleep(1)

    print("\n--- PASO 1: Captura Acustica de Prueba ---")
    args.length_cm = 20.0
    args.radius_cm = 1.5
    args.temp = 20.0
    args.duration = 1.5
    args.samplerate = 44100
    args.min_freq = 150.0
    args.max_freq = 1500.0
    args.simulate = True
    args.plot = False
    args.device = None
    cmd_record(args)

    print("\n--- PASO 2: Analisis de Regresion Lineal ---")
    sample_csv = os.path.join(os.path.dirname(__file__), "data", "sample_experiments.csv")
    args.file = sample_csv
    args.out = "grafica_regresion_demo.png"
    cmd_analyze(args)

    print("\n--- PASO 3: Demostracion Sensor de Nivel de Agua ---")
    total_h = 0.50
    test_freqs = [214.3, 284.6, 422.8, 690.5]
    print(f"Tubo de altura total: {total_h*100:.0f} cm")
    for f in test_freqs:
        lvl = estimate_water_level(f, total_tube_length_m=total_h, sound_speed=343.0, tube_radius_m=0.015)
        print(f"  Frecuencia: {f:6.1f} Hz -> Aire: {lvl['air_column_m']*100:4.1f} cm | Nivel Agua: {lvl['water_height_m']*100:4.1f} cm | Llenado: {lvl['fill_percentage']:4.1f}%")

    print("\n" + "=" * 65)
    print("  [!] PARA TRABAJAR CON SUS DATOS REALES:")
    print("  1. Interfaz Grafica (Recomendado):  python main.py")
    print("  2. Asistente por Consola:           python cli.py interactive")
    print("=" * 65)


def main():
    parser = argparse.ArgumentParser(
        description="Sistema de Medicion de Velocidad del Sonido por Resonancia Acustica - Grupo 1"
    )
    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # devices
    subparsers.add_parser("devices", help="Listar dispositivos de audio disponibles")

    # record
    p_rec = subparsers.add_parser("record", help="Capturar sonido y medir frecuencia de resonancia")
    p_rec.add_argument("--length-cm", "-L", type=float, default=20.0, help="Longitud de la columna de aire en cm")
    p_rec.add_argument("--radius-cm", "-r", type=float, default=1.5, help="Radio del tubo en cm")
    p_rec.add_argument("--temp", "-T", type=float, default=20.0, help="Temperatura ambiente en °C")
    p_rec.add_argument("--duration", "-d", type=float, default=1.5, help="Duracion en segundos")
    p_rec.add_argument("--samplerate", "-fs", type=int, default=44100, help="Tasa de muestreo")
    p_rec.add_argument("--min-freq", type=float, default=150.0, help="Frecuencia minima en Hz")
    p_rec.add_argument("--max-freq", type=float, default=1500.0, help="Frecuencia maxima en Hz")
    p_rec.add_argument("--device", type=int, default=None, help="ID de dispositivo de entrada")
    p_rec.add_argument("--simulate", action="store_true", help="Usar simulacion acustica en lugar de microfono")
    p_rec.add_argument("--plot", action="store_true", help="Generar y mostrar grafica de la captura")

    # analyze
    p_ana = subparsers.add_parser("analyze", help="Analizar serie de datos experimentales con regresion lineal")
    p_ana.add_argument("--file", "-f", type=str, default=None, help="Ruta a archivo CSV o JSON con mediciones")
    p_ana.add_argument("--temp", "-T", type=float, default=20.0, help="Temperatura ambiente en °C")
    p_ana.add_argument("--radius-cm", "-r", type=float, default=1.5, help="Radio del tubo en cm")
    p_ana.add_argument("--out", "-o", type=str, default="grafica_regresion.png", help="Archivo de salida para la grafica")

    # tone
    p_tone = subparsers.add_parser("tone", help="Generar tono senoidal en el altavoz")
    p_tone.add_argument("--freq", "-f", type=float, default=440.0, help="Frecuencia en Hz")
    p_tone.add_argument("--duration", "-d", type=float, default=2.0, help="Duracion en segundos")

    # sweep
    p_swp = subparsers.add_parser("sweep", help="Generar barrido senoidal en el altavoz")
    p_swp.add_argument("--start-freq", type=float, default=200.0, help="Frecuencia inicial en Hz")
    p_swp.add_argument("--end-freq", type=float, default=1200.0, help="Frecuencia final en Hz")
    p_swp.add_argument("--duration", "-d", type=float, default=3.0, help="Duracion en segundos")

    # interactive
    subparsers.add_parser("interactive", help="Asistente interactivo para ingresar mediciones reales paso a paso")

    # demo
    subparsers.add_parser("demo", help="Ejecutar demostracion completa automatizada")

    args = parser.parse_args()

    if args.command == "interactive":
        cmd_interactive(args)
    elif args.command == "devices":
        cmd_devices(args)
    elif args.command == "record":
        cmd_record(args)
    elif args.command == "analyze":
        cmd_analyze(args)
    elif args.command == "tone":
        cmd_tone(args)
    elif args.command == "sweep":
        cmd_sweep(args)
    elif args.command == "demo":
        cmd_demo(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

