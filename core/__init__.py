"""
Paquete Core del Laboratorio de Acústica
"""

from .physics_engine import (
    theoretical_sound_speed,
    fundamental_frequency,
    sound_speed_from_point,
    helmholtz_frequency,
    analyze_resonance_series,
    estimate_water_level,
    frequency_to_musical_note,
)
from .signal_processing import (
    remove_dc_offset,
    apply_bandpass_filter,
    compute_fft,
    find_spectral_peaks,
    refine_peak_parabolic,
    calculate_signal_rms,
)
from .audio_capture import (
    list_audio_devices,
    AudioStreamer,
    record_burst,
    load_wav_file,
    save_wav_file,
)
from .audio_generator import (
    generate_pure_tone,
    generate_frequency_sweep,
    generate_white_noise,
    simulate_pipe_resonance,
    play_audio,
    stop_audio,
)
from .data_manager import ExperimentDataset

