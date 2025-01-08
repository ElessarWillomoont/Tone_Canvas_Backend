import numpy as np
from scipy.interpolate import interp1d

def calculate_times(frames_data, x1, dx):
    return [x1 + (frame['frame'] - 1) * dx for frame in frames_data]

def segment_nonzero_times_and_frequencies(times, frequencies):
    segments = []
    current_segment = {'times': [], 'frequencies': []}
    
    for time, frequency in zip(times, frequencies):
        if frequency > 0:
            current_segment['times'].append(time)
            current_segment['frequencies'].append(frequency)
        else:
            if current_segment['times']:
                segments.append(current_segment)
                current_segment = {'times': [], 'frequencies': []}
    
    if current_segment['times']:
        segments.append(current_segment)
    
    return segments

def interpolate_pitch_segments(segments, target_sample_rate):
    all_new_times = []
    all_interpolated_frequencies = []
    
    for segment in segments:
        times = np.array(segment['times'])
        frequencies = np.array(segment['frequencies'])
        
        interpolation_function = interp1d(times, frequencies, kind='cubic', fill_value="extrapolate")
        segment_new_times = np.arange(times[0], times[-1], 1/target_sample_rate)
        segment_interpolated_frequencies = interpolation_function(segment_new_times)
        
        all_new_times.append(segment_new_times)
        all_interpolated_frequencies.append(segment_interpolated_frequencies)
    
    return all_new_times, all_interpolated_frequencies
