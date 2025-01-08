import numpy as np
from scipy.interpolate import interp1d
import soundfile as sf
import json

def process_pitch_file(file_path, target_sample_rate):
    from utils.file_parsing import parse_praat_pitch_file
    from utils.audio_utils import calculate_times, segment_nonzero_times_and_frequencies, interpolate_pitch_segments
    
    frames_data, x1, dx = parse_praat_pitch_file(file_path)
    times = calculate_times(frames_data, x1, dx)
    primary_frequencies = [frame['candidates'][0]['frequency'] for frame in frames_data]

    segments = segment_nonzero_times_and_frequencies(times, primary_frequencies)
    all_new_times, all_interpolated_frequencies = interpolate_pitch_segments(segments, target_sample_rate)
    
    combined_times = []
    combined_frequencies = []

    previous_end_time = None

    for new_times, interpolated_frequencies in zip(all_new_times, all_interpolated_frequencies):
        if previous_end_time is not None and new_times[0] > previous_end_time:
            zero_times = np.arange(previous_end_time, new_times[0], 1/target_sample_rate)
            combined_times.extend(zero_times)
            combined_frequencies.extend(np.zeros_like(zero_times))
        
        combined_times.extend(new_times)
        combined_frequencies.extend(interpolated_frequencies)
        previous_end_time = new_times[-1]
    
    return np.array(combined_times), np.array(combined_frequencies)

def save_interpolated_data_to_json(times, frequencies, file_path):
    data = [{'time': t, 'frequency': float(f) if f != 0 else 'NaN'} for t, f in zip(times, frequencies)]
    non_zero_frequencies = [f for f in frequencies if f > 0]
    max_frequency = max(non_zero_frequencies)
    min_frequency = min(non_zero_frequencies)
    
    json_data = {
        'max_frequency': max_frequency,
        'min_frequency': min_frequency,
        'data': data
    }
    
    with open(file_path, 'w') as json_file:
        json.dump(json_data, json_file, indent=4)

def generate_sine_wave(frequencies, sample_rate):
    frequencies = np.array(frequencies)
    t = np.arange(len(frequencies)) / sample_rate
    phase = np.cumsum(2 * np.pi * frequencies / sample_rate)
    wave = np.sin(phase)
    return wave
