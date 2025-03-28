import numpy as np
from scipy.interpolate import interp1d
import soundfile as sf
import json

def process_pitch_file(file_path, target_sample_rate):
    """
    Processes a Praat Pitch file, removes initial silence, performs interpolation,
    and ensures consistent sampling.
    
    Args:
        file_path (str): Path to the .Pitch file.
        target_sample_rate (int): Desired output sample rate in Hz.
    
    Returns:
        np.ndarray: Interpolated time values.
        np.ndarray: Interpolated frequency values.
    """
    from utils.file_parsing import parse_praat_pitch_file
    from utils.audio_utils import (
        calculate_times, segment_nonzero_times_and_frequencies, interpolate_pitch_segments
    )
    import numpy as np
    
    # Parse pitch file to extract frames and timing information
    frames_data, x1, dx = parse_praat_pitch_file(file_path)
    times = calculate_times(frames_data, x1, dx)
    
    # Ensure times is not empty
    if len(times) == 0:
        print("Error: No valid time data found in pitch file.")
        return np.array([]), np.array([])

    primary_frequencies = [frame['candidates'][0]['frequency'] for frame in frames_data]
    
    # Print initial values for debugging
    print(f"Initial times: {times[:10]}")
    print(f"Initial frequencies: {primary_frequencies[:10]}")
    
    # Remove leading silence (zero frequency values at the start)
    first_nonzero_index = next((i for i, f in enumerate(primary_frequencies) if f > 0), None)
    if first_nonzero_index is not None:
        times = times[first_nonzero_index:]
        primary_frequencies = primary_frequencies[first_nonzero_index:]
    
    # Normalize time axis to start from zero
    if times:
        times = [t - times[0] for t in times]

    # Segment non-zero frequency regions for better interpolation
    segments = segment_nonzero_times_and_frequencies(times, primary_frequencies)
    
    # Ensure segments are not empty
    if not segments:
        print("Warning: No valid segments found, returning empty arrays.")
        return np.array([]), np.array([])

    all_new_times, all_interpolated_frequencies = interpolate_pitch_segments(segments, target_sample_rate)
    
    # Initialize output arrays
    combined_times = []
    combined_frequencies = []
    previous_end_time = None
    
    # Process each interpolated segment and fill gaps with zero frequency
    for new_times, interpolated_frequencies in zip(all_new_times, all_interpolated_frequencies):
        if len(new_times) == 0:  # 确保 new_times 非空
            print("Warning: Encountered empty new_times, skipping this segment.")
            continue  # 跳过这个空段
        
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
