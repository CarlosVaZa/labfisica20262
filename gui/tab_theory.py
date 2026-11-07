"""
Pestaña 4: Fundamento Teórico, Guía Experimental y Calculadora Acústica
"""

import tkinter as tk
from tkinter import ttk
import numpy as np

from core.physics_engine import (
    theoretical_sound_speed,
    fundamental_frequency,
)
from .styles import COLORS, FONTS


class TheoryTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()

    def _build_ui(self):
        # PanedWindow: Izquierda = Documentación / Guía, Derecha = Calculadora interactiva
        paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        paned.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)

        # Panel izquierdo: Documentación en texto con scroll
        doc_frame = ttk.LabelFrame(paned, text="  Fundamento Teórico y Guía de Laboratorio  ", padding=10)
        paned.add(doc_frame, weight=3)

        text_scroll = ttk.Scrollbar(doc_frame)
        text_scroll.pack(side=tk.RIGHT, fill=tk.Y)

        self.text_widget = tk.Text(
            doc_frame,
            wrap=tk.WORD,
            yscrollcommand=text_scroll.set,
            font=("Segoe UI", 9),
            padx=10,
            pady=10,
            bg="#ffffff",
            relief=tk.FLAT
        )
        self.text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        text_scroll.config(command=self.text_widget.yview)

        self._populate_theory_text()
        self.text_widget.config(state=tk.DISABLED)

        # Panel derecho: Calculadora Acústica Teórica
        calc_frame = ttk.LabelFrame(paned, text="  Calculadora Teórica Rápida  ", padding=12)
        paned.add(calc_frame, weight=2)

        ttk.Label(calc_frame, text="Predicción de Resonancias", font=FONTS["header"]).pack(anchor=tk.W, pady=(0, 10))

        # Entradas
        in_grid = ttk.Frame(calc_frame)
        in_grid.pack(fill=tk.X, pady=(0, 15))

        ttk.Label(in_grid, text="Longitud L (cm):", font=FONTS["body_bold"]).grid(row=0, column=0, sticky=tk.W, pady=4)
        self.var_calc_l = tk.DoubleVar(value=20.0)
        spin_l = ttk.Spinbox(in_grid, from_=5.0, to=150.0, increment=1.0, textvariable=self.var_calc_l, width=10, command=self._recalculate)
        spin_l.grid(row=0, column=1, sticky=tk.W, padx=5, pady=4)

        ttk.Label(in_grid, text="Temperatura T (°C):", font=FONTS["body_bold"]).grid(row=1, column=0, sticky=tk.W, pady=4)
        self.var_calc_t = tk.DoubleVar(value=20.0)
        spin_t = ttk.Spinbox(in_grid, from_=-20.0, to=50.0, increment=1.0, textvariable=self.var_calc_t, width=10, command=self._recalculate)
        spin_t.grid(row=1, column=1, sticky=tk.W, padx=5, pady=4)

        ttk.Label(in_grid, text="Radio Interno r (cm):", font=FONTS["body_bold"]).grid(row=2, column=0, sticky=tk.W, pady=4)
        self.var_calc_r = tk.DoubleVar(value=1.5)
        spin_r = ttk.Spinbox(in_grid, from_=0.0, to=10.0, increment=0.1, textvariable=self.var_calc_r, width=10, command=self._recalculate)
        spin_r.grid(row=2, column=1, sticky=tk.W, padx=5, pady=4)

        ttk.Separator(calc_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)

        # Resultados de la calculadora
        ttk.Label(calc_frame, text="Resultados Físicos Teóricos:", font=FONTS["header"]).pack(anchor=tk.W, pady=(0, 8))

        self.lbl_theo_v = ttk.Label(calc_frame, text="Velocidad teórica v(T): -- m/s", font=FONTS["body_bold"], foreground=COLORS["primary"])
        self.lbl_theo_v.pack(anchor=tk.W, pady=3)

        self.lbl_theo_f1 = ttk.Label(calc_frame, text="Fundamental f1: -- Hz", font=FONTS["body_bold"], foreground=COLORS["success"])
        self.lbl_theo_f1.pack(anchor=tk.W, pady=3)

        self.lbl_theo_f3 = ttk.Label(calc_frame, text="Armónico 3 (f3 = 3f1): -- Hz", font=FONTS["body"])
        self.lbl_theo_f3.pack(anchor=tk.W, pady=2)

        self.lbl_theo_f5 = ttk.Label(calc_frame, text="Armónico 5 (f5 = 5f1): -- Hz", font=FONTS["body"])
        self.lbl_theo_f5.pack(anchor=tk.W, pady=2)

        self.lbl_theo_lambda = ttk.Label(calc_frame, text="Longitud de onda λ1: -- cm", font=FONTS["body"])
        self.lbl_theo_lambda.pack(anchor=tk.W, pady=2)

        self.lbl_theo_leff = ttk.Label(calc_frame, text="Longitud efectiva L_eff: -- cm", font=FONTS["body"])
        self.lbl_theo_leff.pack(anchor=tk.W, pady=2)

        self._recalculate()

    def _recalculate(self):
        try:
            L_cm = self.var_calc_l.get()
            T_c = self.var_calc_t.get()
            r_cm = self.var_calc_r.get()

            L_m = L_cm / 100.0
            r_m = r_cm / 100.0

            v_theo = theoretical_sound_speed(T_c)
            f1 = fundamental_frequency(L_m, sound_speed=v_theo, tube_radius_m=r_m, harmonic_n=1)
            f3 = fundamental_frequency(L_m, sound_speed=v_theo, tube_radius_m=r_m, harmonic_n=2)
            f5 = fundamental_frequency(L_m, sound_speed=v_theo, tube_radius_m=r_m, harmonic_n=3)

            leff_cm = (L_m + 0.61 * r_m) * 100.0
            lambda1_cm = (v_theo / f1) * 100.0

            self.lbl_theo_v.config(text=f"Velocidad teórica v(T): {v_theo:.2f} m/s")
            self.lbl_theo_f1.config(text=f"Fundamental f1: {f1:.2f} Hz")
            self.lbl_theo_f3.config(text=f"Armónico 3 (f3 = 3f1): {f3:.2f} Hz")
            self.lbl_theo_f5.config(text=f"Armónico 5 (f5 = 5f1): {f5:.2f} Hz")
            self.lbl_theo_lambda.config(text=f"Longitud de onda λ1: {lambda1_cm:.2f} cm")
            self.lbl_theo_leff.config(text=f"Longitud efectiva L_eff: {leff_cm:.2f} cm")
        except Exception:
            pass

    def _populate_theory_text(self):
        theory_content = """
======================================================================
  GRUPO 1 - LABORATORIO DE FÍSICA: VELOCIDAD DEL SONIDO POR RESONANCIA
======================================================================

1. PRINCIPIO FÍSICO DE LA RESONANCIA EN TUBOS SEMICERRADOS
----------------------------------------------------------
Un tubo cilíndrico uniforme que contiene agua en su fondo actúa como una columna
de aire abierta en un extremo (la boca del tubo) y cerrada en el otro (la superficie del agua).

• En el extremo cerrado (agua): Las partículas de aire no pueden desplazarse, formando
  un NODO de desplazamiento (o vientre de presión).
• En el extremo abierto (boca): Las partículas vibran libremente con la presión atmosférica,
  formando un ANTINODO (o vientre de desplazamiento).

La condición de resonancia para la frecuencia fundamental (modo n = 1) establece
que la longitud efectiva de la columna de aire equivale a un cuarto de longitud de onda:
    L_eff = λ / 4  ==>  λ = 4 * L_eff

Relacionando con la velocidad de propagación de la onda acústica (v = λ * f):
    f1 = v / (4 * L_eff)
    v = 4 * L_eff * f1

2. CORRECCIÓN DE EXTREMO (END CORRECTION)
----------------------------------------
El antinodo acústico no se ubica exactamente en el borde físico del tubo, sino a una pequeña
distancia ΔL por fuera de la abertura debido a la inercia del aire en la boca:
    L_eff = L + ΔL
    ΔL ≈ 0.61 * r   (donde r es el radio interno del tubo cilíndrico)

3. MÉTODO DE REGRESIÓN LINEAL POR MÍNIMOS CUADRADOS
--------------------------------------------------
Al tomar mediciones para múltiples niveles de agua (variando L), la ecuación se linealiza como:
    L = (v / 4) * (1 / f) - ΔL

Si definimos:
    y = L   (longitud medida en metros)
    x = 1 / f  (inverso de la frecuencia en segundos)
    Pendiente: m = v / 4   ==>   v_exp = 4 * m
    Intercepto: c = -ΔL    ==>   ΔL_exp = -c

Este método elimina el sesgo sistemático del extremo del tubo y minimiza la incertidumbre aleatoria.

4. VELOCIDAD TEÓRICA EN FUNCIÓN DE LA TEMPERATURA
-------------------------------------------------
La velocidad del sonido en el aire depende de la temperatura absoluta (T en Kelvin):
    v(T) = 331.3 * sqrt(1 + T / 273.15)  [m/s]
A 20 °C (293.15 K), v_teórica ≈ 343.2 m/s.

5. GUÍA EXPERIMENTAL PASO A PASO
--------------------------------
1. Colocar agua en el tubo o botella cilíndrica.
2. Medir con regla o cinta milimétrica la longitud L de la columna de aire (desde el agua a la boca).
3. Ubicar el micrófono a unos 2 a 5 cm de la abertura.
4. Generar sonido: sople suavemente rasante a la boca del tubo o emita un barrido acústico con altavoz.
5. Presionar '⚡ Capturar Ráfaga' en la pestaña de tiempo real para capturar la señal acústica.
6. El algoritmo aplica filtro pasa-banda y FFT, detectando automáticamente el pico de resonancia fundamental f1.
7. Presionar '➕ Guardar en Experimento'.
8. Variar la cantidad de agua y repetir para al menos 5 o 6 alturas diferentes.
9. En la pestaña 'Experimento de Laboratorio', observar la recta de regresión y el cálculo de la velocidad experimental.
"""
        self.text_widget.insert(tk.END, theory_content)

