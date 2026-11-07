"""
Aplicación Gráfica Principal: Laboratorio de Física Acústica
===========================================================
Grupo 1 - Medición de la Velocidad del Sonido por Resonancia Acústica
"""

import tkinter as tk
from tkinter import ttk, messagebox
import os
import sys

from core.data_manager import ExperimentDataset
from .styles import COLORS, FONTS
from .tab_realtime import RealtimeTab
from .tab_experiment import ExperimentTab
from .tab_applications import ApplicationsTab
from .tab_theory import TheoryTab


class AcousticLabApp(tk.Tk):
    """Ventana principal de la aplicación de laboratorio."""

    def __init__(self):
        super().__init__()

        self.title("Laboratorio de Física Acústica - Grupo 1 | Velocidad del Sonido por Resonancia")
        self.geometry("1180x760")
        self.minsize(980, 640)

        # Dataset compartido para todo el laboratorio
        self.dataset = ExperimentDataset()

        self._configure_theme()
        self._build_menu()
        self._build_main_ui()
        self._build_status_bar()

        self.protocol("WM_DELETE_WINDOW", self._on_close)
        self.set_status("Aplicación iniciada. Listo para capturar y medir resonancias acústicas.")

    def _configure_theme(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        # Configurar colores y tipografías ttk
        style.configure(".", background=COLORS["bg_main"], font=FONTS["body"])
        style.configure("TLabel", background=COLORS["bg_main"], foreground=COLORS["text_dark"])
        style.configure("TFrame", background=COLORS["bg_main"])
        style.configure("TLabelframe", background=COLORS["bg_main"], foreground=COLORS["text_dark"])
        style.configure("TLabelframe.Label", font=FONTS["header"], foreground=COLORS["primary"], background=COLORS["bg_main"])

        style.configure("TNotebook", background=COLORS["bg_main"], tabmargins=[2, 5, 2, 0])
        style.configure("TNotebook.Tab", font=FONTS["header"], padding=[16, 8], background="#e2e8f0", foreground=COLORS["text_dark"])
        style.map("TNotebook.Tab",
                  background=[("selected", COLORS["bg_card"]), ("active", "#cbd5e1")],
                  foreground=[("selected", COLORS["primary"])])

        style.configure("Treeview", font=FONTS["body"], rowheight=24, background="#ffffff", fieldbackground="#ffffff")
        style.configure("Treeview.Heading", font=FONTS["header"], background="#e2e8f0", foreground=COLORS["text_dark"])
        style.map("Treeview", background=[("selected", COLORS["primary"])], foreground=[("selected", "#ffffff")])

    def _build_menu(self):
        menubar = tk.Menu(self)

        # Menú Archivo
        menu_file = tk.Menu(menubar, tearoff=False)
        menu_file.add_command(label="📁 Cargar Datos Modelo de Laboratorio", command=self._menu_load_sample)
        menu_file.add_separator()
        menu_file.add_command(label="💾 Exportar Mediciones a CSV...", command=self._menu_export_csv)
        menu_file.add_command(label="📂 Importar Mediciones...", command=self._menu_import_csv)
        menu_file.add_separator()
        menu_file.add_command(label="❌ Salir", command=self._on_close)
        menubar.add_cascade(label="Archivo", menu=menu_file)

        # Menú Herramientas
        menu_tools = tk.Menu(menubar, tearoff=False)
        menu_tools.add_command(label="🔊 Emitir Tono Senoidal (440 Hz)", command=lambda: self.tab_realtime._play_tone_440())
        menu_tools.add_command(label="🔊 Emitir Barrido Acústico", command=lambda: self.tab_realtime._play_sweep())
        menu_tools.add_separator()
        menu_tools.add_command(label="🧹 Limpiar Mediciones", command=lambda: self.tab_experiment._clear_all())
        menubar.add_cascade(label="Herramientas", menu=menu_tools)

        # Menú Ayuda
        menu_help = tk.Menu(menubar, tearoff=False)
        menu_help.add_command(label="📖 Guía de Resonancia Acústica", command=lambda: self.notebook.select(3))
        menu_help.add_separator()
        menu_help.add_command(label="ℹ️ Acerca del Proyecto (Grupo 1)", command=self._show_about)
        menubar.add_cascade(label="Ayuda", menu=menu_help)

        self.config(menu=menubar)

    def _build_main_ui(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=8, pady=(4, 0))

        # Pestañas
        self.tab_realtime = RealtimeTab(self.notebook, self)
        self.tab_experiment = ExperimentTab(self.notebook, self)
        self.tab_applications = ApplicationsTab(self.notebook, self)
        self.tab_theory = TheoryTab(self.notebook, self)

        self.notebook.add(self.tab_realtime, text="  🎙️ Captura y Espectro en Vivo  ")
        self.notebook.add(self.tab_experiment, text="  📊 Experimento y Regresión  ")
        self.notebook.add(self.tab_applications, text="  💡 Aplicaciones Prácticas  ")
        self.notebook.add(self.tab_theory, text="  📖 Teoría y Calculadora  ")

    def _build_status_bar(self):
        self.status_bar = ttk.Frame(self, relief=tk.SUNKEN, padding=(8, 4))
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.lbl_status = ttk.Label(self.status_bar, text="Listo", font=FONTS["body"])
        self.lbl_status.pack(side=tk.LEFT)

        lbl_credit = ttk.Label(
            self.status_bar,
            text="Física Ondas y Fluidos • Grupo 1 Lab Física Tarde",
            font=("Segoe UI", 8),
            foreground=COLORS["text_muted"]
        )
        lbl_credit.pack(side=tk.RIGHT)

    def set_status(self, text: str):
        self.lbl_status.config(text=text)

    def _menu_load_sample(self):
        self.tab_experiment._load_sample()
        self.notebook.select(1)

    def _menu_export_csv(self):
        self.tab_experiment._export_csv()

    def _menu_import_csv(self):
        self.tab_experiment._import_csv()

    def _show_about(self):
        about_text = (
            "PROYECTO DE LABORATORIO DE FÍSICA\n"
            "Grupo 1 - Lab Física (Tarde)\n\n"
            "Tema: Medición de la velocidad del sonido mediante resonancia acústica "
            "y programación en Python.\n\n"
            "Características Principales:\n"
            "• Captura en tiempo real y oscilograma con FFT.\n"
            "• Filtro Butterworth y detección de picos con interpolación sub-bin.\n"
            "• Regresión lineal (L vs 1/f) con cálculo de v_exp y corrección de extremo.\n"
            "• Sensor acústico de nivel de líquidos.\n"
            "• Afinador cromático digital de instrumentos.\n"
            "• Simulador de columna de aire acústica integrado.\n\n"
            "Desarrollado en Python con NumPy, SciPy, Matplotlib y SoundDevice."
        )
        messagebox.showinfo("Acerca del Proyecto - Grupo 1", about_text)

    def _on_close(self):
        try:
            self.tab_realtime.cleanup()
        except Exception:
            pass
        self.destroy()


def start_gui():
    app = AcousticLabApp()
    app.mainloop()


if __name__ == "__main__":
    start_gui()

