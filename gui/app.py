"""
Interfaz Gráfica Visual - Grupo 1 Lab Física (Tarde)
===================================================
Medición de la velocidad del sonido mediante resonancia acústica y programación en Python

Modelos: tubo ideal, tubo con corrección de abertura y botella de Helmholtz.
Pestañas: captura y FFT, cálculos y gráficas, y resultados experimentales.
Entradas en cm y mL, cálculos en SI; referencia calculada según la temperatura ambiental.
"""

import tkinter as tk
from pathlib import Path
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.physics_engine import (calculate_speed_of_sound, calculate_theoretical_frequency,
                                 calculate_helmholtz_speed, calculate_helmholtz_frequency, calculate_reference_speed)
from core.signal_processing import filter_ambient_noise, analyze_fft, detect_resonance_frequency
from core.audio_capture import record_microphone, load_audio_wav
from core.data_manager import ExperimentRegistry
from gui.statistics_tab import StatisticsTab


class AcousticLabApp(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("PROYECTO GRUPO 1 - LABORATORIO DE FISICA: Medición de la Velocidad del Sonido por Resonancia Acústica")
        # Ajustar la ventana al escritorio, dejando espacio para la barra de tareas.
        width = min(1180, max(640, self.winfo_screenwidth() - 80))
        height = min(760, max(480, self.winfo_screenheight() - 120))
        self.geometry(f"{width}x{height}+20+20")
        self.minsize(min(760, width), min(480, height))

        # Registro de mediciones (inicia vacío sin datos quemados)
        self.registry = ExperimentRegistry()

        # Variables de estado
        self.current_length_cm = 20.0
        self.current_freq_hz = 0.0
        self.current_calc_result = None
        self.last_audio_data = None
        self.last_audio_raw = None       # audio sin filtrar, para reanalizar
        self.last_audio_sr = 44100       # sample rate del último audio
        self.last_freqs = None
        self.last_mags = None

        self._configure_styles()
        self._build_header()
        self._build_status_bar()
        self._build_main_layout()

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
        header_frame = tk.Frame(self, bg="#1e3a8a", padx=15, pady=8)
        header_frame.pack(fill=tk.X)

        # Lado izquierdo del encabezado: Títulos
        left_header = tk.Frame(header_frame, bg="#1e3a8a")
        left_header.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, anchor=tk.W)

        title_lbl = tk.Label(
            left_header,
            text="PROYECTO GRUPO 1 - LABORATORIO DE FISICA",
            font=("Segoe UI", 12, "bold"),
            fg="#bfdbfe",
            bg="#1e3a8a"
        )
        title_lbl.pack(anchor=tk.W, fill=tk.X)

        subtitle_lbl = tk.Label(
            left_header,
            text="Medición de la velocidad del sonido mediante resonancia acústica y programación en Python",
            font=("Segoe UI", 11),
            fg="#ffffff",
            bg="#1e3a8a"
        )
        subtitle_lbl.pack(anchor=tk.W, fill=tk.X)
        left_header.bind("<Configure>", lambda event: (
            title_lbl.configure(wraplength=max(180, event.width - 10)),
            subtitle_lbl.configure(wraplength=max(180, event.width - 10))
        ))

        # Lado derecho del encabezado: Recuadro visualizador de ondas sonoras (Osciloscopio / Transmisor)
        right_header = tk.Frame(header_frame, bg="#1e3a8a")
        right_header.pack(side=tk.RIGHT, padx=5, pady=0)

        osc_box = tk.Frame(right_header, bg="#0f172a", bd=1, relief=tk.SOLID, padx=6, pady=4)
        osc_box.pack(side=tk.RIGHT)

        top_info = tk.Frame(osc_box, bg="#0f172a")
        top_info.pack(fill=tk.X, pady=(0, 2))

        lbl_wave_title = tk.Label(
            top_info,
            text="📡 MONITOR DE ONDA SONORA",
            font=("Segoe UI", 8, "bold"),
            fg="#38bdf8",
            bg="#0f172a"
        )
        lbl_wave_title.pack(side=tk.LEFT)

        self.lbl_wave_mode = tk.Label(
            top_info,
            text="● EN ESPERA",
            font=("Segoe UI", 8, "bold"),
            fg="#4ade80",
            bg="#0f172a"
        )
        self.lbl_wave_mode.pack(side=tk.RIGHT)

        # Canvas para dibujar las ondas osciloscópicas en tiempo real
        self.wave_canvas = tk.Canvas(
            osc_box,
            width=290,
            height=46,
            bg="#030712",
            highlightthickness=0
        )
        self.wave_canvas.pack()

        # Iniciar bucle de animación de la onda acústica en el encabezado
        self.wave_phase = 0.0
        self.is_recording = False
        self._animate_wave_header()

    def _scroll_panel(self, parent, fill_height=False):
        container = ttk.Frame(parent)
        container.pack(fill=tk.BOTH, expand=True)
        canvas = tk.Canvas(container, bg="#f1f5f9", highlightthickness=0)
        scrollbar = ttk.Scrollbar(container, orient=tk.VERTICAL, command=canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        canvas.configure(yscrollcommand=scrollbar.set)
        panel = ttk.Frame(canvas, padding=12)
        window = canvas.create_window((0, 0), window=panel, anchor="nw")
        def resize_panel(event=None):
            if fill_height:
                canvas.itemconfigure(window, height=max(canvas.winfo_height(), panel.winfo_reqheight()))
            canvas.configure(scrollregion=canvas.bbox("all"))
        def resize_canvas(event):
            canvas.itemconfigure(window, width=event.width)
            resize_panel()
        panel.bind("<Configure>", resize_panel)
        canvas.bind("<Configure>", resize_canvas)
        def wheel(event):
            widget = event.widget
            while widget is not None:
                if widget == container:
                    canvas.yview_scroll(int(-event.delta / 120), "units")
                    break
                widget = getattr(widget, "master", None)
        self.bind("<MouseWheel>", wheel, add="+")
        return panel

    def _build_main_layout(self):
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=8)
        capture_tab = ttk.Frame(self.notebook)
        calc_tab = ttk.Frame(self.notebook)
        results_tab = ttk.Frame(self.notebook, padding=10)
        self.notebook.add(capture_tab, text="Captura y análisis FFT")
        self.notebook.add(calc_tab, text="Cálculos y gráficas")
        self.notebook.add(results_tab, text="Tabla de Resultados experimentales")
        self.statistics_tab = StatisticsTab(self.notebook, self._scroll_panel)
        self.notebook.add(self.statistics_tab, text="Análisis estadístico")
        self.notebook.add(self.statistics_tab.results_tab, text="Resultados estadísticos globales")
        self.statistics_tab.refresh(self.registry.measurements)
        self.var_temperature_celsius = tk.StringVar(value="20")
        self.var_model = tk.StringVar(value="tube")
        self.var_length_cm = tk.StringVar(value="20")
        self.var_diameter_cm = tk.StringVar(value="")
        self.var_neck_diameter_cm = tk.StringVar(value="")
        self.var_neck_length_cm = tk.StringVar(value="")
        self.var_body_volume_ml = tk.StringVar(value="")
        self.var_water_volume_ml = tk.StringVar(value="")
        split = ttk.PanedWindow(capture_tab, orient=tk.HORIZONTAL)
        split.pack(fill=tk.BOTH, expand=True)
        controls = ttk.Frame(split, width=390)
        split.add(controls, weight=2)
        panel = self._scroll_panel(controls)
        geometry = ttk.LabelFrame(panel, text="1. Medición del recipiente y del aire", padding=10)
        geometry.pack(fill=tk.X, pady=(0, 10))
        selector = ttk.Frame(geometry)
        selector.pack(fill=tk.X)
        ttk.Radiobutton(selector, text="Tubo uniforme", variable=self.var_model, value="tube").pack(anchor=tk.W)
        ttk.Radiobutton(selector, text="Botella (Helmholtz)", variable=self.var_model, value="bottle").pack(anchor=tk.W)
        self.tube_fields = ttk.Frame(geometry)
        self.bottle_fields = ttk.Frame(geometry)
        def field(parent, label, variable):
            row = ttk.Frame(parent)
            row.pack(fill=tk.X, pady=4)
            ttk.Label(row, text=label, wraplength=230).pack(side=tk.LEFT)
            ttk.Entry(row, textvariable=variable, width=12).pack(side=tk.RIGHT)
        field(geometry, "Temperatura ambiental (°C)", self.var_temperature_celsius)
        field(self.tube_fields, "Longitud de aire L (cm)", self.var_length_cm)
        field(self.tube_fields, "Diámetro interior D (cm; NO el radio, opcional)", self.var_diameter_cm)
        ttk.Label(self.tube_fields, text="L: desde el agua hasta la abertura.\nD vacío: modelo ideal; con D: corrección 0.61r.", wraplength=340).pack(anchor=tk.W, pady=4)
        field(self.bottle_fields, "Diámetro interior del cuello D (cm)", self.var_neck_diameter_cm)
        field(self.bottle_fields, "Longitud física del cuello ℓ (cm)", self.var_neck_length_cm)
        field(self.bottle_fields, "Volumen del cuerpo (mL)", self.var_body_volume_ml)
        field(self.bottle_fields, "Volumen de agua (mL)", self.var_water_volume_ml)
        ttk.Label(self.bottle_fields, text="Vaire = Vcuerpo − Vagua  (mL)",
                  font=("Segoe UI", 9, "italic"), foreground="#475569",
                  wraplength=340).pack(anchor=tk.W, pady=(0, 4))
        self.lbl_length_m = ttk.Label(geometry, wraplength=340, foreground="#475569")
        self.lbl_length_m.pack(anchor=tk.W, pady=6)
        self.btn_measurement_guide = ttk.Button(panel, text="Cómo medir el tubo uniforme y obtener sus fórmulas",
                                               command=self._open_measurement_guide)
        self.btn_measurement_guide.pack(fill=tk.X, pady=(0, 10))
        audio_box = ttk.LabelFrame(panel, text="2. Captura de audio y análisis por FFT", padding=10)
        audio_box.pack(fill=tk.X)
        ttk.Label(audio_box, text="Genere sonido cerca de la abertura del tubo (soplando o con parlante) y capture la señal.", wraplength=340).pack(anchor=tk.W)
        self.var_duration = tk.StringVar(value="2.0")
        ttk.Label(audio_box, text="Duración (0.5–10 segundos)").pack(anchor=tk.W, pady=(8, 0))
        ttk.Spinbox(audio_box, from_=0.5, to=10, increment=0.5, textvariable=self.var_duration, width=10).pack(anchor=tk.W)
        self.btn_record = tk.Button(
            audio_box, text="🎙  CAPTURAR SONIDO CON MICRÓFONO (2.0 s)",
            command=self._capture_sound, bg="#2563eb", fg="#ffffff",
            activebackground="#1d4ed8", activeforeground="#ffffff",
            disabledforeground="#ffffff", font=("Segoe UI", 10, "bold"),
            relief=tk.FLAT, padx=12, pady=12, cursor="hand2"
        )
        self.btn_record.pack(fill=tk.X, pady=(8, 6))
        self.btn_record.bind("<Configure>", lambda event: self.btn_record.configure(wraplength=max(120, event.width - 24)))
        manual_row = ttk.Frame(audio_box)
        manual_row.pack(fill=tk.X)
        manual_row.columnconfigure((0, 1), weight=1, uniform="audio_buttons")
        for column, text, command in (
            (0, "📂 Cargar Audio WAV...", self._load_wav_file),
            (1, "▣ Ingresar Frecuencia Manual...", self._input_manual_freq),
        ):
            button = tk.Button(manual_row, text=text, command=command,
                               font=("Segoe UI", 9), bg="#f1f5f9", fg="#0f172a",
                               relief=tk.GROOVE, bd=2, padx=5, pady=7, cursor="hand2")
            button.grid(row=0, column=column, sticky="nsew", padx=(0, 4) if column == 0 else (4, 0))
            button.bind("<Configure>", lambda event, control=button: control.configure(wraplength=max(70, event.width - 14)))
        self.var_duration.trace_add("write", self._update_record_button)
        self.var_frequency = tk.StringVar(value="Frecuencia: pendiente de captura")
        ttk.Label(audio_box, textvariable=self.var_frequency, wraplength=340, font=("Segoe UI", 10, "bold")).pack(anchor=tk.W, pady=8)
        ttk.Label(audio_box, text="Revise los datos en la pestaña Cálculos y gráficas.", wraplength=340).pack(anchor=tk.W)

        # --- Parámetros editables del filtro y búsqueda FFT ---
        fft_params_box = ttk.LabelFrame(panel, text="3. Parámetros del filtro y búsqueda FFT", padding=10)
        fft_params_box.pack(fill=tk.X, pady=(10, 0))
        self.var_filter_low = tk.StringVar(value="40")
        self.var_filter_high = tk.StringVar(value="2500")
        self.var_search_min = tk.StringVar(value="50")
        self.var_search_max = tk.StringVar(value="2500")
        self.var_smoothing = tk.StringVar(value="0")
        for label_text, variable in (
            ("Corte inferior del filtro (Hz)", self.var_filter_low),
            ("Corte superior del filtro (Hz)", self.var_filter_high),
            ("Frecuencia mínima de búsqueda (Hz)", self.var_search_min),
            ("Frecuencia máxima de búsqueda (Hz)", self.var_search_max),
            ("Suavizado del espectro (Hz, 0 = sin suavizado)", self.var_smoothing),
        ):
            field(fft_params_box, label_text, variable)
        self.btn_reanalyze = tk.Button(
            fft_params_box, text="🔄 Reanalizar último audio",
            command=self._reanalyze_audio, font=("Segoe UI", 9, "bold"),
            bg="#7c3aed", fg="#ffffff", activebackground="#6d28d9",
            activeforeground="#ffffff", relief=tk.FLAT, padx=8, pady=8, cursor="hand2"
        )
        self.btn_reanalyze.pack(fill=tk.X, pady=(8, 0))
        for var in (self.var_filter_low, self.var_filter_high, self.var_search_min, self.var_search_max, self.var_smoothing):
            var.trace_add("write", self._on_fft_param_change)
        fft_panel = ttk.Frame(split, padding=8)
        split.add(fft_panel, weight=3)
        self.fig_fft = Figure(figsize=(6, 4), dpi=100, facecolor="#f8fafc")
        self.ax_fft = self.fig_fft.add_subplot(111)
        self.fig_fft.subplots_adjust(left=.15, right=.96, bottom=.16, top=.90)
        self.ax_fft.set(title="Espectro FFT", xlabel="Frecuencia (Hz)", ylabel="Amplitud", xlim=(50, 2500))
        self.ax_fft.grid(alpha=.3)
        self.canvas_fft = FigureCanvasTkAgg(self.fig_fft, master=fft_panel)
        self.canvas_fft.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        calc_tab.rowconfigure(0, weight=1)
        calc_tab.columnconfigure(0, weight=1, uniform="calc_columns")
        calc_tab.columnconfigure(1, weight=2, uniform="calc_columns")
        calc_left = ttk.Frame(calc_tab, width=1, height=1)
        calc_left.grid(row=0, column=0, sticky="nsew")
        calc_left.pack_propagate(False)
        calc_right = ttk.Frame(calc_tab, padding=8, width=1, height=1)
        calc_right.grid(row=0, column=1, sticky="nsew")
        calc_right.pack_propagate(False)
        calc_footer = ttk.Frame(calc_left, padding=(12, 8, 28, 12))
        calc_footer.pack(side=tk.BOTTOM, fill=tk.X)
        calc_panel = self._scroll_panel(calc_left, fill_height=True)
        calc_box = ttk.LabelFrame(calc_panel, text="3. Cálculos de la velocidad del sonido", padding=12)
        calc_box.pack(fill=tk.BOTH, expand=True)
        def wrap_calculations(event):
            for widget in calc_box.winfo_children():
                if isinstance(widget, ttk.Label):
                    widget.configure(wraplength=max(100, event.width - 28))
        calc_box.bind("<Configure>", wrap_calculations)
        formula_frame = tk.Frame(calc_box, bg="#eff6ff", highlightbackground="#334155",
                                 highlightthickness=1, height=150)
        formula_frame.pack(fill=tk.X, pady=(0, 12))
        formula_frame.pack_propagate(False)
        self.formula_figure = Figure(figsize=(3, 1.5), dpi=100, facecolor="#eff6ff")
        self.formula_canvas = FigureCanvasTkAgg(self.formula_figure, master=formula_frame)
        self.formula_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)
        self.formula_canvas.get_tk_widget().bind("<Configure>",
            lambda event: self._fit_formula_canvas(self.formula_canvas), add="+")
        self.lbl_sustitucion = ttk.Label(calc_box, text="Capture audio o ingrese una frecuencia.", wraplength=700,
                                        font=("Segoe UI", 10, "bold"))
        self.lbl_sustitucion.pack(anchor=tk.W, pady=4)
        self.lbl_resultado_v = ttk.Label(calc_box, text="Velocidad experimental: pendiente", font=("Segoe UI", 13, "bold"), foreground="#2563eb")
        self.lbl_resultado_v.pack(anchor=tk.W, pady=4)
        self.lbl_comparacion = ttk.Label(calc_box, wraplength=700,
            text="")
        self.lbl_comparacion.pack(anchor=tk.W, pady=4)
        self.lbl_theory_title = ttk.Label(calc_box, wraplength=700, font=("Segoe UI", 10, "bold"))
        self.lbl_theory_title.pack(anchor=tk.W, pady=(12, 4))
        self.lbl_theory_formula = ttk.Label(calc_box, wraplength=300,
                                            font=("Segoe UI", 10, "italic"), foreground="#0f172a")
        self.lbl_theory_formula.pack(anchor=tk.W, pady=(0, 8))
        self.btn_register = tk.Button(
            calc_footer, text="Registrar esta medición", state=tk.DISABLED,
            command=self._register_measurement, bg="#16a34a", fg="#ffffff",
            activebackground="#15803d", activeforeground="#ffffff",
            disabledforeground="#ffffff", font=("Segoe UI", 11, "bold"),
            relief=tk.FLAT, padx=12, pady=18, cursor="hand2")
        self.btn_register.pack(fill=tk.X)
        self.fig = Figure(figsize=(8, 5.2), dpi=100, facecolor="#f8fafc")
        self.fig.subplots_adjust(left=.13, right=.96, top=.92, bottom=.12, hspace=.65)
        self.ax_comp = self.fig.add_subplot(211)
        self.ax_speed = self.fig.add_subplot(212)
        self.canvas = FigureCanvasTkAgg(self.fig, master=calc_right)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        table_box = ttk.LabelFrame(results_tab, text="4. Resultados experimentales", padding=8)
        table_box.pack(fill=tk.BOTH, expand=True)
        columns = {"id": "#", "model": "Modelo", "length_cm": "L (cm)", "diameter_cm": "D (cm)",
                   "frequency_hz": "f medida (Hz)", "theoretical_frequency_hz": "f teórica (Hz)",
                   "formula": "Fórmula", "v_calculada": "v exp (m/s)", "error_pct": "Error (%)",
                   "neck_length_cm": "ℓ cuello (cm)", "body_volume_ml": "Cuerpo (mL)",
                   "water_volume_ml": "Agua (mL)", "air_volume_ml": "Aire (mL)",
                   "temperature_celsius": "T (°C)", "v_teorica": "v teórica (m/s)"}
        self.table_columns = list(columns)
        self.tree = ttk.Treeview(table_box, columns=self.table_columns, show="headings", height=10)
        for key, label in columns.items():
            self.tree.heading(key, text=label)
            self.tree.column(key, width=260 if key == "formula" else 110, minwidth=60, stretch=False)
        table_box.rowconfigure(0, weight=1)
        table_box.columnconfigure(0, weight=1)
        self.tree.grid(row=0, column=0, sticky="nsew")
        sy = ttk.Scrollbar(table_box, orient=tk.VERTICAL, command=self.tree.yview)
        sx = ttk.Scrollbar(table_box, orient=tk.HORIZONTAL, command=self.tree.xview)
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        self.tree.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        buttons = ttk.Frame(results_tab)
        buttons.pack(fill=tk.X, pady=8)
        ttk.Button(buttons, text="Eliminar seleccionado", command=self._delete_selected).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Limpiar tabla", command=self._clear_table).pack(side=tk.LEFT, padx=4)
        ttk.Button(buttons, text="Exportar CSV", command=self._export_csv).pack(side=tk.RIGHT, padx=4)
        for variable in (self.var_temperature_celsius, self.var_model, self.var_length_cm, self.var_diameter_cm, self.var_neck_diameter_cm,
                         self.var_neck_length_cm, self.var_body_volume_ml, self.var_water_volume_ml):
            variable.trace_add("write", self._on_geometry_change)
        self._on_geometry_change()

    @staticmethod
    def _number(variable):
        value = float(variable.get().strip().replace(",", "."))
        if not np.isfinite(value):
            raise ValueError("Ingrese valores numéricos finitos.")
        return value

    def _geometry_inputs(self):
        temperature = self._number(self.var_temperature_celsius)
        calculate_reference_speed(temperature)
        if self.var_model.get() == "tube":
            return dict(model="tube", temperature_celsius=temperature, length_cm=self._number(self.var_length_cm),
                        diameter_cm=None if not self.var_diameter_cm.get().strip() else self._number(self.var_diameter_cm))
        return dict(model="bottle", temperature_celsius=temperature, diameter_cm=self._number(self.var_neck_diameter_cm),
                    neck_length_cm=self._number(self.var_neck_length_cm),
                    body_volume_ml=self._number(self.var_body_volume_ml),
                    water_volume_ml=self._number(self.var_water_volume_ml))

    def _calculate(self, frequency):
        inputs = self._geometry_inputs()
        reference = calculate_reference_speed(inputs["temperature_celsius"])
        if inputs["model"] == "tube":
            return calculate_speed_of_sound(inputs["length_cm"] / 100, frequency, theoretical_speed=reference,
                diameter_meters=None if inputs["diameter_cm"] is None else inputs["diameter_cm"] / 100)
        return calculate_helmholtz_speed(inputs["diameter_cm"] / 100, inputs["neck_length_cm"] / 100,
            inputs["body_volume_ml"] * 1e-6, inputs["water_volume_ml"] * 1e-6, frequency, theoretical_speed=reference)

    def _on_geometry_change(self, *args):
        self.btn_measurement_guide.config(text=("Cómo medir la botella y obtener sus fórmulas"
            if self.var_model.get() == "bottle" else "Cómo medir el tubo uniforme y obtener sus fórmulas"))
        self.tube_fields.pack_forget()
        self.bottle_fields.pack_forget()
        fields = self.tube_fields if self.var_model.get() == "tube" else self.bottle_fields
        fields.pack(fill=tk.X, before=self.lbl_length_m)
        self.current_calc_result = None
        self.btn_register.config(state=tk.DISABLED)
        self.lbl_resultado_v.config(text="Velocidad experimental: pendiente")
        self._update_theory_explanation()
        try:
            preview = self._calculate(1.0)
            if preview["model"] == "tube":
                self.lbl_length_m.config(text=f"L = {preview['length_meters']:.6g} m; r = {preview['radius_meters']:.6g} m")
            else:
                self.lbl_length_m.config(text=f"V aire = {preview['air_volume_m3'] * 1e6:.6g} mL = {preview['air_volume_m3']:.6g} m³")
            self.lbl_sustitucion.config(text="Capture audio o ingrese una frecuencia.")
            if self.current_freq_hz > 0:
                self._compute_and_display()
        except (ValueError, TypeError, tk.TclError) as error:
            self.lbl_length_m.config(text="Complete las medidas del recipiente.")
            self.lbl_sustitucion.config(text="Datos incompletos o invalidos.")
        self._update_comparison_plot()

    def _fit_formula_canvas(self, canvas):
        # MathText keeps subscripts and fractions together; shrink whole equations
        # to the available width instead of breaking them between lines.
        figure = canvas.figure
        for text in figure.texts:
            text.set_fontsize(12)
        canvas.draw()
        renderer = canvas.get_renderer()
        available = max(1, figure.bbox.width - 20)
        for text in figure.texts:
            width = text.get_window_extent(renderer).width
            if width > available:
                text.set_fontsize(12 * available / width)
        canvas.draw_idle()

    def _set_formula_lines(self, canvas, lines):
        figure = canvas.figure
        figure.clear()
        for index, line in enumerate(lines):
            figure.text(.5, 1 - (index + .5) / len(lines), line,
                        ha="center", va="center", color="#1e40af", fontsize=12)
        self._fit_formula_canvas(canvas)

    def _update_theory_explanation(self):
        if self.var_model.get() == "bottle":
            name = "Botella"
            speed_lines = [r"$v = 2\pi \cdot f_H \cdot \sqrt{\frac{V_{\mathrm{aire}} \cdot L_{\mathrm{ef}}}{A}}$"]
            frequency = "fₕ = (v teórica / 2π) × √[A / (Vaire × Lef)]"
        else:
            speed_lines = [
                r"$f_1 = v / (4 \cdot L)\quad\Rightarrow\quad v = 4\cdot L\cdot f_1$",
                r"$v \approx 4\cdot f_1\cdot (L + 0.61\cdot r)$",
            ]
            if self.var_diameter_cm.get().strip():
                name = "Tubo con corrección del radio"
                frequency = "f₁ ≈ v teórica / [4 × (L + 0.61 × r)]"
            else:
                name = "Tubo ideal"
                frequency = "f₁ = v teórica / (4 × L)"
        self.lbl_theory_title.config(text=f"Frecuencia Teórica del modelo ({name})")
        self._set_formula_lines(self.formula_canvas, speed_lines)
        try:
            temperature = self._number(self.var_temperature_celsius)
            reference = calculate_reference_speed(temperature)
            comparison = ("Velocidad teórica del sonido en el aire:\n"
                          "v teórica = 331.3 + 0.606 × T\n"
                          f"v teórica = 331.3 + 0.606 × ({temperature:g}) = {reference:.2f} m/s\n"
                          "T: temperatura ambiental en °C.")
            if self.current_calc_result is not None:
                comparison += f"\nError experimental: {self.current_calc_result['error_porcentual']:.2f} %"
            self.lbl_comparacion.config(text=comparison)
            preview = self._calculate(1.0)
            if preview["model"] == "bottle":
                substitution = (f"fₕ = ({reference:.2f} / 2π) × √["
                                f"{preview['area_m2']:.6g} / ({preview['air_volume_m3']:.6g} × "
                                f"{preview['effective_length_meters']:.6g})]")
            else:
                substitution = f"f₁ = {reference:.2f} / (4 × {preview['effective_length_meters']:.6g})"
            frequency += f"\n{substitution}\nf teórica = {preview['theoretical_frequency_hz']:.2f} Hz"
        except (ValueError, TypeError, tk.TclError):
            # Do not retain a previous theoretical result for invalid inputs.
            try:
                calculate_reference_speed(self._number(self.var_temperature_celsius))
            except (ValueError, TypeError, tk.TclError):
                self.lbl_comparacion.config(text="v teórica = 331.3 + 0.606 × T\nIngrese una temperatura ambiental válida (°C).")
            frequency += "\nComplete los datos para calcular la frecuencia teórica."
        self.lbl_theory_formula.config(text=frequency)

    def _open_measurement_guide(self):
        from PIL import Image, ImageTk
        model = self.var_model.get()
        filename = ("Guía visual de resonancia de Helmholtz.png" if model == "bottle"
                    else "Guia visual del tubo uniforme.png")
        path = Path(__file__).resolve().parent.parent / "imagenes" / filename
        try:
            with Image.open(path) as source:
                original = source.convert("RGB")
        except (OSError, ValueError) as error:
            messagebox.showerror("Guía de medición", f"No se pudo abrir la guía {filename}: {error}", parent=self)
            return
        viewer = tk.Toplevel(self)
        viewer.title("Cómo medir: " + ("Botella" if model == "bottle" else "Tubo uniforme"))
        width = min(1200, max(600, self.winfo_screenwidth() - 100))
        height = min(850, max(400, self.winfo_screenheight() - 120))
        viewer.geometry(f"{width}x{height}")
        toolbar = ttk.Frame(viewer, padding=8)
        toolbar.pack(fill=tk.X)
        area = ttk.Frame(viewer)
        area.pack(fill=tk.BOTH, expand=True)
        area.rowconfigure(0, weight=1)
        area.columnconfigure(0, weight=1)
        canvas = tk.Canvas(area, bg="#e2e8f0", highlightthickness=0)
        canvas.grid(row=0, column=0, sticky="nsew")
        sy = ttk.Scrollbar(area, orient=tk.VERTICAL, command=canvas.yview)
        sx = ttk.Scrollbar(area, orient=tk.HORIZONTAL, command=canvas.xview)
        sy.grid(row=0, column=1, sticky="ns")
        sx.grid(row=1, column=0, sticky="ew")
        canvas.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)
        item = canvas.create_image(0, 0, anchor="nw")
        state = {"fit": True, "scale": 1.0}
        def render(event=None):
            if state["fit"]:
                state["scale"] = min(canvas.winfo_width() / original.width,
                                     canvas.winfo_height() / original.height, 1.0)
            size = (max(1, round(original.width * state["scale"])),
                    max(1, round(original.height * state["scale"])))
            photo = ImageTk.PhotoImage(original.resize(size, Image.Resampling.LANCZOS), master=viewer)
            canvas.image = photo
            canvas.itemconfigure(item, image=photo)
            canvas.configure(scrollregion=(0, 0, *size))
        def zoom(factor):
            state["fit"] = False
            state["scale"] = min(3.0, max(.1, state["scale"] * factor))
            render()
        def fit():
            state["fit"] = True
            render()
            canvas.xview_moveto(0)
            canvas.yview_moveto(0)
        ttk.Button(toolbar, text="Ajustar a ventana", command=fit).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Acercar +", command=lambda: zoom(1.25)).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Alejar −", command=lambda: zoom(.8)).pack(side=tk.LEFT, padx=4)
        ttk.Button(toolbar, text="Cerrar", command=viewer.destroy).pack(side=tk.RIGHT, padx=4)
        canvas.bind("<Configure>", render)
        viewer.bind("<Escape>", lambda event: viewer.destroy())

    def _build_status_bar(self):
        self.status_bar = tk.Frame(self, bg="#e2e8f0", bd=1, relief=tk.SUNKEN, padx=8, pady=4)
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)

        self.lbl_status = tk.Label(self.status_bar, text="Listo para capturar sonido y realizar cálculos.", bg="#e2e8f0", fg="#334155", font=("Segoe UI", 9))
        self.lbl_status.pack(side=tk.LEFT)

        lbl_info = tk.Label(self.status_bar, text="Proyecto: Medición de la velocidad del sonido • Python + FFT", bg="#e2e8f0", fg="#64748b", font=("Segoe UI", 8))
        lbl_info.pack(side=tk.RIGHT)

    def set_status(self, text: str):
        self.lbl_status.config(text=text)

    def _update_record_button(self, *args):
        if self.is_recording:
            return
        try:
            duration = self._number(self.var_duration)
            label = f" ({duration:.1f} s)" if .5 <= duration <= 10 else ""
        except (ValueError, tk.TclError):
            label = ""
        self.btn_record.config(text=f"🎙  CAPTURAR SONIDO CON MICRÓFONO{label}", bg="#2563eb")

    def _capture_sound(self):
        try:
            duration = self._number(self.var_duration)
            if not .5 <= duration <= 10:
                raise ValueError("La duración debe estar entre 0.5 y 10 segundos.")
            self.is_recording = True
            self.btn_record.config(state=tk.DISABLED, text=f"🎙  GRABANDO AUDIO... ({duration:.1f} s)", bg="#d97706")
            self.update()
            audio = record_microphone(duration_sec=duration, sample_rate=44100)
            self._process_audio_signal(audio, 44100)
        except Exception as error:
            self._invalidate_frequency()
            messagebox.showerror("Captura de audio", str(error))
        finally:
            self.is_recording = False
            self.btn_record.config(state=tk.NORMAL)
            self._update_record_button()

    def _animate_wave_header(self):
        """Dibuja en tiempo real las ondas acústicas en el recuadro del encabezado."""
        if not hasattr(self, "wave_canvas") or not self.wave_canvas.winfo_exists():
            return

        c = self.wave_canvas
        w = 290
        h = 46
        mid_y = h / 2.0

        c.delete("all")

        # Rejilla sutil de fondo (estilo osciloscopio / transmisor)
        c.create_line(0, mid_y, w, mid_y, fill="#1e293b", dash=(3, 3))
        for gx in range(40, w, 40):
            c.create_line(gx, 0, gx, h, fill="#0f172a", dash=(2, 4))

        if getattr(self, "is_recording", False):
            # Estado grabando: onda acústica vibrante y enérgica en color ámbar
            self.lbl_wave_mode.config(text="● GRABANDO...", fg="#f59e0b")
            self.wave_phase += 0.35
            pts = []
            for x in range(0, w, 3):
                y = mid_y + (15.0 * np.sin(0.08 * x - self.wave_phase) +
                             6.0 * np.sin(0.18 * x + self.wave_phase * 1.5) +
                             np.random.normal(0, 1.2))
                y = max(3.0, min(h - 3.0, y))
                pts.extend([x, y])
            if len(pts) >= 4:
                c.create_line(*pts, fill="#fbbf24", width=2, smooth=True)

        elif self.last_audio_data is not None and len(self.last_audio_data) > 0:
            # Estado con audio capturado: muestra la forma de onda real registrada
            f_txt = f"f₁ = {self.current_freq_hz:.1f} Hz" if self.current_freq_hz > 0 else "SEÑAL ACTIVA"
            self.lbl_wave_mode.config(text=f"● {f_txt}", fg="#38bdf8")

            # Tomar una ventana representativa del audio real y mapear a los 290 px
            audio = self.last_audio_data
            step = max(1, len(audio) // w)
            sample_segment = audio[::step][:w]
            max_amp = np.max(np.abs(sample_segment)) if len(sample_segment) > 0 else 1.0
            scale = (mid_y - 4.0) / max(0.02, max_amp)

            pts = []
            for x, s in enumerate(sample_segment):
                y = mid_y - s * scale
                y = max(2.0, min(h - 2.0, y))
                pts.extend([x, y])

            if len(pts) >= 4:
                c.create_line(*pts, fill="#38bdf8", width=1.8, smooth=True)

        else:
            # Estado en espera: onda senoidal suave y continua en color verde cian
            self.lbl_wave_mode.config(text="● EN ESPERA", fg="#4ade80")
            self.wave_phase += 0.08
            pts = []
            for x in range(0, w, 4):
                y = mid_y + 11.0 * np.sin(0.06 * x - self.wave_phase)
                pts.extend([x, y])
            if len(pts) >= 4:
                c.create_line(*pts, fill="#4ade80", width=1.6, smooth=True)

        # Reprogramar siguiente frame cada 45 ms (~22 fps suaves sin saturar CPU)
        self.after(45, self._animate_wave_header)

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

    def _invalidate_frequency(self):
        self.current_freq_hz = 0.0
        self.current_calc_result = None
        self.last_audio_data = None
        # Note: last_audio_raw and last_audio_sr are NOT cleared here so that
        # the user can re-analyze with different FFT parameters.
        self.var_frequency.set("Frecuencia: pendiente de captura")
        self.btn_register.config(state=tk.DISABLED)
        self.lbl_resultado_v.config(text="Velocidad experimental: pendiente")
        self.ax_fft.clear()
        try:
            _, _, s_min, s_max, _ = self._get_fft_params()
        except Exception:
            s_min, s_max = 50, 2500
        self.ax_fft.set(title="Espectro FFT: sin captura válida", xlabel="Frecuencia (Hz)", ylabel="Amplitud", xlim=(s_min, s_max))
        self.canvas_fft.draw_idle()

    def _input_manual_freq(self):
        from tkinter import simpledialog
        text = simpledialog.askstring("Frecuencia manual", "Frecuencia de resonancia (Hz):", parent=self)
        if text is None:
            return
        try:
            frequency = float(text.strip().replace(",", "."))
            if not np.isfinite(frequency) or frequency <= 0:
                raise ValueError("Ingrese una frecuencia finita mayor a cero.")
            self._invalidate_frequency()
            self.current_freq_hz = frequency
            self.var_frequency.set(f"Frecuencia manual: {frequency:.2f} Hz")
            self._on_geometry_change()
        except ValueError as error:
            messagebox.showerror("Frecuencia manual", str(error))

    def _get_fft_params(self):
        """Lee y valida los parámetros del filtro y búsqueda FFT de la interfaz."""
        filter_low = self._number(self.var_filter_low)
        filter_high = self._number(self.var_filter_high)
        search_min = self._number(self.var_search_min)
        search_max = self._number(self.var_search_max)
        smoothing = self._number(self.var_smoothing)
        if filter_low <= 0 or filter_high <= 0 or search_min <= 0 or search_max <= 0:
            raise ValueError("Los parámetros de frecuencia deben ser positivos.")
        if filter_low >= filter_high:
            raise ValueError("El corte inferior del filtro debe ser menor que el corte superior.")
        if smoothing < 0:
            raise ValueError("El suavizado debe ser ≥ 0.")
        if search_min >= search_max:
            raise ValueError("La frecuencia mínima debe ser menor que la máxima.")
        return filter_low, filter_high, search_min, search_max, smoothing

    def _process_audio_signal(self, audio, sample_rate=44100):
        self._invalidate_frequency()
        audio = np.asarray(audio)
        if audio.size == 0 or not np.all(np.isfinite(audio)) or np.max(np.abs(audio)) <= 1e-8:
            raise ValueError("El audio está vacío o no contiene una señal válida.")
        # Guardar audio crudo para poder reanalizar con otros parámetros
        self.last_audio_raw = audio.copy()
        self.last_audio_sr = int(sample_rate)
        self._analyze_with_current_params(audio, sample_rate)

    def _analyze_with_current_params(self, audio, sample_rate):
        """Filtra, calcula FFT y detecta el pico con los parámetros actuales de la GUI."""
        try:
            filter_low, filter_high, search_min, search_max, smoothing = self._get_fft_params()
        except (ValueError, tk.TclError) as error:
            raise ValueError(f"Parámetros FFT inválidos: {error}")
        filtered = filter_ambient_noise(audio, sample_rate=sample_rate,
                                        low_cutoff=filter_low, high_cutoff=filter_high)
        freqs, mags = analyze_fft(filtered, sample_rate=sample_rate)
        peak = detect_resonance_frequency(freqs, mags, min_freq=search_min, max_freq=search_max,
                                          smoothing_hz=smoothing, sample_rate=sample_rate,
                                          n_samples=len(audio))
        if peak["frequency_hz"] <= 0 or peak["amplitude"] <= 1e-8:
            raise ValueError(f"No se encontró un pico entre {search_min:.0f} y {search_max:.0f} Hz.")
        self.last_audio_data, self.last_freqs, self.last_mags = audio, freqs, mags
        self.current_freq_hz = peak["frequency_hz"]
        # Indicar si se usó fallback
        if peak.get("fallback", False):
            self.var_frequency.set(f"Pico FFT: {self.current_freq_hz:.2f} Hz ⚠ pico no prominente; revise el espectro")
        else:
            self.var_frequency.set(f"Pico dominante FFT: {self.current_freq_hz:.2f} Hz")
        # --- Dibujar espectro con picos prominentes ---
        self.ax_fft.clear()
        mask = (freqs >= search_min) & (freqs <= search_max)
        self.ax_fft.plot(freqs[mask], mags[mask], color="#2563eb")
        self.ax_fft.plot([self.current_freq_hz], [peak["amplitude"]], "ro",
                         markersize=8, label=f"Pico elegido: {self.current_freq_hz:.2f} Hz")
        # Marcar los 3 picos más prominentes con otro marcador
        for i, pp in enumerate(peak.get("prominent_peaks", [])):
            if abs(pp["frequency_hz"] - self.current_freq_hz) > 0.01:
                self.ax_fft.plot([pp["frequency_hz"]], [pp["amplitude"]], "g^",
                                 markersize=7)
                self.ax_fft.annotate(f'{pp["frequency_hz"]:.1f} Hz',
                                     (pp["frequency_hz"], pp["amplitude"]),
                                     textcoords="offset points", xytext=(4, 6),
                                     fontsize=7, color="#16a34a")
        self.ax_fft.set(title="Espectro FFT", xlabel="Frecuencia (Hz)", ylabel="Amplitud",
                        xlim=(search_min, search_max))
        self.ax_fft.grid(alpha=.3)
        self.ax_fft.legend(fontsize=8)
        self.canvas_fft.draw_idle()
        self._on_geometry_change()
        self.set_status("Audio analizado. Revise el modelo y registre la medición en Cálculos y gráficas.")

    def _on_fft_param_change(self, *args):
        """Reanaliza automáticamente el último audio si los parámetros son válidos."""
        if self.last_audio_raw is None:
            return
        try:
            self._invalidate_frequency()
            self._analyze_with_current_params(self.last_audio_raw, self.last_audio_sr)
        except Exception:
            # Mientras el usuario escribe puede haber valores incompletos temporalmente
            pass

    def _reanalyze_audio(self):
        """Re-procesa el último audio cargado/grabado con los parámetros FFT actuales."""
        if self.last_audio_raw is None:
            messagebox.showinfo("Reanalizar", "No hay audio cargado. Capture o cargue un archivo primero.")
            return
        try:
            self._invalidate_frequency()
            self._analyze_with_current_params(self.last_audio_raw, self.last_audio_sr)
            self.set_status("Audio reanalizado con los parámetros actuales.")
        except Exception as e:
            self._invalidate_frequency()
            messagebox.showerror("Reanalizar", str(e))

    def _compute_and_display(self):
        calc = self._calculate(self.current_freq_hz)
        self.current_calc_result = calc
        self.lbl_sustitucion.config(text=calc["sustitucion_text"])
        self.lbl_resultado_v.config(text=f"Velocidad experimental: {calc['v_experimental']:.2f} m/s")
        self._update_theory_explanation()
        self.btn_register.config(state=tk.NORMAL)

    def _register_measurement(self, silent=False):
        try:
            if self.current_freq_hz <= 0:
                raise ValueError("Capture audio o ingrese una frecuencia primero.")
            self._compute_and_display()
            try:
                filter_low, filter_high, search_min, search_max, smoothing = self._get_fft_params()
            except Exception:
                filter_low = filter_high = search_min = search_max = smoothing = None
            sr = self.last_audio_sr if self.last_audio_raw is not None else None
            entry = self.registry.add_measurement(
                frequency_hz=self.current_freq_hz,
                sample_rate=sr,
                filter_low_cutoff_hz=filter_low,
                filter_high_cutoff_hz=filter_high,
                search_min_hz=search_min,
                search_max_hz=search_max,
                smoothing_hz=smoothing,
                **self._geometry_inputs()
            )
            self._refresh_table()
            self._update_comparison_plot()
            children = self.tree.get_children()
            self.tree.selection_set(children[-1])
            self.tree.see(children[-1])
            self.set_status(f"Medición #{entry['id']} registrada: {entry['v_calculada']:.2f} m/s.")
        except (ValueError, TypeError, tk.TclError) as error:
            self.current_calc_result = None
            self.btn_register.config(state=tk.DISABLED)
            messagebox.showerror("Datos inválidos", str(error))

    def _refresh_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for entry in self.registry.measurements:
            values = []
            for column in self.table_columns:
                value = entry.get(column)
                if column == "model":
                    value = "Tubo" if value == "tube" else "Botella"
                elif isinstance(value, float):
                    value = f"{value:.3f}"
                values.append("—" if value is None else value)
            self.tree.insert("", tk.END, values=values)
        self.statistics_tab.refresh(self.registry.measurements)

    def _update_comparison_plot(self):
        self.ax_comp.clear()
        self.ax_speed.clear()
        model = self.var_model.get()
        records = [m for m in self.registry.measurements if m["model"] == model]
        # A continuous curve uses only the current geometry. Historical points use
        # their own stored theoretical frequency, even if the dimensions changed.
        try:
            geometry = self._geometry_inputs()
            reference = self._calculate(1.0)["v_theoretical"]
            if model == "tube":
                xs = np.linspace(min([8] + [m["length_cm"] for m in records] + [geometry["length_cm"]]),
                                 max([50] + [m["length_cm"] for m in records] + [geometry["length_cm"]]), 160)
                diameter = None if geometry["diameter_cm"] is None else geometry["diameter_cm"] / 100
                ys = [calculate_theoretical_frequency(x / 100, sound_speed=reference, diameter_meters=diameter) for x in xs]
            else:
                upper = max([geometry["body_volume_ml"]] + [m["air_volume_ml"] for m in records])
                lower = min([upper * .1, geometry["body_volume_ml"] - geometry["water_volume_ml"]] + [m["air_volume_ml"] for m in records])
                xs = np.linspace(lower, upper, 160)
                ys = [calculate_helmholtz_frequency(geometry["diameter_cm"] / 100,
                      geometry["neck_length_cm"] / 100, x * 1e-6, 0, sound_speed=reference) for x in xs]
            self.ax_comp.plot(xs, ys, "g--", label=f"Teoría actual: {geometry['temperature_celsius']:g} °C")
        except (ValueError, TypeError, tk.TclError):
            pass
        key = "length_cm" if model == "tube" else "air_volume_ml"
        xs = [m[key] for m in records]
        if records:
            self.ax_comp.scatter(xs, [m["frequency_hz"] for m in records], label="Frecuencia medida", color="#2563eb")
            self.ax_comp.scatter(xs, [m["theoretical_frequency_hz"] for m in records], label="Teoría de cada registro", marker="x", color="#d97706")
            self.ax_speed.scatter(xs, [m["v_calculada"] for m in records], label="Velocidad medida", color="#2563eb")
        try:
            temperature = self._number(self.var_temperature_celsius)
            reference = calculate_reference_speed(temperature)
            self.ax_speed.axhline(reference, linestyle="--", color="green",
                                  label=f"Referencia: {reference:.2f} m/s ({temperature:g} °C)")
        except (ValueError, TypeError, tk.TclError):
            pass
        if records:
            self.ax_speed.scatter(xs, [m["v_teorica"] for m in records],
                                  label="Referencia de cada registro", marker="x", color="#d97706")
        xlabel = "Longitud de aire L (cm)" if model == "tube" else "Volumen de aire V (mL)"
        container_name = "Tubo uniforme" if model == "tube" else "Botella"
        self.ax_comp.set(title=f"Frecuencia vs Nivel de Aire ({container_name})", xlabel=xlabel, ylabel="Frecuencia (Hz)")
        self.ax_speed.set(xlabel=xlabel, ylabel="Velocidad (m/s)")
        for ax in (self.ax_comp, self.ax_speed):
            ax.grid(alpha=.3)
            if ax.get_legend_handles_labels()[0]:
                ax.legend(fontsize=8)
        self.canvas.draw_idle()

    def _delete_selected(self):
        selected = self.tree.selection()
        if not selected:
            return
        index = int(self.tree.item(selected[0])["values"][0]) - 1
        self.registry.remove_measurement(index)
        self._refresh_table()
        self._update_comparison_plot()

    def _clear_table(self):
        if self.registry.measurements and messagebox.askyesno("Confirmar", "¿Limpiar todas las mediciones?"):
            self.registry.clear()
            self._refresh_table()
            self._update_comparison_plot()

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
