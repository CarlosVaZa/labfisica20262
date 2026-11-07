"""
Pestaña 2: Experimento de Laboratorio y Regresión Lineal
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.physics_engine import (
    analyze_resonance_series,
    theoretical_sound_speed,
)
from .styles import COLORS, FONTS


class ExperimentTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self._build_ui()
        self.refresh_table()

    def _build_ui(self):
        # Panel superior de parámetros y botones de acción
        top_bar = ttk.LabelFrame(self, text="  Parámetros del Experimento y Acciones  ", padding=8)
        top_bar.pack(fill=tk.X, padx=10, pady=(10, 5))

        # Temperatura ambiente
        ttk.Label(top_bar, text="Temperatura T (°C):", font=FONTS["body_bold"]).grid(row=0, column=0, padx=5, sticky=tk.W)
        self.temp_var = tk.DoubleVar(value=20.0)
        temp_spin = ttk.Spinbox(top_bar, from_=-10.0, to=50.0, increment=0.5, textvariable=self.temp_var, width=8, command=self._on_param_change)
        temp_spin.grid(row=0, column=1, padx=5, sticky=tk.W)

        # Radio del tubo
        ttk.Label(top_bar, text="Radio Tubo r (cm):", font=FONTS["body_bold"]).grid(row=0, column=2, padx=5, sticky=tk.W)
        self.radius_var = tk.DoubleVar(value=1.5)
        radius_spin = ttk.Spinbox(top_bar, from_=0.0, to=10.0, increment=0.1, textvariable=self.radius_var, width=8, command=self._on_param_change)
        radius_spin.grid(row=0, column=3, padx=5, sticky=tk.W)

        # Botones de gestión
        btn_sample = ttk.Button(top_bar, text="📁 Cargar Datos Modelo", command=self._load_sample)
        btn_sample.grid(row=0, column=4, padx=6)

        btn_manual = ttk.Button(top_bar, text="➕ Agregar Punto Manual", command=self._show_add_dialog)
        btn_manual.grid(row=0, column=5, padx=6)

        btn_delete = ttk.Button(top_bar, text="🗑 Eliminar Selección", command=self._delete_selected)
        btn_delete.grid(row=0, column=6, padx=6)

        btn_clear = ttk.Button(top_bar, text="🧹 Limpiar Todo", command=self._clear_all)
        btn_clear.grid(row=0, column=7, padx=6)

        btn_export = ttk.Button(top_bar, text="💾 Exportar CSV", command=self._export_csv)
        btn_export.grid(row=0, column=8, padx=6)

        btn_import = ttk.Button(top_bar, text="📂 Importar CSV", command=self._import_csv)
        btn_import.grid(row=0, column=9, padx=6)

        # Contenedor central dividido: Izquierda = Tabla de Datos, Derecha = Gráfica y Resultados
        center_split = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        center_split.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)

        # Panel izquierdo: Tabla de datos
        left_frame = ttk.LabelFrame(center_split, text="  Tabla de Mediciones Experimentales  ", padding=6)
        center_split.add(left_frame, weight=2)

        columns = ("id", "length_cm", "freq_hz", "inv_freq_ms", "v_point", "notes")
        self.tree = ttk.Treeview(left_frame, columns=columns, show="headings", selectmode="browse")
        self.tree.heading("id", text="#ID")
        self.tree.heading("length_cm", text="L (cm)")
        self.tree.heading("freq_hz", text="f1 (Hz)")
        self.tree.heading("inv_freq_ms", text="1/f (ms)")
        self.tree.heading("v_point", text="v_puntual (m/s)")
        self.tree.heading("notes", text="Observaciones")

        self.tree.column("id", width=40, anchor=tk.CENTER)
        self.tree.column("length_cm", width=65, anchor=tk.CENTER)
        self.tree.column("freq_hz", width=75, anchor=tk.CENTER)
        self.tree.column("inv_freq_ms", width=75, anchor=tk.CENTER)
        self.tree.column("v_point", width=95, anchor=tk.CENTER)
        self.tree.column("notes", width=140, anchor=tk.W)

        scrollbar = ttk.Scrollbar(left_frame, orient=tk.VERTICAL, command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        self.tree.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Panel derecho: Gráfica de regresión y tarjeta de resultados
        right_frame = ttk.Frame(center_split)
        center_split.add(right_frame, weight=3)

        # Gráfica Matplotlib de regresión
        self.fig = Figure(figsize=(6, 4.2), dpi=100, facecolor="#f8fafc")
        self.fig.subplots_adjust(left=0.12, right=0.95, top=0.90, bottom=0.14)
        self.ax = self.fig.add_subplot(1, 1, 1)
        self.ax.set_title("Regresión Lineal: L vs 1/f (Pendiente m = v/4)", fontsize=11, fontweight="bold", color="#1e293b")
        self.ax.set_xlabel("1 / Frecuencia (ms)", fontsize=9)
        self.ax.set_ylabel("Longitud L (cm)", fontsize=9)
        self.ax.grid(True, linestyle="--", alpha=0.5)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_frame)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        # Barra inferior de resultados del ajuste
        self.results_frame = ttk.LabelFrame(right_frame, text="  Resultados del Análisis Estadístico  ", padding=8)
        self.results_frame.pack(fill=tk.X, pady=(5, 0))

        self.lbl_v_exp = ttk.Label(self.results_frame, text="v_exp: -- m/s", font=FONTS["body_bold"], foreground=COLORS["primary"])
        self.lbl_v_exp.grid(row=0, column=0, padx=8, sticky=tk.W)

        self.lbl_v_theo = ttk.Label(self.results_frame, text="v_teórica: -- m/s", font=FONTS["body"])
        self.lbl_v_theo.grid(row=0, column=1, padx=8, sticky=tk.W)

        self.lbl_error = ttk.Label(self.results_frame, text="Error: -- %", font=FONTS["body_bold"], foreground=COLORS["danger"])
        self.lbl_error.grid(row=0, column=2, padx=8, sticky=tk.W)

        self.lbl_r2 = ttk.Label(self.results_frame, text="R²: --", font=FONTS["body_bold"])
        self.lbl_r2.grid(row=0, column=3, padx=8, sticky=tk.W)

        self.lbl_end_corr = ttk.Label(self.results_frame, text="ΔL exp: -- mm", font=FONTS["body"])
        self.lbl_end_corr.grid(row=1, column=0, columnspan=2, padx=8, pady=(4, 0), sticky=tk.W)

        btn_save_plot = ttk.Button(self.results_frame, text="📷 Guardar Gráfica PNG", command=self._save_plot)
        btn_save_plot.grid(row=1, column=3, padx=8, pady=(4, 0), sticky=tk.E)

    def _on_param_change(self):
        self.app.dataset.temperature_c = self.temp_var.get()
        self.app.dataset.tube_radius_m = self.radius_var.get() / 100.0
        self.refresh_regression()

    def refresh_table(self):
        # Limpiar Treeview
        for item in self.tree.get_children():
            self.tree.delete(item)

        for m in self.app.dataset.measurements:
            f = m["frequency_hz"]
            inv_f_ms = (1.0 / f * 1000.0) if f > 0 else 0.0
            self.tree.insert("", tk.END, values=(
                m["id"],
                f"{m['length_cm']:.2f}",
                f"{m['frequency_hz']:.2f}",
                f"{inv_f_ms:.3f}",
                f"{m['v_point_m_s']:.2f}",
                m.get("notes", "")
            ))

        self.refresh_regression()

    def refresh_regression(self):
        lengths, freqs = self.app.dataset.get_lengths_and_frequencies()
        self.ax.clear()
        self.ax.grid(True, linestyle="--", alpha=0.5)
        self.ax.set_title("Regresión Lineal: L vs 1/f (Pendiente m = v/4)", fontsize=11, fontweight="bold", color="#1e293b")
        self.ax.set_xlabel("1 / Frecuencia (ms)", fontsize=9)
        self.ax.set_ylabel("Longitud L (cm)", fontsize=9)

        if len(lengths) < 2:
            self.ax.text(0.5, 0.5, "Agregue al menos 2 mediciones para graficar la regresión",
                         ha="center", va="center", transform=self.ax.transAxes, color=COLORS["text_muted"], fontsize=10)
            self.lbl_v_exp.config(text="v_exp: -- m/s")
            self.lbl_v_theo.config(text="v_teórica: -- m/s")
            self.lbl_error.config(text="Error: -- %")
            self.lbl_r2.config(text="R²: --")
            self.lbl_end_corr.config(text="ΔL exp: -- mm")
            self.canvas.draw_idle()
            return

        temp = self.temp_var.get()
        radius_m = self.radius_var.get() / 100.0

        try:
            res = analyze_resonance_series(lengths, freqs, temp_celsius=temp, tube_radius_m=radius_m)
        except Exception as e:
            self.ax.text(0.5, 0.5, f"Error en cálculo de regresión: {e}",
                         ha="center", va="center", transform=self.ax.transAxes, color="red")
            self.canvas.draw_idle()
            return

        x_ms = np.array(res["x_inv_freq"]) * 1000.0
        y_cm = np.array(res["y_lengths"]) * 100.0

        # Puntos experimentales
        self.ax.scatter(x_ms, y_cm, color="#1d4ed8", s=60, zorder=5, label="Mediciones de Laboratorio")

        # Recta de ajuste
        x_fit_ms = np.linspace(min(x_ms) * 0.9, max(x_ms) * 1.1, 100)
        x_fit_s = x_fit_ms / 1000.0
        y_fit_cm = (res["slope"] * x_fit_s + res["intercept"]) * 100.0

        self.ax.plot(x_fit_ms, y_fit_cm, color="#dc2626", lw=2,
                     label=f"Ajuste OLS (v = {res['v_experimental']:.1f} m/s, R²={res['r_squared']:.4f})")

        self.ax.legend(loc="upper left", fontsize=8)

        # Actualizar etiquetas de resumen
        self.lbl_v_exp.config(text=f"v_exp: {res['v_experimental']:.2f} ± {res['v_uncertainty']:.2f} m/s")
        self.lbl_v_theo.config(text=f"v_teórica: {res['v_theoretical']:.2f} m/s")
        self.lbl_error.config(text=f"Error: {res['percentage_error']:.2f} %")
        self.lbl_r2.config(text=f"R²: {res['r_squared']:.5f}")

        delta_l_mm = res["experimental_end_correction_m"] * 1000.0
        delta_l_theo_mm = res["theoretical_end_correction_m"] * 1000.0 if res["theoretical_end_correction_m"] else 0.0
        self.lbl_end_corr.config(text=f"ΔL exp: {delta_l_mm:.1f} mm (Teórica 0.61r: {delta_l_theo_mm:.1f} mm)")

        self.canvas.draw_idle()

    def _load_sample(self):
        self.app.dataset.load_sample_dataset()
        self.refresh_table()
        self.app.set_status("Dataset modelo de laboratorio cargado con éxito.")
        messagebox.showinfo("Datos Cargados", "Se ha cargado la serie experimental modelo (7 mediciones entre 12 y 40 cm).")

    def _delete_selected(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showinfo("Selección", "Por favor seleccione una fila en la tabla para eliminar.")
            return

        item = self.tree.item(sel[0])
        val = item["values"]
        meas_id = int(val[0])
        self.app.dataset.remove_measurement(meas_id)
        self.refresh_table()
        self.app.set_status(f"Medición #{meas_id} eliminada.")

    def _clear_all(self):
        if not self.app.dataset.measurements:
            return
        if messagebox.askyesno("Confirmar", "¿Está seguro de eliminar todas las mediciones de la tabla?"):
            self.app.dataset.clear()
            self.refresh_table()
            self.app.set_status("Tabla de mediciones limpiada.")

    def _export_csv(self):
        if not self.app.dataset.measurements:
            messagebox.showwarning("Aviso", "No hay datos para exportar.")
            return

        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=[("CSV files", "*.csv")])
        if path:
            self.app.dataset.export_csv(path)
            messagebox.showinfo("Exportación", f"Datos exportados correctamente en:\n{path}")

    def _import_csv(self):
        path = filedialog.askopenfilename(filetypes=[("CSV files", "*.csv"), ("JSON files", "*.json")])
        if path:
            try:
                if path.endswith(".json"):
                    self.app.dataset.import_json(path)
                else:
                    self.app.dataset.import_csv(path)
                self.refresh_table()
                messagebox.showinfo("Importación", "Datos importados exitosamente.")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo importar el archivo: {e}")

    def _save_plot(self):
        path = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG Image", "*.png"), ("PDF Document", "*.pdf")])
        if path:
            self.fig.savefig(path, dpi=200)
            messagebox.showinfo("Guardar", f"Gráfica guardada en:\n{path}")

    def _show_add_dialog(self):
        dlg = tk.Toplevel(self)
        dlg.title("Agregar Medición Manual")
        dlg.geometry("340x260")
        dlg.resizable(False, False)
        dlg.transient(self)
        dlg.grab_set()

        frame = ttk.Frame(dlg, padding=16)
        frame.pack(fill=tk.BOTH, expand=True)

        ttk.Label(frame, text="Longitud L de columna de aire (cm):", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 2))
        ent_l = ttk.Entry(frame)
        ent_l.insert(0, "25.0")
        ent_l.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Frecuencia fundamental f1 (Hz):", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 2))
        ent_f = ttk.Entry(frame)
        ent_f.insert(0, "340.0")
        ent_f.pack(fill=tk.X, pady=(0, 10))

        ttk.Label(frame, text="Observaciones / Notas:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 2))
        ent_notes = ttk.Entry(frame)
        ent_notes.insert(0, "Medición manual")
        ent_notes.pack(fill=tk.X, pady=(0, 15))

        def _save():
            try:
                l_cm = float(ent_l.get())
                f_hz = float(ent_f.get())
                notes = ent_notes.get()
                if l_cm <= 0 or f_hz <= 0:
                    raise ValueError("Los valores deben ser positivos.")
                self.app.dataset.add_measurement(length_m=l_cm / 100.0, frequency_hz=f_hz, notes=notes)
                self.refresh_table()
                dlg.destroy()
            except ValueError as ve:
                messagebox.showerror("Dato Inválido", f"Por favor ingrese números válidos: {ve}", parent=dlg)

        btn_save = ttk.Button(frame, text="Guardar Punto", command=_save)
        btn_save.pack(fill=tk.X)

