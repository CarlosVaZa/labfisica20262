"""
Punto de Entrada Principal del Proyecto
======================================
Grupo 1 - Lab Física (Tarde)
Medición de la velocidad del sonido mediante resonancia acústica y programación en Python.

Uso:
    python main.py                # Inicia la Interfaz Gráfica interactiva (GUI)
    python main.py --cli [args]   # Ejecuta el modo de línea de comandos (CLI)
    python main.py demo           # Ejecuta la demostración de laboratorio completa
"""

import sys
import os

if __name__ == "__main__":
    # Si se pasa "demo", "record", "analyze", "devices", "tone", "sweep", o flag "--cli", usar CLI
    cli_commands = {"demo", "record", "analyze", "devices", "tone", "sweep", "--cli", "-h", "--help"}

    if len(sys.argv) > 1 and any(arg in cli_commands for arg in sys.argv[1:]):
        # Si se usó --cli como primer argumento, removerlo
        if sys.argv[1] == "--cli":
            sys.argv.pop(1)
        import cli
        cli.main()
    else:
        # Iniciar GUI por defecto
        try:
            from gui.app import start_gui
            start_gui()
        except Exception as e:
            print(f"No se pudo iniciar la interfaz gráfica: {e}")
            print("Iniciando en modo CLI de respaldo:")
            import cli
            cli.main()

