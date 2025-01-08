from flask import Flask, send_from_directory, jsonify, request, send_file
from flask_cors import CORS
import os
import soundfile as sf

from utils.pitch_processing import process_pitch_file, save_interpolated_data_to_json, generate_sine_wave
from utils.file_parsing import parse_praat_pitch_file
from utils.audio_utils import calculate_times, segment_nonzero_times_and_frequencies, interpolate_pitch_segments

app = Flask(__name__)
CORS(app)  # Enable CORS

corpus_dir = os.path.join(os.path.dirname(__file__), 'corpus')
icons_dir = os.path.join(os.path.dirname(__file__), 'icons')
temp_dir = os.path.join(os.path.dirname(__file__), 'temp')

if not os.path.exists(temp_dir):
    os.makedirs(temp_dir)

files = [f for f in os.listdir(corpus_dir) if f.endswith('.wav')]
current_index = 0

@app.route('/api/get-wav-file', methods=['GET'])
def get_wav_file():
    global current_index
    if not files:
        return "No wav files found", 404

    file_to_play = files[current_index]
    return send_from_directory(corpus_dir, file_to_play)

@app.route('/api/switch-wav-file', methods=['POST'])
def switch_wav_file():
    global current_index
    current_index = (current_index + 1) % len(files)
    return jsonify(currentIndex=current_index)

@app.route('/api/get-icon/<filename>', methods=['GET'])
def get_icon(filename):
    return send_from_directory(icons_dir, filename)

@app.route('/api/get-pitch-json', methods=['GET'])
def get_pitch_json():
    global current_index
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

@app.route('/api/get-pitch-audio', methods=['GET'])
def get_pitch_audio():
    global current_index
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

@app.route('/api/get-file-name', methods=['GET'])
def get_file_name():
    global current_index
    if not files:
        return jsonify(error="No wav files found"), 404

    file_name = files[current_index]
    return jsonify(fileName=file_name)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
