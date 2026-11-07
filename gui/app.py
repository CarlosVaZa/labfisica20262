"""
Interfaz Gráfica Visual - Grupo 1 Lab Física (Tarde)
===================================================
Medición de la velocidad del sonido mediante resonancia acústica y programación en Python

Fórmulas implementadas y mostradas según el documento:
    f1 = v / (4 * L)
    v = 4 * L * f1
    Ejemplo: L = 20 cm = 0.20 m, f1 = 425 Hz -> v = 4 * (0.20) * (425) = 340 m/s
    Valor teórico a 20 °C = 343 m/s
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.physics_engine import calculate_speed_of_sound, calculate_theoretical_frequency
from core.signal_processing import filter_ambient_noise, analyze_fft, detect_resonance_frequency
from core.audio_capture import record_microphone, load_audio_wav
from core.data_manager import ExperimentRegistry


class AcousticLabApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("PROYECTO GRUPO 1 - LABORATORIO DE FISICA: Medición de la Velocidad del Sonido por Resonancia Acústica")
        self.geometry("1220x840")
        self.minsize(1050, 720)

        # Registro de mediciones (inicia vacío sin datos quemados)
        self.registry = ExperimentRegistry()

        # Variables de estado
        self.current_length_cm = 20.0
        self.current_freq_hz = 0.0
        self.current_calc_result = None
        self.last_audio_data = None
        self.last_freqs = None
        self.last_mags = None

        self._configure_styles()
        self._build_header()
        self._build_main_layout()
        self._build_status_bar()

    def _configure_styles(self):
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except Exception:
            pass

        self.configure(bg="#f1f5f9")
        style.configure(".", background="#f1f5f9", font=("Segoe UI", 9))
        style.configure("TLabel", background="#f1f5f9", foreground="#0f172a")
        style.configure("TLabelframe", background="#f1f5f9", foreground="#1e3a8a")
        style.configure("TLabelframe.Label", font=("Segoe UI", 10, "bold"), foreground="#1e3a8a", background="#f1f5f9")
        style.configure("Treeview", font=("Segoe UI", 9), rowheight=24, background="#ffffff")
        style.configure("Treeview.Heading", font=("Segoe UI", 9, "bold"), background="#e2e8f0", foreground="#0f172a")
        style.map("Treeview", background=[("selected", "#2563eb")], foreground=[("selected", "#ffffff")])

    def _build_header(self):
        header_frame = tk.Frame(self, bg="#1e3a8a", padx=15, pady=10)
        header_frame.pack(fill=tk.X)

        title_lbl = tk.Label(
            header_frame,
            text="PROYECTO GRUPO 1 - LABORATORIO DE FISICA",
            font=("Segoe UI", 14, "bold"),
            fg="#bfdbfe",
            bg="#1e3a8a"
        )
        title_lbl.pack(anchor=tk.W)

        subtitle_lbl = tk.Label(
            header_frame,
            text="Medición de la velocidad del sonido mediante resonancia acústica y programación en Python",
            font=("Segoe UI", 11),
            fg="#ffffff",
            bg="#1e3a8a"
        )
        subtitle_lbl.pack(anchor=tk.W)

    def _build_main_layout(self):
        # Contenedor central dividido en 2 columnas:
        # Columna Izquierda: Entrada de datos, Captura de sonido, y RECUADRO DE CÁLCULOS
        # Columna Derecha: Gráficas de Matplotlib y Tabla comparativa
        main_split = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_split.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # ---------------------------------------------------------------------
        # PANEL IZQUIERDO: Entradas y Cálculos Físicos
        # ---------------------------------------------------------------------
        left_panel = ttk.Frame(main_split, padding=8)
        main_split.add(left_panel, weight=2)

        # 1. Medir la longitud del espacio lleno de aire (Paso 1 y 2 del doc)
        step1_box = ttk.LabelFrame(left_panel, text="  1. Medición de la Columna de Aire (L)  ", padding=10)
        step1_box.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(
            step1_box,
            text="Longitud del espacio que queda lleno de aire (L):",
            font=("Segoe UI", 9, "bold")
        ).pack(anchor=tk.W, pady=(0, 2))

        input_row = ttk.Frame(step1_box)
        input_row.pack(fill=tk.X, pady=(0, 5))

        self.var_length_cm = tk.DoubleVar(value=20.0)
        self.spin_length = ttk.Spinbox(
            input_row,
            from_=2.0,
            to=150.0,
            increment=1.0,
            textvariable=self.var_length_cm,
            width=10,
            font=("Segoe UI", 11, "bold"),
            command=self._on_length_change
        )
        self.spin_length.pack(side=tk.LEFT, padx=(0, 8))

        ttk.Label(input_row, text="centímetros (cm)", font=("Segoe UI", 10)).pack(side=tk.LEFT)

        self.lbl_length_m = ttk.Label(step1_box, text="Equivalente en metros: L = 0.200 m", font=("Segoe UI", 9, "italic"), foreground="#475569")
        self.lbl_length_m.pack(anchor=tk.W)

        # 2. Captura del sonido mediante micrófono y FFT (Paso 3, 4, 5, 6 y 7 del doc)
        step2_box = ttk.LabelFrame(left_panel, text="  2. Captura de Audio y Análisis por FFT  ", padding=10)
        step2_box.pack(fill=tk.X, pady=(0, 10))

        desc_audio = "Genere sonido cerca de la abertura del tubo (soplando o con parlante) y capture la señal:"
        ttk.Label(step2_box, text=desc_audio, wraplength=380, justify=tk.LEFT).pack(anchor=tk.W, pady=(0, 6))

        # Selector de duración de captura
        dur_row = ttk.Frame(step2_box)
        dur_row.pack(fill=tk.X, pady=(0, 6))

        ttk.Label(dur_row, text="Tiempo de grabación:", font=("Segoe UI", 9, "bold")).pack(side=tk.LEFT)
        self.var_duration = tk.DoubleVar(value=2.0)
        self.spin_duration = ttk.Spinbox(
            dur_row,
            from_=0.5,
            to=10.0,
            increment=0.5,
            textvariable=self.var_duration,
            width=5,
            font=("Segoe UI", 9, "bold"),
            command=self._on_duration_change
        )
        self.spin_duration.pack(side=tk.LEFT, padx=(6, 4))
        self.spin_duration.bind("<KeyRelease>", lambda e: self._on_duration_change())
        ttk.Label(dur_row, text="segundos").pack(side=tk.LEFT)

        self.btn_record = tk.Button(
            step2_box,
            text="🎙️ CAPTURAR SONIDO CON MICRÓFONO (2.0 s)",
            bg="#2563eb",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=12,
            pady=8,
            cursor="hand2",
            command=self._capture_sound
        )
        self.btn_record.pack(fill=tk.X, pady=(0, 6))

        # Opción manual o archivo WAV
        manual_row = ttk.Frame(step2_box)
        manual_row.pack(fill=tk.X, pady=(2, 0))

        btn_wav = ttk.Button(manual_row, text="📂 Cargar Audio WAV...", command=self._load_wav_file)
        btn_wav.pack(side=tk.LEFT, expand=True, fill=tk.X, padx=(0, 4))

        btn_manual = ttk.Button(manual_row, text="⌨️ Ingresar Frecuencia Manual...", command=self._input_manual_freq)
        btn_manual.pack(side=tk.RIGHT, expand=True, fill=tk.X, padx=(4, 0))

        # ---------------------------------------------------------------------
        # 3. RECUADRO DE CÁLCULOS FÍSICOS (MOSTRANDO LAS FÓRMULAS DEL DOCUMENTO)
        # ---------------------------------------------------------------------
        calc_box = ttk.LabelFrame(left_panel, text="  3. Cálculos de la Velocidad del Sonido (Fórmulas de Física)  ", padding=10)
        calc_box.pack(fill=tk.BOTH, expand=True, pady=(0, 5))

        # Banner de fórmulas del documento
        formula_bar = tk.Frame(calc_box, bg="#eff6ff", bd=1, relief=tk.SOLID, padx=8, pady=5)
        formula_bar.pack(fill=tk.X, pady=(0, 6))

        tk.Label(
            formula_bar,
            text="f₁ = v / (4 · L)    ➔    v = 4 · L · f₁",
            font=("Cambria Math", 11, "bold"),
            fg="#1e40af",
            bg="#eff6ff"
        ).pack(anchor=tk.CENTER)

        # Tarjeta con la sustitución numérica de los datos obtenidos
        self.calc_card = tk.Frame(calc_box, bg="#ffffff", bd=1, relief=tk.SOLID, padx=10, pady=8)
        self.calc_card.pack(fill=tk.X, pady=(0, 6))

        self.lbl_sustitucion = tk.Label(
            self.calc_card,
            text="v = 4 · (L) · (f₁)",
            font=("Segoe UI", 10, "bold"),
            fg="#0f172a",
            bg="#ffffff"
        )
        self.lbl_sustitucion.pack(anchor=tk.W, pady=(0, 2))

        self.lbl_resultado_v = tk.Label(
            self.calc_card,
            text="Velocidad Experimental: v = -- m/s",
            font=("Segoe UI", 13, "bold"),
            fg="#2563eb",
            bg="#ffffff"
        )
        self.lbl_resultado_v.pack(anchor=tk.W, pady=(0, 4))

        # Comparación con valor teórico a 20 °C (343 m/s)
        self.lbl_comparacion = tk.Label(
            self.calc_card,
            text="Valor teórico a 20 °C: 343.0 m/s\nError porcentual: -- %  |  Precisión: -- %",
            font=("Segoe UI", 9),
            justify=tk.LEFT,
            fg="#334155",
            bg="#ffffff"
        )
        self.lbl_comparacion.pack(anchor=tk.W)

        # Botón para registrar medición en la tabla
        self.btn_register = tk.Button(
            calc_box,
            text="➕ REGISTRAR ESTA MEDICIÓN EN LA TABLA",
            bg="#16a34a",
            fg="#ffffff",
            font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT,
            padx=10,
            pady=7,
            cursor="hand2",
            state=tk.DISABLED,
            command=self._register_measurement
        )
        self.btn_register.pack(fill=tk.X)

        # ---------------------------------------------------------------------
        # PANEL DERECHO: Gráficas de Matplotlib y Tabla de Resultados
        # ---------------------------------------------------------------------
        right_panel = ttk.Frame(main_split, padding=8)
        main_split.add(right_panel, weight=3)

        # Figura de Matplotlib con 2 subgráficas:
        # Gráfica 1: Espectro FFT con el pico marcado
        # Gráfica 2: Comparativa de Frecuencia vs Nivel de Agua
        self.fig = Figure(figsize=(7, 4.2), dpi=100, facecolor="#f8fafc")
        self.fig.subplots_adjust(left=0.10, right=0.96, top=0.90, bottom=0.12, wspace=0.25)

        # Subplot 1: Espectro FFT
        self.ax_fft = self.fig.add_subplot(1, 2, 1)
        self.ax_fft.set_title("Espectro FFT (Picos de Frecuencia)", fontsize=10, fontweight="bold", color="#1e3a8a")
        self.ax_fft.set_xlabel("Frecuencia (Hz)", fontsize=8)
        self.ax_fft.set_ylabel("Amplitud", fontsize=8)
        self.ax_fft.set_xlim(100, 1500)
        self.ax_fft.set_ylim(0, 1)
        self.ax_fft.grid(True, linestyle="--", alpha=0.4)
        self.line_fft, = self.ax_fft.plot([], [], color="#2563eb", lw=1.5, label="Espectro FFT")
        self.peak_marker, = self.ax_fft.plot([], [], "ro", markersize=8, label="Pico f1")
        self.ax_fft.legend(loc="upper right", fontsize=8)

        # Subplot 2: Comparativa Frecuencia vs Columna de aire L
        self.ax_comp = self.fig.add_subplot(1, 2, 2)
        self.ax_comp.set_title("Frecuencia vs Nivel de Aire (L)", fontsize=10, fontweight="bold", color="#1e3a8a")
        self.ax_comp.set_xlabel("Longitud L (cm)", fontsize=8)
        self.ax_comp.set_ylabel("Frecuencia f1 (Hz)", fontsize=8)
        self.ax_comp.grid(True, linestyle="--", alpha=0.4)
        self.line_theo_comp, = self.ax_comp.plot([], [], "g--", lw=1.5, label="Teórico (343/4L)")
        self.scatter_comp, = self.ax_comp.plot([], [], "bs", markersize=7, label="Mediciones")
        self.ax_comp.legend(loc="upper right", fontsize=8)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # 4. Tabla de Resultados y Comparación (Paso 8 y 9 del documento)
        table_box = ttk.LabelFrame(right_panel, text="  4. Tabla de Resultados Experimentales (Comparar Mediciones)  ", padding=8)
        table_box.pack(fill=tk.BOTH, expand=True)

        cols = ("id", "length_cm", "freq_hz", "formula", "v_calc", "v_theo", "error_pct", "precision_pct")
        self.tree = ttk.Treeview(table_box, columns=cols, show="headings", height=6)
        self.tree.heading("id", text="#")
        self.tree.heading("length_cm", text="L (cm)")
        self.tree.heading("freq_hz", text="f1 (Hz)")
        self.tree.heading("formula", text="Fórmula")
        self.tree.heading("v_calc", text="v exp (m/s)")
        self.tree.heading("v_theo", text="v teo (m/s)")
        self.tree.heading("error_pct", text="Error (%)")
        self.tree.heading("precision_pct", text="Precisión (%)")

        self.tree.column("id", width=35, anchor=tk.CENTER)
        self.tree.column("length_cm", width=65, anchor=tk.CENTER)
        self.tree.column("freq_hz", width=75, anchor=tk.CENTER)
        self.tree.column("formula", width=95, anchor=tk.CENTER)
        self.tree.column("v_calc", width=95, anchor=tk.CENTER)
        self.tree.column("v_theo", width=85, anchor=tk.CENTER)
        self.tree.column("error_pct", width=75, anchor=tk.CENTER)
        self.tree.column("precision_pct", width=85, anchor=tk.CENTER)

        tree_scroll = ttk.Scrollbar(table_box, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        tree_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        # Botones de la tabla
        tbl_btn_row = ttk.Frame(right_panel)
        tbl_btn_row.pack(fill=tk.X, pady=(6, 0))

        btn_del = ttk.Button(tbl_btn_row, text="🗑️ Eliminar Seleccionado", command=self._delete_selected)
        btn_del.pack(side=tk.LEFT, padx=(0, 6))

        btn_clr = ttk.Button(tbl_btn_row, text="🧹 Limpiar Tabla", command=self._clear_table)
        btn_clr.pack(side=tk.LEFT, padx=(0, 6))

        btn_csv = ttk.Button(tbl_btn_row, text="💾 Exportar a CSV / Excel", command=self._export_csv)
        btn_csv.pack(side=tk.RIGHT)

        # Inicializar gráfica comparativa con curva teórica
        self._update_comparison_plot()

    def _build_status_bar(self):
        self.status_bar = tk.Frame(self, bg="#e2e8f0", bd=1, relief=tk.SUNKEN, padx=8, pady=4)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.lbl_status = tk.Label(self.status_bar, text="Listo para capturar sonido y realizar cálculos.", bg="#e2e8f0", fg="#334155", font=("Segoe UI", 9))
        self.lbl_status.pack(side=tk.LEFT)

        lbl_info = tk.Label(self.status_bar, text="Proyecto: Medición de la velocidad del sonido • Python + FFT", bg="#e2e8f0", fg="#64748b", font=("Segoe UI", 8))
        lbl_info.pack(side=tk.RIGHT)

    def set_status(self, text: str):
        self.lbl_status.config(text=text)

    def _on_length_change(self):
        try:
            l_cm = self.var_length_cm.get()
            l_m = l_cm / 100.0
            self.lbl_length_m.config(text=f"Equivalente en metros: L = {l_m:.3f} m")

            # Si ya tenemos frecuencia detectada, recalcular al instante
            if self.current_freq_hz > 0:
                self._compute_and_display(l_m, self.current_freq_hz)
        except Exception:
            pass

    def _on_duration_change(self):
        try:
            d = max(0.5, float(self.var_duration.get()))
            self.btn_record.config(text=f"🎙️ CAPTURAR SONIDO CON MICRÓFONO ({d:.1f} s)")
        except Exception:
            pass

    def _capture_sound(self):
        """Captura audio del micrófono y analiza con FFT (Sección 3 y 5)."""
        try:
            dur = max(0.5, float(self.var_duration.get()))
        except Exception:
            dur = 2.0

        self.btn_record.config(state=tk.DISABLED, text=f"⏳ GRABANDO AUDIO... ({dur:.1f} s)", bg="#d97706")
        self.set_status(f"Grabando audio del micrófono ({dur:.1f} segundos)... Sople sobre la boca del tubo...")
        self.update()

        audio = record_microphone(duration_sec=dur, sample_rate=44100)

        self.btn_record.config(state=tk.NORMAL, text=f"🎙️ CAPTURAR SONIDO CON MICRÓFONO ({dur:.1f} s)", bg="#2563eb")
        self._process_audio_signal(audio, sample_rate=44100)

    def _load_wav_file(self):
        """Carga un archivo WAV existente para análisis."""
        path = filedialog.askopenfilename(
            title="Seleccionar archivo de audio WAV",
            filetypes=[("Archivos WAV", "*.wav"), ("Todos los archivos", "*.*")]
        )
        if not path:
            return

        try:
            audio, sr = load_audio_wav(path)
            self._process_audio_signal(audio, sample_rate=sr)
            self.set_status(f"Archivo WAV cargado y analizado: {path}")
        except Exception as e:
            messagebox.showerror("Error", f"No se pudo cargar el audio: {e}")

    def _input_manual_freq(self):
        """Permite ingresar manualmente la frecuencia fundamental f1."""
        dlg = tk.Toplevel(self)
        dlg.title("Ingresar Frecuencia Fundamental Manual")
        dlg.geometry("320x180")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Frecuencia fundamental f1 (Hz):", font=("Segoe UI", 9, "bold")).pack(anchor=tk.W, pady=(0, 4))
        ent_f = ttk.Entry(frame, font=("Segoe UI", 11))
        ent_f.insert(0, "425.0")
        ent_f.pack(fill=tk.X, pady=(0, 15))

        def _apply():
            try:
                f_val = float(ent_f.get())
                if f_val <= 0:
                    raise ValueError()
                dlg.destroy()
                l_cm = self.var_length_cm.get()
                self._compute_and_display(l_cm / 100.0, f_val)
                self.set_status(f"Frecuencia manual ingresada: {f_val:.1f} Hz")
            except ValueError:
                messagebox.showerror("Error", "Ingrese una frecuencia numérica positiva.", parent=dlg)

        ttk.Button(frame, text="Aceptar y Calcular", command=_apply).pack(fill=tk.X)

    def _process_audio_signal(self, audio: np.ndarray, sample_rate: int = 44100):
        """Aplica filtro para reducir ruido ambiental y FFT (Sección 5 y 8)."""
        # Filtro de ruido ambiental
        filtered = filter_ambient_noise(audio, sample_rate=sample_rate)

        # FFT
        freqs, mags = analyze_fft(filtered, sample_rate=sample_rate)

        # Detección del pico de resonancia
        peak_info = detect_resonance_frequency(freqs, mags, min_freq=120.0, max_freq=1800.0)
        f1 = peak_info["frequency_hz"]

        self.last_audio_data = audio
        self.last_freqs = freqs
        self.last_mags = mags
        self.current_freq_hz = f1

        # Actualizar gráfica FFT
        mask = (freqs >= 100) & (freqs <= 1500)
        if np.any(mask):
            self.line_fft.set_data(freqs[mask], mags[mask])
            max_m = np.max(mags[mask]) if len(mags[mask]) > 0 else 1.0
            self.ax_fft.set_ylim(0.0, max(0.1, max_m * 1.2))

        if f1 > 0:
            self.peak_marker.set_data([f1], [peak_info["amplitude"]])
            self.ax_fft.set_title(f"Espectro FFT (Pico f₁ = {f1:.1f} Hz)", fontsize=10, fontweight="bold", color="#1e3a8a")
        else:
            self.peak_marker.set_data([], [])

        self.canvas.draw_idle()

        # Realizar los cálculos físicos
        l_cm = self.var_length_cm.get()
        l_m = l_cm / 100.0
        self._compute_and_display(l_m, f1)
        self.set_status(f"Captura completada. Frecuencia fundamental detectada: {f1:.1f} Hz.")

    def _compute_and_display(self, length_m: float, freq_hz: float):
        """Calcula la velocidad del sonido según v = 4 * L * f1 y actualiza la pantalla."""
        if length_m <= 0 or freq_hz <= 0:
            return

        self.current_length_cm = length_m * 100.0
        self.current_freq_hz = freq_hz

        calc = calculate_speed_of_sound(length_m, freq_hz, theoretical_speed=343.0)
        self.current_calc_result = calc

        # Mostrar exactamente la sustitución de la fórmula
        self.lbl_sustitucion.config(text=f"v = 4 · ({length_m:.3f} m) · ({freq_hz:.1f} Hz)")
        self.lbl_resultado_v.config(text=f"Velocidad Experimental: v = {calc['v_experimental']:.2f} m/s")

        self.lbl_comparacion.config(
            text=(
                f"Valor teórico a 20 °C : {calc['v_theoretical']:.1f} m/s\n"
                f"Error porcentual     : {calc['error_porcentual']:.2f} %\n"
                f"Precisión de medición : {calc['precision']:.2f} %"
            )
        )

        self.btn_register.config(state=tk.NORMAL)

    def _register_measurement(self):
        """Agrega la medición actual a la tabla de resultados (Sección 8 y 9)."""
        if not self.current_calc_result:
            return

        l_cm = self.current_length_cm
        f1 = self.current_freq_hz

        entry = self.registry.add_measurement(length_cm=l_cm, frequency_hz=f1)

        self.tree.insert("", tk.END, values=(
            entry["id"],
            f"{entry['length_cm']:.1f}",
            f"{entry['frequency_hz']:.1f}",
            entry["formula"],
            f"{entry['v_calculada']:.2f}",
            f"{entry['v_teorica']:.1f}",
            f"{entry['error_pct']:.2f}%",
            f"{entry['precision_pct']:.2f}%"
        ))

        self._update_comparison_plot()
        self.set_status(f"Medición #{entry['id']} registrada: L = {l_cm:.1f} cm, f1 = {f1:.1f} Hz, v = {entry['v_calculada']:.2f} m/s")
        messagebox.showinfo("Medición Registrada", f"Se agregó la medición a la tabla:\n\n• Longitud L: {l_cm:.1f} cm ({l_cm/100:.3f} m)\n• Frecuencia f1: {f1:.1f} Hz\n• v = 4 · L · f1 = {entry['v_calculada']:.2f} m/s\n• Error respecto a 343 m/s: {entry['error_pct']:.2f}%")

    def _update_comparison_plot(self):
        """Actualiza la gráfica comparativa de cómo cambia la frecuencia con la cantidad de agua (Sección 8)."""
        lengths_cm, freqs_hz, _ = self.registry.get_data_arrays()

        # Curva teórica f = 343 / (4 * L) para L entre 8 y 50 cm
        l_dense_cm = np.linspace(8.0, 50.0, 100)
        f_dense_theo = [calculate_theoretical_frequency(l / 100.0, sound_speed=343.0) for l in l_dense_cm]

        self.line_theo_comp.set_data(l_dense_cm, f_dense_theo)

        if lengths_cm:
            self.scatter_comp.set_data(lengths_cm, freqs_hz)
            all_l = list(lengths_cm) + [10, 45]
            all_f = list(freqs_hz) + [min(f_dense_theo), max(f_dense_theo)]
            self.ax_comp.set_xlim(min(all_l) - 2, max(all_l) + 2)
            self.ax_comp.set_ylim(min(all_f) * 0.85, max(all_f) * 1.15)
        else:
            self.scatter_comp.set_data([], [])
            self.ax_comp.set_xlim(8, 50)
            self.ax_comp.set_ylim(150, 1100)

        self.canvas.draw_idle()

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Aviso", "Seleccione una fila de la tabla para eliminarla.")
            return

        item = self.tree.item(sel[0])
        idx = int(item["values"][0]) - 1
        self.registry.remove_measurement(idx)

        # Recargar tabla
        for item in self.tree.get_children():
            self.tree.delete(item)

        for m in self.registry.measurements:
            self.tree.insert("", tk.END, values=(
                m["id"],
                f"{m['length_cm']:.1f}",
                f"{m['frequency_hz']:.1f}",
                m["formula"],
                f"{m['v_calculada']:.2f}",
                f"{m['v_teorica']:.1f}",
                f"{m['error_pct']:.2f}%",
                f"{m['precision_pct']:.2f}%"
            ))

        self._update_comparison_plot()
        self.set_status("Medición eliminada.")

    def _clear_table(self):
        if not self.registry.measurements:
            return
        if messagebox.askyesno("Confirmar", "¿Desea limpiar todas las mediciones registradas?"):
            self.registry.clear()
            for item in self.tree.get_children():
                self.tree.delete(item)
            self._update_comparison_plot()
            self.set_status("Tabla de mediciones limpiada.")

    def _export_csv(self):
        if not self.registry.measurements:
            messagebox.showwarning("Aviso", "No hay datos en la tabla para exportar.")
            return

        path = filedialog.asksaveasfilename(
            defaultextension=".csv",
            filetypes=[("Archivos CSV", "*.csv"), ("Todos los archivos", "*.*")],
            initialfile="mediciones_velocidad_sonido.csv"
        )
        if path:
            try:
                self.registry.export_csv(path)
                messagebox.showinfo("Exportar", f"Mediciones guardadas exitosamente en:\n{path}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo: {e}")


def start_gui():
    app = AcousticLabApp()
    app.mainloop()


if __name__ == "__main__":
    start_gui()
