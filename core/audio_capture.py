"""
Módulo de Captura de Audio
==========================
Administra la captura de señales de audio desde micrófonos físicos o fuentes
virtuales/simuladas mediante sounddevice de manera segura y no bloqueante.
"""

from typing import List, Dict, Optional, Callable, Tuple
import threading
import queue
import numpy as np
import sounddevice as sd

from .audio_generator import simulate_pipe_resonance


def list_audio_devices() -> Dict[str, List[Dict[str, object]]]:
    """
    Retorna la lista de dispositivos de entrada (micrófonos) y salida (altavoces) disponibles.
    """
    inputs = []
    outputs = []
    try:
        devices = sd.query_devices()
        default_in, default_out = sd.default.device
        for idx, dev in enumerate(devices):
            if dev.get("max_input_channels", 0) > 0:
                inputs.append({
                    "id": idx,
                    "name": dev.get("name", f"Dispositivo {idx}"),
                    "channels": dev.get("max_input_channels"),
                    "default_samplerate": dev.get("default_samplerate", 44100.0),
                    "is_default": (idx == default_in)
                })
            if dev.get("max_output_channels", 0) > 0:
                outputs.append({
                    "id": idx,
                    "name": dev.get("name", f"Dispositivo {idx}"),
                    "channels": dev.get("max_output_channels"),
                    "default_samplerate": dev.get("default_samplerate", 44100.0),
                    "is_default": (idx == default_out)
                })
    except Exception as e:
        print(f"Error consultando dispositivos de audio: {e}")

    return {"inputs": inputs, "outputs": outputs}


class AudioStreamer:
    """
    Captura audio en tiempo real en un hilo secundario y mantiene un buffer circular
    disponible para visualización espectral y análisis en la interfaz gráfica.
    """

    def __init__(
        self,
        sample_rate: int = 44100,
        buffer_size: int = 8192,
        block_size: int = 1024,
        device_id: Optional[int] = None
    ):
        self.sample_rate = sample_rate
        self.buffer_size = buffer_size
        self.block_size = block_size
        self.device_id = device_id

        self._stream: Optional[sd.InputStream] = None
        self._is_running = False
        self._lock = threading.Lock()
        self._ring_buffer = np.zeros(self.buffer_size, dtype=np.float32)
        self._simulation_mode = False
        self._sim_length_m = 0.20
        self._sim_phase = 0.0

    @property
    def is_running(self) -> bool:
        return self._is_running

    def set_simulation_mode(self, enabled: bool, pipe_length_m: float = 0.20) -> None:
        """Habilita o deshabilita la generación de audio sintético para pruebas de laboratorio."""
        with self._lock:
            self._simulation_mode = enabled
            self._sim_length_m = pipe_length_m

    def _audio_callback(self, indata, frames, time_info, status):
        """Callback invocado por sounddevice para cada bloque de audio entrante."""
        if status:
            # Reporta sobreflujos o desbordes si ocurren
            pass

        samples = indata[:, 0]  # Canal mono
        with self._lock:
            # Desplazar buffer circular a la izquierda e insertar las nuevas muestras
            n = len(samples)
            if n >= self.buffer_size:
                self._ring_buffer[:] = samples[-self.buffer_size:]
            else:
                self._ring_buffer[:-n] = self._ring_buffer[n:]
                self._ring_buffer[-n:] = samples

    def start(self, device_id: Optional[int] = None) -> bool:
        """Inicia el flujo de audio en vivo."""
        if self._is_running:
            return True

        if device_id is not None:
            self.device_id = device_id

        try:
            self._stream = sd.InputStream(
                samplerate=self.sample_rate,
                blocksize=self.block_size,
                device=self.device_id,
                channels=1,
                dtype="float32",
                callback=self._audio_callback
            )
            self._stream.start()
            self._is_running = True
            return True
        except Exception as e:
            print(f"No se pudo iniciar el stream de micrófono real: {e}. Activando modo simulado.")
            self._simulation_mode = True
            self._is_running = True
            return False

    def stop(self) -> None:
        """Detiene el flujo de audio en vivo."""
        self._is_running = False
        if self._stream is not None:
            try:
                self._stream.stop()
                self._stream.close()
            except Exception:
                pass
            self._stream = None

    def get_latest_buffer(self) -> np.ndarray:
        """
        Retorna una copia del buffer de audio más reciente.
        En modo simulación, sintetiza un bloque resonante.
        """
        with self._lock:
            if self._simulation_mode:
                # Generar soplido sintético continuo para la longitud configurada
                f1 = 343.0 / (4.0 * self._sim_length_m)
                t = np.linspace(0.0, self.buffer_size / self.sample_rate, self.buffer_size, endpoint=False)
                wave = (
                    0.65 * np.sin(2.0 * np.pi * f1 * t + self._sim_phase) +
                    0.15 * np.sin(2.0 * np.pi * 3.0 * f1 * t) +
                    np.random.normal(0.0, 0.05, self.buffer_size)
                )
                self._sim_phase = (self._sim_phase + 2.0 * np.pi * f1 * (self.buffer_size / self.sample_rate)) % (2.0 * np.pi)
                return wave.astype(np.float32)

            return np.copy(self._ring_buffer)


def record_burst(
    duration_sec: float = 1.5,
    sample_rate: int = 44100,
    device_id: Optional[int] = None,
    simulated_length_m: Optional[float] = None
) -> np.ndarray:
    """
    Captura una ráfaga sincrónica de audio de duración fija para una medición precisa.

    Parámetros:
        duration_sec: Duración de la grabación en segundos (ej. 1.5 s).
        sample_rate: Tasa de muestreo.
        device_id: Dispositivo de entrada.
        simulated_length_m: Si se especifica, genera sonido simulado del tubo en lugar de grabar.

    Retorna:
        Arreglo 1D de muestras normalizadas [-1, 1].
    """
    if simulated_length_m is not None:
        audio, _ = simulate_pipe_resonance(
            length_m=simulated_length_m,
            duration_sec=duration_sec,
            sample_rate=sample_rate
        )
        return audio

    total_samples = int(duration_sec * sample_rate)
    try:
        recording = sd.rec(
            total_samples,
            samplerate=sample_rate,
            channels=1,
            dtype="float32",
            device=device_id
        )
        sd.wait()
        return recording.flatten()
    except Exception as e:
        print(f"Fallo en captura de micrófono: {e}. Retornando simulación de respaldo.")
        audio, _ = simulate_pipe_resonance(
            length_m=0.20,
            duration_sec=duration_sec,
            sample_rate=sample_rate
        )
        return audio

