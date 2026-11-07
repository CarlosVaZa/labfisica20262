"""
Generador de Archivos de Audio WAV de Muestra
=============================================
Crea muestras de audio acústico en data/audio_samples/
para pruebas de laboratorio sin micrófono.
"""

import os
from core.audio_capture import save_wav_file
from core.audio_generator import simulate_pipe_resonance

def generate_samples():
    out_dir = os.path.join(os.path.dirname(__file__), "data", "audio_samples")
    os.makedirs(out_dir, exist_ok=True)

    lengths = [0.12, 0.16, 0.20, 0.25, 0.30, 0.35, 0.40]
    for L in lengths:
        audio, f1 = simulate_pipe_resonance(length_m=L, sound_speed=343.0, tube_radius_m=0.015, duration_sec=2.0)
        filename = f"tubo_{int(L*100)}cm_{int(f1)}Hz.wav"
        path = os.path.join(out_dir, filename)
        save_wav_file(path, audio, sample_rate=44100)
        print(f"[+] Generado: {filename} (L={L*100:.0f} cm, f1={f1:.1f} Hz)")

if __name__ == "__main__":
    generate_samples()

