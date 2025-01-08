import os
from flask import send_file
import soundfile as sf

from utils.pitch_processing import process_pitch_file, save_interpolated_data_to_json, generate_sine_wave

def handle_get_pitch_json(files, current_index, temp_dir, corpus_dir):
    if not files:
        return "No wav files found", 404

    pitch_file = os.path.join(corpus_dir, files[current_index].replace('.wav', '.Pitch'))
    if not os.path.exists(pitch_file):
        return "No pitch file found for the current wav file", 404

    target_sample_rate = 100  # Desired sample rate for the output
    new_times, interpolated_frequencies = process_pitch_file(pitch_file, target_sample_rate)

    json_output_path = os.path.join(temp_dir, 'interpolated_pitch_data.json')
    save_interpolated_data_to_json(new_times, interpolated_frequencies, json_output_path)

    return send_file(json_output_path, as_attachment=True)

def handle_get_pitch_audio(files, current_index, temp_dir, corpus_dir):
    if not files:
        return "No wav files found", 404

    pitch_file = os.path.join(corpus_dir, files[current_index].replace('.wav', '.Pitch'))
    if not os.path.exists(pitch_file):
        return "No pitch file found for the current wav file", 404

    target_sample_rate = 44100  # Desired sample rate for the output
    new_times, interpolated_frequencies = process_pitch_file(pitch_file, target_sample_rate)

    sine_wave = generate_sine_wave(interpolated_frequencies, target_sample_rate)
    audio_output_path = os.path.join(temp_dir, 'pitch_only_audio_manually.wav')
    sf.write(audio_output_path, sine_wave, target_sample_rate)

    return send_file(audio_output_path, as_attachment=True)

