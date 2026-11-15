"""Pestañas de análisis y resultados globales, sincronizadas por modelo."""

import tkinter as tk
from tkinter import ttk

import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.statistical_analysis import analyze_tube_measurements, analyze_bottle_measurements


class StatisticsTab(ttk.Frame):
    def __init__(self, parent, scroll_panel):
        super().__init__(parent)
        self.measurements = []
        self.var_model = tk.StringVar(value="tube")
        panel = scroll_panel(self)
        ttk.Label(panel, text="Análisis conjunto de las mediciones registradas por modelo",
                  font=("Segoe UI", 12, "bold"), wraplength=850).pack(anchor=tk.W, pady=(0, 6))
        selector = ttk.Frame(panel)
        selector.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(selector, text="Modelo:").pack(side=tk.LEFT, padx=(0, 12))
        for label, model in (("Tubo uniforme", "tube"), ("Botella (Helmholtz)", "bottle")):
            ttk.Radiobutton(selector, text=label, value=model, variable=self.var_model).pack(side=tk.LEFT, padx=6)
        self.message = ttk.Label(panel, wraplength=850, foreground="#92400e")
        self.message.pack(anchor=tk.W, pady=(0, 8))

        table_box = ttk.LabelFrame(panel, text="A. Mediciones utilizadas", padding=8)
        table_box.pack(fill=tk.X)
        columns = {"id": "N.º de registro", "effective": "L efectiva (m)",
                   "inverse": "1 / L efectiva (m⁻¹)", "frequency": "f₁ experimental (Hz)"}
        self.table = ttk.Treeview(table_box, columns=list(columns), show="headings", height=5)
        for key, label in columns.items():
            self.table.heading(key, text=label)
            self.table.column(key, width=180, minwidth=100)
        self.table.grid(row=0, column=0, sticky="nsew")
        table_box.columnconfigure(0, weight=1)
        sy = ttk.Scrollbar(table_box, orient=tk.VERTICAL, command=self.table.yview)
        sy.grid(row=0, column=1, sticky="ns")
        sx = ttk.Scrollbar(table_box, orient=tk.HORIZONTAL, command=self.table.xview)
        sx.grid(row=1, column=0, sticky="ew")
        self.table.configure(yscrollcommand=sy.set, xscrollcommand=sx.set)

        graph_box = ttk.LabelFrame(panel, text="B. Gráfica de regresión lineal", padding=8)
        graph_box.pack(fill=tk.X, pady=10)
        self.figure = Figure(figsize=(8, 3.4), dpi=100, facecolor="#f8fafc")
        self.figure.subplots_adjust(left=.12, right=.96, top=.86, bottom=.2)
        self.axis = self.figure.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.figure, master=graph_box)
        self.canvas.get_tk_widget().configure(height=340)
        self.canvas.get_tk_widget().pack(fill=tk.X)
        self.fit_text = ttk.Label(graph_box, wraplength=850)
        self.fit_text.pack(anchor=tk.W, pady=6)

        self.results_tab = ttk.Frame(parent)
        results_panel = scroll_panel(self.results_tab)
        self.results_model = ttk.Label(results_panel, font=("Segoe UI", 12, "bold"), wraplength=850)
        self.results_model.pack(anchor=tk.W, pady=(0, 8))
        ttk.Label(results_panel, text="Modelo seleccionado en la pestaña «Análisis estadístico».",
                  wraplength=850).pack(anchor=tk.W, pady=(0, 10))
        global_box = ttk.LabelFrame(results_panel, text="Resultados estadísticos globales", padding=10)
        global_box.pack(fill=tk.X)
        self.results_text = ttk.Label(global_box, wraplength=850, font=("Segoe UI", 10))
        self.results_text.pack(anchor=tk.W)
        self.warning_text = ttk.Label(global_box, wraplength=850, foreground="#92400e")
        self.warning_text.pack(anchor=tk.W, pady=(8, 0))
        self.explanation = ttk.Label(global_box, wraplength=850, foreground="#475569")
        self.explanation.pack(anchor=tk.W, pady=(8, 0))
        self.var_model.trace_add("write", lambda *args: self.refresh(self.measurements))
        # Keep labels responsive to the available width in the shared scroll panel.
        for box in (panel, graph_box, results_panel, global_box):
            box.bind("<Configure>", lambda event, frame=box: self._wrap(frame, event.width), add="+")

    @staticmethod
    def _wrap(frame, width):
        for widget in frame.winfo_children():
            if isinstance(widget, ttk.Label):
                widget.configure(wraplength=max(120, width - 30))

    def refresh(self, measurements):
        self.measurements = measurements
        bottle = self.var_model.get() == "bottle"
        analysis = (analyze_bottle_measurements if bottle else analyze_tube_measurements)(measurements)
        symbol = "fH" if bottle else "f₁"
        variable = "X" if bottle else "(1/L efectiva)"
        factor = "2πm" if bottle else "4m"
        name = "Botella (Helmholtz)" if bottle else "Tubo uniforme"
        self.results_model.config(text=f"Resultados estadísticos globales — {name}")
        columns = ({"id": "N.º de registro", "volume": "V aire (m³)", "area": "A (m²)",
                    "effective": "L efectiva cuello (m)", "x": "X (m⁻¹)", "frequency": "fH experimental (Hz)"}
                   if bottle else {"id": "N.º de registro", "effective": "L efectiva (m)",
                                   "inverse": "1 / L efectiva (m⁻¹)", "frequency": "f₁ experimental (Hz)"})
        self.table.configure(columns=list(columns))
        for key, label in columns.items():
            self.table.heading(key, text=label)
            self.table.column(key, width=155 if bottle else 180, minwidth=100)
        physical = ("X = √[A / (Vaire × L efectiva)]; fH = mX + b; v global = 2πm.\n"
                    "IC 95 %: 2πm ± 2π t(0.975, n−2) SE(m)." if bottle else
                    "OLS con intercepto libre: f₁ = m(1/L efectiva) + b; v global = 4m.\n"
                    "IC 95 %: 4m ± 4 t(0.975, n−2) SE(m).")
        self.explanation.config(text=physical +
            "\nEl intervalo supone errores independientes con varianza constante y normalidad para la inferencia t; "
            "no incorpora la incertidumbre geométrica.\nReferencia global: promedio de las velocidades teóricas históricas. "
            "Con temperaturas distintas, el ajuste supone una aproximación de velocidad común.")
        self.analysis = analysis
        self.table.delete(*self.table.get_children())
        for row in analysis["rows"]:
            values = ((row["id"], f"{row['air_volume_m3']:.8g}", f"{row['area_m2']:.8g}",
                       f"{row['effective_length_m']:.8g}", f"{row['x']:.8g}", f"{row['frequency_hz']:.8g}")
                      if bottle else (row["id"], f"{row['effective_length_m']:.8g}",
                                      f"{row['inverse_length']:.8g}", f"{row['frequency_hz']:.8g}"))
            self.table.insert("", tk.END, values=values)
        self.axis.clear()
        self.axis.set(xlabel=(r"$X = \sqrt{A / (V_{\mathrm{aire}} L_{\mathrm{ef}})}$ (m⁻¹)" if bottle else
                              "Inverso de longitud efectiva 1/L efectiva (m⁻¹)"),
                      ylabel=f"Frecuencia experimental {symbol} (Hz)", title=f"{name}: regresión experimental")
        self.axis.grid(alpha=.3)
        rows, fit = analysis["rows"], analysis["fit"]
        self.message.config(text=analysis["message"])
        self.warning_text.config(text="\n".join(analysis["warnings"]))
        if rows:
            self.axis.scatter([r["x"] for r in rows], [r["frequency_hz"] for r in rows],
                              color="#2563eb", label="Mediciones registradas")
        if fit is None:
            self.fit_text.config(text="Ajuste pendiente: se necesitan datos válidos con valores X distintos.")
            self.results_text.config(text=f"Mediciones válidas utilizadas: {len(rows)}\n"
                                     f"{analysis['message']}\nSin resultados globales disponibles.")
        else:
            x = np.linspace(min(r["x"] for r in rows), max(r["x"] for r in rows), 160)
            self.axis.plot(x, fit["slope"] * x + fit["intercept"], color="#16a34a", label="Ajuste por mínimos cuadrados")
            r_squared = "no definido" if fit["r_squared"] is None else f"{fit['r_squared']:.6f}"
            equation = f"{symbol} = {fit['slope']:.6g} × {variable} {fit['intercept']:+.6g}"
            self.axis.set_title(f"{equation}\nR² = {r_squared}", fontsize=10)
            self.fit_text.config(text=f"{equation}\nPendiente m = {fit['slope']:.6g} m/s; "
                                 f"intercepto b = {fit['intercept']:.6g} Hz; R² = {r_squared}")
            def value(key, unit):
                return "no disponible" if fit[key] is None else f"{fit[key]:.4f} {unit}"
            ci = fit["speed_ci95"]
            interval = ("no disponible" if ci is None else f"[{ci[0]:.4f}, {ci[1]:.4f}] m/s")
            self.results_text.config(text=(
                f"Velocidad experimental global ({factor}): {fit['speed']:.4f} m/s\n"
                f"Velocidad teórica de referencia global: {value('reference', 'm/s')}\n"
                f"Temperatura promedio: {value('mean_temperature', '°C')}\n"
                f"Diferencia (global − referencia): {value('difference', 'm/s')}\n"
                f"Error porcentual global: {value('error_pct', '%')}\n"
                f"Intervalo de confianza del 95 %: {interval}\n"
                f"Cantidad de mediciones utilizadas: {fit['n']}"))
        if rows:
            self.axis.legend(fontsize=8)
        self.canvas.draw_idle()
