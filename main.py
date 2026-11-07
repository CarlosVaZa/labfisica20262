"""
Punto de Entrada Principal del Proyecto
======================================
Grupo 1 - Lab Física (Tarde)
Medición de la velocidad del sonido mediante resonancia acústica y programación en Python.

Uso:
    python main.py               # Inicia la Interfaz Gráfica interactiva (GUI)
    python main.py --cli         # Modo interactivo en terminal (sin GUI)
    python run_gui.py            # Lanzador directo de la Interfaz Gráfica
"""

import sys
import os

if __name__ == "__main__":
    # Solo si el usuario solicita explícitamente modo CLI con flags como --cli o subcomandos cli
    cli_flags = {"--cli", "-c", "cli"}

    if len(sys.argv) > 1 and sys.argv[1] in cli_flags:
        sys.argv.pop(1)
        import cli
        cli.main()
    else:
        # Por defecto SIEMPRE iniciar la Interfaz Gráfica Visual (GUI)
        print("=" * 70)
        print("  INICIANDO INTERFAZ VISUAL (GUI) - LABORATORIO DE FISICA ACUSTICA")
        print("  Grupo 1 - Medicion de la Velocidad del Sonido por Resonancia")
        print("=" * 70)
        print("[+] Abriendo ventana grafica interactiva en su pantalla...")
        try:
            from gui.app import start_gui
            start_gui()
        except Exception as e:
            print(f"[-] No se pudo desplegar la interfaz gráfica de escritorio: {e}")
            print("[*] Iniciando modo interactivo por consola de respaldo:")
            import cli
            cli.cmd_interactive(None)

