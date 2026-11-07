"""
Pestaña 3: Aplicaciones Prácticas (Sensor de Nivel de Agua y Afinador Digital)
"""

import tkinter as tk
from tkinter import ttk
import numpy as np

from core.physics_engine import (
    estimate_water_level,
    frequency_to_musical_note,
    fundamental_frequency,
)
from .styles import COLORS, FONTS


class ApplicationsTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # Contenedor con dos grandes bloques: Izquierda = Sensor de Nivel, Derecha = Afinador Digital
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # -------------------------------------------------------------
        # 1. SENSOR ACÚSTICO DE NIVEL DE AGUA
        # -------------------------------------------------------------
        frame_water = ttk.LabelFrame(paned, text="  1. Sensor Acústico de Nivel de Líquidos  ", padding=12)
        paned.add(frame_water, weight=1)

        desc_water = (
            "Aprovecha que la columna de aire resuena a mayor frecuencia a medida que sube el nivel de agua. "
            "Permite estimar el volumen y altura del líquido sin contacto físico invasivo."
        )
        ttk.Label(frame_water, text=desc_water, wraplength=380, justify=tk.LEFT, font=FONTS["body"]).pack(anchor=tk.W, pady=(0, 10))

        # Parámetros del recipiente
        param_grid = ttk.Frame(frame_water)
        param_grid.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(param_grid, text="Altura Total del Depósito H (cm):", font=FONTS["body_bold"]).grid(row=0, column=0, sticky=tk.W, pady=3)
        self.var_tank_height = tk.DoubleVar(value=50.0)
        spin_h = ttk.Spinbox(param_grid, from_=10.0, to=300.0, increment=5.0, textvariable=self.var_tank_height, width=8, command=self._update_water_calc)
        spin_h.grid(row=0, column=1, sticky=tk.W, padx=5, pady=3)

        ttk.Label(param_grid, text="Radio Interno del Tubo r (cm):", font=FONTS["body_bold"]).grid(row=1, column=0, sticky=tk.W, pady=3)
        self.var_tank_radius = tk.DoubleVar(value=2.5)
        spin_r = ttk.Spinbox(param_grid, from_=0.5, to=50.0, increment=0.5, textvariable=self.var_tank_radius, width=8, command=self._update_water_calc)
        spin_r.grid(row=1, column=1, sticky=tk.W, padx=5, pady=3)

        ttk.Label(param_grid, text="Frecuencia Resonante Medida (Hz):", font=FONTS["body_bold"]).grid(row=2, column=0, sticky=tk.W, pady=3)
        self.var_input_freq = tk.DoubleVar(value=380.0)
        self.spin_freq = ttk.Spinbox(param_grid, from_=50.0, to=2000.0, increment=5.0, textvariable=self.var_input_freq, width=8, command=self._update_water_calc)
        self.spin_freq.grid(row=2, column=1, sticky=tk.W, padx=5, pady=3)

        btn_sync = ttk.Button(frame_water, text="🔄 Tomar Frecuencia de la Captura Actual", command=self._sync_with_realtime)
        btn_sync.pack(anchor=tk.W, pady=(0, 10))

        # Contenedor visual del tanque
        display_frame = ttk.Frame(frame_water)
        display_frame.pack(fill=tk.BOTH, expand=True, pady=5)

        # Canvas con representación gráfica del tubo/tanque
        self.tank_canvas = tk.Canvas(display_frame, width=130, height=220, bg="#ffffff", bd=1, relief=tk.SOLID)
        self.tank_canvas.pack(side=tk.LEFT, padx=(0, 15), pady=5)

        # Indicadores numéricos del nivel
        info_frame = ttk.Frame(display_frame)
        info_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, pady=5)

        ttk.Label(info_frame, text="NIVEL DE AGUA ESTIMADO:", font=FONTS["metric_label"], foreground=COLORS["text_muted"]).pack(anchor=tk.W)
        self.lbl_water_cm = tk.Label(info_frame, text="-- cm", font=FONTS["metric_value"], fg=COLORS["primary"], bg=COLORS["bg_main"])
        self.lbl_water_cm.pack(anchor=tk.W, pady=(0, 6))

        ttk.Label(info_frame, text="COLUMNA DE AIRE RESTANTE:", font=FONTS["metric_label"], foreground=COLORS["text_muted"]).pack(anchor=tk.W)
        self.lbl_air_cm = tk.Label(info_frame, text="-- cm", font=FONTS["subtitle"], fg=COLORS["secondary"], bg=COLORS["bg_main"])
        self.lbl_air_cm.pack(anchor=tk.W, pady=(0, 6))

        ttk.Label(info_frame, text="PORCENTAJE DE LLENADO:", font=FONTS["metric_label"], foreground=COLORS["text_muted"]).pack(anchor=tk.W)
        self.lbl_pct = tk.Label(info_frame, text="-- %", font=FONTS["subtitle"], fg=COLORS["success"], bg=COLORS["bg_main"])
        self.lbl_pct.pack(anchor=tk.W, pady=(0, 6))

        ttk.Label(info_frame, text="VOLUMEN ESTIMADO:", font=FONTS["metric_label"], foreground=COLORS["text_muted"]).pack(anchor=tk.W)
        self.lbl_volume = tk.Label(info_frame, text="-- L", font=FONTS["subtitle"], fg=COLORS["accent_blue"], bg=COLORS["bg_main"])
        self.lbl_volume.pack(anchor=tk.W)

        # -------------------------------------------------------------
        # 2. AFINADOR DIGITAL CROMÁTICO
        # -------------------------------------------------------------
        frame_tuner = ttk.LabelFrame(paned, text="  2. Afinador Acústico Digital de Instrumentos  ", padding=12)
        paned.add(frame_tuner, weight=1)

        desc_tuner = (
            "Emplea la FFT y la interpolación sub-bin para identificar notas musicales con precisión de cents. "
            "Ideal para cuerdas, vientos o comprobar la afinación musical de la columna de aire."
        )
        ttk.Label(frame_tuner, text=desc_tuner, wraplength=380, justify=tk.LEFT, font=FONTS["body"]).pack(anchor=tk.W, pady=(0, 10))

        # Panel visual del afinador
        tuner_box = tk.Frame(frame_tuner, bg="#1e293b", bd=2, relief=tk.GROOVE, padx=15, pady=15)
        tuner_box.pack(fill=tk.X, pady=(0, 15))

        self.lbl_tuner_note = tk.Label(tuner_box, text="A4", font=("Segoe UI", 36, "bold"), fg="#38bdf8", bg="#1e293b")
        self.lbl_tuner_note.pack()

        self.lbl_tuner_freq = tk.Label(tuner_box, text="440.0 Hz  (Objetivo: 440.0 Hz)", font=FONTS["body"], fg="#cbd5e1", bg="#1e293b")
        self.lbl_tuner_freq.pack(pady=(0, 8))

        # Canvas con aguja de desviación en Cents (-50 a +50)
        self.tuner_canvas = tk.Canvas(tuner_box, width=320, height=60, bg="#0f172a", highlightthickness=0)
        self.tuner_canvas.pack(pady=5)

        self.lbl_tuner_status = tk.Label(tuner_box, text="¡PERFECTAMENTE AFINADO!", font=FONTS["body_bold"], fg="#4ade80", bg="#1e293b")
        self.lbl_tuner_status.pack(pady=(4, 0))

        # Referencia rápida de cuerdas de guitarra
        ttk.Label(frame_tuner, text="Frecuencias de Afinación Estándar (Guitarra 6 cuerdas):", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(10, 4))
        strings_box = ttk.Treeview(frame_tuner, columns=("str", "note", "freq"), show="headings", height=6)
        strings_box.heading("str", text="Cuerda")
        strings_box.heading("note", text="Nota")
        strings_box.heading("freq", text="Frecuencia (Hz)")
        strings_box.column("str", width=60, anchor=tk.CENTER)
        strings_box.column("note", width=60, anchor=tk.CENTER)
        strings_box.column("freq", width=120, anchor=tk.CENTER)

        guitar_notes = [
            ("1ª (Aguda)", "E4", "329.63 Hz"),
            ("2ª", "B3", "246.94 Hz"),
            ("3ª", "G3", "196.00 Hz"),
            ("4ª", "D3", "146.83 Hz"),
            ("5ª", "A2", "110.00 Hz"),
            ("6ª (Grave)", "E2", "82.41 Hz"),
        ]
        for s, n, f in guitar_notes:
            strings_box.insert("", tk.END, values=(s, n, f))
        strings_box.pack(fill=tk.X)

        self._update_water_calc()
        self._update_tuner(440.0)

    def _sync_with_realtime(self):
        f = self.app.tab_realtime.last_detected_freq
        if f > 20.0:
            self.var_input_freq.set(round(f, 1))
            self._update_water_calc()
            self._update_tuner(f)
            self.app.set_status(f"Frecuencia sincronizada desde captura: {f:.1f} Hz")
        else:
            self.app.set_status("No hay frecuencia reciente en la pestaña de captura.")

    def _update_water_calc(self):
        try:
            h_tank_cm = self.var_tank_height.get()
            h_tank_m = h_tank_cm / 100.0
            r_tank_m = self.var_tank_radius.get() / 100.0
            freq = self.var_input_freq.get()

            v_sound = self.app.dataset.temperature_c
            v_theo = self.app.dataset.tube_radius_m
            sound_speed = 343.0

            calc = estimate_water_level(
                detected_freq_hz=freq,
                total_tube_length_m=h_tank_m,
                sound_speed=sound_speed,
                tube_radius_m=r_tank_m
            )

            water_cm = calc["water_height_m"] * 100.0
            air_cm = calc["air_column_m"] * 100.0
            pct = calc["fill_percentage"]

            # Volumen de agua en litros: V = pi * r^2 * h * 1000
            vol_liters = np.pi * (r_tank_m ** 2) * calc["water_height_m"] * 1000.0

            self.lbl_water_cm.config(text=f"{water_cm:.1f} cm")
            self.lbl_air_cm.config(text=f"{air_cm:.1f} cm")
            self.lbl_pct.config(text=f"{pct:.1f} %")
            self.lbl_volume.config(text=f"{vol_liters:.2f} Litros")

            # Dibujar tanque en Canvas
            self._draw_tank(pct, water_cm, air_cm)
            self._update_tuner(freq)
        except Exception:
            pass

    def _draw_tank(self, pct, water_cm, air_cm):
        c = self.tank_canvas
        c.delete("all")

        # Dimensiones del tanque en canvas
        x0, y0 = 30, 20
        x1, y1 = 100, 190
        tank_h = y1 - y0

        # Nivel de agua proporcional
        water_px = (pct / 100.0) * tank_h
        water_y0 = y1 - water_px

        # Agua (azul)
        c.create_rectangle(x0, water_y0, x1, y1, fill="#38bdf8", outline="")

        # Columna de aire (gris claro)
        c.create_rectangle(x0, y0, x1, water_y0, fill="#f1f5f9", outline="")

        # Contorno del tubo/tanque (tubo abierto arriba, cerrado abajo)
        c.create_line(x0, y0, x0, y1, width=3, fill="#334155")
        c.create_line(x0, y1, x1, y1, width=3, fill="#334155")
        c.create_line(x1, y1, x1, y0, width=3, fill="#334155")

        # Marcas de escala
        for p in [0.25, 0.50, 0.75]:
            ym = y1 - p * tank_h
            c.create_line(x0 - 5, ym, x0, ym, fill="#64748b", width=1)
            c.create_text(x0 - 15, ym, text=f"{int(p*100)}%", font=("Segoe UI", 7), fill="#64748b")

        # Texto del porcentaje en el centro
        c.create_text((x0 + x1) / 2, 205, text=f"Llenado: {pct:.1f}%", font=("Segoe UI", 8, "bold"), fill="#0f172a")

    def _update_tuner(self, freq_hz: float):
        info = frequency_to_musical_note(freq_hz)
        cents = info["cents_deviation"]
        note = info["note"]
        target = info["target_freq"]

        self.lbl_tuner_note.config(text=note)
        self.lbl_tuner_freq.config(text=f"{freq_hz:.1f} Hz  (Objetivo: {target:.1f} Hz)")

        # Aguja en canvas (-50 a +50 cents)
        c = self.tuner_canvas
        c.delete("all")
        w, h = 320, 60
        cx = w / 2

        # Fondo con marcas
        c.create_line(cx, 10, cx, h - 10, fill="#ffffff", width=2)
        c.create_text(cx, 8, text="0", fill="#94a3b8", font=("Segoe UI", 7))
        c.create_text(cx - 80, 8, text="-25", fill="#94a3b8", font=("Segoe UI", 7))
        c.create_text(cx + 80, 8, text="+25", fill="#94a3b8", font=("Segoe UI", 7))
        c.create_text(25, 8, text="BEMOL (-)", fill="#ef4444", font=("Segoe UI", 7, "bold"))
        c.create_text(w - 30, 8, text="SOST. (+)", fill="#ef4444", font=("Segoe UI", 7, "bold"))

        # Posición de la aguja
        clamped_cents = max(-50.0, min(50.0, cents))
        needle_x = cx + (clamped_cents / 50.0) * (w / 2 - 30)

        # Color según desviación
        if abs(cents) < 5.0:
            needle_color = "#22c55e"  # Verde
            status_text = f"¡AFINADO! ({cents:+.1f} cents)"
            status_color = "#4ade80"
        elif cents < 0:
            needle_color = "#eab308"  # Amarillo
            status_text = f"Ligeramente grave / bemol ({cents:+.1f} cents)"
            status_color = "#fde047"
        else:
            needle_color = "#f97316"  # Naranja
            status_text = f"Ligeramente agudo / sostenido ({cents:+.1f} cents)"
            status_color = "#fdba74"

        # Dibujar aguja
        c.create_line(needle_x, 15, needle_x, h - 5, fill=needle_color, width=4)
        c.create_oval(needle_x - 5, h - 15, needle_x + 5, h - 5, fill=needle_color, outline="")

        self.lbl_tuner_status.config(text=status_text, fg=status_color)
