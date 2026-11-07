"""
Pestaña 1: Captura Acústica y Análisis Espectral en Tiempo Real
"""

import tkinter as tk
from tkinter import ttk, messagebox
import numpy as np
import matplotlib
matplotlib.use("TkAgg")
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from core.physics_engine import (
    sound_speed_from_point,
    theoretical_sound_speed,
    frequency_to_musical_note,
)
from core.signal_processing import (
    apply_bandpass_filter,
    compute_fft,
    find_spectral_peaks,
    calculate_signal_rms,
)
from core.audio_capture import list_audio_devices, AudioStreamer, record_burst
from core.audio_generator import generate_pure_tone, generate_frequency_sweep, play_audio, stop_audio
from .styles import COLORS, FONTS


class RealtimeTab(ttk.Frame):
    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.streamer = AudioStreamer(sample_rate=44100, buffer_size=8192)

        self.last_detected_freq = 0.0
        self.last_measured_v = 0.0
        self.is_streaming = False
        self._timer_id = None

        self._build_ui()
        self._populate_audio_devices()

    def _build_ui(self):
        # Panel izquierdo de control
        control_frame = ttk.LabelFrame(self, text="  Configuración y Captura  ", padding=12)
        control_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(10, 5), pady=10)

        # Dispositivo de entrada
        ttk.Label(control_frame, text="Dispositivo de Micrófono:", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 2))
        self.device_combo = ttk.Combobox(control_frame, state="readonly", width=28)
        self.device_combo.pack(fill=tk.X, pady=(0, 10))

        # Checkbox Modo Simulación
        self.sim_var = tk.BooleanVar(value=False)
        sim_chk = ttk.Checkbutton(
            control_frame,
            text="Modo Simulación (Sin Micrófono)",
            variable=self.sim_var,
            command=self._on_sim_toggle
        )
        sim_chk.pack(anchor=tk.W, pady=(0, 10))

        # Longitud de columna de aire L
        ttk.Label(control_frame, text="Longitud Columna de Aire L (cm):", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 2))
        self.length_var = tk.DoubleVar(value=20.0)
        length_spin = ttk.Spinbox(control_frame, from_=5.0, to=100.0, increment=0.5, textvariable=self.length_var, width=15)
        length_spin.pack(fill=tk.X, pady=(0, 10))

        # Radio del tubo r
        ttk.Label(control_frame, text="Radio Interno Tubo r (cm):", font=FONTS["body_bold"]).pack(anchor=tk.W, pady=(0, 2))
        self.radius_var = tk.DoubleVar(value=1.5)
        radius_spin = ttk.Spinbox(control_frame, from_=0.0, to=10.0, increment=0.1, textvariable=self.radius_var, width=15)
        radius_spin.pack(fill=tk.X, pady=(0, 15))

        # Botones de captura
        self.btn_stream = tk.Button(
            control_frame,
            text="🔴 Iniciar Monitor en Vivo",
            bg=COLORS["primary"],
            fg="white",
            font=FONTS["body_bold"],
            relief=tk.FLAT,
            padx=10,
            pady=8,
            cursor="hand2",
            command=self._toggle_stream
        )
        self.btn_stream.pack(fill=tk.X, pady=(0, 8))

        btn_record = tk.Button(
            control_frame,
            text="⚡ Capturar Ráfaga (1.5 s)",
            bg=COLORS["accent_blue"],
            fg="white",
            font=FONTS["body_bold"],
            relief=tk.FLAT,
            padx=10,
            pady=8,
            cursor="hand2",
            command=self._record_burst
        )
        btn_record.pack(fill=tk.X, pady=(0, 8))

        btn_add = tk.Button(
            control_frame,
            text="➕ Guardar en Experimento",
            bg=COLORS["success"],
            fg="white",
            font=FONTS["body_bold"],
            relief=tk.FLAT,
            padx=10,
            pady=8,
            cursor="hand2",
            command=self._add_to_experiment
        )
        btn_add.pack(fill=tk.X, pady=(0, 15))

        # Separador y Generador acústico
        ttk.Separator(control_frame, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=10)
        ttk.Label(control_frame, text="Generador Acústico (Parlante):", font=FONTS["header"]).pack(anchor=tk.W, pady=(0, 5))

        btn_tone = ttk.Button(control_frame, text="🔊 Tono Senoidal (440 Hz)", command=self._play_tone_440)
        btn_tone.pack(fill=tk.X, pady=(0, 5))

        btn_sweep = ttk.Button(control_frame, text="🔊 Barrido (200-1200 Hz)", command=self._play_sweep)
        btn_sweep.pack(fill=tk.X, pady=(0, 5))

        btn_stop_snd = ttk.Button(control_frame, text="⏹ Detener Audio", command=stop_audio)
        btn_stop_snd.pack(fill=tk.X, pady=(0, 10))

        # Panel derecho: Métricas arriba y Gráficas abajo
        right_panel = ttk.Frame(self)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(5, 10), pady=10)

        # Fila de Tarjetas de Métricas
        cards_frame = ttk.Frame(right_panel)
        cards_frame.pack(fill=tk.X, pady=(0, 10))

        self.card_freq = self._create_metric_card(cards_frame, "FRECUENCIA FUNDAMENTAL (f1)", "-- Hz", COLORS["primary"])
        self.card_v = self._create_metric_card(cards_frame, "VELOCIDAD PUNTUAL (v)", "-- m/s", COLORS["success"])
        self.card_note = self._create_metric_card(cards_frame, "NOTA MUSICAL", "--", COLORS["accent_blue"])
        self.card_snr = self._create_metric_card(cards_frame, "SNR / CALIDAD", "-- dB", COLORS["secondary"])

        self.card_freq.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self.card_v.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self.card_note.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)
        self.card_snr.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=4)

        # Gráficas Matplotlib
        self.fig = Figure(figsize=(8, 6), dpi=100, facecolor="#f8fafc")
        self.fig.subplots_adjust(left=0.08, right=0.96, top=0.92, bottom=0.10, hspace=0.35)

        self.ax_time = self.fig.add_subplot(2, 1, 1)
        self.ax_time.set_title("Señal Acústica en el Tiempo (Osciloscopio)", fontsize=10, fontweight="bold", color="#1e293b")
        self.ax_time.set_xlabel("Tiempo (ms)", fontsize=8)
        self.ax_time.set_ylabel("Amplitud", fontsize=8)
        self.ax_time.set_ylim(-1.0, 1.0)
        self.ax_time.grid(True, linestyle="--", alpha=0.4)
        self.line_time, = self.ax_time.plot([], [], color="#0284c7", lw=1.2)

        self.ax_freq = self.fig.add_subplot(2, 1, 2)
        self.ax_freq.set_title("Espectro de Frecuencias (FFT)", fontsize=10, fontweight="bold", color="#1e293b")
        self.ax_freq.set_xlabel("Frecuencia (Hz)", fontsize=8)
        self.ax_freq.set_ylabel("Magnitud Normalizada", fontsize=8)
        self.ax_freq.set_xlim(50, 2000)
        self.ax_freq.set_ylim(0.0, 1.0)
        self.ax_freq.grid(True, linestyle="--", alpha=0.4)
        self.line_freq, = self.ax_freq.plot([], [], color="#e11d48", lw=1.5, label="Espectro")
        self.peak_point, = self.ax_freq.plot([], [], "o", color="#b91c1c", markersize=7, label="Resonancia f1")
        self.ax_freq.legend(loc="upper right", fontsize=8)

        self.canvas = FigureCanvasTkAgg(self.fig, master=right_panel)
        self.canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

    def _create_metric_card(self, parent, label_text, default_val, accent_color):
        card = tk.Frame(parent, bg=COLORS["bg_card"], bd=1, relief=tk.SOLID)
        lbl_title = tk.Label(card, text=label_text, font=FONTS["metric_label"], fg=COLORS["text_muted"], bg=COLORS["bg_card"])
        lbl_title.pack(anchor=tk.W, padx=8, pady=(6, 2))
        lbl_val = tk.Label(card, text=default_val, font=FONTS["metric_value"], fg=accent_color, bg=COLORS["bg_card"])
        lbl_val.pack(anchor=tk.W, padx=8, pady=(0, 6))
        card.lbl_val = lbl_val
        return card

    def _populate_audio_devices(self):
        devs = list_audio_devices()
        self.device_map = {}
        values = []
        for d in devs["inputs"]:
            label = f"[{d['id']}] {d['name'][:25]}"
            self.device_map[label] = d["id"]
            values.append(label)
        self.device_combo["values"] = values
        if values:
            self.device_combo.current(0)

    def _on_sim_toggle(self):
        is_sim = self.sim_var.get()
        L_m = self.length_var.get() / 100.0
        self.streamer.set_simulation_mode(is_sim, pipe_length_m=L_m)

    def _toggle_stream(self):
        if self.is_streaming:
            self.is_streaming = False
            self.streamer.stop()
            if self._timer_id:
                self.after_cancel(self._timer_id)
                self._timer_id = None
            self.btn_stream.config(text="🔴 Iniciar Monitor en Vivo", bg=COLORS["primary"])
        else:
            dev_label = self.device_combo.get()
            dev_id = self.device_map.get(dev_label, None)
            self._on_sim_toggle()
            self.streamer.start(device_id=dev_id)
            self.is_streaming = True
            self.btn_stream.config(text="⏹ Detener Monitor", bg=COLORS["danger"])
            self._update_realtime_loop()

    def _update_realtime_loop(self):
        if not self.is_streaming:
            return

        # Actualizar longitud para simulación si cambió
        self.streamer._sim_length_m = max(0.05, self.length_var.get() / 100.0)

        buffer = self.streamer.get_latest_buffer()
        if len(buffer) > 0:
            self._process_and_plot(buffer, is_live=True)

        self._timer_id = self.after(80, self._update_realtime_loop)

    def _record_burst(self):
        L_cm = self.length_var.get()
        L_m = L_cm / 100.0
        r_m = self.radius_var.get() / 100.0

        dev_label = self.device_combo.get()
        dev_id = self.device_map.get(dev_label, None)
        sim_len = L_m if self.sim_var.get() else None

        # Desactivar temporalmente live stream si estaba activo
        was_streaming = self.is_streaming
        if was_streaming:
            self._toggle_stream()

        self.btn_stream.config(state=tk.DISABLED)
        self.app.set_status("Grabando ráfaga acústica (1.5 segundos)... Sople o acerque el parlante...")
        self.update_idletasks()

        audio = record_burst(
            duration_sec=1.5,
            sample_rate=44100,
            device_id=dev_id,
            simulated_length_m=sim_len
        )

        self.btn_stream.config(state=tk.NORMAL)
        self.app.set_status("Ráfaga acústica capturada y procesada.")

        self._process_and_plot(audio, is_live=False)

        if was_streaming:
            self._toggle_stream()

    def _process_and_plot(self, audio: np.ndarray, is_live: bool = False):
        if len(audio) == 0:
            return

        sample_rate = 44100
        # Filtrado paso banda
        filtered = apply_bandpass_filter(audio, sample_rate, low_cutoff=80.0, high_cutoff=2500.0)
        freqs, mag, mag_db = compute_fft(filtered, sample_rate, window_type="hann")

        # Picos
        peaks = find_spectral_peaks(freqs, mag, min_freq=120.0, max_freq=1800.0)

        L_cm = self.length_var.get()
        L_m = L_cm / 100.0
        r_m = self.radius_var.get() / 100.0

        if peaks:
            f1 = peaks[0]["frequency"]
            amp = peaks[0]["amplitude"]
            snr = peaks[0]["snr_db"]
            v_point = sound_speed_from_point(L_m, f1, tube_radius_m=r_m)
            note_info = frequency_to_musical_note(f1)

            self.last_detected_freq = f1
            self.last_measured_v = v_point

            self.card_freq.lbl_val.config(text=f"{f1:.1f} Hz")
            self.card_v.lbl_val.config(text=f"{v_point:.1f} m/s")
            self.card_note.lbl_val.config(text=f"{note_info['note']} ({note_info['cents_deviation']:+.0f}c)")
            self.card_snr.lbl_val.config(text=f"{snr:.1f} dB")

            # Actualizar punto en espectro
            self.peak_point.set_data([f1], [amp])
        else:
            self.peak_point.set_data([], [])

        # Actualizar gráfica temporal (mostrar ventana de 1500 muestras ~34 ms)
        n_disp = min(1500, len(audio))
        t_ms = np.linspace(0.0, (n_disp / sample_rate) * 1000.0, n_disp)
        self.line_time.set_data(t_ms, audio[:n_disp])
        self.ax_time.set_xlim(0.0, t_ms[-1] if len(t_ms) > 0 else 30.0)

        # Actualizar gráfica espectral (50 a 1800 Hz)
        mask = (freqs >= 50) & (freqs <= 1800)
        if np.any(mask):
            self.line_freq.set_data(freqs[mask], mag[mask])
            max_m = np.max(mag[mask]) if len(mag[mask]) > 0 else 1.0
            self.ax_freq.set_ylim(0.0, max(0.2, max_m * 1.15))

        self.canvas.draw_idle()

    def _add_to_experiment(self):
        if self.last_detected_freq <= 0.0:
            messagebox.showwarning("Atención", "No hay una medición acústica válida disponible para agregar.\nRealice primero una captura.")
            return

        L_cm = self.length_var.get()
        L_m = L_cm / 100.0
        f1 = self.last_detected_freq
        v_est = self.last_measured_v

        entry = self.app.dataset.add_measurement(
            length_m=L_m,
            frequency_hz=f1,
            notes=f"Medición capturada ({L_cm:.1f} cm)"
        )
        self.app.tab_experiment.refresh_table()
        self.app.set_status(f"Punto guardado en experimento: L = {L_cm:.1f} cm, f = {f1:.1f} Hz, v = {v_est:.1f} m/s")
        messagebox.showinfo("Guardado", f"Medición agregada al Experimento:\n• Longitud L: {L_cm:.1f} cm\n• Frecuencia: {f1:.1f} Hz\n• Velocidad puntual: {v_est:.1f} m/s")

    def _play_tone_440(self):
        tone = generate_pure_tone(440.0, duration_sec=2.0)
        play_audio(tone)

    def _play_sweep(self):
        sweep = generate_frequency_sweep(200.0, 1200.0, duration_sec=3.0)
        play_audio(sweep)

    def cleanup(self):
        self.is_streaming = False
        if self._timer_id:
            self.after_cancel(self._timer_id)
        self.streamer.stop()
        stop_audio()

